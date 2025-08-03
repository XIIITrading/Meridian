"""
Overview widget for Meridian Trading System
Handles ticker entry, session management, metrics display, and M15 zones
"""

from datetime import datetime, date, time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QDateTimeEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QSplitter, QFrame, QMessageBox, QDoubleSpinBox, QScrollArea,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, pyqtSlot
from PyQt6.QtGui import QFont, QColor

# Import dark theme
from ..dark_theme import DarkTheme, DarkStyleSheets

# Import Polygon service
from services.polygon_service import PolygonService

logger = logging.getLogger(__name__)


class TrendSelector(QComboBox):
    """Custom combo box for trend selection with color coding"""
    
    def __init__(self):
        super().__init__()
        self.addItems(["Bull", "Bear", "Range"])
        self.setStyleSheet(DarkStyleSheets.COMBO_BOX)
        self.currentTextChanged.connect(self._update_style)
        
    def _update_style(self, text: str):
        """Update combo box style based on selection"""
        base_style = DarkStyleSheets.COMBO_BOX
        
        if text == "Bull":
            color_style = f"""
                QComboBox {{
                    color: {DarkTheme.BULL};
                    font-weight: bold;
                }}
            """
        elif text == "Bear":
            color_style = f"""
                QComboBox {{
                    color: {DarkTheme.BEAR};
                    font-weight: bold;
                }}
            """
        else:  # Range
            color_style = f"""
                QComboBox {{
                    color: {DarkTheme.RANGE};
                    font-weight: bold;
                }}
            """
        
        self.setStyleSheet(base_style + color_style)


class SessionInfoFrame(QFrame):
    """Frame for session information (ticker, datetime, etc.)"""
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(DarkStyleSheets.FRAME)
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Ticker Entry
        layout.addWidget(QLabel("Ticker Entry:"))
        self.ticker_input = QLineEdit()
        self.ticker_input.setMaxLength(10)
        self.ticker_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.ticker_input.setPlaceholderText("Enter ticker...")
        layout.addWidget(self.ticker_input)
        
        # Live Toggle
        self.live_toggle = QCheckBox("Live Toggle")
        self.live_toggle.setStyleSheet(DarkStyleSheets.CHECKBOX)
        self.live_toggle.setChecked(True)
        layout.addWidget(self.live_toggle)
        
        # DateTime Entry
        layout.addWidget(QLabel("DateTime Entry:"))
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        layout.addWidget(self.datetime_input)
        
        # Fetch Market Data Button
        self.fetch_data_btn = QPushButton("Fetch Market Data")
        self.fetch_data_btn.setStyleSheet(DarkStyleSheets.BUTTON_SECONDARY)
        self.fetch_data_btn.setMinimumWidth(140)
        layout.addWidget(self.fetch_data_btn)
        
        # Spacer
        layout.addStretch()
        
        # Run Analysis Button
        self.run_analysis_btn = QPushButton("Run Analysis")
        self.run_analysis_btn.setStyleSheet(DarkStyleSheets.BUTTON_PRIMARY)
        self.run_analysis_btn.setMinimumWidth(120)
        layout.addWidget(self.run_analysis_btn)
        
        self.setLayout(layout)


class SectionHeader(QLabel):
    """Styled section header label"""
    
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(f"""
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
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class WeeklyAnalysisFrame(QFrame):
    """Frame for weekly analysis data entry"""
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(DarkStyleSheets.FRAME)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Grid layout for fields
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row 1: Trend Direction and Internal Trend
        grid.addWidget(QLabel("Trend Direction:"), 0, 0)
        self.trend_direction = TrendSelector()
        grid.addWidget(self.trend_direction, 0, 1)
        
        grid.addWidget(QLabel("Internal Trend:"), 0, 2)
        self.internal_trend = TrendSelector()
        grid.addWidget(self.internal_trend, 0, 3)
        
        # Row 2: Position and EOW Bias
        grid.addWidget(QLabel("Position in Structure:"), 1, 0)
        self.position_structure = QSpinBox()
        self.position_structure.setRange(0, 100)
        self.position_structure.setSuffix("%")
        self.position_structure.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        grid.addWidget(self.position_structure, 1, 1)
        
        grid.addWidget(QLabel("EOW Bias:"), 1, 2)
        self.eow_bias = TrendSelector()
        grid.addWidget(self.eow_bias, 1, 3)
        
        # Row 3: Notes
        grid.addWidget(QLabel("Notes:"), 2, 0)
        self.notes = QTextEdit()
        self.notes.setStyleSheet(DarkStyleSheets.TEXT_AREA)
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Weekly analysis notes...")
        grid.addWidget(self.notes, 2, 1, 1, 3)
        
        layout.addLayout(grid)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Get weekly analysis data"""
        return {
            'trend_direction': self.trend_direction.currentText(),
            'internal_trend': self.internal_trend.currentText(),
            'position_structure': self.position_structure.value(),
            'eow_bias': self.eow_bias.currentText(),
            'notes': self.notes.toPlainText()
        }
    
    def clear_all(self):
        """Clear all fields"""
        self.trend_direction.setCurrentIndex(0)
        self.internal_trend.setCurrentIndex(0)
        self.position_structure.setValue(0)
        self.eow_bias.setCurrentIndex(0)
        self.notes.clear()


class DailyAnalysisFrame(QFrame):
    """Frame for daily analysis data entry"""
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(DarkStyleSheets.FRAME)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Grid layout for fields
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Row 1: Trend Direction and Internal Trend
        grid.addWidget(QLabel("Trend Direction:"), 0, 0)
        self.trend_direction = TrendSelector()
        grid.addWidget(self.trend_direction, 0, 1)
        
        grid.addWidget(QLabel("Internal Trend:"), 0, 2)
        self.internal_trend = TrendSelector()
        grid.addWidget(self.internal_trend, 0, 3)
        
        # Row 2: Position and EOD Bias
        grid.addWidget(QLabel("Position in Structure:"), 1, 0)
        self.position_structure = QSpinBox()
        self.position_structure.setRange(0, 100)
        self.position_structure.setSuffix("%")
        self.position_structure.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        grid.addWidget(self.position_structure, 1, 1)
        
        grid.addWidget(QLabel("EOD Bias:"), 1, 2)
        self.eod_bias = TrendSelector()
        grid.addWidget(self.eod_bias, 1, 3)
        
        # Row 3: Price Levels Label
        grid.addWidget(QLabel("Six Significant Price Levels:"), 2, 0, 1, 4)
        
        # Row 4: Price level inputs (3 above, 3 below)
        levels_layout = QHBoxLayout()
        levels_layout.setSpacing(10)
        
        # Above levels
        above_label = QLabel("Above:")
        above_label.setStyleSheet(f"color: {DarkTheme.SUCCESS};")
        levels_layout.addWidget(above_label)
        
        self.above_levels = []
        for i in range(3):
            level_input = QDoubleSpinBox()
            level_input.setDecimals(2)
            level_input.setRange(0, 99999.99)
            level_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
            level_input.setPrefix(f"A{i+1}: ")
            self.above_levels.append(level_input)
            levels_layout.addWidget(level_input)
        
        # Separator
        levels_layout.addWidget(QLabel("|"))
        
        # Below levels
        below_label = QLabel("Below:")
        below_label.setStyleSheet(f"color: {DarkTheme.ERROR};")
        levels_layout.addWidget(below_label)
        
        self.below_levels = []
        for i in range(3):
            level_input = QDoubleSpinBox()
            level_input.setDecimals(2)
            level_input.setRange(0, 99999.99)
            level_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
            level_input.setPrefix(f"B{i+1}: ")
            self.below_levels.append(level_input)
            levels_layout.addWidget(level_input)
        
        grid.addLayout(levels_layout, 3, 0, 1, 4)
        
        # Row 5: Notes
        grid.addWidget(QLabel("Notes:"), 4, 0)
        self.notes = QTextEdit()
        self.notes.setStyleSheet(DarkStyleSheets.TEXT_AREA)
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Daily analysis notes...")
        grid.addWidget(self.notes, 4, 1, 1, 3)
        
        layout.addLayout(grid)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Get daily analysis data"""
        return {
            'trend_direction': self.trend_direction.currentText(),
            'internal_trend': self.internal_trend.currentText(),
            'position_structure': self.position_structure.value(),
            'eod_bias': self.eod_bias.currentText(),
            'price_levels': [level.value() for level in self.above_levels + self.below_levels],
            'notes': self.notes.toPlainText()
        }
    
    def clear_all(self):
        """Clear all fields"""
        self.trend_direction.setCurrentIndex(0)
        self.internal_trend.setCurrentIndex(0)
        self.position_structure.setValue(0)
        self.eod_bias.setCurrentIndex(0)
        for level in self.above_levels + self.below_levels:
            level.setValue(0)
        self.notes.clear()


class MetricsFrame(QFrame):
    """Frame for displaying ATR metrics and price levels"""
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(DarkStyleSheets.FRAME)
        self._init_ui()
    
    def _init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Metrics header
        metrics_label = QLabel("Metrics")
        metrics_label.setStyleSheet(f"font-weight: bold; color: {DarkTheme.TEXT_PRIMARY};")
        metrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(metrics_label, 0, 0, 1, 4)
        
        # ATR Row - All calculated (read-only)
        # 5-Minute ATR
        layout.addWidget(QLabel("5-Minute ATR:"), 1, 0)
        self.atr_5min = QLineEdit()
        self.atr_5min.setReadOnly(True)
        self.atr_5min.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_5min.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_5min, 1, 1)
        
        # 10-Minute ATR
        layout.addWidget(QLabel("10-Minute ATR:"), 1, 2)
        self.atr_10min = QLineEdit()
        self.atr_10min.setReadOnly(True)
        self.atr_10min.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_10min.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_10min, 1, 3)
        
        # 15-Minute ATR
        layout.addWidget(QLabel("15-Minute ATR:"), 2, 0)
        self.atr_15min = QLineEdit()
        self.atr_15min.setReadOnly(True)
        self.atr_15min.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_15min.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_15min, 2, 1)
        
        # Daily ATR
        layout.addWidget(QLabel("Daily ATR:"), 2, 2)
        self.daily_atr = QLineEdit()
        self.daily_atr.setReadOnly(True)
        self.daily_atr.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.daily_atr.setPlaceholderText("Calculated")
        layout.addWidget(self.daily_atr, 2, 3)
        
        # Price Row
        # Current Price at DateTime
        layout.addWidget(QLabel("Current Price at DateTime:"), 3, 0)
        self.current_price = QLineEdit()
        self.current_price.setReadOnly(True)
        self.current_price.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.current_price.setPlaceholderText("Calculated")
        layout.addWidget(self.current_price, 3, 1)
        
        # Open Price
        layout.addWidget(QLabel("Open Price (If DateTime\nEntered is after Open):"), 3, 2)
        self.open_price = QLineEdit()
        self.open_price.setReadOnly(True)
        self.open_price.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.open_price.setPlaceholderText("Calculated at market open")
        layout.addWidget(self.open_price, 3, 3)
        
        # ATR High/Low
        layout.addWidget(QLabel("ATR High:"), 4, 0)
        self.atr_high = QLineEdit()
        self.atr_high.setReadOnly(True)
        self.atr_high.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_high.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_high, 4, 1)
        
        layout.addWidget(QLabel("ATR Low:"), 4, 2)
        self.atr_low = QLineEdit()
        self.atr_low.setReadOnly(True)
        self.atr_low.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_low.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_low, 4, 3)
        
        self.setLayout(layout)
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update all metric displays with calculated values"""
        if 'atr_5min' in metrics:
            self.atr_5min.setText(f"{metrics['atr_5min']:.2f}")
        if 'atr_10min' in metrics:
            self.atr_10min.setText(f"{metrics['atr_10min']:.2f}")
        if 'atr_15min' in metrics:
            self.atr_15min.setText(f"{metrics['atr_15min']:.2f}")
        if 'daily_atr' in metrics:
            self.daily_atr.setText(f"{metrics['daily_atr']:.2f}")
        if 'current_price' in metrics:
            self.current_price.setText(f"{metrics['current_price']:.2f}")
        if 'open_price' in metrics:
            self.open_price.setText(f"{metrics['open_price']:.2f}")
        if 'atr_high' in metrics:
            self.atr_high.setText(f"{metrics['atr_high']:.2f}")
        if 'atr_low' in metrics:
            self.atr_low.setText(f"{metrics['atr_low']:.2f}")
    
    def clear_all(self):
        """Clear all metric displays"""
        self.atr_5min.clear()
        self.atr_10min.clear()
        self.atr_15min.clear()
        self.daily_atr.clear()
        self.current_price.clear()
        self.open_price.clear()
        self.atr_high.clear()
        self.atr_low.clear()


class M15ZoneTable(QTableWidget):
    """Table for M15 zone data entry"""
    
    def __init__(self):
        super().__init__(6, 5)  # 6 rows, 5 columns
        self.setStyleSheet(DarkStyleSheets.TABLE)
        self._init_table()
        
        # Set fixed height for exactly 6 rows
        self.verticalHeader().setDefaultSectionSize(30)
        header_height = self.horizontalHeader().height()
        row_height = 30 * 6  # 6 rows at 30 pixels each
        self.setFixedHeight(header_height + row_height + 2)  # +2 for borders
        
    def _init_table(self):
        # Set headers
        headers = ["Zone", "Candlestick DateTime", "Level", "Zone High", "Zone Low"]
        self.setHorizontalHeaderLabels(headers)
        
        # Hide vertical header (row numbers)
        self.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.setColumnWidth(0, 50)
        
        # Initialize zone numbers and colors
        for row in range(6):
            # Zone number
            zone_item = QTableWidgetItem(str(row + 1))
            zone_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            zone_item.setFlags(zone_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Apply zone color
            if row < len(DarkTheme.ZONE_COLORS):
                zone_item.setBackground(QColor(DarkTheme.ZONE_COLORS[row]))
            
            self.setItem(row, 0, zone_item)
            
            # Initialize other cells
            for col in range(1, 5):
                item = QTableWidgetItem("")
                self.setItem(row, col, item)
    
    def get_zone_data(self):
        """Get all zone data from the table"""
        zones = []
        for row in range(self.rowCount()):
            zone_data = {
                'zone_number': row + 1,
                'datetime': self.item(row, 1).text() if self.item(row, 1) else "",
                'level': self.item(row, 2).text() if self.item(row, 2) else "",
                'high': self.item(row, 3).text() if self.item(row, 3) else "",
                'low': self.item(row, 4).text() if self.item(row, 4) else "",
            }
            zones.append(zone_data)
        return zones


class CalculationsDisplay(QWidget):
    """Widget for displaying calculation results"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Calculations")
        title.setStyleSheet(f"""
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
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create two rows of displays
        # Row 1: HVN displays
        hvn_layout = QHBoxLayout()
        
        self.hvn_7day = self._create_calc_display("7-Day HVN")
        self.hvn_14day = self._create_calc_display("14-Day HVN")
        self.hvn_30day = self._create_calc_display("30-Day HVN")
        
        hvn_layout.addWidget(self.hvn_7day)
        hvn_layout.addWidget(self.hvn_14day)
        hvn_layout.addWidget(self.hvn_30day)
        
        layout.addLayout(hvn_layout)
        
        # Row 2: Camarilla Pivots
        cam_layout = QHBoxLayout()
        
        self.cam_monthly = self._create_calc_display("Monthly Cam Pivots")
        self.cam_weekly = self._create_calc_display("Weekly Cam Pivots")
        self.cam_daily = self._create_calc_display("Daily Cam Pivots")
        
        cam_layout.addWidget(self.cam_monthly)
        cam_layout.addWidget(self.cam_weekly)
        cam_layout.addWidget(self.cam_daily)
        
        layout.addLayout(cam_layout)
        
        self.setLayout(layout)
    
    def _create_calc_display(self, title):
        """Create a calculation display widget"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet(DarkStyleSheets.FRAME)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"font-weight: bold; color: {DarkTheme.TEXT_PRIMARY};")
        layout.addWidget(label)
        
        text_area = QTextEdit()
        text_area.setStyleSheet(DarkStyleSheets.TEXT_AREA)
        text_area.setMinimumHeight(120)
        text_area.setReadOnly(True)
        layout.addWidget(text_area)
        
        frame.setLayout(layout)
        frame.text_area = text_area  # Store reference for access
        return frame


class OverviewWidget(QWidget):
    """
    Main overview widget containing all primary controls and displays
    """
    
    # Signals
    save_to_database = pyqtSignal(dict)  # Save session data to Supabase
    analysis_requested = pyqtSignal(dict)  # Session data for analysis
    data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DarkStyleSheets.WIDGET_CONTAINER)
        
        # Initialize Polygon service
        self.polygon_service = PolygonService()
        self.polygon_service.metrics_updated.connect(self._on_metrics_updated)
        self.polygon_service.connection_status.connect(self._on_connection_status)
        
        self._init_ui()
        self._connect_polygon_signals()
    
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
        container_layout.addWidget(self.session_info)
        
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
        
        # Metrics section
        self.metrics_frame = MetricsFrame()
        container_layout.addWidget(self.metrics_frame)
        
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
        
        # Save to Database button
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        
        self.save_to_db_btn = QPushButton("Save to Supabase")
        self.save_to_db_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.SUCCESS};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:pressed {{
                background-color: #3d8b40;
            }}
        """)
        self.save_to_db_btn.setMinimumWidth(200)
        self.save_to_db_btn.clicked.connect(self._on_save_to_database)
        save_button_layout.addWidget(self.save_to_db_btn)
        
        save_button_layout.addStretch()
        container_layout.addLayout(save_button_layout)
        
        # Add stretch at bottom
        container_layout.addStretch()
        
        container.setLayout(container_layout)
        scroll_area.setWidget(container)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def _connect_polygon_signals(self):
        """Connect Polygon service signals"""
        # Connect fetch button
        self.session_info.fetch_data_btn.clicked.connect(self._fetch_market_data)
        
        # Auto-fetch when ticker is entered and loses focus
        self.session_info.ticker_input.editingFinished.connect(self._on_ticker_changed)
        
        # Connect datetime changes for potential re-fetch
        self.session_info.datetime_input.dateTimeChanged.connect(self._on_datetime_changed)
    
    @pyqtSlot()
    def _fetch_market_data(self):
        """Fetch market data from Polygon"""
        ticker = self.session_info.ticker_input.text().strip()
        if not ticker:
            QMessageBox.warning(self, "Missing Ticker", "Please enter a ticker symbol.")
            return
        
        session_datetime = self.session_info.datetime_input.dateTime().toPyDateTime()
        
        # Update status
        self.session_info.fetch_data_btn.setEnabled(False)
        self.session_info.fetch_data_btn.setText("Fetching...")
        
        # Update status bar if available
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Fetching market data for {ticker}...")
        
        # Fetch data
        self.polygon_service.fetch_session_data(ticker, session_datetime)
    
    @pyqtSlot()
    def _on_ticker_changed(self):
        """Handle ticker change - only fetch if we have a valid ticker"""
        ticker = self.session_info.ticker_input.text().strip()
        if ticker and len(ticker) >= 1:  # Only auto-fetch if ticker is entered
            self._fetch_market_data()
    
    @pyqtSlot()
    def _on_datetime_changed(self):
        """Handle datetime change - only fetch if we have a ticker"""
        ticker = self.session_info.ticker_input.text().strip()
        if ticker:
            # Optional: Only fetch if datetime changed significantly
            # For now, we'll let the user manually fetch after datetime changes
            pass
    
    @pyqtSlot(dict)
    def _on_metrics_updated(self, metrics: dict):
        """Handle metrics update from Polygon service"""
        self.metrics_frame.update_metrics(metrics)
        
        # Re-enable button
        self.session_info.fetch_data_btn.setEnabled(True)
        self.session_info.fetch_data_btn.setText("Fetch Market Data")
        
        # Update status bar if available
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("Market data fetched successfully", 5000)
        
        # Emit data changed signal
        self.data_changed.emit()
    
    @pyqtSlot(bool, str)
    def _on_connection_status(self, connected: bool, message: str):
        """Handle connection status from Polygon service"""
        if not connected:
            QMessageBox.warning(
                self, 
                "Polygon Connection", 
                f"Unable to connect to Polygon REST API:\n{message}\n\n"
                "Please ensure the Polygon server is running at http://localhost:8000"
            )
    
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
        return {
            'ticker': self.session_info.ticker_input.text().strip().upper(),
            'is_live': self.session_info.live_toggle.isChecked(),
            'datetime': self.session_info.datetime_input.dateTime().toPyDateTime(),
            'weekly': self.weekly_frame.get_data(),
            'daily': self.daily_frame.get_data(),
            'zones': self.zone_table.get_zone_data(),
            'timestamp': datetime.now()
        }
    
    def load_session_data(self, session_data: Dict[str, Any]):
        """Load session data into the UI"""
        # Load ticker and datetime
        if 'ticker' in session_data:
            self.session_info.ticker_input.setText(session_data['ticker'])
        
        if 'is_live' in session_data:
            self.session_info.live_toggle.setChecked(session_data['is_live'])
        
        if 'datetime' in session_data:
            dt = session_data['datetime']
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            self.session_info.datetime_input.setDateTime(QDateTime(dt))
        
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
        
        # Load zones
        if 'zones' in session_data and session_data['zones']:
            for row, zone in enumerate(session_data['zones'][:6]):
                if 'datetime' in zone:
                    self.zone_table.item(row, 1).setText(zone['datetime'])
                if 'level' in zone:
                    self.zone_table.item(row, 2).setText(str(zone['level']))
                if 'high' in zone:
                    self.zone_table.item(row, 3).setText(str(zone['high']))
                if 'low' in zone:
                    self.zone_table.item(row, 4).setText(str(zone['low']))
        
        # After loading, fetch market data
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
        self.session_info.datetime_input.setDateTime(QDateTime.currentDateTime())
        
        # Clear weekly
        self.weekly_frame.clear_all()
        
        # Clear daily
        self.daily_frame.clear_all()
        
        # Clear metrics
        self.metrics_frame.clear_all()
        
        # Clear table
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