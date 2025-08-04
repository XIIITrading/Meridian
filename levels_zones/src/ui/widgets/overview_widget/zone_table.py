"""
Zone table for the Overview Widget
Handles M15 zone data entry in a table format
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.dark_theme import DarkTheme, DarkStyleSheets


class M15ZoneTable(QTableWidget):
    """Table for M15 zone data entry"""
    
    def __init__(self):
        super().__init__(6, 6)  # 6 rows, 6 columns (increased from 5)
        self.setStyleSheet(DarkStyleSheets.TABLE)
        self._init_table()
        
        # Set fixed height for exactly 6 rows
        self.verticalHeader().setDefaultSectionSize(30)
        header_height = self.horizontalHeader().height()
        row_height = 30 * 6  # 6 rows at 30 pixels each
        self.setFixedHeight(header_height + row_height + 2)  # +2 for borders
        
    def _init_table(self):
        # Set headers
        headers = ["Zone", "Date", "Time", "Level", "Zone High", "Zone Low"]
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
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
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
            for col in range(1, 6):  # Updated from range(1, 5)
                item = QTableWidgetItem("")
                # Set light gray text as hint for date and time columns
                if col == 1:  # Date column
                    item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
                    item.setText("yyyy-mm-dd")
                elif col == 2:  # Time column
                    item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
                    item.setText("hh:mm:ss")
                self.setItem(row, col, item)
        
        # Connect itemChanged to clear placeholder text when user starts typing
        self.itemChanged.connect(self._on_item_changed)
    
    def _on_item_changed(self, item):
        """Clear placeholder text and restore normal color when user edits"""
        row = item.row()
        col = item.column()
        text = item.text()
        
        # For date column
        if col == 1 and text and text != "yyyy-mm-dd":
            item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))
        elif col == 1 and not text:
            item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
            item.setText("yyyy-mm-dd")
            
        # For time column
        if col == 2 and text and text != "hh:mm:ss":
            item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))
        elif col == 2 and not text:
            item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
            item.setText("hh:mm:ss")
    
    def get_zone_data(self):
        """Get all zone data from the table"""
        zones = []
        for row in range(self.rowCount()):
            # Get text, but ignore placeholder text
            date_text = self.item(row, 1).text() if self.item(row, 1) else ""
            if date_text == "yyyy-mm-dd":
                date_text = ""
                
            time_text = self.item(row, 2).text() if self.item(row, 2) else ""
            if time_text == "hh:mm:ss":
                time_text = ""
            
            zone_data = {
                'zone_number': row + 1,
                'date': date_text,
                'time': time_text,
                'level': self.item(row, 3).text() if self.item(row, 3) else "",
                'high': self.item(row, 4).text() if self.item(row, 4) else "",
                'low': self.item(row, 5).text() if self.item(row, 5) else "",
            }
            zones.append(zone_data)
        return zones