"""
Calculations display for the Overview Widget
Shows HVN and Camarilla pivot calculation results
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