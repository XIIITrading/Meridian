"""
Pivot Confluence Widget for Camarilla Pivot Zones
Replaces M15 zone data entry with Daily Camarilla pivot confluence table
"""

from typing import Dict, List, Any
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.dark_theme import DarkTheme, DarkStyleSheets

logger = logging.getLogger(__name__)


class PivotConfluenceWidget(QWidget):
    """Widget for displaying and configuring Daily Camarilla pivot confluence"""
    
    # Signals
    confluence_settings_changed = pyqtSignal()  # When user changes checkbox settings
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DarkStyleSheets.WIDGET_CONTAINER)
        
        # Store pivot zone data
        self.pivot_zones_data: List[Dict[str, Any]] = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and update button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Daily Camarilla Pivot Confluence")
        title_label.setStyleSheet(f"""
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
        header_layout.addWidget(title_label)
        
        # Update Confluence button
        self.update_confluence_btn = QPushButton("Update Confluence")
        self.update_confluence_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.INFO};
                border: none;
                border-radius: 3px;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #1976d2;
            }}
            QPushButton:pressed {{
                background-color: #0d47a1;
            }}
            QPushButton:disabled {{
                background-color: {DarkTheme.BG_LIGHT};
                color: {DarkTheme.TEXT_DISABLED};
            }}
        """)
        self.update_confluence_btn.setMaximumWidth(150)
        self.update_confluence_btn.setToolTip("Recalculate confluence with current settings")
        self.update_confluence_btn.clicked.connect(self.confluence_settings_changed.emit)
        header_layout.addWidget(self.update_confluence_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Create the pivot table
        self.pivot_table = self._create_pivot_table()
        layout.addWidget(self.pivot_table)
        
        self.setLayout(layout)
    
    def _create_pivot_table(self) -> QTableWidget:
        """Create the pivot confluence table"""
        # 6 rows (R6, R4, R3, S3, S4, S6), 13 columns
        table = QTableWidget(6, 13)
        table.setStyleSheet(DarkStyleSheets.TABLE)
        
        # Set headers
        headers = [
            "Level", "Price", "Zone Range",
            "7-Day HVN", "14-Day HVN", "30-Day HVN",
            "Monthly Pivots", "Weekly Pivots", "Weekly Zones",
            "Daily Zones", "ATR Zones", "Score", "Level"
        ]
        table.setHorizontalHeaderLabels(headers)
        
        # Set column properties
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Level
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Price
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Zone Range
        
        # Confluence checkboxes - fixed width
        for col in range(3, 11):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
        
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # Score
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed)  # Level
        
        table.setColumnWidth(0, 60)   # Level
        table.setColumnWidth(1, 80)   # Price
        table.setColumnWidth(11, 60)  # Score
        table.setColumnWidth(12, 50)  # Level
        
        # Set checkbox column widths
        for col in range(3, 11):
            table.setColumnWidth(col, 80)
        
        # Hide row headers
        table.verticalHeader().setVisible(False)
        
        # Initialize with level names
        level_names = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
        level_colors = [DarkTheme.ERROR, DarkTheme.WARNING, DarkTheme.INFO,
                       DarkTheme.INFO, DarkTheme.WARNING, DarkTheme.ERROR]
        
        for row, (level_name, color) in enumerate(zip(level_names, level_colors)):
            # Level name
            level_item = QTableWidgetItem(level_name)
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            level_item.setBackground(QColor(color))
            level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, level_item)
            
            # Price (read-only, will be populated by analysis)
            price_item = QTableWidgetItem("")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 1, price_item)
            
            # Zone Range (read-only, will be populated by analysis)
            range_item = QTableWidgetItem("")
            range_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            range_item.setFlags(range_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 2, range_item)
            
            # Score (read-only)
            score_item = QTableWidgetItem("0")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item.setFlags(score_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 11, score_item)
            
            # Level designation (read-only)
            level_item = QTableWidgetItem("L1")
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 12, level_item)
            
            # Create checkboxes for confluence sources (columns 3-10)
            for col in range(3, 11):
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                checkbox = QCheckBox()
                checkbox.setChecked(True)  # Default to checked
                checkbox.setStyleSheet(DarkStyleSheets.CHECKBOX)
                checkbox.stateChanged.connect(self.confluence_settings_changed.emit)
                
                checkbox_layout.addWidget(checkbox)
                table.setCellWidget(row, col, checkbox_widget)
        
        # Set table height for exactly 6 rows
        table.verticalHeader().setDefaultSectionSize(35)
        header_height = table.horizontalHeader().height()
        row_height = 35 * 6
        table.setFixedHeight(header_height + row_height + 2)
        
        return table
    
    def update_pivot_data(self, pivot_confluence_results):
        """Update the table with pivot confluence results"""
        if not pivot_confluence_results or not hasattr(pivot_confluence_results, 'pivot_zones'):
            logger.warning("No pivot confluence results to display")
            return
        
        # Store the data
        self.pivot_zones_data = pivot_confluence_results.pivot_zones
        
        # Update table with results
        level_order = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
        
        for zone in pivot_confluence_results.pivot_zones:
            try:
                # Find the row for this level
                row = level_order.index(zone.level_name)
                
                # Update price
                self.pivot_table.item(row, 1).setText(f"${zone.pivot_price:.2f}")
                
                # Update zone range
                range_text = f"${zone.zone_low:.2f} - ${zone.zone_high:.2f}"
                self.pivot_table.item(row, 2).setText(range_text)
                
                # Update score
                self.pivot_table.item(row, 11).setText(f"{zone.confluence_score:.0f}")
                
                # Update level designation
                self.pivot_table.item(row, 12).setText(f"L{zone.level_designation.value}")
                
                # Color code based on score
                score_item = self.pivot_table.item(row, 11)
                level_item = self.pivot_table.item(row, 12)
                
                if zone.confluence_score >= 12:
                    color = QColor(DarkTheme.SUCCESS)
                elif zone.confluence_score >= 8:
                    color = QColor(DarkTheme.INFO)
                elif zone.confluence_score >= 5:
                    color = QColor(DarkTheme.WARNING)
                elif zone.confluence_score >= 2:
                    color = QColor(DarkTheme.TEXT_SECONDARY)
                else:
                    color = QColor(DarkTheme.TEXT_DISABLED)
                
                score_item.setForeground(color)
                level_item.setForeground(color)
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not update row for level {zone.level_name}: {e}")
                continue
    
    def get_confluence_settings(self) -> Dict[str, Dict[str, bool]]:
        """Get current confluence checkbox settings"""
        settings = {}
        level_names = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
        source_names = [
            'hvn_7day', 'hvn_14day', 'hvn_30day',
            'monthly_pivots', 'weekly_pivots', 'weekly_zones',
            'daily_zones', 'atr_zones'
        ]
        
        for row, level_name in enumerate(level_names):
            settings[level_name] = {}
            
            for col, source_name in enumerate(source_names, start=3):
                widget = self.pivot_table.cellWidget(row, col)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        settings[level_name][source_name] = checkbox.isChecked()
                    else:
                        settings[level_name][source_name] = True  # Default
                else:
                    settings[level_name][source_name] = True  # Default
        
        return settings
    
    def clear_data(self):
        """Clear all pivot data"""
        self.pivot_zones_data = []
        
        # Clear price, range, score, and level columns
        for row in range(6):
            self.pivot_table.item(row, 1).setText("")  # Price
            self.pivot_table.item(row, 2).setText("")  # Range
            self.pivot_table.item(row, 11).setText("0")  # Score
            self.pivot_table.item(row, 12).setText("L1")  # Level
            
            # Reset colors
            self.pivot_table.item(row, 11).setForeground(QColor(DarkTheme.TEXT_PRIMARY))
            self.pivot_table.item(row, 12).setForeground(QColor(DarkTheme.TEXT_PRIMARY))