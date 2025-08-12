"""
Dialog for selecting a session to load from the database
"""

from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QDateEdit, QLineEdit, QMessageBox
)
from PyQt6.QtCore import QDate

from ui.dark_theme import get_combined_stylesheet


class SessionPickerDialog(QDialog):
    """Dialog for selecting a session to load"""
    
    def __init__(self, sessions: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.selected_session_id = None
        self.sessions = sessions
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the session picker UI"""
        self.setWindowTitle("Select Session to Load")
        self.setMinimumSize(800, 400)
        
        # Apply dark theme
        self.setStyleSheet(get_combined_stylesheet())
        
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Ticker filter
        filter_layout.addWidget(QLabel("Ticker:"))
        self.ticker_filter = QLineEdit()
        self.ticker_filter.setPlaceholderText("Filter by ticker...")
        self.ticker_filter.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.ticker_filter)
        
        # Date filter
        filter_layout.addWidget(QLabel("Date:"))
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setSpecialValueText("All dates")
        self.date_filter.dateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.date_filter)
        
        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Sessions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Ticker", "Session ID", "Date", "Live", "Weekly", "Daily", "Levels"
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        
        # Populate table
        self._populate_table(self.sessions)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _populate_table(self, sessions: List[Dict[str, Any]]):
        """Populate the table with session data"""
        self.table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            # Ticker
            self.table.setItem(row, 0, QTableWidgetItem(session['ticker']))
            
            # Session ID
            self.table.setItem(row, 1, QTableWidgetItem(session['ticker_id']))
            
            # Date
            date_str = session['date'].strftime('%Y-%m-%d')
            self.table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Live status
            live_status = "✓" if session['is_live'] else ""
            self.table.setItem(row, 3, QTableWidgetItem(live_status))
            
            # Weekly data
            weekly_status = "✓" if session['has_weekly'] else ""
            self.table.setItem(row, 4, QTableWidgetItem(weekly_status))
            
            # Daily data
            daily_status = "✓" if session['has_daily'] else ""
            self.table.setItem(row, 5, QTableWidgetItem(daily_status))
            
            # Level count
            self.table.setItem(row, 6, QTableWidgetItem(str(session['level_count'])))
            
        # Resize columns to content
        self.table.resizeColumnsToContents()
        
    def _apply_filters(self):
        """Apply filters to the table"""
        ticker_filter = self.ticker_filter.text().upper()
        
        # Check if date filter has a real date or is showing special text
        has_date_filter = self.date_filter.date() != self.date_filter.minimumDate()
        date_filter = self.date_filter.date().toPyDate() if has_date_filter else None
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Check ticker filter
            if ticker_filter:
                ticker_item = self.table.item(row, 0)
                if ticker_item and ticker_filter not in ticker_item.text():
                    show_row = False
            
            # Check date filter
            if date_filter:
                date_item = self.table.item(row, 2)
                if date_item:
                    row_date = datetime.strptime(date_item.text(), '%Y-%m-%d').date()
                    if row_date != date_filter:
                        show_row = False
            
            self.table.setRowHidden(row, not show_row)
            
    def _clear_filters(self):
        """Clear all filters"""
        self.ticker_filter.clear()
        self.date_filter.setDate(self.date_filter.minimumDate())
        self._apply_filters()
        
    def _on_double_click(self):
        """Handle double-click on a row"""
        self._on_accept()
        
    def _on_accept(self):
        """Handle accept button"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            session_id_item = self.table.item(current_row, 1)
            if session_id_item:
                self.selected_session_id = session_id_item.text()
                self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a session to load.")