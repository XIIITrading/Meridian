"""
Overview widget for Meridian Trading System
Handles ticker entry, session management, metrics display, and Camarilla Pivot Confluence
UPDATED: Replaced M15 zones with Pivot Confluence system
"""

from datetime import datetime, date, time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
import traceback

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QMessageBox,
    QHBoxLayout, QPushButton, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, pyqtSlot, QDate, QTime
from PyQt6.QtGui import QColor

# Import dark theme
from ui.dark_theme import DarkTheme, DarkStyleSheets

# Import local components
from .components import SectionHeader
from .session_info import SessionInfoFrame
from .analysis_frames import WeeklyAnalysisFrame, DailyAnalysisFrame
from .metrics_frame import MetricsFrame
from .pivot_confluence_widget import PivotConfluenceWidget  # NEW IMPORT
from .calculations import CalculationsDisplay

logger = logging.getLogger(__name__)


class OverviewWidget(QWidget):
    """
    Main overview widget containing all primary controls and displays
    UPDATED: Uses Pivot Confluence instead of M15 zones
    """
    
    # Signals
    save_to_database = pyqtSignal(dict)  # Save session data to Supabase
    analysis_requested = pyqtSignal(dict)  # Session data for analysis
    data_changed = pyqtSignal()
    fetch_market_data = pyqtSignal(dict)  # Request market data fetch
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DarkStyleSheets.WIDGET_CONTAINER)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the UI following the wireframe layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(DarkStyleSheets.SCROLL_BAR)
        
        # Container widget for scroll area
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)
        
        # Top section: Ticker entry, Live toggle, DateTime, Run Analysis
        self.session_info = SessionInfoFrame()
        self.session_info.run_analysis_btn.clicked.connect(self._on_run_analysis)
        self.session_info.fetch_data_btn.clicked.connect(self._fetch_market_data)
        self.session_info.save_to_db_btn.clicked.connect(self._on_save_to_database)
        self.session_info.clear_all_btn.clicked.connect(self._on_clear_all)
        container_layout.addWidget(self.session_info)
        
        # Metrics section
        self.metrics_frame = MetricsFrame()
        container_layout.addWidget(self.metrics_frame)
        
        # Weekly Analysis Section
        weekly_header = SectionHeader("Weekly Analysis")
        container_layout.addWidget(weekly_header)
        
        self.weekly_frame = WeeklyAnalysisFrame()
        container_layout.addWidget(self.weekly_frame)
        
        # Daily Analysis Section
        daily_header = SectionHeader("Daily Analysis")
        container_layout.addWidget(daily_header)
        
        self.daily_frame = DailyAnalysisFrame()
        container_layout.addWidget(self.daily_frame)
        
        # REPLACED: M15 Zone Data Entry with Daily Camarilla Pivot Confluence
        self.pivot_confluence_widget = PivotConfluenceWidget()
        self.pivot_confluence_widget.confluence_settings_changed.connect(self._on_confluence_settings_changed)
        container_layout.addWidget(self.pivot_confluence_widget)
        
        # Calculations section
        self.calculations = CalculationsDisplay()
        container_layout.addWidget(self.calculations)
        
        # REMOVED: M15 Zones Ranked section (now integrated into pivot confluence widget)
        
        # Add stretch at bottom
        container_layout.addStretch()
        
        container.setLayout(container_layout)
        scroll_area.setWidget(container)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    @property
    def save_to_db_btn(self):
        """Access save button from session info frame"""
        return self.session_info.save_to_db_btn
    
    @property
    def run_analysis_btn(self):
        """Access run analysis button from session info frame"""
        return self.session_info.run_analysis_btn
    
    def _connect_signals(self):
        """Connect internal signals"""
        # Connect ticker changes
        self.session_info.ticker_changed.connect(self._on_ticker_changed)
        
        # Connect data changes from all input widgets
        self.weekly_frame.trend_direction.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.weekly_frame.internal_trend.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.weekly_frame.position_structure.valueChanged.connect(lambda: self.data_changed.emit())
        self.weekly_frame.eow_bias.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.weekly_frame.notes.textChanged.connect(lambda: self.data_changed.emit())
        
        # Connect weekly price levels
        for level in self.weekly_frame.weekly_levels:
            level.valueChanged.connect(lambda: self.data_changed.emit())
        
        self.daily_frame.trend_direction.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.internal_trend.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.position_structure.valueChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.eod_bias.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.notes.textChanged.connect(lambda: self.data_changed.emit())
        
        for level in self.daily_frame.price_levels:
            level.valueChanged.connect(lambda: self.data_changed.emit())
    
    def statusBar(self):
        """Get the main window's status bar"""
        main_window = self.window()
        if hasattr(main_window, 'statusBar'):
            return main_window.statusBar()
        # Return a dummy status bar if not found
        return QStatusBar()
    
    def _on_ticker_changed(self, ticker: str):
        """Handle ticker changes"""
        if len(ticker.strip()) >= 1:
            self.data_changed.emit()
    
    def _on_confluence_settings_changed(self):
        """Handle confluence settings changes"""
        self.data_changed.emit()
        # Optionally trigger re-analysis if data exists
        self.statusBar().showMessage("Confluence settings updated", 3000)
    
    @pyqtSlot()
    def _fetch_market_data(self):
        """Fetch market data from Polygon"""
        ticker = self.session_info.ticker_input.text().strip()
        if not ticker:
            QMessageBox.warning(self, "Missing Ticker", "Please enter a ticker symbol.")
            return
        
        # Combine date and time
        date = self.session_info.date_input.date().toPyDate()
        time = self.session_info.time_input.time().toPyTime()
        datetime_val = datetime.combine(date, time)
        
        # Emit signal to fetch market data
        self.fetch_market_data.emit({
            'ticker': ticker.upper(),
            'datetime': datetime_val
        })
    
    @pyqtSlot()
    def _on_run_analysis(self):
        """Handle run analysis button click"""
        # Validate required fields
        if not self.session_info.ticker_input.text().strip():
            QMessageBox.warning(self, "Missing Data", "Please enter a ticker symbol.")
            return
        
        # Collect all data
        data = self.collect_session_data()
        
        # Emit signal for analysis
        self.analysis_requested.emit(data)
    
    @pyqtSlot()
    def _on_save_to_database(self):
        """Handle save to database button click with detailed debugging"""
        logger.info("="*60)
        logger.info("OVERVIEW WIDGET: SAVE TO DATABASE INITIATED")
        logger.info("="*60)
        
        # Validate required fields
        ticker = self.session_info.ticker_input.text().strip()
        if not ticker:
            logger.warning("No ticker entered")
            QMessageBox.warning(self, "Missing Data", "Please enter a ticker symbol.")
            return
        
        logger.info(f"Ticker: {ticker}")
        
        try:
            # Collect all data with logging
            logger.info("Collecting session data from UI...")
            data = self.collect_session_data()
            
            # Log what we collected
            logger.debug("Collected session data structure:")
            self._log_collected_data(data)
            
            # Emit signal for database save
            logger.info("Emitting save_to_database signal...")
            self.save_to_database.emit(data)
            logger.info("Signal emitted successfully")
            
        except Exception as e:
            logger.error(f"Exception during data collection: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while collecting data:\n{str(e)}\n\nCheck console for details."
            )
        finally:
            logger.info("="*60)
            logger.info("SAVE HANDLER COMPLETE")
            logger.info("="*60)
    
    @pyqtSlot()
    def _on_clear_all(self):
        """Handle clear all button click"""
        reply = QMessageBox.question(
            self, 
            'Clear All Data', 
            'Are you sure you want to clear all data?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_all()
            self.statusBar().showMessage("All data cleared", 3000)
    
    def _log_collected_data(self, data: Dict[str, Any], indent: int = 0):
        """Helper to log collected data structure"""
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                logger.debug(f"{prefix}{key}: <dict> with {len(value)} keys")
                if indent < 2:  # Limit depth
                    self._log_collected_data(value, indent + 1)
            elif isinstance(value, list):
                logger.debug(f"{prefix}{key}: <list> with {len(value)} items")
                if value and len(value) > 0:
                    if isinstance(value[0], dict) and indent < 2:
                        logger.debug(f"{prefix}  [0]:")
                        self._log_collected_data(value[0], indent + 2)
                    elif not isinstance(value[0], dict):
                        sample = value[:3] if len(value) > 3 else value
                        logger.debug(f"{prefix}  Sample: {sample}")
            elif isinstance(value, datetime):
                logger.debug(f"{prefix}{key}: {value.isoformat()} (datetime)")
            else:
                if isinstance(value, str) and len(value) > 50:
                    logger.debug(f"{prefix}{key}: '{value[:50]}...' (str, {len(value)} chars)")
                else:
                    logger.debug(f"{prefix}{key}: {value} ({type(value).__name__})")
    
    def validate_and_save(self):
        """Validate data and trigger save (called from main window)"""
        self._on_save_to_database()
    
    def collect_session_data(self) -> Dict[str, Any]:
        """Collect all session data from the widget with debugging"""
        logger.debug("Starting data collection...")
        
        # Get current price from metrics if available
        current_price_text = self.metrics_frame.current_price.text()
        pre_market_price = 0
        if current_price_text:
            try:
                pre_market_price = float(current_price_text)
                logger.debug(f"Pre-market price: {pre_market_price}")
            except ValueError:
                logger.warning(f"Could not parse pre-market price: {current_price_text}")
        
        # Combine date and time
        date = self.session_info.date_input.date().toPyDate()
        time = self.session_info.time_input.time().toPyTime()
        datetime_val = datetime.combine(date, time)
        logger.debug(f"DateTime: {datetime_val}")
        
        # Collect metrics data
        metrics_data = {}
        
        # Helper function to safely get float value from QLineEdit
        def get_metric_value(widget, name):
            text = widget.text().strip()
            if text:
                try:
                    value = float(text)
                    logger.debug(f"  {name}: {value}")
                    return value
                except ValueError:
                    logger.warning(f"  {name}: Could not parse '{text}'")
                    return 0.0
            logger.debug(f"  {name}: Empty")
            return 0.0
        
        # Collect all metric values
        logger.debug("Collecting metrics...")
        metrics_data['atr_5min'] = get_metric_value(self.metrics_frame.atr_5min, "atr_5min")
        metrics_data['atr_15min'] = get_metric_value(self.metrics_frame.atr_15min, "atr_15min")
        metrics_data['atr_2hour'] = get_metric_value(self.metrics_frame.atr_2hour, "atr_2hour")
        metrics_data['daily_atr'] = get_metric_value(self.metrics_frame.daily_atr, "daily_atr")
        metrics_data['atr_high'] = get_metric_value(self.metrics_frame.atr_high, "atr_high")
        metrics_data['atr_low'] = get_metric_value(self.metrics_frame.atr_low, "atr_low")
        
        # Collect weekly data
        logger.debug("Collecting weekly data...")
        weekly_data = self.weekly_frame.get_data()
        logger.debug(f"  Weekly data keys: {list(weekly_data.keys())}")
        
        # Collect daily data
        logger.debug("Collecting daily data...")
        daily_data = self.daily_frame.get_data()
        logger.debug(f"  Daily data keys: {list(daily_data.keys())}")
        
        # Collect pivot confluence settings
        logger.debug("Collecting pivot confluence settings...")
        pivot_confluence_settings = self.pivot_confluence_widget.get_confluence_settings()
        logger.debug(f"  Pivot confluence settings: {len(pivot_confluence_settings)} levels")
        
        # Build final data structure
        session_data = {
            'ticker': self.session_info.ticker_input.text().strip().upper(),
            'is_live': self.session_info.live_toggle.isChecked(),
            'datetime': datetime_val,
            'weekly': weekly_data,
            'daily': daily_data,
            'pivot_confluence_settings': pivot_confluence_settings,  # NEW
            'pre_market_price': pre_market_price,
            'metrics': metrics_data,
            'timestamp': datetime.now()
        }
        
        logger.debug("Data collection complete")
        return session_data
    
    def load_session_data(self, session_data: Dict[str, Any]):
        """Load session data into the UI"""
        # Clear existing data first
        self.clear_all()
        
        # Load ticker and datetime
        if 'ticker' in session_data:
            self.session_info.ticker_input.setText(session_data['ticker'])
        
        if 'is_live' in session_data:
            self.session_info.live_toggle.setChecked(session_data['is_live'])
        
        if 'datetime' in session_data:
            dt = session_data['datetime']
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            # Split datetime into date and time
            self.session_info.date_input.setDate(QDate(dt.year, dt.month, dt.day))
            self.session_info.time_input.setTime(QTime(dt.hour, dt.minute, dt.second))
        
        # Load weekly data
        if 'weekly' in session_data and session_data['weekly']:
            weekly = session_data['weekly']
            if 'trend_direction' in weekly:
                idx = self.weekly_frame.trend_direction.findText(weekly['trend_direction'])
                if idx >= 0:
                    self.weekly_frame.trend_direction.setCurrentIndex(idx)
            if 'internal_trend' in weekly:
                idx = self.weekly_frame.internal_trend.findText(weekly['internal_trend'])
                if idx >= 0:
                    self.weekly_frame.internal_trend.setCurrentIndex(idx)
            if 'position_structure' in weekly:
                self.weekly_frame.position_structure.setValue(int(weekly['position_structure']))
            if 'eow_bias' in weekly:
                idx = self.weekly_frame.eow_bias.findText(weekly['eow_bias'])
                if idx >= 0:
                    self.weekly_frame.eow_bias.setCurrentIndex(idx)
            if 'notes' in weekly:
                self.weekly_frame.notes.setPlainText(weekly['notes'])
            
            # Load weekly price levels
            if 'price_levels' in weekly:
                levels = weekly['price_levels']
                for i, level in enumerate(levels[:4]):  # Load up to 4 levels
                    if i < len(self.weekly_frame.weekly_levels):
                        self.weekly_frame.weekly_levels[i].setValue(float(level))
        
        # Load daily data
        if 'daily' in session_data and session_data['daily']:
            daily = session_data['daily']
            if 'trend_direction' in daily:
                idx = self.daily_frame.trend_direction.findText(daily['trend_direction'])
                if idx >= 0:
                    self.daily_frame.trend_direction.setCurrentIndex(idx)
            if 'internal_trend' in daily:
                idx = self.daily_frame.internal_trend.findText(daily['internal_trend'])
                if idx >= 0:
                    self.daily_frame.internal_trend.setCurrentIndex(idx)
            if 'position_structure' in daily:
                self.daily_frame.position_structure.setValue(int(daily['position_structure']))
            if 'eod_bias' in daily:
                idx = self.daily_frame.eod_bias.findText(daily['eod_bias'])
                if idx >= 0:
                    self.daily_frame.eod_bias.setCurrentIndex(idx)
            if 'notes' in daily:
                self.daily_frame.notes.setPlainText(daily['notes'])
            
            # Load price levels
            if 'price_levels' in daily:
                levels = daily['price_levels']
                for i, level in enumerate(levels[:6]):  # Load up to 6 levels
                    if i < len(self.daily_frame.price_levels):
                        self.daily_frame.price_levels[i].setValue(float(level))
        
        # After loading, fetch market data if we have a ticker
        if 'ticker' in session_data:
            self._fetch_market_data()
    
    def update_calculations(self, results: Dict[str, Any]):
        """Update calculation displays with analysis results"""
        # Update metrics
        if 'metrics' in results:
            self.metrics_frame.update_metrics(results['metrics'])
        
        # Update HVN displays
        if 'hvn_7day' in results:
            self.calculations.hvn_7day.text_area.setText(results['hvn_7day'])
        if 'hvn_14day' in results:
            self.calculations.hvn_14day.text_area.setText(results['hvn_14day'])
        if 'hvn_30day' in results:
            self.calculations.hvn_30day.text_area.setText(results['hvn_30day'])
        
        # Update Camarilla displays
        if 'cam_monthly' in results:
            self.calculations.cam_monthly.text_area.setText(results['cam_monthly'])
        if 'cam_weekly' in results:
            self.calculations.cam_weekly.text_area.setText(results['cam_weekly'])
        if 'cam_daily' in results:
            self.calculations.cam_daily.text_area.setText(results['cam_daily'])
        
        # Update Zone displays
        if 'weekly_zones' in results:
            self.calculations.weekly_zones.text_area.setText(results['weekly_zones'])
        if 'daily_zones' in results:
            self.calculations.daily_zones.text_area.setText(results['daily_zones'])
        if 'atr_zones' in results:
            self.calculations.atr_zones.text_area.setText(results['atr_zones'])
        
        # UPDATE: Pivot confluence widget with results
        if 'pivot_confluence_results' in results:
            self.pivot_confluence_widget.update_pivot_data(results['pivot_confluence_results'])
        
        # REMOVED: zones_ranked text widget (now handled by pivot confluence widget)
    
    def clear_all(self):
        """Clear all input fields and results"""
        # Clear session info
        self.session_info.ticker_input.clear()
        self.session_info.live_toggle.setChecked(True)
        self.session_info.date_input.setDate(QDate.currentDate())
        self.session_info.time_input.setTime(QTime.currentTime())
        
        # Clear weekly
        self.weekly_frame.clear_all()
        
        # Clear daily
        self.daily_frame.clear_all()
        
        # Clear metrics
        self.metrics_frame.clear_all()
        
        # Clear pivot confluence widget
        self.pivot_confluence_widget.clear_data()
        
        # Clear calculations
        self.calculations.hvn_7day.text_area.clear()
        self.calculations.hvn_14day.text_area.clear()
        self.calculations.hvn_30day.text_area.clear()
        self.calculations.cam_monthly.text_area.clear()
        self.calculations.cam_weekly.text_area.clear()
        self.calculations.cam_daily.text_area.clear()
        self.calculations.weekly_zones.text_area.clear()
        self.calculations.daily_zones.text_area.clear()
        self.calculations.atr_zones.text_area.clear()
        
        # Reset placeholders
        self.calculations.hvn_7day.text_area.setPlaceholderText("HVN 7-day analysis will appear here...")
        self.calculations.hvn_14day.text_area.setPlaceholderText("HVN 14-day analysis will appear here...")
        self.calculations.hvn_30day.text_area.setPlaceholderText("HVN 30-day analysis will appear here...")
        self.calculations.cam_monthly.text_area.setPlaceholderText("Monthly Camarilla pivots will appear here...")
        self.calculations.cam_weekly.text_area.setPlaceholderText("Weekly Camarilla pivots will appear here...")
        self.calculations.cam_daily.text_area.setPlaceholderText("Daily Camarilla pivots will appear here...")
        self.calculations.weekly_zones.text_area.setPlaceholderText("Weekly zones will appear here after analysis...\n\nCreated from WL1-WL4 ± 2-Hour ATR")
        self.calculations.daily_zones.text_area.setPlaceholderText("Daily zones will appear here after analysis...\n\nCreated from DL1-DL6 ± 15-Minute ATR")
        self.calculations.atr_zones.text_area.setPlaceholderText(
            "ATR Zones will appear here after analysis...\n\n"
            "Dynamic zones based on:\n"
            "• ATR High: Current + Daily ATR ± 5min ATR\n"
            "• ATR Low: Current - Daily ATR ± 5min ATR"
        )
        
        # Emit data changed signal to reset the modified flag
        self.data_changed.emit()