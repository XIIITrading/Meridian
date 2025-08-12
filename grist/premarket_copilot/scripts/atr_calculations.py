"""
ATR Calculation Script for Grist Co-Pilot
Pulls 5-min, 15-min, 2-hour, and Daily ATR values
"""

import sys
import os
from datetime import datetime, date, timedelta, time
from decimal import Decimal
import pandas as pd
import logging
from typing import Dict, Optional, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from src.data package
from src.data import PolygonBridge, TradingSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ATRCalculator:
    """
    Calculate ATR values for different timeframes
    """
    
    def __init__(self, base_url: str = "http://localhost:8200/api/v1"):
        """Initialize with Polygon Bridge"""
        self.bridge = PolygonBridge(base_url=base_url)
        
        # Market hours in UTC (9:30 AM - 4:00 PM ET)
        self.market_open_utc = time(14, 30)  # 9:30 AM ET
        self.market_close_utc = time(21, 0)  # 4:00 PM ET
        
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[Decimal]:
        """
        Calculate Average True Range (ATR) from OHLC data.
        
        Args:
            df: DataFrame with OHLC columns
            period: ATR period (default 14)
            
        Returns:
            ATR value as Decimal or None
        """
        try:
            if len(df) < period + 1:
                logger.warning(f"Insufficient data for ATR calculation: {len(df)} bars")
                return None
            
            # Calculate True Range
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate ATR (exponential moving average)
            atr = true_range.ewm(span=period, adjust=False).mean()
            
            # Return the latest ATR value
            latest_atr = atr.iloc[-1]
            return Decimal(str(round(latest_atr, 4)))
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None
    
    def filter_regular_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter dataframe to only include regular trading hours
        UTC: 14:30 - 21:00 (9:30 AM - 4:00 PM ET)
        """
        if df.empty:
            return df
        
        # Ensure timezone-naive for comparison
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Filter by time
        mask = (df.index.time >= self.market_open_utc) & (df.index.time <= self.market_close_utc)
        return df[mask]
    
    def resample_to_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample data to specified timeframe
        
        Args:
            df: Source DataFrame
            timeframe: Target timeframe ('5min', '15min', '2h', etc.)
            
        Returns:
            Resampled DataFrame
        """
        try:
            resampled = df.resample(timeframe).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling to {timeframe}: {e}")
            return pd.DataFrame()
    
    def calculate_intraday_atrs(self, 
                               symbol: str, 
                               analysis_date: date) -> Dict[str, Optional[Decimal]]:
        """
        Calculate 5-min, 15-min, and 2-hour ATRs from prior day's regular hours
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis (will use prior day's data)
            
        Returns:
            Dictionary with ATR values
        """
        results = {
            'atr_5min': None,
            'atr_15min': None,
            'atr_2hr': None
        }
        
        try:
            # Get prior trading day (skip weekends)
            prior_day = analysis_date - timedelta(days=1)
            while prior_day.weekday() > 4:  # Saturday = 5, Sunday = 6
                prior_day = prior_day - timedelta(days=1)
            
            # Need extra days for ATR calculation (14 periods)
            # For 2-hour bars, we need more days
            start_date = prior_day - timedelta(days=10)
            
            logger.info(f"Fetching 5-minute data from {start_date} to {prior_day}")
            
            # Fetch 5-minute data
            df_5min = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=prior_day.strftime('%Y-%m-%d'),
                timeframe='5min'
            )
            
            if df_5min is None or df_5min.empty:
                logger.warning(f"No 5-minute data available for {symbol}")
                return results
            
            # Filter to regular hours only
            df_regular = self.filter_regular_hours(df_5min)
            
            if df_regular.empty:
                logger.warning(f"No regular hours data for {symbol}")
                return results
            
            # Calculate 5-minute ATR
            logger.info("Calculating 5-minute ATR...")
            results['atr_5min'] = self.calculate_atr(df_regular, period=14)
            
            # Resample to 15-minute and calculate ATR
            logger.info("Calculating 15-minute ATR...")
            df_15min = self.resample_to_timeframe(df_regular, '15min')
            if not df_15min.empty:
                results['atr_15min'] = self.calculate_atr(df_15min, period=14)
            
            # Resample to 2-hour and calculate ATR
            logger.info("Calculating 2-hour ATR...")
            df_2hr = self.resample_to_timeframe(df_regular, '2h')
            if not df_2hr.empty:
                results['atr_2hr'] = self.calculate_atr(df_2hr, period=14)
            
        except Exception as e:
            logger.error(f"Error calculating intraday ATRs: {e}")
        
        return results
    
    def calculate_daily_atr(self, 
                           symbol: str, 
                           analysis_date: date,
                           period: int = 14) -> Optional[Decimal]:
        """
        Calculate Daily ATR using trailing 14 days of daily bars
        
        Args:
            symbol: Stock ticker
            analysis_date: End date for calculation
            period: ATR period (default 14)
            
        Returns:
            Daily ATR value or None
        """
        try:
            # Need extra days for ATR calculation
            start_date = analysis_date - timedelta(days=period + 10)
            
            logger.info(f"Fetching daily data from {start_date} to {analysis_date}")
            
            # Fetch daily bars
            df_daily = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=analysis_date.strftime('%Y-%m-%d'),
                timeframe='1day'
            )
            
            if df_daily is None or df_daily.empty:
                logger.warning(f"No daily data available for {symbol}")
                return None
            
            # Calculate daily ATR
            return self.calculate_atr(df_daily, period=period)
            
        except Exception as e:
            logger.error(f"Error calculating daily ATR: {e}")
            return None
    
    def get_all_atrs(self, 
                     symbol: str, 
                     analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get all ATR values for a symbol
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis (defaults to today)
            
        Returns:
            Dictionary with all ATR values and metadata
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        # Validate ticker first
        logger.info(f"Validating ticker {symbol}...")
        if not self.bridge.validate_ticker(symbol):
            return {
                'error': f"Invalid ticker: {symbol}",
                'symbol': symbol,
                'analysis_date': analysis_date
            }
        
        logger.info(f"Calculating ATRs for {symbol} on {analysis_date}")
        
        # Get intraday ATRs (from prior day's regular hours)
        intraday_atrs = self.calculate_intraday_atrs(symbol, analysis_date)
        
        # Get daily ATR
        daily_atr = self.calculate_daily_atr(symbol, analysis_date)
        
        # Compile results
        results = {
            'symbol': symbol,
            'analysis_date': analysis_date,
            'ticker_id': f"{symbol}.{analysis_date.strftime('%m%d%y')}",
            'atr_5min': intraday_atrs['atr_5min'],
            'atr_15min': intraday_atrs['atr_15min'],
            'atr_2hr': intraday_atrs['atr_2hr'],
            'daily_atr': daily_atr,
            'calculated_at': datetime.now()
        }
        
        # Log results
        logger.info("ATR Calculation Results:")
        for key, value in results.items():
            if 'atr' in key and value is not None:
                logger.info(f"  {key}: {value}")
        
        return results


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate ATR values for a ticker')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD)', 
                       default=date.today().strftime('%Y-%m-%d'))
    parser.add_argument('--api-url', help='Polygon API URL',
                       default='http://localhost:8200/api/v1')
    
    args = parser.parse_args()
    
    # Parse date
    analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    
    # Create calculator
    calculator = ATRCalculator(base_url=args.api_url)
    
    # Test connection
    connected, msg = calculator.bridge.test_connection()
    if not connected:
        logger.error(f"Failed to connect to Polygon API: {msg}")
        return 1
    
    logger.info(f"Connected to Polygon API: {msg}")
    
    # Calculate ATRs
    results = calculator.get_all_atrs(args.ticker.upper(), analysis_date)
    
    # Display results
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return 1
    
    print(f"\n📊 ATR Analysis for {results['symbol']}")
    print(f"📅 Date: {results['analysis_date']}")
    print(f"🔑 Ticker ID: {results['ticker_id']}")
    print("-" * 40)
    
    # Format ATR values
    atr_display = [
        ("5-Minute ATR", results.get('atr_5min')),
        ("15-Minute ATR", results.get('atr_15min')),
        ("2-Hour ATR", results.get('atr_2hr')),
        ("Daily ATR", results.get('daily_atr'))
    ]
    
    for label, value in atr_display:
        if value is not None:
            print(f"{label:15} : {value:>10.4f}")
        else:
            print(f"{label:15} : {'N/A':>10}")
    
    print("-" * 40)
    print(f"Calculated at: {results['calculated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())