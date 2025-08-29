"""
Data models for Zone Identification module
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class TradingLevel:
    """
    A tradeable fractal candlestick with confluence backing
    """
    # Fractal data (no defaults - must come first)
    datetime: datetime
    fractal_type: str  # 'high' or 'low'
    high_price: float
    low_price: float
    open_price: float
    close_price: float
    volume: float
    
    # Confluence data (no defaults)
    confluence_score: float
    confluence_level: str  # L1-L5
    overlapping_zones: List[Dict]  # Zones this fractal overlaps with
    
    # Trading metadata (no defaults)
    distance_from_price: float
    distance_percentage: float
    priority_score: float  # Combined score for ranking
    
    # Confluence factors (with defaults - must come last)
    has_hvn: bool = False
    has_camarilla: bool = False
    has_weekly: bool = False
    has_daily: bool = False
    has_atr: bool = False
    has_multiple_timeframes: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for export"""
        return {
            'datetime': self.datetime.isoformat(),
            'type': self.fractal_type,
            'high': self.high_price,
            'low': self.low_price,
            'open': self.open_price,
            'close': self.close_price,
            'volume': self.volume,
            'confluence_score': self.confluence_score,
            'confluence_level': self.confluence_level,
            'zone_count': len(self.overlapping_zones),
            'has_hvn': self.has_hvn,
            'has_camarilla': self.has_camarilla,
            'has_weekly': self.has_weekly,
            'has_daily': self.has_daily,
            'has_atr': self.has_atr,
            'has_multiple_timeframes': self.has_multiple_timeframes,
            'distance_pct': self.distance_percentage,
            'priority': self.priority_score
        }