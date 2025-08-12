"""
Worker thread for running analysis calculations with HVN integration and Confluence Engine
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

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
from data.polygon_bridge import PolygonBridge

# Set up logging
logger = logging.getLogger(__name__)


class AnalysisThread(QThread):
    """Worker thread for running analysis calculations with HVN integration and Confluence Engine"""
    
    # Signals
    progress = pyqtSignal(int, str)  # Progress percentage and message
    finished = pyqtSignal(dict)      # Analysis results
    error = pyqtSignal(str)          # Error message
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__()
        self.session_data = session_data
        self.polygon_service = PolygonService()
        self.hvn_engine = HVNEngine()
        self.confluence_calculator = HVNConfluenceCalculator()
        self.camarilla_engine = CamarillaEngine()
        self.camarilla_confluence = CamarillaConfluenceCalculator()
        self.confluence_engine = ConfluenceEngine()
        
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
        """Run the analysis in background thread"""
        try:
            self.progress.emit(10, "Starting analysis...")
            
            ticker = self.session_data['ticker']
            analysis_datetime = self.session_data['datetime']
            
            # Step 1: Fetch market data
            self.progress.emit(15, f"Fetching market data for {ticker}...")
            
            # Create a temporary event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize results
            results = {
                'status': 'in_progress',
                'timestamp': datetime.now(),
                'ticker': ticker
            }
            
            # Step 2: Get HVN analysis data
            self.progress.emit(25, "Fetching volume profile data...")
            
            # Create PolygonBridge directly since we're in a worker thread
            bridge = PolygonBridge()
            
            # Fetch data for HVN analysis
            end_date = analysis_datetime.date()
            start_date = end_date - timedelta(days=120)  # Get enough for all timeframes
            
            logger.info(f"Fetching data from {start_date} to {end_date} for HVN analysis")
            
            data_5min = bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe='5min'
            )
            
            if data_5min.empty:
                raise ValueError(f"No data returned for {ticker}")
            
            # Ensure UTC timezone
            data_5min = self._ensure_utc(data_5min)
            
            # Ensure timestamp column exists for volume profile
            if 'timestamp' not in data_5min.columns:
                data_5min['timestamp'] = data_5min.index
                logger.info("Added timestamp column to data")
            
            logger.info(f"Fetched {len(data_5min)} bars for HVN analysis")
            
            self.progress.emit(40, "Calculating 7-day HVN zones...")
            
            # Step 3: Run HVN analysis for each timeframe
            hvn_results = {}
            
            try:
                # 7-day analysis
                hvn_results['7day'] = self.hvn_engine.analyze_timeframe(
                    data_5min, 
                    timeframe_days=7,
                    include_pre=True,
                    include_post=True
                )
                logger.info(f"7-day HVN: Found {len(hvn_results['7day'].peaks)} peaks")
                
                self.progress.emit(50, "Calculating 14-day HVN zones...")
                
                # 14-day analysis
                hvn_results['14day'] = self.hvn_engine.analyze_timeframe(
                    data_5min,
                    timeframe_days=14,
                    include_pre=True,
                    include_post=True
                )
                logger.info(f"14-day HVN: Found {len(hvn_results['14day'].peaks)} peaks")
                
                self.progress.emit(55, "Calculating 30-day HVN zones...")
                
                # 30-day analysis
                hvn_results['30day'] = self.hvn_engine.analyze_timeframe(
                    data_5min,
                    timeframe_days=30,
                    include_pre=True,
                    include_post=True
                )
                logger.info(f"30-day HVN: Found {len(hvn_results['30day'].peaks)} peaks")
                
            except Exception as e:
                logger.error(f"Error in HVN calculations: {e}")
                raise
            
            self.progress.emit(60, "Calculating Camarilla pivots...")
            
            # Step 4: Calculate Camarilla pivots
            # Set the analysis date for the Camarilla engine
            self.camarilla_engine.set_analysis_date(analysis_datetime)
            
            camarilla_results = {}
            
            # For daily Camarilla, we use 5-minute data (prior trading day 08:00-23:59 UTC)
            camarilla_results['daily'] = self.camarilla_engine.calculate_from_data(
                data_5min, 'daily'  # Pass 5-minute data for daily calculations
            )
            
            # For weekly and monthly, fetch daily data
            data_daily = bridge.get_historical_bars(
                ticker=ticker,
                start_date=end_date - timedelta(days=60),  # Extra buffer for trailing calculations
                end_date=end_date,
                timeframe='day'
            )
            
            if not data_daily.empty:
                # Ensure UTC timezone
                data_daily = self._ensure_utc(data_daily)
                logger.info(f"Fetched {len(data_daily)} daily bars for weekly/monthly Camarilla")
                
                # Weekly Camarilla (uses trailing 5 days)
                camarilla_results['weekly'] = self.camarilla_engine.calculate_from_data(
                    data_daily, 'weekly'
                )
                
                # Monthly Camarilla (uses trailing 30 days)
                camarilla_results['monthly'] = self.camarilla_engine.calculate_from_data(
                    data_daily, 'monthly'
                )
            else:
                logger.warning("No daily data available for weekly/monthly Camarilla calculations")
            
            self.progress.emit(70, "Calculating ATR metrics...")
            
            # Step 5: Calculate ATR metrics
            metrics = self._calculate_metrics(data_5min, data_daily, analysis_datetime)
            
            # Get current price for reference
            current_price = float(self.session_data.get('pre_market_price', 0))
            if current_price == 0:
                if 'metrics' in self.session_data and 'current_price' in self.session_data['metrics']:
                    current_price = float(self.session_data['metrics']['current_price'])
            if current_price == 0:
                current_price = float(data_5min['close'].iloc[-1])
                logger.info(f"Using latest close price as current price: ${current_price:.2f}")
            
            # Store current price in metrics for formatter
            metrics['analysis_current_price'] = current_price
            
            # Add HVN peak counts to metrics
            metrics['hvn_7day_count'] = len(hvn_results.get('7day', {}).peaks) if hvn_results.get('7day') else 0
            metrics['hvn_14day_count'] = len(hvn_results.get('14day', {}).peaks) if hvn_results.get('14day') else 0
            metrics['hvn_30day_count'] = len(hvn_results.get('30day', {}).peaks) if hvn_results.get('30day') else 0
            
            self.progress.emit(80, "Calculating confluence analysis...")
            
            # Step 6: Run Confluence Analysis - REAL IMPLEMENTATION
            try:
                # Transform HVN results to expected format (map string keys to int keys)
                hvn_results_mapped = {}
                if '7day' in hvn_results and hvn_results['7day']:
                    hvn_results_mapped[7] = hvn_results['7day']
                if '14day' in hvn_results and hvn_results['14day']:
                    hvn_results_mapped[14] = hvn_results['14day']
                if '30day' in hvn_results and hvn_results['30day']:
                    hvn_results_mapped[30] = hvn_results['30day']
                
                # Extract M15 zones from session data
                m15_zones = self.session_data.get('zones', [])
                
                # Extract daily price levels (6 levels: 3 above, 3 below)
                daily_levels = []
                if 'daily' in self.session_data and 'price_levels' in self.session_data['daily']:
                    daily_levels = [float(level) for level in self.session_data['daily']['price_levels'] if level and float(level) > 0]
                
                # Run confluence calculation
                confluence_results = self.confluence_engine.calculate_confluence(
                    m15_zones=m15_zones,
                    hvn_results=hvn_results_mapped,
                    camarilla_results=camarilla_results,
                    daily_levels=daily_levels,
                    metrics=metrics
                )
                
                logger.info(f"Confluence analysis complete: {confluence_results.zones_with_confluence}/{len(confluence_results.zone_scores)} zones have confluence")
                
            except Exception as e:
                logger.error(f"Error in confluence calculations: {e}")
                # Fall back to placeholder if confluence fails
                class FallbackConfluenceResults:
                    def __init__(self):
                        self.zone_scores = []
                        self.total_inputs_checked = 0
                        self.zones_with_confluence = 0
                
                confluence_results = FallbackConfluenceResults()
                logger.warning("Using fallback confluence results due to error")
            
            self.progress.emit(95, "Formatting results...")
            
            # Store current price for formatters
            self._current_price = current_price
            
            # Step 7: Format all results
            results.update({
                'status': 'completed',
                'metrics': metrics,
                'hvn_7day': self._format_hvn_result(hvn_results.get('7day')),
                'hvn_14day': self._format_hvn_result(hvn_results.get('14day')),
                'hvn_30day': self._format_hvn_result(hvn_results.get('30day')),
                'cam_daily': self._format_camarilla_result(camarilla_results.get('daily')),
                'cam_weekly': self._format_camarilla_result(camarilla_results.get('weekly')),
                'cam_monthly': self._format_camarilla_result(camarilla_results.get('monthly')),
                'zones_ranked': self._format_confluence_zones(confluence_results, current_price),
                'confluence_results': confluence_results,  # Store raw confluence results
                'raw_hvn_results': hvn_results,
                'raw_camarilla_results': camarilla_results,
                'current_price': current_price  # Include for reference
            })
            
            logger.info(f"Analysis complete for {ticker}")
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            self.error.emit(str(e))
    
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
                direction = "↑" if distance > 0 else "↓"
            
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
    
    def _format_confluence_zones(self, confluence_results, current_price: float) -> str:
        """Format confluence zones for display using the confluence engine's formatter"""
        if not confluence_results or not hasattr(confluence_results, 'zone_scores'):
            return "Confluence analysis could not be completed\n" + \
                   "HVN and Camarilla results are available separately"
        
        # Use the confluence engine's built-in formatter
        return self.confluence_engine.format_confluence_result(confluence_results, current_price)