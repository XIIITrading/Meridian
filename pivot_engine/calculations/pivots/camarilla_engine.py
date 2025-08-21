"""
Camarilla pivot calculator engine - optimized for Polygon aggregated bars
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


@dataclass
class CamarillaPivot:
    level_name: str
    price: float
    strength: int
    timeframe: str


@dataclass
class CamarillaResult:
    timeframe: str
    close: float
    high: float
    low: float
    pivots: List[CamarillaPivot]
    range_type: str
    central_pivot: float


class CamarillaEngine:
    """
    Camarilla pivot point calculator - optimized for Polygon aggregated bars
    """
    
    # US market holidays (you can expand this list)
    US_HOLIDAYS = [
        '2025-01-01',  # New Year's Day
        '2025-01-20',  # MLK Day
        '2025-02-17',  # Presidents Day
        '2025-04-18',  # Good Friday
        '2025-05-26',  # Memorial Day
        '2025-06-19',  # Juneteenth
        '2025-07-04',  # Independence Day
        '2025-09-01',  # Labor Day
        '2025-11-27',  # Thanksgiving
        '2025-12-25',  # Christmas
    ]
    
    def __init__(self, polygon_client=None, analysis_date: Optional[datetime] = None):
        """
        Initialize with optional Polygon client for fetching aggregated bars
        
        Args:
            polygon_client: Polygon REST client instance
            analysis_date: Optional analysis date for calculations
        """
        self.polygon_client = polygon_client
        self.analysis_date = analysis_date
    
    def set_analysis_date(self, analysis_date: datetime):
        """Set the analysis date for daily calculations"""
        self.analysis_date = analysis_date
    
    def _get_prior_trading_day(self, current_date: pd.Timestamp) -> pd.Timestamp:
        """Get the prior trading day, skipping weekends and holidays"""
        prior_date = current_date - timedelta(days=1)
        
        # Convert holidays to pandas timestamps
        holidays = pd.to_datetime(self.US_HOLIDAYS)
        
        # Keep going back until we find a trading day
        while prior_date.weekday() >= 5 or prior_date.normalize() in holidays:
            prior_date = prior_date - timedelta(days=1)
        
        return prior_date
    
    def fetch_aggregated_data(self, ticker: str, timeframe: str, 
                            analysis_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch pre-aggregated data from Polygon based on timeframe
        
        Args:
            ticker: Stock ticker symbol
            timeframe: 'daily', 'weekly', or 'monthly'
            analysis_date: Reference date for calculations
            
        Returns:
            DataFrame with aggregated OHLC data
        """
        if self.polygon_client is None:
            raise ValueError("Polygon client not provided")
        
        if analysis_date is None:
            analysis_date = datetime.now()
        
        # Determine date range and multiplier/timespan for Polygon API
        if timeframe == 'daily':
            # Get last 5 trading days for daily pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(days=10)).strftime('%Y-%m-%d')
            multiplier = 1
            timespan = 'day'
            
        elif timeframe == 'weekly':
            # Get last 8 weeks of data for weekly pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(weeks=8)).strftime('%Y-%m-%d')
            multiplier = 1
            timespan = 'week'
            
        elif timeframe == 'monthly':
            # Get last 6 months of data for monthly pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(days=180)).strftime('%Y-%m-%d')
            multiplier = 1
            timespan = 'month'
            
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        # Fetch data from Polygon
        try:
            aggs = self.polygon_client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=start_date,
                to=end_date,
                adjusted=True,
                sort='asc',
                limit=50000
            )
            
            # Convert to DataFrame
            data_list = []
            for agg in aggs:
                data_list.append({
                    'timestamp': pd.Timestamp(agg.timestamp, unit='ms', tz='UTC'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Polygon: {e}")
    
    def calculate_from_data(self, data: pd.DataFrame, timeframe: str) -> CamarillaResult:
        """
        Calculate Camarilla pivots from OHLC data
        
        Args:
            data: DataFrame with OHLC data (can be intraday for daily calculations or pre-aggregated)
            timeframe: Timeframe string ('daily', 'weekly', 'monthly')
            
        Returns:
            CamarillaResult with calculated pivots
        """
        if data.empty:
            return None
        
        # Ensure data is in UTC
        if data.index.tz is None:
            # If timezone-naive, localize to UTC
            data = data.copy()
            data.index = data.index.tz_localize('UTC')
        else:
            # Check if timezone is UTC (works for both pytz and datetime.timezone)
            tz_name = str(data.index.tz)
            if 'UTC' not in tz_name and 'utc' not in tz_name:
                # If has timezone but not UTC, convert to UTC
                data = data.copy()
                data.index = data.index.tz_convert('UTC')
        
        # Handle daily timeframe with specific logic for minute data
        if timeframe == 'daily':
            if self.analysis_date is None:
                raise ValueError("Analysis date must be set for daily calculations")
            
            # Ensure analysis_date is timezone-aware in UTC
            if self.analysis_date.tzinfo is None:
                analysis_date = pd.Timestamp(self.analysis_date).tz_localize('UTC')
            else:
                analysis_date = pd.Timestamp(self.analysis_date).tz_convert('UTC')
            
            # Check if we're working with intraday data (many bars per day) or daily data (one bar per day)
            daily_data_check = data[data.index.date == analysis_date.date()]
            
            if len(daily_data_check) > 1:
                # Working with intraday data - use the original complex logic
                # Get prior trading day
                prior_trading_day = self._get_prior_trading_day(analysis_date)
                
                # Define time range: 08:00 to 23:59 UTC
                start_time = prior_trading_day.replace(hour=8, minute=0, second=0, microsecond=0)
                end_time = prior_trading_day.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Filter data for the specific time range
                period_data = data[(data.index >= start_time) & (data.index <= end_time)]
                
                if period_data.empty:
                    # If no data in extended hours, try regular trading hours (13:30-20:00 UTC)
                    start_time = prior_trading_day.replace(hour=13, minute=30, second=0, microsecond=0)
                    end_time = prior_trading_day.replace(hour=20, minute=0, second=0, microsecond=0)
                    period_data = data[(data.index >= start_time) & (data.index <= end_time)]
                    
                    if period_data.empty:
                        return None
                
                # Calculate high, low, close for the period from intraday data
                high = float(period_data['high'].max())
                low = float(period_data['low'].min())
                close = float(period_data.iloc[-1]['close'])  # Last close of the period
            else:
                # Working with daily aggregated data - just use the prior day's bar
                prior_trading_day = self._get_prior_trading_day(analysis_date)
                
                # Find the bar for the prior trading day
                period_data = data[data.index.date == prior_trading_day.date()]
                if period_data.empty:
                    # If no exact match, use the most recent bar
                    period_data = data.tail(1)
                
                if period_data.empty:
                    return None
                
                # Extract OHLC values from the daily bar
                bar = period_data.iloc[-1]
                high = float(bar['high'])
                low = float(bar['low'])
                close = float(bar['close'])
            
        else:
            # For weekly and monthly with pre-aggregated data
            if timeframe == 'weekly':
                # Use the most recent complete weekly bar
                period_data = data.tail(1)
                
            elif timeframe == 'monthly':
                # Use the most recent complete monthly bar
                period_data = data.tail(1)
                
            else:
                raise ValueError(f"Invalid timeframe: {timeframe}")
            
            if period_data.empty:
                return None
            
            # Extract OHLC values from the aggregated bar
            bar = period_data.iloc[-1]
            high = float(bar['high'])
            low = float(bar['low'])
            close = float(bar['close'])
        
        # Calculate range
        range_val = high - low
        
        # Calculate pivot point (central pivot)
        pivot = (high + low + close) / 3
        
        # Calculate Camarilla levels
        pivots = []
        
        # Resistance levels
        r1 = close + range_val * 1.1 / 12
        r2 = close + range_val * 1.1 / 6
        r3 = close + range_val * 1.1 / 4
        r4 = close + range_val * 1.1 / 2
        r5 = (high / low) * close
        r6 = r5 + 1.168 * (r5 - r4)
        
        # Support levels
        s1 = close - range_val * 1.1 / 12
        s2 = close - range_val * 1.1 / 6
        s3 = close - range_val * 1.1 / 4
        s4 = close - range_val * 1.1 / 2
        s5 = close - (r5 - close)
        s6 = close - (r6 - close)
        
        # Add pivots with strength scores
        pivots.extend([
            CamarillaPivot('R6', r6, 6, timeframe),
            CamarillaPivot('R5', r5, 5, timeframe),
            CamarillaPivot('R4', r4, 4, timeframe),
            CamarillaPivot('R3', r3, 3, timeframe),
            CamarillaPivot('R2', r2, 2, timeframe),
            CamarillaPivot('R1', r1, 1, timeframe),
            CamarillaPivot('S1', s1, 1, timeframe),
            CamarillaPivot('S2', s2, 2, timeframe),
            CamarillaPivot('S3', s3, 3, timeframe),
            CamarillaPivot('S4', s4, 4, timeframe),
            CamarillaPivot('S5', s5, 5, timeframe),
            CamarillaPivot('S6', s6, 6, timeframe),
        ])
        
        # Determine range type
        if close > pivot:
            range_type = 'higher'
        elif close < pivot:
            range_type = 'lower'
        else:
            range_type = 'neutral'
        
        return CamarillaResult(
            timeframe=timeframe,
            close=close,
            high=high,
            low=low,
            pivots=pivots,
            range_type=range_type,
            central_pivot=pivot
        )
    
    def calculate_pivots(self, ticker: str, timeframe: str, 
                        analysis_date: Optional[datetime] = None) -> CamarillaResult:
        """
        Convenience method to fetch aggregated data and calculate pivots in one call
        
        Args:
            ticker: Stock ticker symbol
            timeframe: 'daily', 'weekly', or 'monthly'
            analysis_date: Reference date for calculations
            
        Returns:
            CamarillaResult with calculated pivots
        """
        # Fetch aggregated data
        data = self.fetch_aggregated_data(ticker, timeframe, analysis_date)
        
        # Calculate pivots
        return self.calculate_from_data(data, timeframe, analysis_date)


# Example usage:
"""
from polygon import RESTClient

# Initialize with your Polygon API key
polygon_client = RESTClient("YOUR_API_KEY")
camarilla_engine = CamarillaEngine(polygon_client)

# Calculate daily pivots for AAPL
daily_pivots = camarilla_engine.calculate_pivots("AAPL", "daily")

# Calculate weekly pivots for SPY
weekly_pivots = camarilla_engine.calculate_pivots("SPY", "weekly")

# Calculate monthly pivots for QQQ
monthly_pivots = camarilla_engine.calculate_pivots("QQQ", "monthly")
"""