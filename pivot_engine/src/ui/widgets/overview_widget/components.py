"""
Utility components for the Overview Widget
Contains small reusable components used across the overview interface
"""

from PyQt6.QtWidgets import QComboBox, QLabel
from PyQt6.QtCore import Qt

from ui.dark_theme import DarkTheme, DarkStyleSheets


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