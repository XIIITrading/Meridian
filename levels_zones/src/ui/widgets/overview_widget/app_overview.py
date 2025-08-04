"""
Overview widget for Meridian Trading System
Handles ticker entry, session management, metrics display, and M15 zones
"""

from datetime import datetime, date, time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, pyqtSlot, QDate, QTime

# Import dark theme
from ui.dark_theme import DarkTheme, DarkStyleSheets

# Import local components
from .components import SectionHeader
from .session_info import SessionInfoFrame
from .analysis_frames import WeeklyAnalysisFrame, DailyAnalysisFrame
from .metrics_frame import MetricsFrame
from .zone_table import M15ZoneTable
from .calculations import CalculationsDisplay

logger = logging.getLogger(__name__)


class OverviewWidget(QWidget):
    """
    Main overview widget containing all primary controls and displays
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
        self.session_info.save_to_db_btn.clicked.connect(self._on_save_to_database)  # Connect the save button
        container_layout.addWidget(self.session_info)
        
        # Metrics section (MOVED UP HERE)
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
        
        # M15 Zone Data Entry
        zone_label = QLabel("M15 Zone Data Entry")
        zone_label.setStyleSheet(f"""
            QLabel {{
                background-color: {DarkTheme.BG_DARK};
                color: {DarkTheme.TEXT_PRIMARY};
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {DarkTheme.BORDER_NORMAL};
                border-radius: 3px;
            }}
        """)
        zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(zone_label)
        
        self.zone_table = M15ZoneTable()
        container_layout.addWidget(self.zone_table)
        
        # Calculations section
        self.calculations = CalculationsDisplay()
        container_layout.addWidget(self.calculations)
        
        # M15 Zones Ranked section
        zones_ranked_label = QLabel("M15 Zones Ranked")
        zones_ranked_label.setStyleSheet(f"""
            QLabel {{
                background-color: {DarkTheme.BG_DARK};
                color: {DarkTheme.TEXT_PRIMARY};
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {DarkTheme.BORDER_NORMAL};
                border-radius: 3px;
            }}
        """)
        zones_ranked_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(zones_ranked_label)
        
        self.zones_ranked = QTextEdit()
        self.zones_ranked.setStyleSheet(DarkStyleSheets.TEXT_AREA)
        self.zones_ranked.setPlaceholderText("M15 Zones Confluence Ranking will appear here after analysis...")
        self.zones_ranked.setMinimumHeight(200)
        self.zones_ranked.setReadOnly(True)
        container_layout.addWidget(self.zones_ranked)
        
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
        
        self.daily_frame.trend_direction.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.internal_trend.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.position_structure.valueChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.eod_bias.currentTextChanged.connect(lambda: self.data_changed.emit())
        self.daily_frame.notes.textChanged.connect(lambda: self.data_changed.emit())
        
        for level in self.daily_frame.above_levels + self.daily_frame.below_levels:
            level.valueChanged.connect(lambda: self.data_changed.emit())
    
    def _on_ticker_changed(self, ticker: str):
        """Handle ticker changes"""
        if len(ticker.strip()) >= 1:
            self.data_changed.emit()
    
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
        """Handle save to database button click"""
        # Validate required fields
        if not self.session_info.ticker_input.text().strip():
            QMessageBox.warning(self, "Missing Data", "Please enter a ticker symbol.")
            return
        
        # Collect all data
        data = self.collect_session_data()
        
        # Emit signal for database save
        self.save_to_database.emit(data)
    
    def validate_and_save(self):
        """Validate data and trigger save (called from main window)"""
        self._on_save_to_database()
    
    def collect_session_data(self) -> Dict[str, Any]:
        """Collect all session data from the widget"""
        # Get current price from metrics if available
        current_price_text = self.metrics_frame.current_price.text()
        pre_market_price = 0
        if current_price_text:
            try:
                pre_market_price = float(current_price_text)
            except ValueError:
                pass
        
        # Combine date and time
        date = self.session_info.date_input.date().toPyDate()
        time = self.session_info.time_input.time().toPyTime()
        datetime_val = datetime.combine(date, time)
        
        return {
            'ticker': self.session_info.ticker_input.text().strip().upper(),
            'is_live': self.session_info.live_toggle.isChecked(),
            'datetime': datetime_val,
            'weekly': self.weekly_frame.get_data(),
            'daily': self.daily_frame.get_data(),
            'zones': self.zone_table.get_zone_data(),
            'pre_market_price': pre_market_price,
            'timestamp': datetime.now()
        }
    
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
                for i, level in enumerate(levels[:3]):  # Above levels
                    if i < len(self.daily_frame.above_levels):
                        self.daily_frame.above_levels[i].setValue(float(level))
                for i, level in enumerate(levels[3:6]):  # Below levels
                    if i < len(self.daily_frame.below_levels):
                        self.daily_frame.below_levels[i].setValue(float(level))
        
        # Load zones - UPDATED SECTION
        if 'zones' in session_data and session_data['zones']:
            for row, zone in enumerate(session_data['zones'][:6]):
                if 'datetime' in zone and zone['datetime']:
                    # Split datetime into date and time
                    datetime_str = zone['datetime']
                    if 'T' in datetime_str or ' ' in datetime_str:
                        # Full datetime format
                        try:
                            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                            self.zone_table.item(row, 1).setText(dt.strftime('%Y-%m-%d'))
                            self.zone_table.item(row, 2).setText(dt.strftime('%H:%M:%S'))
                        except:
                            # Fallback: treat as time only
                            self.zone_table.item(row, 2).setText(datetime_str)
                    else:
                        # Just time format (backward compatibility)
                        self.zone_table.item(row, 2).setText(datetime_str)
                
                # Handle separate date/time fields if they exist
                if 'date' in zone:
                    self.zone_table.item(row, 1).setText(zone['date'])
                if 'time' in zone:
                    self.zone_table.item(row, 2).setText(zone['time'])
                
                if 'level' in zone:
                    self.zone_table.item(row, 3).setText(str(zone['level']))
                if 'high' in zone:
                    self.zone_table.item(row, 4).setText(str(zone['high']))
                if 'low' in zone:
                    self.zone_table.item(row, 5).setText(str(zone['low']))
        
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
        
        # Update zones ranking
        if 'zones_ranked' in results:
            self.zones_ranked.setText(results['zones_ranked'])
    
    def clear_all(self):
        """Clear all input fields"""
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
        
        # Clear table - UPDATED FOR NEW COLUMN COUNT
        for row in range(self.zone_table.rowCount()):
            for col in range(1, self.zone_table.columnCount()):
                if self.zone_table.item(row, col):
                    self.zone_table.item(row, col).setText("")
        
        # Clear calculations
        self.calculations.hvn_7day.text_area.clear()
        self.calculations.hvn_14day.text_area.clear()
        self.calculations.hvn_30day.text_area.clear()
        self.calculations.cam_monthly.text_area.clear()
        self.calculations.cam_weekly.text_area.clear()
        self.calculations.cam_daily.text_area.clear()
        self.zones_ranked.clear()