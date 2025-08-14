# levels_zones/src/ui/widgets/overview_widget/metrics_frame.py

"""
Metrics frame for the Overview Widget
Displays ATR metrics and price levels
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt

from ui.dark_theme import DarkTheme, DarkStyleSheets


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
        
        # 15-Minute ATR (moved to position 2)
        layout.addWidget(QLabel("15-Minute ATR:"), 1, 2)
        self.atr_15min = QLineEdit()
        self.atr_15min.setReadOnly(True)
        self.atr_15min.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_15min.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_15min, 1, 3)
        
        # 2-Hour ATR (replacing 10-minute)
        layout.addWidget(QLabel("2-Hour ATR:"), 2, 0)
        self.atr_2hour = QLineEdit()
        self.atr_2hour.setReadOnly(True)
        self.atr_2hour.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        self.atr_2hour.setPlaceholderText("Calculated")
        layout.addWidget(self.atr_2hour, 2, 1)
        
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
        if 'atr_2hour' in metrics:  # Changed from atr_10min
            self.atr_2hour.setText(f"{metrics['atr_2hour']:.2f}")
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
        self.atr_2hour.clear()  # Changed from atr_10min
        self.atr_15min.clear()
        self.daily_atr.clear()
        self.current_price.clear()
        self.open_price.clear()
        self.atr_high.clear()
        self.atr_low.clear()