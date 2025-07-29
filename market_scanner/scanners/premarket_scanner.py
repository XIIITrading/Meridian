"""
Pre-market scanner implementation.
Coordinates data fetching, filtering, and scoring.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_scanner import BaseScanner
from ..data import PolygonDataFetcher, TickerManager, TickerList
from ..filters import PremarketFilter, FilterCriteria, InterestScoreWeights
from ..config import config
from ..utils.market_timing import MarketTiming

logger = logging.getLogger(__name__)

class PremarketScanner(BaseScanner):
    """
    Pre-market scanner for S&P 500 and other indices.
    Coordinates data fetching, metric calculations, and filtering.
    """
    
    def __init__(self,
                 ticker_list: TickerList = TickerList.SP500,
                 filter_criteria: Optional[FilterCriteria] = None,
                 score_weights: Optional[InterestScoreWeights] = None,
                 cache_enabled: bool = True,
                 parallel_workers: int = None):
        """Initialize the pre-market scanner."""
        # Data components
        self.ticker_list = ticker_list
        self.data_fetcher = PolygonDataFetcher(cache_enabled=cache_enabled)
        self.ticker_manager = TickerManager()
        
        # Filter components
        self.filter = PremarketFilter(
            criteria=filter_criteria,
            weights=score_weights
        )
        
        # Configuration
        self.parallel_workers = parallel_workers or config.DEFAULT_PARALLEL_WORKERS
        
        # Load tickers
        self.tickers = self.ticker_manager.get_tickers(ticker_list)
        logger.info(f"Loaded {len(self.tickers)} {ticker_list.value} tickers")
        
        # Cache for storing fetched data
        self.data_cache = {}
    
    def run_scan(self, 
                scan_time: Optional[datetime] = None,
                lookback_days: int = None,
                progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """Run the complete pre-market scan."""
        if scan_time is None:
            scan_time = datetime.now(timezone.utc)
        else:
            # Ensure timezone aware
            if scan_time.tzinfo is None:
                scan_time = scan_time.replace(tzinfo=timezone.utc)
        
        lookback_days = lookback_days or config.DEFAULT_LOOKBACK_DAYS
        
        logger.info(f"Starting pre-market scan at {scan_time}")
        
        # Determine market dates
        market_dates = self._get_market_dates(scan_time, lookback_days)
        
        # Fetch data for all tickers
        market_data = self._fetch_all_ticker_data(
            market_dates=market_dates,
            scan_time=scan_time,
            progress_callback=progress_callback
        )
        
        if market_data.empty:
            logger.warning("No market data fetched")
            return pd.DataFrame()
        
        logger.info(f"Fetched data for {len(market_data)} tickers")
        
        # Apply filters and calculate scores
        filtered_data = self.filter.apply_filters(market_data)
        
        # Rank by interest score
        ranked_data = self.filter.rank_by_interest(filtered_data)
        
        # Add scan metadata
        ranked_data['scan_time'] = scan_time
        ranked_data['ticker_list'] = self.ticker_list.value
        
        logger.info(f"Scan complete: {len(ranked_data)} stocks passed filters")
        
        return ranked_data
    
    def _get_market_dates(self, scan_time: datetime, lookback_days: int) -> Dict[str, datetime]:
        """Determine relevant market dates for data fetching."""
        # For historical data (ATR calculation)
        history_end = scan_time.replace(hour=0, minute=0, second=0, microsecond=0)
        history_start = history_end - timedelta(days=lookback_days + 5)  # Extra days for weekends
        
        # For pre-market data (4:00 AM to scan time)
        premarket_date = scan_time.date()
        premarket_start = datetime.combine(
            premarket_date, 
            time(config.PREMARKET_START_HOUR, config.PREMARKET_START_MINUTE, 0)
        ).replace(tzinfo=timezone.utc)
        
        return {
            'history_start': history_start,
            'history_end': history_end,
            'premarket_start': premarket_start,
            'premarket_end': scan_time
        }
    
    def _fetch_all_ticker_data(self,
                              market_dates: Dict[str, datetime],
                              scan_time: datetime,
                              progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """Fetch data for all tickers in parallel."""
        all_data = []
        failed_tickers = []
        
        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(
                    self._fetch_single_ticker_data,
                    ticker,
                    market_dates,
                    scan_time
                ): ticker
                for ticker in self.tickers
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                completed += 1
                
                try:
                    ticker_data = future.result()
                    if ticker_data is not None:
                        all_data.append(ticker_data)
                except Exception as e:
                    logger.error(f"Failed to fetch data for {ticker}: {e}")
                    failed_tickers.append(ticker)
                
                # Progress callback
                if progress_callback:
                    progress_callback(completed, len(self.tickers), ticker)
                
                # Log progress every 50 tickers
                if completed % 50 == 0:
                    logger.info(f"Progress: {completed}/{len(self.tickers)} tickers processed")
        
        if failed_tickers:
            logger.warning(f"Failed to fetch data for {len(failed_tickers)} tickers: {failed_tickers[:10]}...")
        
        # Combine all data into DataFrame
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()
    
    def _fetch_single_ticker_data(self,
                                 ticker: str,
                                 market_dates: Dict[str, datetime],
                                 scan_time: datetime) -> Optional[Dict]:
        """Fetch and calculate all required data for a single ticker."""
        try:
            # Fetch historical data for ATR and average volume
            historical_df = self.data_fetcher.fetch_historical(
                ticker,
                market_dates['history_start'],
                market_dates['history_end']
            )
            
            if historical_df.empty:
                return None
            
            # Calculate metrics from historical data
            atr = self._calculate_atr(historical_df, period=14)
            avg_daily_volume = self._calculate_avg_volume(historical_df, period=20)
            current_price = historical_df['close'].iloc[-1]
            
            # Skip if price outside range (early filter)
            if current_price < self.filter.criteria.min_price or \
               current_price > self.filter.criteria.max_price:
                return None
            
            # Fetch pre-market data
            premarket_volume = self._fetch_premarket_volume(
                ticker,
                market_dates['premarket_start'],
                market_dates['premarket_end']
            )
            
            # Calculate derived metrics
            dollar_volume = current_price * avg_daily_volume
            atr_percent = (atr / current_price) * 100 if current_price > 0 else 0
            
            # Return data dictionary
            return {
                'ticker': ticker,
                'price': current_price,
                'avg_daily_volume': avg_daily_volume,
                'premarket_volume': premarket_volume,
                'dollar_volume': dollar_volume,
                'atr': atr,
                'atr_percent': atr_percent,
                'fetch_time': scan_time
            }
            
        except Exception as e:
            logger.debug(f"Error fetching data for {ticker}: {e}")
            return None
    
    def _fetch_premarket_volume(self,
                               ticker: str,
                               start_time: datetime,
                               end_time: datetime) -> float:
        """Fetch pre-market volume for a ticker."""
        try:
            # Fetch 1-minute bars for pre-market session
            df = self.data_fetcher.fetch_intraday(
                ticker,
                start_time,
                end_time,
                timeframe='1min'
            )
            
            if df.empty:
                return 0.0
            
            # Sum volume for pre-market period
            return float(df['volume'].sum())
            
        except Exception as e:
            logger.debug(f"Failed to fetch pre-market data for {ticker}: {e}")
            return 0.0
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range (ATR)."""
        if len(df) < period:
            return 0.0
        
        # Calculate True Range
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        
        df['true_range'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        
        # Calculate ATR using EMA
        atr = df['true_range'].ewm(span=period, adjust=False).mean()
        
        return float(atr.iloc[-1]) if not atr.empty else 0.0
    
    def _calculate_avg_volume(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate average daily volume."""
        if len(df) < period:
            # Use all available data if less than period
            return float(df['volume'].mean()) if not df.empty else 0.0
        
        # Use most recent N days
        return float(df['volume'].tail(period).mean())
    
    def get_summary_stats(self, scan_results: pd.DataFrame) -> Dict:
        """Generate summary statistics for scan results."""
        if scan_results.empty:
            return {
                'ticker_list': self.ticker_list.value,
                'total_scanned': len(self.tickers),
                'passed_filters': 0,
                'pass_rate': '0.0%',
                'top_sectors': []
            }
        
        summary = {
            'ticker_list': self.ticker_list.value,
            'total_scanned': len(self.tickers),
            'passed_filters': len(scan_results),
            'pass_rate': f"{(len(scan_results) / len(self.tickers) * 100):.1f}%",
            'avg_interest_score': scan_results['interest_score'].mean(),
            'interest_score_std': scan_results['interest_score'].std(),
            'top_5_tickers': scan_results.head(5)['ticker'].tolist(),
            'avg_premarket_volume': scan_results['premarket_volume'].mean(),
            'avg_atr_percent': scan_results['atr_percent'].mean()
        }
        
        return summary
    
    def export_results(self, scan_results: pd.DataFrame, output_path: str):
        """Export scan results to file."""
        # Prepare display columns
        display_columns = [
            'rank', 'ticker', 'price', 'interest_score',
            'premarket_volume', 'avg_daily_volume',
            'atr', 'atr_percent', 'dollar_volume'
        ]
        
        # Format numeric columns
        formatted_df = scan_results[display_columns].copy()
        formatted_df['price'] = formatted_df['price'].apply(lambda x: f"${x:.2f}")
        formatted_df['premarket_volume'] = formatted_df['premarket_volume'].apply(lambda x: f"{x:,.0f}")
        formatted_df['avg_daily_volume'] = formatted_df['avg_daily_volume'].apply(lambda x: f"{x:,.0f}")
        formatted_df['atr'] = formatted_df['atr'].apply(lambda x: f"${x:.2f}")
        formatted_df['atr_percent'] = formatted_df['atr_percent'].apply(lambda x: f"{x:.2f}%")
        formatted_df['dollar_volume'] = formatted_df['dollar_volume'].apply(lambda x: f"${x:,.0f}")
        
        # Save to CSV
        formatted_df.to_csv(output_path, index=False)
        logger.info(f"Results exported to {output_path}")