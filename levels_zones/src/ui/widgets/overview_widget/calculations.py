"""
Calculations display for the Overview Widget
Shows HVN and Camarilla pivot calculation results, plus zone displays
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTextEdit
)
from PyQt6.QtCore import Qt

from ui.dark_theme import DarkTheme, DarkStyleSheets


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
        
        # Row 3: Zone Displays
        zones_layout = QHBoxLayout()
        
        self.weekly_zones = self._create_calc_display("Weekly Zones (2Hr ATR)")
        self.daily_zones = self._create_calc_display("Daily Zones (15min ATR)")
        self.atr_zones = self._create_calc_display("ATR Zones (5min ATR)")
        
        zones_layout.addWidget(self.weekly_zones)
        zones_layout.addWidget(self.daily_zones)
        zones_layout.addWidget(self.atr_zones)
        
        layout.addLayout(zones_layout)
        
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
        text_area.setStyleSheet(DarkStyleSheets.CALCULATION_TEXT_AREA)
        text_area.setMinimumHeight(120)
        text_area.setReadOnly(True)
        
        # Set placeholder text based on the title
        if "7-Day HVN" in title:
            text_area.setPlaceholderText("HVN 7-day analysis will appear here...")
        elif "14-Day HVN" in title:
            text_area.setPlaceholderText("HVN 14-day analysis will appear here...")
        elif "30-Day HVN" in title:
            text_area.setPlaceholderText("HVN 30-day analysis will appear here...")
        elif "Monthly Cam" in title:
            text_area.setPlaceholderText("Monthly Camarilla pivots will appear here...")
        elif "Weekly Cam" in title:
            text_area.setPlaceholderText("Weekly Camarilla pivots will appear here...")
        elif "Daily Cam" in title:
            text_area.setPlaceholderText("Daily Camarilla pivots will appear here...")
        elif "Weekly Zones" in title:
            text_area.setPlaceholderText("Weekly zones will appear here after analysis...\n\nCreated from WL1-WL4 ± 2-Hour ATR")
        elif "Daily Zones" in title:
            text_area.setPlaceholderText("Daily zones will appear here after analysis...\n\nCreated from DL1-DL6 ± 15-Minute ATR")
        elif "ATR Zones" in title:
            text_area.setPlaceholderText(
                "ATR Zones will appear here after analysis...\n\n"
                "Dynamic zones based on:\n"
                "• ATR High: Current + Daily ATR ± 5min ATR\n"
                "• ATR Low: Current - Daily ATR ± 5min ATR"
            )
        
        layout.addWidget(text_area)
        
        frame.setLayout(layout)
        frame.text_area = text_area
        return frame
    
    def clear_all(self):
        """Clear all calculation displays"""
        # Clear HVN displays
        self.hvn_7day.text_area.clear()
        self.hvn_14day.text_area.clear()
        self.hvn_30day.text_area.clear()
        
        # Clear Camarilla displays
        self.cam_monthly.text_area.clear()
        self.cam_weekly.text_area.clear()
        self.cam_daily.text_area.clear()
        
        # Clear Zone displays
        self.weekly_zones.text_area.clear()
        self.daily_zones.text_area.clear()
        self.atr_zones.text_area.clear()