"""
Analysis frames for the Overview Widget
Contains Weekly and Daily analysis data entry frames
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
    QTextEdit, QHBoxLayout, QDoubleSpinBox
)

from ui.dark_theme import DarkTheme, DarkStyleSheets
from .components import TrendSelector


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
        
        # Row 3: Weekly Price Levels (wl1-wl4)
        grid.addWidget(QLabel("Weekly Levels:"), 2, 0)
        
        levels_layout = QHBoxLayout()
        levels_layout.setSpacing(10)
        
        self.weekly_levels = []
        for i in range(4):  # Only 4 levels now (wl1-wl4)
            level_input = QDoubleSpinBox()
            level_input.setDecimals(2)
            level_input.setRange(0, 99999.99)
            level_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
            level_input.setPrefix(f"WL{i+1}: ")
            self.weekly_levels.append(level_input)
            levels_layout.addWidget(level_input)
        
        grid.addLayout(levels_layout, 2, 1, 1, 3)
        
        # Row 4: Notes
        grid.addWidget(QLabel("Notes:"), 3, 0)
        self.notes = QTextEdit()
        self.notes.setStyleSheet(DarkStyleSheets.TEXT_AREA)
        self.notes.setMaximumHeight(60)
        self.notes.setPlaceholderText("Weekly analysis notes...")
        grid.addWidget(self.notes, 3, 1, 1, 3)
        
        layout.addLayout(grid)
        self.setLayout(layout)
    
    def get_data(self) -> Dict[str, Any]:
        """Get weekly analysis data"""
        return {
            'trend_direction': self.trend_direction.currentText(),
            'internal_trend': self.internal_trend.currentText(),
            'position_structure': self.position_structure.value(),
            'eow_bias': self.eow_bias.currentText(),
            'price_levels': [level.value() for level in self.weekly_levels],  # Add this line
            'notes': self.notes.toPlainText()
        }
    
    def clear_all(self):
        """Clear all fields"""
        self.trend_direction.setCurrentIndex(0)
        self.internal_trend.setCurrentIndex(0)
        self.position_structure.setValue(0)
        self.eow_bias.setCurrentIndex(0)
        for level in self.weekly_levels:  # Clear weekly levels
            level.setValue(0)
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
        
        # Row 4: Price level inputs (6 levels, no above/below distinction)
        levels_layout = QHBoxLayout()
        levels_layout.setSpacing(10)
        
        self.price_levels = []
        for i in range(6):
            level_input = QDoubleSpinBox()
            level_input.setDecimals(2)
            level_input.setRange(0, 99999.99)
            level_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
            level_input.setPrefix(f"L{i+1}: ")
            self.price_levels.append(level_input)
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
            'price_levels': [level.value() for level in self.price_levels],
            'notes': self.notes.toPlainText()
        }
    
    def clear_all(self):
        """Clear all fields"""
        self.trend_direction.setCurrentIndex(0)
        self.internal_trend.setCurrentIndex(0)
        self.position_structure.setValue(0)
        self.eod_bias.setCurrentIndex(0)
        for level in self.price_levels:
            level.setValue(0)
        self.notes.clear()