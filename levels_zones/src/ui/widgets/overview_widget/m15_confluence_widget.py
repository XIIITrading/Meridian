"""
M15 Confluence Widget for displaying zone confluence in table format
Replaces text-based confluence display with visual table showing checkmarks
"""

from typing import Dict, List, Any, Optional
import logging
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.dark_theme import DarkTheme, DarkStyleSheets

logger = logging.getLogger(__name__)


class M15ConfluenceWidget(QWidget):
    """Widget for displaying M15 zone confluence in a table format"""
    
    # Signal when user wants to refresh confluence
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(DarkStyleSheets.WIDGET_CONTAINER)
        
        # Store zone confluence data
        self.zone_scores = []
        self.current_price = 0.0
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("M15 Zones Confluence Ranking")
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
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Create the confluence table
        self.confluence_table = self._create_confluence_table()
        layout.addWidget(self.confluence_table)
        
        # Legend
        legend_label = QLabel("Legend: L5=Highest (12+), L4=High (8-12), L3=Medium (5-8), L2=Low (2.5-5), L1=Minimal (<2.5)")
        legend_label.setStyleSheet(f"""
            QLabel {{
                color: {DarkTheme.TEXT_SECONDARY};
                font-size: 11px;
                padding: 5px;
            }}
        """)
        legend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(legend_label)
        
        self.setLayout(layout)
    
    def _create_confluence_table(self) -> QTableWidget:
        """Create the confluence table with visual indicators"""
        # 6 rows for M15 zones, columns for all confluence sources
        table = QTableWidget(6, 16)
        table.setStyleSheet(DarkStyleSheets.TABLE)
        
        # Set headers
        headers = [
            "Zone", "Price Range", "Direction",
            "HVN 7D", "HVN 14D", "HVN 30D",
            "Cam Monthly", "Cam Weekly", "Cam Daily",
            "Weekly Zones", "Daily Zones", "ATR Zones",
            "Daily Levels", "Metrics",
            "Score", "Level"
        ]
        table.setHorizontalHeaderLabels(headers)
        
        # Set column resize mode
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(40)
        
        # Set specific column widths for better visibility
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Zone
        table.setColumnWidth(0, 50)
        header.setSectionResizeMode(14, QHeaderView.ResizeMode.Fixed)  # Score
        table.setColumnWidth(14, 60)
        header.setSectionResizeMode(15, QHeaderView.ResizeMode.Fixed)  # Level
        table.setColumnWidth(15, 50)
        
        # Hide row headers
        table.verticalHeader().setVisible(False)
        
        # Set table height for exactly 6 rows
        table.verticalHeader().setDefaultSectionSize(35)
        header_height = table.horizontalHeader().height()
        row_height = 35 * 6
        table.setFixedHeight(header_height + row_height + 2)
        
        # Initialize empty cells
        for row in range(6):
            for col in range(16):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, col, item)
        
        return table
    
    def update_confluence_data(self, confluence_results: Any, current_price: Optional[float] = None):
        """Update the table with confluence results"""
        if not confluence_results or not hasattr(confluence_results, 'zone_scores'):
            logger.warning("No confluence results to display")
            self._clear_table()
            return
        
        # Store current price
        if current_price:
            self.current_price = float(current_price)
        
        # Get zone scores and sort by price (highest to lowest)
        self.zone_scores = sorted(
            confluence_results.zone_scores,
            key=lambda z: float(z.zone_center),
            reverse=True
        )
        
        # Clear table first
        self._clear_table()
        
        # Source type to column mapping
        source_to_col = {
            'HVN_7DAY': 3,
            'HVN_14DAY': 4,
            'HVN_30DAY': 5,
            'CAMARILLA_MONTHLY': 6,
            'CAMARILLA_WEEKLY': 7,
            'CAMARILLA_DAILY': 8,
            'WEEKLY_ZONES': 9,
            'DAILY_ZONES': 10,
            'ATR_ZONES': 11,
            'DAILY_LEVELS': 12,
            'ATR_LEVELS': 13,
            'REFERENCE_PRICES': 13  # Group with ATR levels in Metrics column
        }
        
        # Update table with zone data
        for row, zone_score in enumerate(self.zone_scores[:6]):  # Limit to 6 zones
            try:
                # Zone number with color
                zone_item = self.confluence_table.item(row, 0)
                zone_item.setText(str(zone_score.zone_number))
                if zone_score.zone_number - 1 < len(DarkTheme.ZONE_COLORS):
                    zone_item.setBackground(QColor(DarkTheme.ZONE_COLORS[zone_score.zone_number - 1]))
                
                # Price range
                range_item = self.confluence_table.item(row, 1)
                range_text = f"${float(zone_score.zone_low):.2f}-${float(zone_score.zone_high):.2f}"
                range_item.setText(range_text)
                
                # Direction relative to current price
                direction_item = self.confluence_table.item(row, 2)
                if self.current_price > 0:
                    zone_center = float(zone_score.zone_center)
                    if zone_center > self.current_price:
                        direction_item.setText("↑")
                        direction_item.setForeground(QColor(DarkTheme.BULL))
                    elif zone_center < self.current_price:
                        direction_item.setText("↓")
                        direction_item.setForeground(QColor(DarkTheme.BEAR))
                    else:
                        direction_item.setText("←→")
                        direction_item.setForeground(QColor(DarkTheme.RANGE))
                
                # Clear all confluence indicators for this row
                for col in range(3, 14):
                    item = self.confluence_table.item(row, col)
                    item.setText("")
                    item.setBackground(QColor(DarkTheme.BG_DARK))
                
                # Update confluence indicators
                for confluence_input in zone_score.confluent_inputs:
                    source_type = confluence_input.source_type
                    # Convert enum to string for mapping
                    source_key = source_type.name if hasattr(source_type, 'name') else str(source_type)
                    
                    if source_key in source_to_col:
                        col_idx = source_to_col[source_key]
                        item = self.confluence_table.item(row, col_idx)
                        
                        # Set checkmark
                        current_text = item.text()
                        if not current_text:
                            item.setText("✓")
                        else:
                            # Multiple confluences in same category
                            count = current_text.count("✓") + 1
                            if count <= 3:
                                item.setText("✓" * count)
                            else:
                                item.setText(f"✓×{count}")
                        
                        item.setForeground(QColor(DarkTheme.SUCCESS))
                        item.setBackground(QColor(DarkTheme.BG_LIGHT))
                
                # Score
                score_item = self.confluence_table.item(row, 14)
                score_item.setText(f"{zone_score.score:.1f}")
                
                # Level designation
                level_item = self.confluence_table.item(row, 15)
                level_item.setText(zone_score.confluence_level.value)
                
                # Color code based on score
                if zone_score.score >= 12:
                    color = QColor(DarkTheme.SUCCESS)
                elif zone_score.score >= 8:
                    color = QColor(DarkTheme.INFO)
                elif zone_score.score >= 5:
                    color = QColor(DarkTheme.WARNING)
                elif zone_score.score >= 2.5:
                    color = QColor("#FFA500")  # Orange
                else:
                    color = QColor(DarkTheme.TEXT_DISABLED)
                
                score_item.setForeground(color)
                level_item.setForeground(color)
                
                # Bold the highest scoring zone
                if row == 0:  # First zone after sorting by score
                    font = score_item.font()
                    font.setBold(True)
                    score_item.setFont(font)
                    level_item.setFont(font)
                
            except Exception as e:
                logger.error(f"Error updating row {row}: {e}")
                continue
    
    def _clear_table(self):
        """Clear all table data"""
        for row in range(6):
            for col in range(16):
                item = self.confluence_table.item(row, col)
                if item:
                    item.setText("")
                    item.setBackground(QColor(DarkTheme.BG_DARK))
                    item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))
                    
                    # Reset font
                    font = item.font()
                    font.setBold(False)
                    item.setFont(font)
    
    def clear_data(self):
        """Clear all confluence data"""
        self.zone_scores = []
        self.current_price = 0.0
        self._clear_table()
    
    def get_top_zones(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get the top scoring zones"""
        if not self.zone_scores:
            return []
        
        top_zones = []
        for zone in self.zone_scores[:count]:
            top_zones.append({
                'zone_number': zone.zone_number,
                'price_range': f"${float(zone.zone_low):.2f}-${float(zone.zone_high):.2f}",
                'score': zone.score,
                'level': zone.confluence_level.value,
                'confluences': len(zone.confluent_inputs)
            })
        
        return top_zones