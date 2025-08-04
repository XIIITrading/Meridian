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