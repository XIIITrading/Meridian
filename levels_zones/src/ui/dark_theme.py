"""
Dark theme configuration for Meridian Trading System
Provides a professional dark theme with grey accents
"""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtCore import Qt


class DarkTheme:
    """Dark theme color and style definitions"""
    
    # Background colors - different shades of grey
    BG_DARKEST = "#232323"      # RGB(35,35,35) - Main background
    BG_DARK = "#2b2b2b"         # RGB(43,43,43) - Secondary background
    BG_MEDIUM = "#353535"       # RGB(53,53,53) - Input fields
    BG_LIGHT = "#404040"        # RGB(64,64,64) - Hover states
    BG_LIGHTER = "#4a4a4a"      # RGB(74,74,74) - Selected items
    
    # Border and separator colors
    BORDER_DARK = "#1a1a1a"     # RGB(26,26,26) - Darker borders
    BORDER_NORMAL = "#555555"   # RGB(85,85,85) - Normal borders
    BORDER_LIGHT = "#666666"    # RGB(102,102,102) - Light borders
    BORDER_FOCUS = "#0d7377"    # Teal accent for focused elements
    
    # Text colors
    TEXT_PRIMARY = "#e0e0e0"    # RGB(224,224,224) - Primary text
    TEXT_SECONDARY = "#b0b0b0"  # RGB(176,176,176) - Secondary text
    TEXT_DISABLED = "#707070"   # RGB(112,112,112) - Disabled text
    TEXT_PLACEHOLDER = "#808080" # RGB(128,128,128) - Placeholder text
    
    # Accent colors
    ACCENT_PRIMARY = "#0d7377"   # Teal - Primary accent
    ACCENT_HOVER = "#14a1a5"     # Lighter teal - Hover state
    ACCENT_PRESSED = "#0a5a5d"   # Darker teal - Pressed state
    
    # Status colors
    SUCCESS = "#4caf50"         # Green
    WARNING = "#ff9800"         # Orange
    ERROR = "#f44336"           # Red
    INFO = "#2196f3"            # Blue
    
    # Trading specific colors
    BULL = "#26a69a"            # Teal-green for bullish
    BEAR = "#ef5350"            # Light red for bearish
    RANGE = "#ffa726"           # Orange for range
    
    # Zone colors (for the 6 zones)
    ZONE_COLORS = [
        "#ef5350",  # Zone 1 - Red
        "#ff7043",  # Zone 2 - Deep Orange
        "#ffa726",  # Zone 3 - Orange
        "#66bb6a",  # Zone 4 - Green
        "#42a5f5",  # Zone 5 - Blue
        "#ab47bc",  # Zone 6 - Purple
    ]
    
    # Font settings
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"
    FONT_SIZE_SMALL = 11
    FONT_SIZE_NORMAL = 11
    FONT_SIZE_MEDIUM = 12
    FONT_SIZE_LARGE = 13
    FONT_SIZE_XLARGE = 14
    FONT_SIZE_TITLE = 16


class DarkStyleSheets:
    """Complete style sheets for dark theme"""
    
    # Main window style
    MAIN_WINDOW = f"""
        QMainWindow {{
            background-color: {DarkTheme.BG_DARKEST};
        }}
    """
    
    # Widget container style
    WIDGET_CONTAINER = f"""
        QWidget {{
            background-color: {DarkTheme.BG_DARKEST};
            color: {DarkTheme.TEXT_PRIMARY};
        }}
    """
    
    # Group box style
    GROUP_BOX = f"""
        QGroupBox {{
            background-color: {DarkTheme.BG_DARK};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
            font-weight: bold;
            color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_PRIMARY};
        }}
    """
    
    # Input fields (LineEdit, SpinBox, etc.)
    INPUT_FIELD = f"""
        QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{
            background-color: {DarkTheme.BG_MEDIUM};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 3px;
            padding: 5px;
            color: {DarkTheme.TEXT_PRIMARY};
            selection-background-color: {DarkTheme.ACCENT_PRIMARY};
            selection-color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
            border: 1px solid {DarkTheme.BORDER_FOCUS};
            background-color: {DarkTheme.BG_LIGHT};
        }}
        
        QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
        QDateEdit:disabled, QTimeEdit:disabled, QDateTimeEdit:disabled {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_DISABLED};
            border: 1px solid {DarkTheme.BORDER_DARK};
        }}
        
        QLineEdit::placeholder {{
            color: {DarkTheme.TEXT_PLACEHOLDER};
        }}
    """
    
    # ComboBox style
    COMBO_BOX = f"""
        QComboBox {{
            background-color: {DarkTheme.BG_MEDIUM};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 3px;
            padding: 5px;
            color: {DarkTheme.TEXT_PRIMARY};
            min-width: 100px;
        }}
        
        QComboBox:focus {{
            border: 1px solid {DarkTheme.BORDER_FOCUS};
            background-color: {DarkTheme.BG_LIGHT};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {DarkTheme.TEXT_PRIMARY};
            margin-right: 5px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {DarkTheme.BG_DARK};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            selection-background-color: {DarkTheme.ACCENT_PRIMARY};
            color: {DarkTheme.TEXT_PRIMARY};
        }}
    """
    
    # Button styles
    BUTTON_PRIMARY = f"""
        QPushButton {{
            background-color: {DarkTheme.ACCENT_PRIMARY};
            border: none;
            border-radius: 3px;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            text-align: center;
        }}
        
        QPushButton:hover {{
            background-color: {DarkTheme.ACCENT_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkTheme.ACCENT_PRESSED};
        }}
        
        QPushButton:disabled {{
            background-color: {DarkTheme.BG_LIGHT};
            color: {DarkTheme.TEXT_DISABLED};
        }}
    """
    
    BUTTON_SECONDARY = f"""
        QPushButton {{
            background-color: {DarkTheme.BG_LIGHT};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 3px;
            color: {DarkTheme.TEXT_PRIMARY};
            padding: 8px 16px;
        }}
        
        QPushButton:hover {{
            background-color: {DarkTheme.BG_LIGHTER};
            border: 1px solid {DarkTheme.BORDER_LIGHT};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkTheme.BG_MEDIUM};
        }}
        
        QPushButton:disabled {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_DISABLED};
            border: 1px solid {DarkTheme.BORDER_DARK};
        }}
    """
    
    # Table style
    TABLE = f"""
        QTableWidget {{
            background-color: {DarkTheme.BG_DARK};
            alternate-background-color: {DarkTheme.BG_MEDIUM};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            gridline-color: {DarkTheme.BORDER_DARK};
            color: {DarkTheme.TEXT_PRIMARY};
            selection-background-color: {DarkTheme.ACCENT_PRIMARY};
            selection-color: white;
        }}
        
        QTableWidget::item {{
            padding: 5px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {DarkTheme.ACCENT_PRIMARY};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {DarkTheme.BG_MEDIUM};
            color: {DarkTheme.TEXT_PRIMARY};
            border: none;
            border-right: 1px solid {DarkTheme.BORDER_DARK};
            border-bottom: 1px solid {DarkTheme.BORDER_NORMAL};
            padding: 6px;
            font-weight: bold;
        }}
        
        QTableCornerButton::section {{
            background-color: {DarkTheme.BG_MEDIUM};
            border: none;
            border-right: 1px solid {DarkTheme.BORDER_DARK};
            border-bottom: 1px solid {DarkTheme.BORDER_NORMAL};
        }}
    """
    
    # Text area style
    TEXT_AREA = f"""
        QTextEdit, QPlainTextEdit {{
            background-color: {DarkTheme.BG_MEDIUM};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 3px;
            color: {DarkTheme.TEXT_PRIMARY};
            padding: 8px;
            font-family: {DarkTheme.FONT_FAMILY_MONO};
            font-size: {DarkTheme.FONT_SIZE_NORMAL}px;
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {DarkTheme.BORDER_FOCUS};
            background-color: {DarkTheme.BG_LIGHT};
        }}
        
        QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_DISABLED};
            border: 1px solid {DarkTheme.BORDER_DARK};
        }}
    """
    
    # Label styles
    LABEL_PRIMARY = f"""
        QLabel {{
            color: {DarkTheme.TEXT_PRIMARY};
            background-color: transparent;
        }}
    """
    
    LABEL_SECONDARY = f"""
        QLabel {{
            color: {DarkTheme.TEXT_SECONDARY};
            background-color: transparent;
        }}
    """
    
    LABEL_TITLE = f"""
        QLabel {{
            color: {DarkTheme.TEXT_PRIMARY};
            font-size: {DarkTheme.FONT_SIZE_TITLE}px;
            font-weight: bold;
            background-color: transparent;
        }}
    """
    
    # CheckBox style
    CHECKBOX = f"""
        QCheckBox {{
            color: {DarkTheme.TEXT_PRIMARY};
            spacing: 5px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            background-color: {DarkTheme.BG_MEDIUM};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {DarkTheme.ACCENT_PRIMARY};
            border: 1px solid {DarkTheme.ACCENT_PRIMARY};
        }}
        
        QCheckBox::indicator:checked:disabled {{
            background-color: {DarkTheme.BG_LIGHT};
            border: 1px solid {DarkTheme.BORDER_DARK};
        }}
        
        QCheckBox::indicator:unchecked:hover {{
            background-color: {DarkTheme.BG_LIGHT};
            border: 1px solid {DarkTheme.BORDER_LIGHT};
        }}
    """
    
    # Scroll bar style
    SCROLL_BAR = f"""
        QScrollBar:vertical {{
            background-color: {DarkTheme.BG_DARK};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {DarkTheme.BG_LIGHTER};
            min-height: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {DarkTheme.BORDER_NORMAL};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {DarkTheme.BG_DARK};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {DarkTheme.BG_LIGHTER};
            min-width: 20px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {DarkTheme.BORDER_NORMAL};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            width: 0px;
        }}
    """
    
    # Menu bar style
    MENU_BAR = f"""
        QMenuBar {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_PRIMARY};
            border-bottom: 1px solid {DarkTheme.BORDER_DARK};
            padding: 2px;
        }}
        
        QMenuBar::item {{
            padding: 4px 10px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {DarkTheme.BG_LIGHT};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {DarkTheme.BG_LIGHTER};
        }}
    """
    
    # Menu style
    MENU = f"""
        QMenu {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 20px;
            border-radius: 3px;
        }}
        
        QMenu::item:selected {{
            background-color: {DarkTheme.ACCENT_PRIMARY};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {DarkTheme.BORDER_DARK};
            margin: 4px 10px;
        }}
    """
    
    # Status bar style
    STATUS_BAR = f"""
        QStatusBar {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_SECONDARY};
            border-top: 1px solid {DarkTheme.BORDER_DARK};
        }}
        
        QStatusBar::item {{
            border: none;
        }}
    """
    
    # Tool bar style
    TOOL_BAR = f"""
        QToolBar {{
            background-color: {DarkTheme.BG_DARK};
            border-bottom: 1px solid {DarkTheme.BORDER_DARK};
            padding: 4px;
            spacing: 4px;
        }}
        
        QToolBar::separator {{
            background-color: {DarkTheme.BORDER_NORMAL};
            width: 1px;
            margin: 4px 8px;
        }}
    """
    
    # Frame style for sections
    FRAME = f"""
        QFrame {{
            background-color: {DarkTheme.BG_DARK};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            border-radius: 5px;
        }}
    """


def apply_dark_theme(app):
    """
    Apply the dark theme to a QApplication instance
    
    Args:
        app: QApplication instance
    """
    # Create palette
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(DarkTheme.BG_DARKEST))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(DarkTheme.TEXT_PRIMARY))
    
    # Base colors (for input widgets)
    palette.setColor(QPalette.ColorRole.Base, QColor(DarkTheme.BG_MEDIUM))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DarkTheme.BG_DARK))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(DarkTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(DarkTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DarkTheme.TEXT_PLACEHOLDER))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(DarkTheme.BG_LIGHT))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(DarkTheme.TEXT_PRIMARY))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(DarkTheme.ACCENT_PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    
    # Apply palette
    app.setPalette(palette)
    
    # Set default font
    font = QFont(DarkTheme.FONT_FAMILY, DarkTheme.FONT_SIZE_NORMAL)
    app.setFont(font)
    
    # Apply global style sheet
    global_style = f"""
        QToolTip {{
            background-color: {DarkTheme.BG_LIGHTER};
            color: {DarkTheme.TEXT_PRIMARY};
            border: 1px solid {DarkTheme.BORDER_NORMAL};
            padding: 4px;
        }}
        
        QMessageBox {{
            background-color: {DarkTheme.BG_DARK};
            color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QMessageBox QLabel {{
            color: {DarkTheme.TEXT_PRIMARY};
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
        }}
    """
    
    app.setStyleSheet(global_style)


def get_combined_stylesheet():
    """
    Get all stylesheets combined into one string
    
    Returns:
        str: Combined stylesheet
    """
    return "\n".join([
        DarkStyleSheets.MAIN_WINDOW,
        DarkStyleSheets.WIDGET_CONTAINER,
        DarkStyleSheets.GROUP_BOX,
        DarkStyleSheets.INPUT_FIELD,
        DarkStyleSheets.COMBO_BOX,
        DarkStyleSheets.BUTTON_PRIMARY,
        DarkStyleSheets.TABLE,
        DarkStyleSheets.TEXT_AREA,
        DarkStyleSheets.LABEL_PRIMARY,
        DarkStyleSheets.CHECKBOX,
        DarkStyleSheets.SCROLL_BAR,
        DarkStyleSheets.MENU_BAR,
        DarkStyleSheets.MENU,
        DarkStyleSheets.STATUS_BAR,
        DarkStyleSheets.TOOL_BAR,
        DarkStyleSheets.FRAME,
    ])