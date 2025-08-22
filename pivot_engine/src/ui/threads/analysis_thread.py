"""
Worker thread for running analysis calculations with enhanced debugging
UPDATED: Completely removed M15 zone processing - Pure Pivot Confluence System
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
from calculations.confluence.pivot_confluence_engine import PivotConfluenceEngine
from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
from calculations.zones.daily_zone_calc import DailyZoneCalculator
from calculations.zones.atr_zone_calc import ATRZoneCalculator
from data.polygon_bridge import PolygonBridge
from calculations.zones.market_structure_zones import MarketStructureZoneCalculator

# Set up enhanced logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AnalysisThread(QThread):
    """Worker thread for running analysis calculations - Pure Pivot Confluence System"""
    
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
            logger.info("ANALYSIS THREAD INITIALIZATION - PIVOT CONFLUENCE SYSTEM")
            logger.info(f"Ticker: {session_data.get('ticker', 'UNKNOWN')}")
            logger.info(f"DateTime: {session_data.get('datetime', 'UNKNOWN')}")
            logger.info("="*60)
            
            self.polygon_service = PolygonService()
            self.hvn_engine = HVNEngine()
            self.confluence_calculator = HVNConfluenceCalculator()
            self.camarilla_engine = CamarillaEngine()
            self.camarilla_confluence = CamarillaConfluenceCalculator()
            self.pivot_confluence_engine = PivotConfluenceEngine()
            self.weekly_zone_calc = WeeklyZoneCalculator()
            self.daily_zone_calc = DailyZoneCalculator()
            self.atr_zone_calc = ATRZoneCalculator()
            self.market_structure_calc = MarketStructureZoneCalculator()
            
            logger.info("All calculators initialized successfully (Pivot Confluence System)")
            
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
            df.index = df.index.tz_localize('UTC')
        else:
            tz_name = str(df.index.tz)
            if 'UTC' not in tz_name and 'utc' not in tz_name:
                df.index = df.index.tz_convert('UTC')
        
        return df
        
    def run(self):
        """Run the analysis with enhanced debugging - Pure Pivot Confluence"""
        try:
            logger.info("\n" + "="*80)
            logger.info("ANALYSIS THREAD STARTING - PIVOT CONFLUENCE SYSTEM")
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
            
            # Step 4: Camarilla Pivots
            self._log_step("Step 4: Camarilla Pivots", "Starting pivot calculations")
            self.progress.emit(60, "Calculating Camarilla pivots...")
            
            camarilla_results = {}
            data_daily = pd.DataFrame()
            
            try:
                self.camarilla_engine.set_analysis_date(analysis_datetime)
                
                # Daily Camarilla (PRIMARY - used for pivot zones)
                self._log_step("Camarilla Daily", "Calculating (PRIMARY for pivot zones)...")
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
                    
                    # Weekly Camarilla (confluence source)
                    self._log_step("Camarilla Weekly", "Calculating (confluence source)...")
                    camarilla_results['weekly'] = self.camarilla_engine.calculate_from_data(
                        data_daily, 'weekly'
                    )
                    
                    # Monthly Camarilla (confluence source)
                    self._log_step("Camarilla Monthly", "Calculating (confluence source)...")
                    camarilla_results['monthly'] = self.camarilla_engine.calculate_from_data(
                        data_daily, 'monthly'
                    )
                else:
                    self._log_step("Warning", "No daily data for weekly/monthly Camarilla")
                    
            except Exception as e:
                error_msg = self._log_error("Camarilla Calculations", e)
                logger.warning("Camarilla failed, continuing with other calculations...")
            
            # Step 5: Weekly Zones
            self._log_step("Step 5: Weekly Zones", "Calculating weekly zones (confluence source)")
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
            self._log_step("Step 6: Daily Zones", "Calculating daily zones (confluence source)")
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
            self._log_step("Step 7: ATR Zones", "Calculating ATR zones (confluence source)")
            self.progress.emit(72, "Calculating ATR zones...")
            
            atr_zone_result = None
            atr_zones = []
            
            try:
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

            #Step 8: Calculate Market Structure Zones
            self._log_step("Step 7.5: Market Structure Zones", "Calculating market structure zones")
            self.progress.emit(74, "Calculating market structure zones...")

            market_structure_result = None
            market_structure_zones = []

            try:
                if 'metrics' in self.session_data and 'atr_5min' in self.session_data['metrics']:
                    atr_5min = float(self.session_data['metrics']['atr_5min'])
                else:
                    atr_5min = metrics.get('atr_5min', 0)
                
                if atr_5min > 0:
                    market_structure_result = self.market_structure_calc.calculate_zones_from_data(
                        data_5min,
                        analysis_datetime,
                        atr_5min
                    )
                    
                    if market_structure_result:
                        market_structure_zones = self.market_structure_calc.get_zones_for_confluence(
                            market_structure_result
                        )
                        
                        # Add metrics to main metrics dict
                        if 'metrics' in market_structure_result:
                            metrics.update(market_structure_result['metrics'])
                        
                        self._log_step("Market Structure Zones Complete", 
                                    f"Created {len(market_structure_zones)} zones from market structure")
                    else:
                        self._log_step("Warning", "Market structure zone calculation returned no results")
                else:
                    self._log_step("Info", "No 5-minute ATR available for market structure zones")
                    
            except Exception as e:
                error_msg = self._log_error("Market Structure Zones", e)
                logger.warning("Market structure zones failed, continuing...")
            
            # Step 9: Calculate Metrics
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
                metrics = {}
            
            # Step 10: Get Current Price
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
            
            # Step 10: Pivot Confluence Analysis (CORE SYSTEM)
            self._log_step("Step 10: Pivot Confluence Analysis", "PRIMARY CONFLUENCE SYSTEM")
            self.progress.emit(80, "Calculating pivot confluence analysis...")
            
            try:
                # Map HVN results for pivot confluence
                hvn_results_mapped = {}
                if '7day' in hvn_results and hvn_results['7day']:
                    hvn_results_mapped[7] = hvn_results['7day']
                if '14day' in hvn_results and hvn_results['14day']:
                    hvn_results_mapped[14] = hvn_results['14day']
                if '30day' in hvn_results and hvn_results['30day']:
                    hvn_results_mapped[30] = hvn_results['30day']
                
                # Get daily Camarilla pivots (PRIMARY ZONES)
                daily_camarilla = camarilla_results.get('daily')
                if not daily_camarilla:
                    self._log_step("ERROR", "No Daily Camarilla pivots found - REQUIRED for pivot system")
                    raise ValueError("Daily Camarilla pivots are REQUIRED for pivot confluence system")
                
                # Get 5min ATR for zone creation
                atr_5min = metrics.get('atr_5min', 0)
                if atr_5min <= 0:
                    self._log_step("Warning", "No 5min ATR found, using fallback")
                    atr_5min = metrics.get('daily_atr', 2.0) * 0.1  # Fallback: 10% of daily ATR
                
                # Filter camarilla_results to exclude daily (since that's our base)
                other_camarilla = {k: v for k, v in camarilla_results.items() if k != 'daily'}
                
                self._log_step("Pivot Confluence Setup", 
                             f"Base: Daily Camarilla (R6,R4,R3,S3,S4,S6), 5min ATR: {atr_5min:.4f}")
                self._log_step("Confluence Sources", 
                             f"HVN: {len(hvn_results_mapped)} timeframes, "
                             f"Other Camarilla: {len(other_camarilla)} timeframes, "
                             f"Weekly Zones: {len(weekly_zones)}, Daily Zones: {len(daily_zones)}, "
                             f"ATR Zones: {len(atr_zones)}")
                
                # Run pivot confluence calculation
                pivot_confluence_results = self.pivot_confluence_engine.calculate_confluence(
                    daily_camarilla=daily_camarilla,
                    atr_5min=atr_5min,
                    current_price=current_price,
                    hvn_results=hvn_results_mapped,
                    camarilla_results=other_camarilla,  # Weekly and Monthly only
                    weekly_zones=weekly_zones,
                    daily_zones=daily_zones,
                    atr_zones=atr_zones,
                    market_structure_zones=market_structure_zones 
                )
                
                zones_with_confluence = pivot_confluence_results.zones_with_confluence
                total_zones = len(pivot_confluence_results.pivot_zones)
                
                self._log_step("Pivot Confluence Complete", 
                             f"SUCCESS: {zones_with_confluence}/{total_zones} pivot zones have confluence")
                
                # Log individual zone results
                for zone in pivot_confluence_results.pivot_zones:
                    self._log_step(f"Zone {zone.level_name}", 
                                 f"Price: ${zone.pivot_price:.2f}, "
                                 f"Zone: ${zone.zone_low:.2f}-${zone.zone_high:.2f}, "
                                 f"Score: {zone.confluence_score:.1f}, "
                                 f"Level: L{zone.level_designation.value}")
                
            except Exception as e:
                error_msg = self._log_error("Pivot Confluence Analysis", e)
                # Create fallback
                class FallbackPivotConfluenceResults:
                    def __init__(self):
                        self.pivot_zones = []
                        self.total_confluence_sources = 0
                        self.zones_with_confluence = 0
                
                pivot_confluence_results = FallbackPivotConfluenceResults()
                logger.warning("Using fallback pivot confluence results")
            
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
                    'market_structure_zones': self._format_market_structure_zones(market_structure_result),  # NEW
                    'pivot_confluence_results': pivot_confluence_results,  # PRIMARY RESULTS
                    'zones_ranked': self._format_pivot_confluence_zones(pivot_confluence_results, current_price),
                    'raw_hvn_results': hvn_results,
                    'raw_camarilla_results': camarilla_results,
                    'raw_weekly_zones': weekly_zone_result,
                    'raw_daily_zones': daily_zone_result,
                    'raw_atr_zones': atr_zone_result,
                    'raw_market_structure': market_structure_result,  # NEW
                    'current_price': current_price
                })
    
                self._log_step("Formatting Complete", "All results formatted successfully")
                
            except Exception as e:
                error_msg = self._log_error("Results Formatting", e)
                # Still try to return partial results
            
            # Final step
            self._log_step("Analysis Complete", f"SUCCESS: Pivot confluence analysis completed for {ticker}")
            logger.info("\n" + "="*80)
            logger.info("ANALYSIS THREAD COMPLETED SUCCESSFULLY - PIVOT CONFLUENCE SYSTEM")
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
            
            # 5-minute ATR (CRITICAL for pivot zone creation)
            atr_5min = self._calculate_atr(data_5min, period=14)
            metrics['atr_5min'] = float(atr_5min)
            logger.info(f"5-minute ATR calculated: {atr_5min:.4f} (used for pivot zones)")
            
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
                logger.info(f"Calculated 2-hour ATR: {atr_2hour:.2f}")
            
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
            target_datetime = pd.Timestamp(target_datetime).tz_localize('UTC')
        else:
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

    def _format_market_structure_zones(self, zone_result: Optional[Dict]) -> str:
        """Format market structure zones for display"""
        if not zone_result:
            return "No market structure zones calculated"
        
        if hasattr(self.market_structure_calc, 'format_zones_for_display'):
            return self.market_structure_calc.format_zones_for_display(zone_result)
        
        # Fallback formatting
        output = []
        output.append(f"Market Structure Zones")
        output.append(f"5-Minute ATR: ${zone_result.get('atr_5min', 0):.2f}")
        output.append("-" * 40)
        
        for zone in zone_result.get('zones', []):
            output.append(f"{zone.get('name', 'Unknown')}: "
                        f"${zone.get('low', 0):.2f} - ${zone.get('high', 0):.2f}")
            output.append(f"  Level: ${zone.get('level', 0):.2f}")
        
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
    
    def _format_pivot_confluence_zones(self, pivot_results, current_price: float) -> str:
        """Format pivot confluence zones for display using the pivot engine's formatter"""
        if not pivot_results or not hasattr(pivot_results, 'pivot_zones'):
            return "Pivot confluence analysis could not be completed\n" + \
                   "HVN and Camarilla results are available separately"
        
        # Use the pivot confluence engine's built-in formatter
        return self.pivot_confluence_engine.format_confluence_result(pivot_results)