"""
Overview widget for Meridian Trading System
Handles ticker entry, session management, metrics display, and M15 zones
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
        self.session_info.save_to_db_btn.clicked.connect(self._on_save_to_database)
        self.session_info.clear_all_btn.clicked.connect(self._on_clear_all)  # NEW CONNECTION
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
        
        # M15 Zone Data Entry with Query Data button
        zone_header_layout = QHBoxLayout()
        
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
        zone_header_layout.addWidget(zone_label)
        
        # Add Query Data button
        self.query_data_btn = QPushButton("Query Data")
        self.query_data_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.INFO};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #1976d2;
            }}
            QPushButton:pressed {{
                background-color: #0d47a1;
            }}
            QPushButton:disabled {{
                background-color: {DarkTheme.BG_LIGHT};
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        self.query_data_btn.setMaximumWidth(120)
        self.query_data_btn.setToolTip("Query M15 candle data from Polygon (Ctrl+Q)")
        self.query_data_btn.setShortcut("Ctrl+Q")
        self.query_data_btn.clicked.connect(self._on_query_zone_data)
        zone_header_layout.addWidget(self.query_data_btn)
        
        zone_header_layout.addStretch()
        container_layout.addLayout(zone_header_layout)
        
        # Add the zone table
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
        # Apply larger font size to zones ranked text area
        zones_ranked_style = DarkStyleSheets.TEXT_AREA + """
            QTextEdit {
                font-size: 14px;
                line-height: 1.4;
            }
        """
        self.zones_ranked.setStyleSheet(zones_ranked_style)
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
    def _on_query_zone_data(self):
        """Query and populate M15 zone candle data from Polygon"""
        ticker = self.session_info.ticker_input.text().strip()
        if not ticker:
            QMessageBox.warning(self, "Missing Ticker", "Please enter a ticker symbol.")
            return
        
        # Validate zone times first
        time_errors = self.zone_table.validate_zone_times()
        if time_errors:
            QMessageBox.warning(
                self, 
                "Invalid Time Format", 
                "Please correct the following time format errors:\n\n" + "\n".join(time_errors)
            )
            return
        
        # Check if we have any valid zones
        valid_zone_count = self.zone_table.get_valid_zone_count()
        if valid_zone_count == 0:
            QMessageBox.warning(
                self, 
                "No Valid Zones", 
                "Please enter date and time (in UTC) for at least one zone.\n\n"
                "Time format: hh:mm:ss\n"
                "Example: 14:30:00 for market open"
            )
            return
        
        # Import the calculator with proper path handling
        import sys
        from pathlib import Path
        
        # Navigate to project root
        widget_dir = Path(__file__).parent
        project_root = widget_dir.parent.parent.parent.parent
        
        # Add project root to path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Also add src path for the data imports inside m15_zone_calc
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        try:
            # Now import should work
            from calculations.candlestick.m15_zone_calc import M15ZoneCalculator
        except ImportError as e:
            logger.error(f"Failed to import M15ZoneCalculator: {e}")
            QMessageBox.critical(
                self, 
                "Import Error", 
                f"Failed to import M15 Zone Calculator:\n{str(e)}\n\n"
                "Please ensure the calculations/candlestick/m15_zone_calc.py file exists."
            )
            return
        
        # Disable button and show progress
        self.query_data_btn.setEnabled(False)
        self.query_data_btn.setText("Querying...")
        
        # Show status
        self.statusBar().showMessage(f"Querying M15 candle data for {ticker} ({valid_zone_count} zones)...")
        
        try:
            # Get zone data from table
            zones = self.zone_table.get_zone_data()
            
            # Create calculator and fetch data
            calculator = M15ZoneCalculator()
            
            # Test connection first
            connected, msg = calculator.test_connection()
            if not connected:
                raise Exception(f"Polygon connection failed: {msg}")
            
            # Fetch candle data for all zones
            results = calculator.fetch_all_zone_candles(ticker.upper(), zones)
            
            # Track results
            updated_count = 0
            failed_zones = []
            
            # Update table with results
            for zone_idx, candle_data in results:
                if candle_data:
                    # Update the table cells
                    self.zone_table.item(zone_idx, 3).setText(f"{candle_data['mid']:.2f}")
                    self.zone_table.item(zone_idx, 4).setText(f"{candle_data['high']:.2f}")
                    self.zone_table.item(zone_idx, 5).setText(f"{candle_data['low']:.2f}")
                    
                    # Set text color to indicate successful fetch
                    for col in [3, 4, 5]:
                        self.zone_table.item(zone_idx, col).setForeground(QColor(DarkTheme.SUCCESS))
                    
                    updated_count += 1
                else:
                    # Check if this zone had valid date/time
                    zone = zones[zone_idx]
                    if zone.get('date') and zone.get('time') and \
                       zone['date'] != 'yyyy-mm-dd' and \
                       zone['time'] not in ['hh:mm:ss', 'hh:mm:ss UTC']:
                        failed_zones.append(f"Zone {zone_idx + 1}: {zone['date']} {zone['time']}")
            
            # Show results
            self.statusBar().showMessage(f"Query complete: {updated_count} zones updated", 5000)
            
            if updated_count > 0:
                message = f"Successfully queried data for {updated_count} zone(s).\n\n"
                message += "Data populated:\n"
                message += "• Level = Midpoint of candle (High + Low) / 2\n"
                message += "• Zone High = Candle High\n"
                message += "• Zone Low = Candle Low"
                
                if failed_zones:
                    message += f"\n\nNo data found for {len(failed_zones)} zone(s):\n"
                    message += "\n".join(failed_zones[:5])
                    if len(failed_zones) > 5:
                        message += f"\n... and {len(failed_zones) - 5} more"
                
                QMessageBox.information(self, "Query Complete", message)
                self.data_changed.emit()
            else:
                QMessageBox.warning(
                    self, 
                    "No Data Found", 
                    "No candle data found for the specified zones.\n\n"
                    "Please check:\n"
                    "• Times are in UTC format\n"
                    "• Times are within market hours (08:00-00:00 UTC)\n"
                    "• Dates are valid trading days (Mon-Fri)\n"
                    "• Ticker symbol is correct"
                )
                
        except Exception as e:
            logger.error(f"Error querying zone data: {e}")
            self.statusBar().showMessage("Query failed", 3000)
            QMessageBox.critical(
                self, 
                "Query Error", 
                f"Error querying candle data:\n\n{str(e)}\n\n"
                "Please check your Polygon connection and try again."
            )
        
        finally:
            # Re-enable button
            self.query_data_btn.setEnabled(True)
            self.query_data_btn.setText("Query Data")
    
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
        # REMOVED: metrics_data['atr_10min'] = get_metric_value(self.metrics_frame.atr_10min, "atr_10min")
        metrics_data['atr_15min'] = get_metric_value(self.metrics_frame.atr_15min, "atr_15min")
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
        
        # Collect zones
        logger.debug("Collecting zone data...")
        zones_data = self.zone_table.get_zone_data()
        logger.debug(f"  Zones: {len(zones_data)} zones collected")
        
        # Build final data structure
        session_data = {
            'ticker': self.session_info.ticker_input.text().strip().upper(),
            'is_live': self.session_info.live_toggle.isChecked(),
            'datetime': datetime_val,
            'weekly': weekly_data,
            'daily': daily_data,
            'zones': zones_data,
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
        
        # Load zones
        if 'zones' in session_data and session_data['zones']:
            for row, zone in enumerate(session_data['zones'][:6]):
                zone_data = {}
                
                # Handle datetime formats
                if 'datetime' in zone and zone['datetime']:
                    # Split datetime into date and time
                    datetime_str = zone['datetime']
                    if 'T' in datetime_str or ' ' in datetime_str:
                        # Full datetime format
                        try:
                            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                            zone_data['date'] = dt.strftime('%Y-%m-%d')
                            zone_data['time'] = dt.strftime('%H:%M:%S')
                        except:
                            # Fallback: treat as time only
                            zone_data['time'] = datetime_str
                    else:
                        # Just time format (backward compatibility)
                        zone_data['time'] = datetime_str
                
                # Handle separate date/time fields if they exist
                if 'date' in zone:
                    zone_data['date'] = zone['date']
                if 'time' in zone:
                    zone_data['time'] = zone['time']
                
                if 'level' in zone:
                    zone_data['level'] = zone['level']
                if 'high' in zone:
                    zone_data['high'] = zone['high']
                if 'low' in zone:
                    zone_data['low'] = zone['low']
                
                self.zone_table.set_zone_data(row, zone_data)
        
        # After loading, fetch market data if we have a ticker
        if 'ticker' in session_data:
            self._fetch_market_data()
    
    # In levels_zones/src/ui/widgets/overview_widget/app_overview.py

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
        
        # Update Daily Zones display
        if 'daily_zones' in results:
            self.calculations.daily_zones.text_area.setText(results['daily_zones'])
        
        # Update ATR Zones Display - NOW FULLY IMPLEMENTED
        if 'atr_zones' in results:
            self.calculations.atr_zones.text_area.setText(results['atr_zones'])
        else:
            # Show informative message if ATR zones couldn't be calculated
            self.calculations.atr_zones.text_area.setText(
                "ATR Zones: Pending calculation\n\n"
                "ATR zones require:\n"
                "• Daily ATR value\n"
                "• 5-minute ATR value\n"
                "• Current price\n\n"
                "These will be calculated during analysis."
            )
        
        # Update zones ranking
        if 'zones_ranked' in results:
            self.zones_ranked.setText(results['zones_ranked'])

    
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
        
        # Clear table
        self.zone_table.clear_all_zones()
        
        # Clear calculations - ALL displays including zones
        self.calculations.hvn_7day.text_area.clear()
        self.calculations.hvn_14day.text_area.clear()
        self.calculations.hvn_30day.text_area.clear()
        self.calculations.cam_monthly.text_area.clear()
        self.calculations.cam_weekly.text_area.clear()
        self.calculations.cam_daily.text_area.clear()
        self.calculations.weekly_zones.text_area.clear()
        self.calculations.daily_zones.text_area.clear()
        self.calculations.atr_zones.text_area.clear()  # Only need this once
        
        # Clear zones ranked
        self.zones_ranked.clear()
        
        # Reset placeholders for HVN
        self.calculations.hvn_7day.text_area.setPlaceholderText("HVN 7-day analysis will appear here...")
        self.calculations.hvn_14day.text_area.setPlaceholderText("HVN 14-day analysis will appear here...")
        self.calculations.hvn_30day.text_area.setPlaceholderText("HVN 30-day analysis will appear here...")
        
        # Reset placeholders for Camarilla
        self.calculations.cam_monthly.text_area.setPlaceholderText("Monthly Camarilla pivots will appear here...")
        self.calculations.cam_weekly.text_area.setPlaceholderText("Weekly Camarilla pivots will appear here...")
        self.calculations.cam_daily.text_area.setPlaceholderText("Daily Camarilla pivots will appear here...")
        
        # Reset placeholders for Zones
        self.calculations.weekly_zones.text_area.setPlaceholderText("Weekly zones will appear here after analysis...\n\nCreated from WL1-WL4 ± 2-Hour ATR")
        self.calculations.daily_zones.text_area.setPlaceholderText("Daily zones will appear here after analysis...\n\nCreated from DL1-DL6 ± 15-Minute ATR")
        self.calculations.atr_zones.text_area.setPlaceholderText(
            "ATR Zones will appear here after analysis...\n\n"
            "Dynamic zones based on:\n"
            "• ATR High: Current + Daily ATR ± 5min ATR\n"
            "• ATR Low: Current - Daily ATR ± 5min ATR"
        )
        
        # Reset zones ranked placeholder
        self.zones_ranked.setPlaceholderText("M15 Zones Confluence Ranking will appear here after analysis...")
        
        # Emit data changed signal to reset the modified flag
        self.data_changed.emit()
    
        
        # Emit data changed signal to reset the modified flag
        self.data_changed.emit()