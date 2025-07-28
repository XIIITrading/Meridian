# market_review/pre_market/sp500_filter/sp500_bridge.py
"""
Market Bridge - Data Coordination Layer
Fetches data from Polygon and coordinates with the market filter engine.
Handles pre-market data, ATR calculations, and derived metrics.
Supports both S&P 500 and All US Equities scanning modes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time
from typing import Dict, List, Optional, Tuple
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
import time as time_module

# Import External Components
from polygon import DataFetcher
from polygon.config import PolygonConfig

# Import Local Components
from market_review.pre_market.sp500_filter.market_filter import MarketFilter, FilterCriteria, InterestScoreWeights
from market_review.pre_market.sp500_filter.sp500_tickers import get_sp500_tickers, check_update_status
from market_review.pre_market.sp500_filter.us_equities import USEquitiesUniverse, get_us_equities

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SP500Bridge:
    """
    Bridge between Polygon data and market filter calculations.
    Coordinates data fetching, metric calculations, and filtering.
    Can operate in 'sp500' mode or 'all_equities' mode.
    """
    
    def __init__(self,
                 filter_criteria: Optional[FilterCriteria] = None,
                 score_weights: Optional[InterestScoreWeights] = None,
                 cache_enabled: bool = True,
                 parallel_workers: int = 10,
                 mode: str = 'sp500',
                 exchanges: Optional[List[str]] = None,
                 rate_limit_delay: float = 0.05):
        """
        Initialize the market bridge.
        
        Args:
            filter_criteria: Filter criteria for market filter
            score_weights: Weights for interest score calculation
            cache_enabled: Enable Polygon data caching
            parallel_workers: Number of parallel workers for data fetching
            mode: 'sp500' for S&P 500 only, 'all_equities' for all US stocks
            exchanges: List of exchanges (only used in all_equities mode)
            rate_limit_delay: Delay between API calls in seconds
        """
        # Initialize components
        try:
            self.fetcher = DataFetcher(config=PolygonConfig({'cache_enabled': cache_enabled}))
        except Exception as e:
            logger.error(f"Failed to initialize DataFetcher: {e}")
            raise
        
        # Market filter engine
        self.filter_engine = MarketFilter(
            criteria=filter_criteria,
            weights=score_weights
        )
        
        # Configuration
        self.parallel_workers = parallel_workers
        self.mode = mode
        self.rate_limit_delay = rate_limit_delay
        
        # Load tickers based on mode
        if mode == 'sp500':
            check_update_status()  # Warn if list is stale
            self.tickers = get_sp500_tickers(check_staleness=False)
            logger.info(f"Loaded {len(self.tickers)} S&P 500 tickers")
        elif mode == 'all_equities':
            # Use US Equities Universe
            self.universe = USEquitiesUniverse(exchanges=exchanges, exclude_otc=True)
            self.tickers = self.universe.get_all_tickers()
            logger.info(f"Loaded {len(self.tickers)} US equity tickers")
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'sp500' or 'all_equities'")
        
        # Cache for storing fetched data
        self.data_cache = {}
        
        # Rate limiting
        self.last_api_call_time = 0
        
    def run_morning_scan(self, 
                        scan_time: Optional[datetime] = None,
                        lookback_days: int = 14,
                        progress_callback: Optional[callable] = None,
                        max_tickers: Optional[int] = None) -> pd.DataFrame:
        """
        Run the complete morning market scan.
        
        Args:
            scan_time: Time to run scan for (default: now)
            lookback_days: Days of history for ATR calculation
            progress_callback: Optional callback for progress updates
            max_tickers: Maximum number of tickers to process (for testing)
            
        Returns:
            DataFrame with filtered and ranked results
        """
        if scan_time is None:
            scan_time = datetime.now(timezone.utc)
        else:
            # Ensure timezone aware
            if scan_time.tzinfo is None:
                scan_time = scan_time.replace(tzinfo=timezone.utc)
        
        logger.info(f"Starting morning scan at {scan_time} in {self.mode} mode")
        
        # Limit tickers if specified
        tickers_to_scan = self.tickers[:max_tickers] if max_tickers else self.tickers
        
        # Determine market dates
        market_dates = self._get_market_dates(scan_time, lookback_days)
        
        # Fetch data for all tickers
        market_data = self._fetch_all_ticker_data(
            tickers=tickers_to_scan,
            market_dates=market_dates,
            scan_time=scan_time,
            progress_callback=progress_callback
        )
        
        if market_data.empty:
            logger.warning("No market data fetched")
            return pd.DataFrame()
        
        logger.info(f"Fetched data for {len(market_data)} tickers")
        
        # Apply filters and calculate scores
        filtered_data = self.filter_engine.apply_filters(market_data)
        
        # Rank by interest score
        ranked_data = self.filter_engine.rank_by_interest(filtered_data)
        
        # Add scan metadata
        ranked_data['scan_time'] = scan_time
        ranked_data['scan_mode'] = self.mode
        
        logger.info(f"Scan complete: {len(ranked_data)} stocks passed filters")
        
        return ranked_data
    
    def _get_market_dates(self, scan_time: datetime, lookback_days: int) -> Dict[str, datetime]:
        """
        Determine relevant market dates for data fetching.
        
        Returns dict with:
            - history_start: Start of historical data for ATR
            - history_end: End of historical data
            - premarket_start: Start of pre-market session
            - premarket_end: End of pre-market session (scan time)
        """
        # For historical data (ATR calculation)
        history_end = scan_time.replace(hour=0, minute=0, second=0, microsecond=0)
        history_start = history_end - timedelta(days=lookback_days + 5)  # Extra days for weekends
        
        # For pre-market data (4:00 AM to scan time)
        premarket_date = scan_time.date()
        premarket_start = datetime.combine(
            premarket_date, 
            time(4, 0, 0)
        ).replace(tzinfo=timezone.utc)
        
        return {
            'history_start': history_start,
            'history_end': history_end,
            'premarket_start': premarket_start,
            'premarket_end': scan_time
        }
    
    def _fetch_all_ticker_data(self,
                              tickers: List[str],
                              market_dates: Dict[str, datetime],
                              scan_time: datetime,
                              progress_callback: Optional[callable] = None) -> pd.DataFrame:
        """
        Fetch data for all tickers in parallel.
        
        Args:
            tickers: List of tickers to fetch
            market_dates: Dictionary of relevant market dates
            scan_time: Current scan time
            progress_callback: Optional progress callback
            
        Returns:
            DataFrame with all ticker data and calculated metrics
        """
        all_data = []
        failed_tickers = []
        
        # Adjust parallel workers based on mode
        workers = self.parallel_workers
        if self.mode == 'all_equities':
            # Use more workers but with rate limiting
            workers = min(self.parallel_workers * 2, 50)
        
        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_ticker = {
                executor.submit(
                    self._fetch_single_ticker_data,
                    ticker,
                    market_dates,
                    scan_time
                ): ticker
                for ticker in tickers
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
                    progress_callback(completed, len(tickers), ticker)
                
                # Log progress at different intervals based on mode
                log_interval = 50 if self.mode == 'sp500' else 200
                if completed % log_interval == 0:
                    logger.info(f"Progress: {completed}/{len(tickers)} tickers processed")
        
        if failed_tickers:
            logger.warning(f"Failed to fetch data for {len(failed_tickers)} tickers")
            if len(failed_tickers) <= 20:
                logger.warning(f"Failed tickers: {failed_tickers}")
            else:
                logger.warning(f"Failed tickers (first 20): {failed_tickers[:20]}...")
        
        # Combine all data into DataFrame
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()
    
    def _fetch_single_ticker_data(self,
                                 ticker: str,
                                 market_dates: Dict[str, datetime],
                                 scan_time: datetime) -> Optional[Dict]:
        """
        Fetch and calculate all required data for a single ticker.
        
        Returns:
            Dictionary with ticker data or None if failed
        """
        # Rate limiting for all_equities mode
        if self.mode == 'all_equities' and self.rate_limit_delay > 0:
            current_time = time_module.time()
            time_since_last_call = current_time - self.last_api_call_time
            if time_since_last_call < self.rate_limit_delay:
                time_module.sleep(self.rate_limit_delay - time_since_last_call)
            self.last_api_call_time = time_module.time()
        
        try:
            # Fetch historical data for ATR and average volume
            historical_df = self._fetch_historical_data(
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
            if current_price < self.filter_engine.criteria.min_price or \
               current_price > self.filter_engine.criteria.max_price:
                return None
            
            # For all_equities mode, apply additional pre-filters to save API calls
            if self.mode == 'all_equities':
                # Skip if volume too low
                if avg_daily_volume < self.filter_engine.criteria.min_avg_volume * 0.5:
                    return None
                # Skip if ATR too low
                if atr < self.filter_engine.criteria.min_atr * 0.5:
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
    
    def _fetch_historical_data(self,
                              ticker: str,
                              start_date: datetime,
                              end_date: datetime) -> pd.DataFrame:
        """
        Fetch historical daily data for ATR and volume calculations.
        """
        try:
            df = self.fetcher.fetch_data(
                symbol=ticker,
                timeframe='1d',
                start_date=start_date,
                end_date=end_date,
                use_cache=True,
                validate=True,
                fill_gaps=True
            )
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing required columns for {ticker}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.debug(f"Failed to fetch historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def _fetch_premarket_volume(self,
                               ticker: str,
                               start_time: datetime,
                               end_time: datetime) -> float:
        """
        Fetch pre-market volume for a ticker.
        
        Returns:
            Total pre-market volume
        """
        try:
            # Fetch 1-minute bars for pre-market session
            df = self.fetcher.fetch_data(
                symbol=ticker,
                timeframe='1min',
                start_date=start_time,
                end_date=end_time,
                use_cache=True,
                validate=True
            )
            
            if df.empty:
                return 0.0
            
            # Sum volume for pre-market period
            return float(df['volume'].sum())
            
        except Exception as e:
            logger.debug(f"Failed to fetch pre-market data for {ticker}: {e}")
            return 0.0
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR).
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period (default 14)
            
        Returns:
            Current ATR value
        """
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
        """
        Calculate average daily volume.
        
        Args:
            df: DataFrame with volume data
            period: Period for average (default 20 days)
            
        Returns:
            Average daily volume
        """
        if len(df) < period:
            # Use all available data if less than period
            return float(df['volume'].mean()) if not df.empty else 0.0
        
        # Use most recent N days
        return float(df['volume'].tail(period).mean())
    
    def get_summary_stats(self, scan_results: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for scan results.
        
        Args:
            scan_results: DataFrame with scan results
            
        Returns:
            Dictionary with summary statistics
        """
        if scan_results.empty:
            return {
                'total_scanned': len(self.tickers),
                'passed_filters': 0,
                'pass_rate': '0.0%',
                'top_sectors': [],
                'scan_mode': self.mode
            }
        
        summary = {
            'total_scanned': len(self.tickers),
            'passed_filters': len(scan_results),
            'pass_rate': f"{(len(scan_results) / len(self.tickers) * 100):.1f}%",
            'avg_interest_score': scan_results['interest_score'].mean(),
            'interest_score_std': scan_results['interest_score'].std(),
            'top_5_tickers': scan_results.head(5)['ticker'].tolist(),
            'avg_premarket_volume': scan_results['premarket_volume'].mean(),
            'avg_atr_percent': scan_results['atr_percent'].mean(),
            'scan_mode': self.mode
        }
        
        return summary
    
    def export_results(self, scan_results: pd.DataFrame, output_path: str):
        """
        Export scan results to file.
        
        Args:
            scan_results: DataFrame with scan results
            output_path: Path for output file
        """
        # Prepare display columns
        display_columns = [
            'rank', 'ticker', 'price', 'interest_score',
            'premarket_volume', 'avg_daily_volume',
            'atr', 'atr_percent', 'dollar_volume'
        ]
        
        # Add scan_mode if present
        if 'scan_mode' in scan_results.columns:
            display_columns.append('scan_mode')
        
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


# Example usage
def example_scan(mode='sp500'):
    """Example of running a morning scan."""
    
    # Initialize bridge with custom criteria
    if mode == 'all_equities':
        # More restrictive criteria for all equities
        criteria = FilterCriteria(
            min_price=5.0,
            max_price=500.0,
            min_avg_volume=1_000_000,
            min_premarket_volume=500_000,
            min_premarket_volume_ratio=0.02,
            min_dollar_volume=5_000_000,
            min_atr=1.0,
            min_atr_percent=1.0
        )
        parallel_workers = 20
    else:
        # Standard criteria for S&P 500
        criteria = FilterCriteria(
            min_price=10.0,
            max_price=400.0,
            min_avg_volume=1_000_000
        )
        parallel_workers = 10
    
    bridge = SP500Bridge(
        filter_criteria=criteria,
        parallel_workers=parallel_workers,
        mode=mode,
        rate_limit_delay=0.05 if mode == 'all_equities' else 0
    )
    
    # Progress callback
    def progress(completed, total, ticker):
        interval = 10 if mode == 'sp500' else 100
        if completed % interval == 0 or completed == total:
            print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Processing {ticker}")
    
    # Run scan
    print(f"\nStarting {mode} morning scan...")
    print(f"Total tickers to scan: {len(bridge.tickers)}")
    
    if mode == 'all_equities':
        print("\n⚠️  WARNING: This will take 30-60 minutes to complete!")
        response = input("Continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Scan cancelled.")
            return
    
    results = bridge.run_morning_scan(progress_callback=progress)
    
    if not results.empty:
        print(f"\nFound {len(results)} stocks passing all filters")
        print("\nTop 10 by Interest Score:")
        print(results.head(10)[['ticker', 'price', 'interest_score', 'atr_percent']])
        
        # Get summary
        summary = bridge.get_summary_stats(results)
        print("\nScan Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Export results
        output_file = f"{mode}_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        bridge.export_results(results, output_file)
    else:
        print("No stocks passed the filters")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run market scan')
    parser.add_argument('--mode', choices=['sp500', 'all_equities'], 
                       default='sp500', help='Scanner mode')
    args = parser.parse_args()
    
    example_scan(mode=args.mode)