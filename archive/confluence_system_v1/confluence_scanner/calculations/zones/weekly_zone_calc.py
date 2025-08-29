# calculations/zones/weekly_zone_calc.py - Simplified for confluence_scanner

"""
Weekly Zone Calculator - Simplified version
Transforms weekly levels into zones using ATR bands
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class WeeklyZoneCalculator:
    """Calculator for transforming weekly levels into zones"""
    
    def __init__(self):
        """Initialize the calculator"""
        logger.info("WeeklyZoneCalculator initialized (simplified)")
    
    def create_weekly_zones(self, 
                          weekly_levels: List[float], 
                          atr_m15: float,
                          current_price: float) -> List[Dict]:
        """
        Create zones from weekly levels using 15-minute ATR
        Uses 2x M15 ATR for weekly zones (wider than daily zones)
        
        Args:
            weekly_levels: List of weekly price levels (WL1-WL4)
            atr_m15: 15-minute ATR value
            current_price: Current market price
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        # Use 2x M15 ATR for weekly zones (they should be wider)
        zone_width = atr_m15 * 2
        
        for i, level in enumerate(weekly_levels, 1):
            if level and level > 0:
                # Calculate zone boundaries
                zone_high = level + zone_width
                zone_low = level - zone_width
                
                zone = {
                    'name': f'WL{i}',
                    'level': level,
                    'high': zone_high,
                    'low': zone_low,
                    'zone_size': zone_high - zone_low,
                    'center': level,
                    'type': 'resistance' if level > current_price else 'support',
                    'distance': abs(level - current_price),
                    'distance_pct': abs(level - current_price) / current_price * 100 if current_price > 0 else 0
                }
                zones.append(zone)
                logger.debug(f"Created zone WL{i}: {zone_low:.2f} - {zone_high:.2f}")
        
        return zones