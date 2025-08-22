"""
Pivot Confluence Widget for Camarilla Pivot Zones
Replaces M15 zone data entry with Daily Camarilla pivot confluence table
"""

from typing import Dict, List, Any
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton
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
        """Create the pivot confluence table with visual indicators"""
        # 6 rows (R6, R4, R3, S3, S4, S6), 19 columns (added PD Open and PD Close)
        table = QTableWidget(6, 19)
        table.setStyleSheet(DarkStyleSheets.TABLE)
        
        # Set headers - separated market structure components with PD Open and PD Close
        headers = [
            "Level", "Price", "Zone Range",
            "7-Day HVN", "14-Day HVN", "30-Day HVN",
            "Monthly Pivots", "Weekly Pivots", "Weekly Zones",
            "Daily Zones", "ATR Zones", 
            "ON High", "ON Low", "PD High", "PD Low", "PD Open", "PD Close",  # Added PD Open and PD Close
            "Score", "Level"
        ]
        table.setHorizontalHeaderLabels(headers)
        
        # Set column resize mode - all columns stretch equally
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Optionally set minimum widths to prevent columns from becoming too narrow
        header.setMinimumSectionSize(35)  # Minimum width of 35 pixels per column
        
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
            
            # Price (read-only)
            price_item = QTableWidgetItem("")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 1, price_item)
            
            # Zone Range (read-only)
            range_item = QTableWidgetItem("")
            range_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            range_item.setFlags(range_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 2, range_item)
            
            # Confluence indicator cells (columns 3-16)
            for col in range(3, 17):
                indicator_item = QTableWidgetItem("")
                indicator_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                indicator_item.setFlags(indicator_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, col, indicator_item)
            
            # Score (read-only)
            score_item = QTableWidgetItem("0")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item.setFlags(score_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 17, score_item)
            
            # Level designation (read-only)
            level_item = QTableWidgetItem("L1")
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 18, level_item)
        
        # Set table height for exactly 6 rows
        table.verticalHeader().setDefaultSectionSize(35)
        header_height = table.horizontalHeader().height()
        row_height = 35 * 6
        table.setFixedHeight(header_height + row_height + 2)
        
        return table
    
    def update_pivot_data(self, pivot_confluence_results):
        """Update the table with pivot confluence results and visual indicators"""
        if not pivot_confluence_results or not hasattr(pivot_confluence_results, 'pivot_zones'):
            logger.warning("No pivot confluence results to display")
            return
        
        # Store the data
        self.pivot_zones_data = pivot_confluence_results.pivot_zones
        
        # Clear all confluence indicators first
        self._clear_confluence_indicators()
        
        # Map confluence sources to column indices - separated market structure with PD Open/Close
        source_to_col = {
            'hvn_7day': 3,
            'hvn_14day': 4,
            'hvn_30day': 5,
            'monthly_pivots': 6,
            'weekly_pivots': 7,
            'weekly_zones': 8,
            'daily_zones': 9,
            'atr_zones': 10,
            'overnight_high': 11,  # Separated market structure
            'overnight_low': 12,
            'prior_day_high': 13,
            'prior_day_low': 14,
            'prior_day_open': 15,   # Added
            'prior_day_close': 16,  # Added
        }
        
        # Update table with results
        level_order = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
        
        for zone in pivot_confluence_results.pivot_zones:
            try:
                # Find the row for this level
                row = level_order.index(zone.level_name)
                
                # Update price
                self.pivot_table.item(row, 1).setText(f"${zone.pivot_price:.2f}")
                
                # Update zone range - more compact format
                range_text = f"${zone.zone_low:.2f}-${zone.zone_high:.2f}"
                self.pivot_table.item(row, 2).setText(range_text)
                
                # Update confluence indicators
                self._update_confluence_indicators(row, zone, source_to_col)
                
                # Update score (column 17 now)
                self.pivot_table.item(row, 17).setText(f"{zone.confluence_score:.0f}")
                
                # Update level designation (column 18 now)
                self.pivot_table.item(row, 18).setText(f"L{zone.level_designation.value}")
                
                # Color code based on score
                score_item = self.pivot_table.item(row, 17)
                level_item = self.pivot_table.item(row, 18)
                
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
    
    def _clear_confluence_indicators(self):
        """Clear all confluence indicator cells"""
        for row in range(6):
            for col in range(3, 17):  # Confluence columns (including all market structure)
                item = self.pivot_table.item(row, col)
                if item:
                    item.setText("")
                    item.setBackground(QColor(DarkTheme.BG_DARK))
                    item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))

    def _update_confluence_indicators(self, row: int, zone, source_to_col: Dict[str, int]):
        """Update confluence indicators for a specific zone"""
        try:
            # Check if zone has confluence_sources attribute
            if not hasattr(zone, 'confluence_sources') or not zone.confluence_sources:
                logger.debug(f"Zone {zone.level_name} has no confluence sources")
                return
            
            # Group confluence sources by type
            contributing_sources = {}
            
            for confluence_source in zone.confluence_sources:
                try:
                    # Get source type - handle both enum and string cases
                    if hasattr(confluence_source, 'source'):
                        if hasattr(confluence_source.source, 'value'):
                            source_type = confluence_source.source.value
                        else:
                            source_type = str(confluence_source.source)
                    else:
                        logger.warning(f"Confluence source missing 'source' attribute")
                        continue
                    
                    # Get source name for market structure separation
                    source_name = getattr(confluence_source, 'source_name', '')
                    
                    # Handle market structure sources separately
                    if source_type == 'market_structure':
                        # Map specific market structure sources (including PD Open/Close)
                        if 'Overnight High' in source_name:
                            contributing_sources['overnight_high'] = True
                        elif 'Overnight Low' in source_name:
                            contributing_sources['overnight_low'] = True
                        elif 'Prior Day High' in source_name:
                            contributing_sources['prior_day_high'] = True
                        elif 'Prior Day Low' in source_name:
                            contributing_sources['prior_day_low'] = True
                        elif 'Prior Day Open' in source_name:
                            contributing_sources['prior_day_open'] = True
                        elif 'Prior Day Close' in source_name:
                            contributing_sources['prior_day_close'] = True
                    else:
                        # Direct mapping for other sources
                        source_mapping = {
                            'hvn_7day': 'hvn_7day',
                            'hvn_14day': 'hvn_14day',
                            'hvn_30day': 'hvn_30day',
                            'monthly_pivots': 'monthly_pivots',
                            'weekly_pivots': 'weekly_pivots',
                            'weekly_zones': 'weekly_zones',
                            'daily_zones': 'daily_zones',
                            'atr_zones': 'atr_zones',
                        }
                        
                        mapped_source = source_mapping.get(source_type)
                        if mapped_source:
                            contributing_sources[mapped_source] = True
                            logger.debug(f"Mapped {source_type} -> {mapped_source} for {zone.level_name}")
                        
                except Exception as e:
                    logger.warning(f"Error processing confluence source: {e}")
                    continue
            
            # Update visual indicators
            for source_name, col_idx in source_to_col.items():
                item = self.pivot_table.item(row, col_idx)
                if item:
                    if contributing_sources.get(source_name, False):
                        # Show confluence indicator
                        item.setText("✓")
                        item.setForeground(QColor(DarkTheme.SUCCESS))
                        item.setBackground(QColor(DarkTheme.BG_LIGHT))
                        logger.debug(f"Set indicator for {zone.level_name} - {source_name}")
                    else:
                        # No confluence
                        item.setText("")
                        item.setBackground(QColor(DarkTheme.BG_DARK))
                        item.setForeground(QColor(DarkTheme.TEXT_PRIMARY))
            
            logger.info(f"Updated indicators for {zone.level_name}: {list(contributing_sources.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating confluence indicators for row {row}: {e}")
    
    def get_confluence_settings(self) -> Dict[str, Dict[str, bool]]:
        """Get confluence settings - all enabled since we show actual confluences"""
        settings = {}
        level_names = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
        source_names = [
            'hvn_7day', 'hvn_14day', 'hvn_30day',
            'monthly_pivots', 'weekly_pivots', 'weekly_zones',
            'daily_zones', 'atr_zones', 'market_structure'
        ]
        
        # Since we're showing actual confluences, all sources are enabled
        for level_name in level_names:
            settings[level_name] = {}
            for source_name in source_names:
                settings[level_name][source_name] = True
        
        return settings
    
    def clear_data(self):
        """Clear all pivot data"""
        self.pivot_zones_data = []
        
        # Clear all confluence indicators first
        self._clear_confluence_indicators()
        
        # Clear price, range, score, and level columns
        for row in range(6):
            self.pivot_table.item(row, 1).setText("")  # Price
            self.pivot_table.item(row, 2).setText("")  # Range
            self.pivot_table.item(row, 17).setText("0")  # Score (updated column)
            self.pivot_table.item(row, 18).setText("L1")  # Level (updated column)
            
            # Reset colors
            self.pivot_table.item(row, 17).setForeground(QColor(DarkTheme.TEXT_PRIMARY))
            self.pivot_table.item(row, 18).setForeground(QColor(DarkTheme.TEXT_PRIMARY))