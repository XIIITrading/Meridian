# calculations/zones/daily_zone_calc.py - Simplified for confluence_scanner

"""
Daily Zone Calculator - Simplified version
Transforms daily levels into zones using ATR bands
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class DailyZoneCalculator:
    """Calculator for transforming daily levels into zones"""
    
    def __init__(self):
        """Initialize the calculator"""
        logger.info("DailyZoneCalculator initialized (simplified)")
    
    def create_daily_zones(self, 
                          daily_levels: List[float], 
                          atr_m15: float,
                          current_price: float) -> List[Dict]:
        """
        Create zones from daily levels using 15-minute ATR
        
        Args:
            daily_levels: List of daily price levels (DL1-DL6)
            atr_m15: 15-minute ATR value
            current_price: Current market price
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        for i, level in enumerate(daily_levels, 1):
            if level and level > 0:
                # Calculate zone boundaries - half M15 ATR above and below
                zone_high = level + (atr_m15 * 0.5)
                zone_low = level - (atr_m15 * 0.5)
                
                zone = {
                    'name': f'DL{i}',
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
                logger.debug(f"Created zone DL{i}: {zone_low:.2f} - {zone_high:.2f}")
        
        return zones