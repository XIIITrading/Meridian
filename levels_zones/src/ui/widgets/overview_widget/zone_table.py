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
        super().__init__(6, 6)  # 6 rows, 6 columns
        self.setStyleSheet(DarkStyleSheets.TABLE)
        self._init_table()
        
        # Set fixed height for exactly 6 rows
        self.verticalHeader().setDefaultSectionSize(30)
        header_height = self.horizontalHeader().height()
        row_height = 30 * 6  # 6 rows at 30 pixels each
        self.setFixedHeight(header_height + row_height + 2)  # +2 for borders
        
    def _init_table(self):
        # Set headers - add UTC indicator
        headers = ["Zone", "Date", "Time (UTC)", "Level", "Zone High", "Zone Low"]
        self.setHorizontalHeaderLabels(headers)
        
        # Add tooltip to time column header
        self.horizontalHeaderItem(2).setToolTip(
            "Enter time in UTC format (hh:mm:ss)\n"
            "Market hours in UTC:\n"
            "• Pre-market: 08:00-14:30\n"
            "• Regular: 14:30-21:00\n"
            "• After-hours: 21:00-00:00"
        )
        
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
            for col in range(1, 6):
                item = QTableWidgetItem("")
                # Set light gray text as hint for date and time columns
                if col == 1:  # Date column
                    item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
                    item.setText("yyyy-mm-dd")
                    item.setToolTip("Enter date in YYYY-MM-DD format")
                elif col == 2:  # Time column
                    item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
                    item.setText("hh:mm:ss UTC")  # Added UTC indicator
                    item.setToolTip(
                        "Enter time in UTC (hh:mm:ss)\n"
                        "Example: 14:30:00 for market open\n"
                        "Example: 21:00:00 for market close"
                    )
                elif col == 3:  # Level column
                    item.setToolTip("Mid price of the candle (calculated automatically)")
                elif col == 4:  # Zone High column
                    item.setToolTip("High price of the 15-minute candle")
                elif col == 5:  # Zone Low column
                    item.setToolTip("Low price of the 15-minute candle")
                    
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
            
        # For time column - updated for UTC
        if col == 2 and text and text not in ["hh:mm:ss", "hh:mm:ss UTC"]:
            item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))
        elif col == 2 and not text:
            item.setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
            item.setText("hh:mm:ss UTC")
    
    def get_zone_data(self):
        """Get all zone data from the table"""
        zones = []
        for row in range(self.rowCount()):
            # Get text, but ignore placeholder text
            date_text = self.item(row, 1).text() if self.item(row, 1) else ""
            if date_text == "yyyy-mm-dd":
                date_text = ""
                
            time_text = self.item(row, 2).text() if self.item(row, 2) else ""
            if time_text in ["hh:mm:ss", "hh:mm:ss UTC"]:
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
    
    def set_zone_data(self, row: int, data: dict):
        """Set data for a specific zone row"""
        if 0 <= row < self.rowCount():
            if 'date' in data and data['date']:
                self.item(row, 1).setText(data['date'])
                self.item(row, 1).setForeground(QColor(DarkTheme.TEXT_PRIMARY))
            if 'time' in data and data['time']:
                self.item(row, 2).setText(data['time'])
                self.item(row, 2).setForeground(QColor(DarkTheme.TEXT_PRIMARY))
            if 'level' in data:
                self.item(row, 3).setText(str(data['level']))
            if 'high' in data:
                self.item(row, 4).setText(str(data['high']))
            if 'low' in data:
                self.item(row, 5).setText(str(data['low']))
    
    def clear_zone_data(self, row: int):
        """Clear data for a specific zone row"""
        if 0 <= row < self.rowCount():
            # Reset date
            self.item(row, 1).setText("yyyy-mm-dd")
            self.item(row, 1).setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
            
            # Reset time
            self.item(row, 2).setText("hh:mm:ss UTC")
            self.item(row, 2).setForeground(QColor(DarkTheme.TEXT_PLACEHOLDER))
            
            # Clear other fields
            for col in range(3, 6):
                self.item(row, col).setText("")
    
    def clear_all_zones(self):
        """Clear all zone data"""
        for row in range(self.rowCount()):
            self.clear_zone_data(row)
    
    def validate_zone_times(self):
        """Validate that all zone times are in valid UTC format"""
        errors = []
        
        for row in range(self.rowCount()):
            time_text = self.item(row, 2).text() if self.item(row, 2) else ""
            
            # Skip empty or placeholder
            if not time_text or time_text in ["hh:mm:ss", "hh:mm:ss UTC"]:
                continue
            
            # Check time format
            time_parts = time_text.split(':')
            if len(time_parts) != 3:
                errors.append(f"Zone {row + 1}: Invalid time format. Use hh:mm:ss")
                continue
            
            try:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2])
                
                if not (0 <= hour <= 23):
                    errors.append(f"Zone {row + 1}: Hour must be 0-23")
                if not (0 <= minute <= 59):
                    errors.append(f"Zone {row + 1}: Minute must be 0-59")
                if not (0 <= second <= 59):
                    errors.append(f"Zone {row + 1}: Second must be 0-59")
                    
            except ValueError:
                errors.append(f"Zone {row + 1}: Time must contain only numbers")
        
        return errors
    
    def get_valid_zone_count(self):
        """Get count of zones with valid date and time entries"""
        count = 0
        for row in range(self.rowCount()):
            date_text = self.item(row, 1).text() if self.item(row, 1) else ""
            time_text = self.item(row, 2).text() if self.item(row, 2) else ""
            
            if (date_text and date_text != "yyyy-mm-dd" and 
                time_text and time_text not in ["hh:mm:ss", "hh:mm:ss UTC"]):
                count += 1
        
        return count