"""
Worker thread for running analysis calculations with enhanced debugging
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import traceback

# Add parent directory to path for calculations imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import asyncio

from services.polygon_service import PolygonService
from calculations.volume.hvn_engine import HVNEngine
from calculations.confluence.hvn_confluence import HVNConfluenceCalculator
from calculations.pivots.camarilla_engine import CamarillaEngine
from calculations.confluence.camarilla_confluence import CamarillaConfluenceCalculator
from calculations.confluence.confluence_engine import ConfluenceEngine
from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
from calculations.zones.daily_zone_calc import DailyZoneCalculator
from calculations.zones.atr_zone_calc import ATRZoneCalculator
from data.polygon_bridge import PolygonBridge

# Set up enhanced logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure DEBUG level


class AnalysisThread(QThread):
    """Worker thread for running analysis calculations with enhanced debugging"""
    
    # Signals
    progress = pyqtSignal(int, str)  # Progress percentage and message
    finished = pyqtSignal(dict)      # Analysis results
    error = pyqtSignal(str)          # Error message
    debug_message = pyqtSignal(str)  # Debug messages for UI status bar
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__()
        self.session_data = session_data
        self.current_step = "Initialization"
        
        # Initialize with error handling
        try:
            logger.info("="*60)
            logger.info("ANALYSIS THREAD INITIALIZATION")
            logger.info(f"Ticker: {session_data.get('ticker', 'UNKNOWN')}")
            logger.info(f"DateTime: {session_data.get('datetime', 'UNKNOWN')}")
            logger.info("="*60)
            
            self.polygon_service = PolygonService()
            self.hvn_engine = HVNEngine()
            self.confluence_calculator = HVNConfluenceCalculator()
            self.camarilla_engine = CamarillaEngine()
            self.camarilla_confluence = CamarillaConfluenceCalculator()
            self.confluence_engine = ConfluenceEngine()
            self.weekly_zone_calc = WeeklyZoneCalculator()
            self.daily_zone_calc = DailyZoneCalculator()
            self.atr_zone_calc = ATRZoneCalculator()
            
            logger.info("All calculators initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize calculators: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _log_step(self, step: str, details: str = ""):
        """Log and emit debug message for each step"""
        self.current_step = step
        message = f"[{datetime.now().strftime('%H:%M:%S')}] {step}"
        if details:
            message += f": {details}"
        
        logger.info(message)
        self.debug_message.emit(message)
    
    def _log_error(self, step: str, error: Exception):
        """Log detailed error information"""
        error_msg = f"ERROR in {step}: {str(error)}"
        logger.error("="*60)
        logger.error(f"STEP FAILED: {step}")
        logger.error(f"Error Type: {type(error).__name__}")
        logger.error(f"Error Message: {str(error)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error("="*60)
        return error_msg
    
    def _ensure_utc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure DataFrame has UTC timezone"""
        if df.empty:
            return df
            
        df = df.copy()
        
        if df.index.tz is None:
            # If timezone-naive, localize to UTC
            df.index = df.index.tz_localize('UTC')
        else:
            # Check if timezone is UTC (works for both pytz and datetime.timezone)
            tz_name = str(df.index.tz)
            if 'UTC' not in tz_name and 'utc' not in tz_name:
                # If has timezone but not UTC, convert to UTC
                df.index = df.index.tz_convert('UTC')
        
        return df
        
    def run(self):
        """Run the analysis with enhanced debugging"""
        try:
            logger.info("\n" + "="*80)
            logger.info("ANALYSIS THREAD STARTING")
            logger.info("="*80 + "\n")
            
            # Step 0: Initial setup
            self._log_step("Initial Setup", "Extracting session data")
            self.progress.emit(5, "Initializing analysis...")
            
            ticker = self.session_data['ticker']
            analysis_datetime = self.session_data['datetime']
            
            self._log_step("Session Data", f"Ticker: {ticker}, DateTime: {analysis_datetime}")
            
            # Initialize results
            results = {
                'status': 'in_progress',
                'timestamp': datetime.now(),
                'ticker': ticker
            }
            
            # Step 1: Fetch market data
            self._log_step("Step 1: Fetch Market Data", f"Starting fetch for {ticker}")
            self.progress.emit(15, f"Fetching market data for {ticker}...")
            
            try:
                # Create event loop for async operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create PolygonBridge
                bridge = PolygonBridge()
                
                # Test connection
                connected, msg = bridge.test_connection()
                if not connected:
                    raise ConnectionError(f"Polygon connection failed: {msg}")
                
                self._log_step("Polygon Connection", "Successfully connected")
                
            except Exception as e:
                error_msg = self._log_error("Polygon Connection", e)
                self.error.emit(error_msg)
                return
            
            # Step 2: Fetch historical data
            self._log_step("Step 2: Fetch Historical Data", "Fetching 5-minute bars")
            self.progress.emit(25, "Fetching volume profile data...")
            
            try:
                end_date = analysis_datetime.date()
                start_date = end_date - timedelta(days=120)
                
                self._log_step("Date Range", f"{start_date} to {end_date}")
                
                data_5min = bridge.get_historical_bars(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe='5min'
                )
                
                if data_5min.empty:
                    raise ValueError(f"No 5-minute data returned for {ticker}")
                
                # Ensure UTC timezone
                data_5min = self._ensure_utc(data_5min)
                
                # Ensure timestamp column exists
                if 'timestamp' not in data_5min.columns:
                    data_5min['timestamp'] = data_5min.index
                
                self._log_step("Data Fetched", f"{len(data_5min)} 5-minute bars")
                
            except Exception as e:
                error_msg = self._log_error("Historical Data Fetch", e)
                self.error.emit(error_msg)
                return
            
            # Step 3: HVN Analysis
            self._log_step("Step 3: HVN Analysis", "Starting volume profile calculations")
            self.progress.emit(40, "Calculating 7-day HVN zones...")
            
            hvn_results = {}
            
            try:
                # 7-day HVN
                self._log_step("HVN 7-Day", "Calculating...")
                hvn_results['7day'] = self.hvn_engine.analyze_timeframe(
                    data_5min, 
                    timeframe_days=7,
                    include_pre=True,
                    include_post=True
                )
                peaks_7d = len(hvn_results['7day'].peaks) if hvn_results['7day'] else 0
                self._log_step("HVN 7-Day Complete", f"Found {peaks_7d} peaks")
                
                self.progress.emit(50, "Calculating 14-day HVN zones...")
                
                # 14-day HVN
                self._log_step("HVN 14-Day", "Calculating...")
                hvn_results['14day'] = self.hvn_engine.analyze_timeframe(
                    data_5min,
                    timeframe_days=14,
                    include_pre=True,
                    include_post=True
                )
                peaks_14d = len(hvn_results['14day'].peaks) if hvn_results['14day'] else 0
                self._log_step("HVN 14-Day Complete", f"Found {peaks_14d} peaks")
                
                self.progress.emit(55, "Calculating 30-day HVN zones...")
                
                # 30-day HVN
                self._log_step("HVN 30-Day", "Calculating...")
                hvn_results['30day'] = self.hvn_engine.analyze_timeframe(
                    data_5min,
                    timeframe_days=30,
                    include_pre=True,
                    include_post=True
                )
                peaks_30d = len(hvn_results['30day'].peaks) if hvn_results['30day'] else 0
                self._log_step("HVN 30-Day Complete", f"Found {peaks_30d} peaks")
                
            except Exception as e:
                error_msg = self._log_error("HVN Calculations", e)
                logger.warning("HVN failed, continuing with other calculations...")
                # Don't return - continue with other calculations
            
            # Step 4: Camarilla Pivots
            self._log_step("Step 4: Camarilla Pivots", "Starting pivot calculations")
            self.progress.emit(60, "Calculating Camarilla pivots...")
            
            camarilla_results = {}
            data_daily = pd.DataFrame()  # Initialize for later use
            
            try:
                self.camarilla_engine.set_analysis_date(analysis_datetime)
                
                # Daily Camarilla
                self._log_step("Camarilla Daily", "Calculating...")
                camarilla_results['daily'] = self.camarilla_engine.calculate_from_data(
                    data_5min, 'daily'
                )
                
                # Fetch daily data for weekly/monthly
                self._log_step("Fetching Daily Data", "For weekly/monthly Camarilla")
                data_daily = bridge.get_historical_bars(
                    ticker=ticker,
                    start_date=end_date - timedelta(days=60),
                    end_date=end_date,
                    timeframe='day'
                )
                
                if not data_daily.empty:
                    data_daily = self._ensure_utc(data_daily)
                    self._log_step("Daily Data", f"Fetched {len(data_daily)} daily bars")
                    
                    # Weekly Camarilla
                    self._log_step("Camarilla Weekly", "Calculating...")
                    camarilla_results['weekly'] = self.camarilla_engine.calculate_from_data(
                        data_daily, 'weekly'
                    )
                    
                    # Monthly Camarilla
                    self._log_step("Camarilla Monthly", "Calculating...")
                    camarilla_results['monthly'] = self.camarilla_engine.calculate_from_data(
                        data_daily, 'monthly'
                    )
                else:
                    self._log_step("Warning", "No daily data for weekly/monthly Camarilla")
                    
            except Exception as e:
                error_msg = self._log_error("Camarilla Calculations", e)
                logger.warning("Camarilla failed, continuing with other calculations...")
            
            # Step 5: Weekly Zones
            self._log_step("Step 5: Weekly Zones", "Calculating weekly zones")
            self.progress.emit(65, "Calculating weekly zones...")
            
            weekly_zone_result = None
            weekly_zones = []
            
            try:
                if ('weekly' in self.session_data and 
                    'price_levels' in self.session_data['weekly']):
                    
                    levels = self.session_data['weekly']['price_levels']
                    valid_levels = [l for l in levels if l and float(l) > 0]
                    self._log_step("Weekly Levels", f"Found {len(valid_levels)} valid levels")
                    
                    if 'metrics' in self.session_data:
                        self.session_data['metrics'].update(results.get('metrics', {}))
                    
                    weekly_zone_result = self.weekly_zone_calc.calculate_zones_from_session(
                        self.session_data,
                        ticker,
                        analysis_datetime
                    )
                    
                    if weekly_zone_result:
                        weekly_zones = self.weekly_zone_calc.get_zones_for_confluence(weekly_zone_result)
                        self._log_step("Weekly Zones Complete", 
                                     f"Created {len(weekly_zones)} zones, "
                                     f"2-hour ATR: ${weekly_zone_result.get('atr_2hour', 0):.2f}")
                    else:
                        self._log_step("Warning", "Weekly zone calculation returned no results")
                else:
                    self._log_step("Info", "No weekly levels available")
                    
            except Exception as e:
                error_msg = self._log_error("Weekly Zones", e)
                logger.warning("Weekly zones failed, continuing...")
            
            # Step 6: Daily Zones
            self._log_step("Step 6: Daily Zones", "Calculating daily zones")
            self.progress.emit(68, "Calculating daily zones...")
            
            daily_zone_result = None
            daily_zones = []
            
            try:
                if ('daily' in self.session_data and 
                    'price_levels' in self.session_data['daily']):
                    
                    levels = self.session_data['daily']['price_levels']
                    valid_levels = [l for l in levels if l and float(l) > 0]
                    self._log_step("Daily Levels", f"Found {len(valid_levels)} valid levels")
                    
                    if 'metrics' in self.session_data:
                        self.session_data['metrics'].update(results.get('metrics', {}))
                    
                    daily_zone_result = self.daily_zone_calc.calculate_zones_from_session(
                        self.session_data,
                        ticker,
                        analysis_datetime
                    )
                    
                    if daily_zone_result:
                        daily_zones = self.daily_zone_calc.get_zones_for_confluence(daily_zone_result)
                        self._log_step("Daily Zones Complete", 
                                     f"Created {len(daily_zones)} zones, "
                                     f"15-minute ATR: ${daily_zone_result.get('atr_15min', 0):.2f}")
                    else:
                        self._log_step("Warning", "Daily zone calculation returned no results")
                else:
                    self._log_step("Info", "No daily levels available")
                    
            except Exception as e:
                error_msg = self._log_error("Daily Zones", e)
                logger.warning("Daily zones failed, continuing...")
            
            # Step 7: ATR Zones
            self._log_step("Step 7: ATR Zones", "Calculating ATR zones")
            self.progress.emit(72, "Calculating ATR zones...")
            
            atr_zone_result = None
            atr_zones = []
            
            try:
                # Log what metrics we have
                if 'metrics' in self.session_data:
                    metrics = self.session_data['metrics']
                    self._log_step("Available Metrics", 
                                 f"daily_atr: {metrics.get('daily_atr', 'N/A')}, "
                                 f"atr_5min: {metrics.get('atr_5min', 'N/A')}")
                
                if ('metrics' in self.session_data and 
                    'daily_atr' in self.session_data['metrics'] and
                    'atr_5min' in self.session_data['metrics']):
                    
                    if 'metrics' in results:
                        self.session_data['metrics'].update(results['metrics'])
                    
                    atr_zone_result = self.atr_zone_calc.calculate_zones_from_session(
                        self.session_data,
                        ticker,
                        analysis_datetime
                    )
                    
                    if atr_zone_result:
                        atr_zones = self.atr_zone_calc.get_zones_for_confluence(atr_zone_result)
                        self._log_step("ATR Zones Complete", 
                                     f"Created {len(atr_zones)} zones, "
                                     f"5-min ATR: ${atr_zone_result.get('atr_5min', 0):.2f}, "
                                     f"Daily ATR: ${atr_zone_result.get('daily_atr', 0):.2f}")
                    else:
                        self._log_step("Warning", "ATR zone calculation returned no results")
                else:
                    self._log_step("Info", "Required metrics not available for ATR zones")
                    
            except Exception as e:
                error_msg = self._log_error("ATR Zones", e)
                logger.warning("ATR zones failed, continuing...")
            
            # Step 8: Calculate Metrics
            self._log_step("Step 8: Calculate Metrics", "Calculating ATR and price metrics")
            self.progress.emit(75, "Calculating metrics...")
            
            try:
                metrics = self._calculate_metrics(data_5min, data_daily, analysis_datetime)
                
                # Add zone ATRs if calculated
                if weekly_zone_result and 'atr_2hour' in weekly_zone_result:
                    metrics['atr_2hour'] = float(weekly_zone_result['atr_2hour'])
                if daily_zone_result and 'atr_15min' in daily_zone_result:
                    metrics['atr_15min'] = float(daily_zone_result['atr_15min'])
                
                self._log_step("Metrics Complete", f"Calculated {len(metrics)} metrics")
                
            except Exception as e:
                error_msg = self._log_error("Metrics Calculation", e)
                metrics = {}  # Use empty metrics if failed
            
            # Step 9: Get Current Price
            self._log_step("Step 9: Current Price", "Determining current price")
            
            current_price = float(self.session_data.get('pre_market_price', 0))
            if current_price == 0:
                if 'metrics' in self.session_data and 'current_price' in self.session_data['metrics']:
                    current_price = float(self.session_data['metrics']['current_price'])
            if current_price == 0:
                current_price = float(data_5min['close'].iloc[-1])
            
            self._log_step("Current Price", f"${current_price:.2f}")
            metrics['analysis_current_price'] = current_price
            
            # Add HVN peak counts to metrics
            metrics['hvn_7day_count'] = len(hvn_results.get('7day', {}).peaks) if hvn_results.get('7day') else 0
            metrics['hvn_14day_count'] = len(hvn_results.get('14day', {}).peaks) if hvn_results.get('14day') else 0
            metrics['hvn_30day_count'] = len(hvn_results.get('30day', {}).peaks) if hvn_results.get('30day') else 0
            
            # Step 10: Confluence Analysis
            self._log_step("Step 10: Confluence Analysis", "Calculating confluence scores")
            self.progress.emit(80, "Calculating confluence analysis...")
            
            try:
                # Map HVN results
                hvn_results_mapped = {}
                if '7day' in hvn_results and hvn_results['7day']:
                    hvn_results_mapped[7] = hvn_results['7day']
                if '14day' in hvn_results and hvn_results['14day']:
                    hvn_results_mapped[14] = hvn_results['14day']
                if '30day' in hvn_results and hvn_results['30day']:
                    hvn_results_mapped[30] = hvn_results['30day']
                
                # Get M15 zones
                m15_zones = self.session_data.get('zones', [])
                self._log_step("M15 Zones", f"Found {len(m15_zones)} zones")
                
                # Get daily levels
                daily_levels = []
                if 'daily' in self.session_data and 'price_levels' in self.session_data['daily']:
                    daily_levels = [float(level) for level in self.session_data['daily']['price_levels'] 
                                  if level and float(level) > 0]
                
                self._log_step("Confluence Inputs", 
                             f"M15: {len(m15_zones)}, HVN: {len(hvn_results_mapped)}, "
                             f"Weekly: {len(weekly_zones)}, Daily: {len(daily_zones)}, "
                             f"ATR: {len(atr_zones)}, Daily Levels: {len(daily_levels)}")
                
                # Run confluence calculation
                confluence_results = self.confluence_engine.calculate_confluence(
                    m15_zones=m15_zones,
                    hvn_results=hvn_results_mapped,
                    camarilla_results=camarilla_results,
                    daily_levels=daily_levels,
                    weekly_zones=weekly_zones,
                    daily_zones=daily_zones,
                    atr_zones=atr_zones,
                    metrics=metrics
                )
                
                zones_with_confluence = confluence_results.zones_with_confluence if hasattr(confluence_results, 'zones_with_confluence') else 0
                total_zones = len(confluence_results.zone_scores) if hasattr(confluence_results, 'zone_scores') else 0
                
                self._log_step("Confluence Complete", 
                             f"{zones_with_confluence}/{total_zones} zones have confluence")
                
            except Exception as e:
                error_msg = self._log_error("Confluence Analysis", e)
                # Create fallback
                class FallbackConfluenceResults:
                    def __init__(self):
                        self.zone_scores = []
                        self.total_inputs_checked = 0
                        self.zones_with_confluence = 0
                
                confluence_results = FallbackConfluenceResults()
                logger.warning("Using fallback confluence results")
            
            # Step 11: Format Results
            self._log_step("Step 11: Format Results", "Formatting all results for display")
            self.progress.emit(95, "Formatting results...")
            
            # Store current price for formatters
            self._current_price = current_price
            
            try:
                # Format all results
                results.update({
                    'status': 'completed',
                    'metrics': metrics,
                    'hvn_7day': self._format_hvn_result(hvn_results.get('7day')),
                    'hvn_14day': self._format_hvn_result(hvn_results.get('14day')),
                    'hvn_30day': self._format_hvn_result(hvn_results.get('30day')),
                    'cam_daily': self._format_camarilla_result(camarilla_results.get('daily')),
                    'cam_weekly': self._format_camarilla_result(camarilla_results.get('weekly')),
                    'cam_monthly': self._format_camarilla_result(camarilla_results.get('monthly')),
                    'weekly_zones': self._format_weekly_zones(weekly_zone_result),
                    'daily_zones': self._format_daily_zones(daily_zone_result),
                    'atr_zones': self._format_atr_zones(atr_zone_result),
                    'zones_ranked': self._format_confluence_zones(confluence_results, current_price),
                    'confluence_results': confluence_results,
                    'raw_hvn_results': hvn_results,
                    'raw_camarilla_results': camarilla_results,
                    'raw_weekly_zones': weekly_zone_result,
                    'raw_daily_zones': daily_zone_result,
                    'raw_atr_zones': atr_zone_result,
                    'current_price': current_price
                })
                
                self._log_step("Formatting Complete", "All results formatted")
                
            except Exception as e:
                error_msg = self._log_error("Results Formatting", e)
                # Still try to return partial results
            
            # Final step
            self._log_step("Analysis Complete", f"Successfully completed for {ticker}")
            logger.info("\n" + "="*80)
            logger.info("ANALYSIS THREAD COMPLETED SUCCESSFULLY")
            logger.info("="*80 + "\n")
            
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            logger.error("\n" + "="*80)
            logger.error("ANALYSIS THREAD FAILED")
            logger.error(f"Final error: {str(e)}")
            logger.error(f"Last step: {self.current_step}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error("="*80 + "\n")
            
            self.error.emit(f"Analysis failed at {self.current_step}: {str(e)}")
    
    def _calculate_metrics(self, data_5min, data_daily, analysis_datetime):
        """Calculate ATR and price metrics"""
        metrics = {}
        
        try:
            # Ensure data is UTC
            data_5min = self._ensure_utc(data_5min)
            if not data_daily.empty:
                data_daily = self._ensure_utc(data_daily)
            
            # Ensure analysis_datetime is UTC
            if analysis_datetime.tzinfo is None:
                analysis_datetime = pd.Timestamp(analysis_datetime).tz_localize('UTC')
            else:
                analysis_datetime = pd.Timestamp(analysis_datetime).tz_convert('UTC')
            
            # 5-minute ATR
            atr_5min = self._calculate_atr(data_5min, period=14)
            metrics['atr_5min'] = float(atr_5min)
            
            # 10-minute ATR (resample)
            data_10min = data_5min.resample('10min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            atr_10min = self._calculate_atr(data_10min, period=14)
            metrics['atr_10min'] = float(atr_10min)
            
            # 15-minute ATR (resample)
            data_15min = data_5min.resample('15min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            atr_15min = self._calculate_atr(data_15min, period=14)
            metrics['atr_15min'] = float(atr_15min)
            
            # 2-hour ATR (resample)
            data_2hour = data_5min.resample('2H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            if len(data_2hour) >= 14:
                atr_2hour = self._calculate_atr(data_2hour, period=14)
                metrics['atr_2hour'] = float(atr_2hour)
                logger.info(f"Calculated 2-hour ATR in metrics: {atr_2hour:.2f}")
            
            # Daily ATR
            if not data_daily.empty:
                daily_atr = self._calculate_atr(data_daily, period=14)
                metrics['daily_atr'] = float(daily_atr)
            else:
                metrics['daily_atr'] = 0.0
            
            # Get current price
            current_price = self._get_price_at_datetime(data_5min, analysis_datetime)
            metrics['current_price'] = float(current_price)
            
            # Calculate ATR bands
            metrics['atr_high'] = metrics['current_price'] + metrics.get('daily_atr', 0)
            metrics['atr_low'] = metrics['current_price'] - metrics.get('daily_atr', 0)
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise
        
        return metrics
    
    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        if len(data) < period:
            return 0.0
        
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.0
    
    def _get_price_at_datetime(self, data, target_datetime):
        """Get price at specific datetime"""
        # Ensure target datetime is timezone-aware in UTC
        if target_datetime.tzinfo is None:
            # If naive, assume it's UTC and localize
            target_datetime = pd.Timestamp(target_datetime).tz_localize('UTC')
        else:
            # If already timezone-aware, convert to UTC
            target_datetime = pd.Timestamp(target_datetime).tz_convert('UTC')
        
        # Now both data.index and target_datetime are in UTC
        if target_datetime in data.index:
            return float(data.loc[target_datetime, 'close'])
        
        # Find nearest
        time_diffs = abs(data.index - target_datetime)
        nearest_idx = time_diffs.argmin()
        return float(data.iloc[nearest_idx]['close'])
    
    def _format_hvn_result(self, result) -> str:
        """Format HVN result for display with enhanced information"""
        if not result or not result.peaks:
            return "No significant volume peaks found"
        
        # Get current price if available
        current_price = getattr(self, '_current_price', 0)
        if current_price == 0:
            current_price = float(self.session_data.get('pre_market_price', 0))
        
        output = []
        output.append(f"Price Range: ${result.price_range[0]:.2f} - ${result.price_range[1]:.2f}")
        output.append(f"Data Points: {result.data_points:,} bars")
        output.append(f"Peaks Found: {len(result.peaks)}")
        
        if current_price > 0:
            output.append(f"Current Price: ${current_price:.2f}")
        
        output.append("\nTop Volume Peaks:")
        output.append("Rank  Price      Volume%   Distance")
        output.append("-" * 40)
        
        for peak in result.peaks[:5]:  # Show top 5
            distance_pct = 0
            direction = ""
            if current_price > 0:
                distance = peak.price - current_price
                distance_pct = abs(distance) / current_price * 100
                direction = "^" if distance > 0 else "v"
            
            output.append(
                f"#{peak.rank:<4} ${peak.price:<9.2f} {peak.volume_percent:<8.2f}% "
                f"{distance_pct:>6.2f}% {direction}"
            )
        
        # Add support/resistance zones
        if current_price > 0:
            output.append("\nKey Zones:")
            
            # Find nearest support (below current price)
            support_peaks = [p for p in result.peaks if p.price < current_price]
            if support_peaks:
                nearest_support = max(support_peaks, key=lambda p: p.price)
                output.append(f"  Support: ${nearest_support.price:.2f} ({nearest_support.volume_percent:.1f}% volume)")
            
            # Find nearest resistance (above current price)
            resistance_peaks = [p for p in result.peaks if p.price > current_price]
            if resistance_peaks:
                nearest_resistance = min(resistance_peaks, key=lambda p: p.price)
                output.append(f"  Resistance: ${nearest_resistance.price:.2f} ({nearest_resistance.volume_percent:.1f}% volume)")
        
        return "\n".join(output)
    
    def _format_camarilla_result(self, result) -> str:
        """Format Camarilla result for display"""
        if not result:
            return "No Camarilla levels calculated"
        
        output = []
        output.append(f"Pivot: ${result.central_pivot:.2f}")
        output.append(f"Range Type: {result.range_type}")
        output.append("\nResistance Levels:")
        
        # Find R3, R4, R6 levels
        for pivot in result.pivots:
            if pivot.level_name in ['R6', 'R4', 'R3']:
                output.append(f"{pivot.level_name}: ${pivot.price:.2f}")
        
        output.append("\nSupport Levels:")
        
        # Find S3, S4, S6 levels
        for pivot in result.pivots:
            if pivot.level_name in ['S3', 'S4', 'S6']:
                output.append(f"{pivot.level_name}: ${pivot.price:.2f}")
        
        return "\n".join(output)
    
    def _format_weekly_zones(self, zone_result: Optional[Dict]) -> str:
        """Format weekly zones for display"""
        if not zone_result:
            return "No weekly zones calculated (weekly levels required)"
        
        # Use the weekly zone calculator's formatter if available
        if hasattr(self.weekly_zone_calc, 'format_zones_for_display'):
            return self.weekly_zone_calc.format_zones_for_display(zone_result)
        
        # Fallback formatting
        output = []
        output.append(f"Weekly Zones Analysis")
        output.append(f"2-Hour ATR: ${zone_result.get('atr_2hour', 0):.2f}")
        output.append("-" * 40)
        
        for zone in zone_result.get('all_zones', []):
            output.append(f"{zone['name']}: ${zone['low']:.2f} - ${zone['high']:.2f}")
            output.append(f"  Center: ${zone['level']:.2f}")
            output.append(f"  Size: ${zone['zone_size']:.2f}")
        
        return "\n".join(output)
    
    def _format_daily_zones(self, zone_result: Optional[Dict]) -> str:
        """Format daily zones for display"""
        if not zone_result:
            return "No daily zones calculated (daily levels required)"
        
        # Use the daily zone calculator's formatter if available
        if hasattr(self.daily_zone_calc, 'format_zones_for_display'):
            return self.daily_zone_calc.format_zones_for_display(zone_result)
        
        # Fallback formatting
        output = []
        output.append(f"Daily Zones Analysis")
        output.append(f"15-Minute ATR: ${zone_result.get('atr_15min', 0):.2f}")
        output.append("-" * 40)
        
        for zone in zone_result.get('all_zones', []):
            output.append(f"{zone['name']}: ${zone['low']:.2f} - ${zone['high']:.2f}")
            output.append(f"  Center: ${zone['level']:.2f}")
            output.append(f"  Size: ${zone['zone_size']:.2f}")
        
        return "\n".join(output)
    
    def _format_atr_zones(self, zone_result: Optional[Dict]) -> str:
        """Format ATR zones for display"""
        if not zone_result:
            return "No ATR zones calculated (requires metrics)"
        
        # Use the ATR zone calculator's formatter if available
        if hasattr(self.atr_zone_calc, 'format_zones_for_display'):
            return self.atr_zone_calc.format_zones_for_display(zone_result)
        
        # Fallback formatting
        output = []
        output.append(f"ATR Zones Analysis")
        output.append(f"5-Minute ATR: ${zone_result.get('atr_5min', 0):.2f}")
        output.append(f"Daily ATR: ${zone_result.get('daily_atr', 0):.2f}")
        output.append("-" * 40)
        
        for zone in zone_result.get('all_zones', []):
            output.append(f"{zone['name']}: ${zone['low']:.2f} - ${zone['high']:.2f}")
            output.append(f"  Center: ${zone['level']:.2f}")
            output.append(f"  Size: ${zone['zone_size']:.2f}")
        
        return "\n".join(output)
    
    def _format_confluence_zones(self, confluence_results, current_price: float) -> str:
        """Format confluence zones for display using the confluence engine's formatter"""
        if not confluence_results or not hasattr(confluence_results, 'zone_scores'):
            return "Confluence analysis could not be completed\n" + \
                   "HVN and Camarilla results are available separately"
        
        # Use the confluence engine's built-in formatter
        return self.confluence_engine.format_confluence_result(confluence_results, current_price)