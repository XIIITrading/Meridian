"""
Session information frame for the Overview Widget
Handles ticker entry, live toggle, date/time selection, and action buttons
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QDateEdit, QTimeEdit, QPushButton
)
from PyQt6.QtCore import QDate, QTime, pyqtSignal

from ui.dark_theme import DarkTheme, DarkStyleSheets


class SessionInfoFrame(QFrame):
    """Frame for session information (ticker, datetime, etc.)"""
    
    # Add signal for ticker changes
    ticker_changed = pyqtSignal(str)
    
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
        self.ticker_input.textChanged.connect(self._on_ticker_text_changed)
        layout.addWidget(self.ticker_input)
        
        # Live Toggle
        self.live_toggle = QCheckBox("Live Toggle")
        self.live_toggle.setStyleSheet(DarkStyleSheets.CHECKBOX)
        self.live_toggle.setChecked(True)
        layout.addWidget(self.live_toggle)
        
        # Date Entry
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        layout.addWidget(self.date_input)
        
        # Time Entry
        layout.addWidget(QLabel("Time:"))
        self.time_input = QTimeEdit()
        self.time_input.setTime(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm:ss")
        self.time_input.setStyleSheet(DarkStyleSheets.INPUT_FIELD)
        layout.addWidget(self.time_input)
        
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
        
        # Clear All Button (NEW - between Run Analysis and Save)
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.WARNING};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #e68900;
            }}
            QPushButton:pressed {{
                background-color: #cc7a00;
            }}
        """)
        self.clear_all_btn.setMinimumWidth(100)
        self.clear_all_btn.setToolTip("Clear all inputs and results (Ctrl+Shift+C)")
        self.clear_all_btn.setShortcut("Ctrl+Shift+C")
        layout.addWidget(self.clear_all_btn)
        
        # Save to Supabase Button
        self.save_to_db_btn = QPushButton("Save to Supabase")
        self.save_to_db_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.SUCCESS};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:pressed {{
                background-color: #3d8b40;
            }}
        """)
        self.save_to_db_btn.setMinimumWidth(120)
        layout.addWidget(self.save_to_db_btn)
        
        self.setLayout(layout)
    
    def _on_ticker_text_changed(self, text: str):
        """Handle ticker text changes"""
        self.ticker_changed.emit(text)