"""
Camarilla pivot calculator engine
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
    Camarilla pivot point calculator
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
        # Add more holidays as needed
    ]
    
    def __init__(self, analysis_date: Optional[datetime] = None):
        """Initialize with optional analysis date for daily calculations"""
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
    
    def calculate_from_data(self, data: pd.DataFrame, timeframe: str) -> CamarillaResult:
        """
        Calculate Camarilla pivots from OHLC data
        
        Args:
            data: DataFrame with OHLC data (intraday data for daily calculations)
            timeframe: Timeframe string ('daily', 'weekly', 'monthly')
                - 'daily': Uses prior trading day 08:00-23:59 UTC
                - 'weekly': Uses trailing 5 trading days
                - 'monthly': Uses trailing 30 trading days
            
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
        
        # Handle daily timeframe with specific time range
        if timeframe == 'daily':
            if self.analysis_date is None:
                raise ValueError("Analysis date must be set for daily calculations")
            
            # Ensure analysis_date is timezone-aware in UTC
            if self.analysis_date.tzinfo is None:
                analysis_date = pd.Timestamp(self.analysis_date).tz_localize('UTC')
            else:
                analysis_date = pd.Timestamp(self.analysis_date).tz_convert('UTC')
            
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
            
            # Calculate high, low, close for the period
            high = float(period_data['high'].max())
            low = float(period_data['low'].min())
            close = float(period_data.iloc[-1]['close'])  # Last close of the period
            
        else:
            # For weekly and monthly, use trailing days approach
            if timeframe == 'weekly':
                lookback = 5
            elif timeframe == 'monthly':
                lookback = 30
            else:
                raise ValueError(f"Invalid timeframe: {timeframe}")
            
            # Ensure we have enough data
            if len(data) < lookback:
                return None
            
            # Get the relevant period data
            period_data = data.tail(lookback)
            
            # Calculate high, low, close for the period
            high = float(period_data['high'].max())
            low = float(period_data['low'].min())
            close = float(period_data.iloc[-1]['close'])  # Use most recent close
        
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