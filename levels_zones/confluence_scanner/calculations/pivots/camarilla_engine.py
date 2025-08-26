# calculations/pivots/camarilla_engine.py - Updated for your PolygonClient

"""
Camarilla pivot calculator engine - adapted for confluence_scanner PolygonClient
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
    Camarilla pivot point calculator - adapted for confluence_scanner
    """
    
    # US market holidays
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
        Initialize with optional Polygon client
        
        Args:
            polygon_client: PolygonClient instance from data.polygon_client
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
        Fetch data using the confluence_scanner's PolygonClient
        
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
        
        # Determine date range and timeframe string for fetch_bars
        if timeframe == 'daily':
            # Get last 10 trading days for daily pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(days=20)).strftime('%Y-%m-%d')
            tf_string = '1day'
            
        elif timeframe == 'weekly':
            # Get last 8 weeks of data for weekly pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(weeks=12)).strftime('%Y-%m-%d')
            tf_string = '1week'
            
        elif timeframe == 'monthly':
            # Get last 6 months of data for monthly pivots
            end_date = analysis_date.strftime('%Y-%m-%d')
            start_date = (analysis_date - timedelta(days=200)).strftime('%Y-%m-%d')
            tf_string = '1month'
            
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        # Use the PolygonClient's fetch_bars method
        try:
            df = self.polygon_client.fetch_bars(
                symbol=ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe=tf_string
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            # If specific timeframe not supported, try alternatives
            if timeframe == 'weekly' and 'Invalid timeframe' in str(e):
                # Fall back to daily bars and resample
                df = self.polygon_client.fetch_bars(ticker, start_date, end_date, '1day')
                if df is not None and not df.empty:
                    # Resample to weekly
                    weekly = df.resample('W').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    return weekly
            
            elif timeframe == 'monthly' and 'Invalid timeframe' in str(e):
                # Fall back to daily bars and resample
                df = self.polygon_client.fetch_bars(ticker, start_date, end_date, '1day')
                if df is not None and not df.empty:
                    # Resample to monthly
                    monthly = df.resample('M').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    return monthly
            
            raise RuntimeError(f"Failed to fetch data: {e}")
    
    def calculate_from_data(self, data: pd.DataFrame, timeframe: str, 
                          analysis_date: Optional[datetime] = None) -> CamarillaResult:
        """
        Calculate Camarilla pivots from OHLC data
        
        Args:
            data: DataFrame with OHLC data
            timeframe: Timeframe string ('daily', 'weekly', 'monthly')
            analysis_date: Analysis date for daily calculations
            
        Returns:
            CamarillaResult with calculated pivots
        """
        if data.empty:
            return None
        
        # Use analysis_date if provided, otherwise use instance variable
        if analysis_date is None:
            analysis_date = self.analysis_date
        
        # For daily timeframe, use the prior trading day's data
        if timeframe == 'daily':
            if analysis_date is None:
                # Use the last bar if no analysis date
                bar = data.iloc[-1]
            else:
                # Find the bar for the prior trading day
                analysis_pd = pd.Timestamp(analysis_date)
                if analysis_pd.tzinfo is None:
                    analysis_pd = analysis_pd.tz_localize('UTC')
                
                prior_day = self._get_prior_trading_day(analysis_pd)
                
                # Find data for prior day
                if data.index.tz is not None:
                    mask = data.index.date == prior_day.date()
                else:
                    mask = pd.to_datetime(data.index).date == prior_day.date()
                
                prior_data = data[mask]
                
                if prior_data.empty:
                    # Use most recent bar if specific date not found
                    bar = data.iloc[-1]
                else:
                    bar = prior_data.iloc[-1]
                    
            high = float(bar['high'])
            low = float(bar['low'])
            close = float(bar['close'])
            
        else:
            # For weekly and monthly, use the most recent complete bar
            bar = data.iloc[-1]
            high = float(bar['high'])
            low = float(bar['low'])
            close = float(bar['close'])
        
        # Calculate range
        range_val = high - low
        
        if range_val == 0:
            return None  # Can't calculate pivots with zero range
        
        # Calculate pivot point (central pivot)
        pivot = (high + low + close) / 3
        
        # Calculate Camarilla levels
        pivots = []
        
        # Resistance levels
        r1 = close + range_val * 1.1 / 12
        r2 = close + range_val * 1.1 / 6
        r3 = close + range_val * 1.1 / 4
        r4 = close + range_val * 1.1 / 2
        
        # Handle division by zero for R5
        if low != 0:
            r5 = (high / low) * close
        else:
            r5 = close * 1.1  # Fallback
            
        r6 = r5 + 1.168 * (r5 - r4) if r5 > r4 else r5 * 1.05
        
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
        Convenience method to fetch data and calculate pivots
        
        Args:
            ticker: Stock ticker symbol
            timeframe: 'daily', 'weekly', or 'monthly'
            analysis_date: Reference date for calculations
            
        Returns:
            CamarillaResult with calculated pivots
        """
        # Store analysis date if provided
        if analysis_date:
            self.analysis_date = analysis_date
            
        # Fetch aggregated data using our PolygonClient
        data = self.fetch_aggregated_data(ticker, timeframe, analysis_date)
        
        if data.empty:
            return None
        
        # Calculate pivots
        return self.calculate_from_data(data, timeframe, analysis_date)
    
    def calculate_from_existing_data(self, data: pd.DataFrame, timeframe: str) -> CamarillaResult:
        """
        Calculate pivots from already fetched data (useful when scanner already has the data)
        
        Args:
            data: DataFrame with OHLC data
            timeframe: 'daily', 'weekly', or 'monthly'
            
        Returns:
            CamarillaResult with calculated pivots
        """
        return self.calculate_from_data(data, timeframe, self.analysis_date)