"""
Polygon service layer for market data operations
Integrates with Polygon.io API for data fetching and HVN calculations
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time
from decimal import Decimal
import pandas as pd
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from data.polygon_bridge import PolygonBridge
from calculations.volume.hvn_engine import HVNEngine, TimeframeResult
from calculations.volume.volume_profile import VolumeProfile
from calculations.confluence.hvn_confluence import HVNConfluenceCalculator

logger = logging.getLogger(__name__)


class PolygonDataWorker(QThread):
    """Worker thread for polygon data operations"""
    
    # Signals
    progress = pyqtSignal(int, str)  # progress percentage, message
    data_ready = pyqtSignal(dict)    # results
    error = pyqtSignal(str)          # error message
    
    def __init__(self, operation: str, params: Dict[str, Any]):
        super().__init__()
        self.operation = operation
        self.params = params
        self.bridge = PolygonBridge()
        self.hvn_engine = HVNEngine(levels=100)
        
    def run(self):
        """Execute the requested operation"""
        try:
            if self.operation == 'fetch_and_calculate':
                self._fetch_and_calculate()
            elif self.operation == 'fetch_atr_data':
                self._fetch_atr_data()
            elif self.operation == 'fetch_hvn_analysis':
                self._fetch_hvn_analysis()
        except Exception as e:
            logger.error(f"Worker error in {self.operation}: {str(e)}")
            self.error.emit(str(e))

    def _fetch_and_calculate(self):
        """Fetch all data and calculate metrics"""
        ticker = self.params['ticker']
        session_datetime = self.params['datetime']
        
        self.progress.emit(10, f"Fetching data for {ticker}...")
        
        # Everything is in UTC - no timezone conversions needed
        market_open_utc = time(14, 30)  # 9:30 AM ET in UTC
        session_time = session_datetime.time()
        is_pre_market = session_time < market_open_utc
        
        # Calculate date ranges
        session_date = session_datetime.date()
        end_date = session_date
        start_date = end_date - timedelta(days=30)  # Get 30 days for calculations
        
        results = {
            'ticker': ticker,
            'datetime': session_datetime,
            'metrics': {}
        }
        
        try:
            # Fetch 5-minute data
            self.progress.emit(20, "Fetching 5-minute data...")
            data_5min = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe='5min'  # Native 5-minute bars
            )
            
            # Fetch 15-minute data DIRECTLY from Polygon
            self.progress.emit(30, "Fetching 15-minute data...")
            data_15min = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe='15min'  # Native 15-minute bars
            )
            
            # Calculate 5-minute ATR
            if not data_5min.empty:
                if data_5min.index.tz is not None:
                    data_5min.index = data_5min.index.tz_localize(None)
                
                atr_5min = self._calculate_atr(data_5min, period=14)
                results['metrics']['atr_5min'] = float(atr_5min)
                
                # Get current price at specified datetime
                current_price = self._get_price_at_datetime(data_5min, session_datetime)
                results['metrics']['current_price'] = float(current_price)
                
                # Get open price if after market open
                if not is_pre_market:
                    open_price = self._get_session_open_price(data_5min, session_date)
                    results['metrics']['open_price'] = float(open_price)
                else:
                    results['metrics']['pre_market_price'] = float(current_price)
            
            # Calculate 15-minute ATR from native 15-min bars
            if not data_15min.empty:
                if data_15min.index.tz is not None:
                    data_15min.index = data_15min.index.tz_localize(None)
                
                atr_15min = self._calculate_atr(data_15min, period=14)
                results['metrics']['atr_15min'] = float(atr_15min)
            
            # For 2-hour ATR
            self.progress.emit(40, "Calculating 2-hour ATR...")
            if not data_15min.empty:
                # Resample 15-min to 2-hour (8 bars = 2 hours)
                data_2hour = self._resample_data(data_15min, '2H')
                if len(data_2hour) >= 14:
                    atr_2hour = self._calculate_atr(data_2hour, period=14)
                    results['metrics']['atr_2hour'] = float(atr_2hour)
                    logger.info(f"Calculated 2-hour ATR: {atr_2hour:.2f}")
                else:
                    # Not enough 2-hour bars, use what we have
                    atr_2hour = self._calculate_atr(data_2hour, period=min(14, len(data_2hour)-1))
                    results['metrics']['atr_2hour'] = float(atr_2hour)
            
            # Fetch daily data for daily ATR
            self.progress.emit(70, "Fetching daily data...")
            start_date_daily = end_date - timedelta(days=30)
            data_daily = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date_daily,
                end_date=end_date,
                timeframe='day'  # Native daily bars
            )
            
            if not data_daily.empty:
                if data_daily.index.tz is not None:
                    data_daily.index = data_daily.index.tz_localize(None)
                
                # Calculate daily ATR (14 periods)
                daily_atr = self._calculate_atr(data_daily, period=14)
                results['metrics']['daily_atr'] = float(daily_atr)
                
                # Calculate ATR bands
                base_price = results['metrics'].get('pre_market_price', 
                            results['metrics'].get('current_price', 0))
                
                if base_price > 0 and daily_atr > 0:
                    results['metrics']['atr_high'] = base_price + float(daily_atr)
                    results['metrics']['atr_low'] = base_price - float(daily_atr)
            
            # Store data for HVN analysis
            results['data_5min'] = data_5min
            results['data_15min'] = data_15min  # Store native 15-min data
            results['data_daily'] = data_daily
            
            self.progress.emit(100, "Data fetch complete!")
            self.data_ready.emit(results)
            
        except Exception as e:
            logger.error(f"Error in fetch_and_calculate: {str(e)}")
            self.error.emit(f"Failed to fetch data: {str(e)}")
    
    def _fetch_hvn_analysis(self):
        """Perform HVN analysis on multiple timeframes"""
        ticker = self.params['ticker']
        session_date = self.params['datetime'].date()
        
        self.progress.emit(10, f"Starting HVN analysis for {ticker}...")
        
        try:
            # Fetch required data (120 days for longest timeframe)
            end_date = session_date
            start_date = end_date - timedelta(days=120)
            
            self.progress.emit(20, "Fetching historical data...")
            data = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe='5min'
            )
            
            if data.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # Strip timezone info if present
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            
            # Run HVN analysis for each timeframe
            results = {
                'ticker': ticker,
                'hvn_results': {}
            }
            
            # 7-day analysis
            self.progress.emit(40, "Analyzing 7-day volume profile...")
            results['hvn_results']['7day'] = self.hvn_engine.analyze_timeframe(
                data, 
                timeframe_days=7,
                include_pre=True,
                include_post=True
            )
            
            # 14-day analysis (new addition for UI)
            self.progress.emit(55, "Analyzing 14-day volume profile...")
            results['hvn_results']['14day'] = self.hvn_engine.analyze_timeframe(
                data,
                timeframe_days=14,
                include_pre=True,
                include_post=True
            )
            
            # 30-day analysis
            self.progress.emit(70, "Analyzing 30-day volume profile...")
            results['hvn_results']['30day'] = self.hvn_engine.analyze_timeframe(
                data,
                timeframe_days=30,
                include_pre=True,
                include_post=True
            )
            
            # Calculate confluence if we have multiple timeframes
            self.progress.emit(85, "Calculating confluence zones...")
            
            # Get current price
            current_price = float(data['close'].iloc[-1])
            
            # Prepare results for confluence calculator
            confluence_input = {}
            
            # Map to expected timeframe keys for confluence calculator
            if results['hvn_results'].get('7day'):
                confluence_input[15] = results['hvn_results']['7day']
            if results['hvn_results'].get('14day'):
                confluence_input[60] = results['hvn_results']['14day']  
            if results['hvn_results'].get('30day'):
                confluence_input[120] = results['hvn_results']['30day']
            
            # Calculate confluence
            confluence_calc = HVNConfluenceCalculator()
            confluence_analysis = confluence_calc.calculate(
                results=confluence_input,
                current_price=current_price,
                max_zones=10
            )
            
            results['confluence_analysis'] = confluence_analysis
            results['current_price'] = current_price
            
            self.progress.emit(100, "HVN analysis complete!")
            self.data_ready.emit(results)
            
        except Exception as e:
            logger.error(f"Error in HVN analysis: {str(e)}")
            self.error.emit(f"HVN analysis failed: {str(e)}")
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(data) < period:
            return 0.0
        
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.0
    
    def _resample_data(self, data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data to different timeframe"""
        return data.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    
    def _get_price_at_datetime(self, data: pd.DataFrame, target_datetime: datetime) -> float:
        """Get price at specific datetime - all in UTC"""
        # Ensure data index has no timezone info for simple comparison
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # Ensure target datetime has no timezone info
        if hasattr(target_datetime, 'tzinfo') and target_datetime.tzinfo is not None:
            target_datetime = target_datetime.replace(tzinfo=None)
        
        if target_datetime in data.index:
            return float(data.loc[target_datetime, 'close'])
        
        # Find nearest available price
        time_diffs = abs(data.index - target_datetime)
        nearest_idx = time_diffs.argmin()
        return float(data.iloc[nearest_idx]['close'])

    def _get_session_open_price(self, data: pd.DataFrame, session_date) -> float:
        """Get opening price for regular trading session"""
        # Filter for session date
        session_data = data[data.index.date == session_date]
        
        if session_data.empty:
            return 0.0
        
        # Find first bar after 14:30 UTC (9:30 AM ET)
        market_open_utc = time(14, 30)
        
        for idx, row in session_data.iterrows():
            if idx.time() >= market_open_utc:
                return float(row['open'])
        
        # If no regular hours data, return first available
        return float(session_data.iloc[0]['open'])
    
    def _get_session_open_price(self, data: pd.DataFrame, session_date) -> float:
        """Get opening price for regular trading session"""
        # Filter for session date
        session_data = data[data.index.date == session_date]
        
        if session_data.empty:
            return 0.0
        
        # Find first bar after 14:30 UTC (9:30 AM ET)
        market_open_utc = time(14, 30)
        
        for idx, row in session_data.iterrows():
            if idx.time() >= market_open_utc:
                return float(row['open'])
        
        # If no regular hours data, return first available
        return float(session_data.iloc[0]['open'])


class PolygonService(QObject):
    """Service class for Polygon.io data operations with Qt signal support"""
    
    # Signals for UI feedback
    data_fetch_started = pyqtSignal(str)  # ticker
    data_fetch_completed = pyqtSignal(dict)  # results
    data_fetch_failed = pyqtSignal(str)  # error message
    
    hvn_analysis_started = pyqtSignal(str)  # ticker
    hvn_analysis_completed = pyqtSignal(dict)  # results
    hvn_analysis_failed = pyqtSignal(str)  # error message
    
    progress_update = pyqtSignal(int, str)  # percentage, message
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self._cached_data = {}
    
    def fetch_market_data(self, ticker: str, session_datetime: datetime):
        """
        Fetch market data and calculate ATR metrics
        
        Args:
            ticker: Stock ticker
            session_datetime: Analysis datetime (in UTC)
        """
        if self.worker and self.worker.isRunning():
            logger.warning("Previous operation still running")
            return
        
        self.data_fetch_started.emit(ticker)
        
        # Create worker thread
        self.worker = PolygonDataWorker(
            operation='fetch_and_calculate',
            params={
                'ticker': ticker.upper(),
                'datetime': session_datetime
            }
        )
        
        # Connect signals
        self.worker.progress.connect(self.progress_update.emit)
        self.worker.data_ready.connect(self._on_data_ready)
        self.worker.error.connect(self._on_data_error)
        
        # Start worker
        self.worker.start()
    
    def fetch_hvn_analysis(self, ticker: str, session_datetime: datetime):
        """
        Perform HVN analysis for multiple timeframes
        
        Args:
            ticker: Stock ticker
            session_datetime: Analysis datetime (in UTC)
        """
        if self.worker and self.worker.isRunning():
            logger.warning("Previous operation still running")
            return
        
        self.hvn_analysis_started.emit(ticker)
        
        # Create worker for HVN analysis
        self.worker = PolygonDataWorker(
            operation='fetch_hvn_analysis',
            params={
                'ticker': ticker.upper(),
                'datetime': session_datetime
            }
        )
        
        # Connect signals
        self.worker.progress.connect(self.progress_update.emit)
        self.worker.data_ready.connect(self._on_hvn_ready)
        self.worker.error.connect(self._on_hvn_error)
        
        # Start worker
        self.worker.start()
    
    def _on_data_ready(self, results: dict):
        """Handle successful data fetch"""
        # Cache the data
        ticker = results.get('ticker')
        if ticker:
            self._cached_data[ticker] = results
        
        self.data_fetch_completed.emit(results)
    
    def _on_data_error(self, error_msg: str):
        """Handle data fetch error"""
        self.data_fetch_failed.emit(error_msg)
    
    def _on_hvn_ready(self, results: dict):
        """Handle successful HVN analysis"""
        self.hvn_analysis_completed.emit(results)
    
    def _on_hvn_error(self, error_msg: str):
        """Handle HVN analysis error"""
        self.hvn_analysis_failed.emit(error_msg)
    
    def get_cached_data(self, ticker: str) -> Optional[dict]:
        """Get cached data for ticker if available"""
        return self._cached_data.get(ticker.upper())
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cached_data.clear()