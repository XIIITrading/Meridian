# calculations/zones/atr_zone_calc.py - Updated for confluence_scanner

"""
ATR Zone Calculator
Creates dynamic volatility-based zones using ATR levels
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class ATRZoneCalculator:
    """Calculator for creating ATR-based zones"""
    
    def __init__(self):
        """Initialize the calculator"""
        logger.info("ATRZoneCalculator initialized")
    
    def create_atr_zones(self, 
                        atr_high: float, 
                        atr_low: float,
                        atr_m15: float,
                        current_price: float) -> List[Dict]:
        """
        Create zones from ATR levels using 15-minute ATR
        
        Args:
            atr_high: Current price + daily ATR (resistance level)
            atr_low: Current price - daily ATR (support level)
            atr_m15: 15-minute ATR value for zone width
            current_price: Current market price
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        # Create ATR High Zone (resistance zone)
        if atr_high and atr_high > 0:
            zone_high = atr_high + atr_m15
            zone_low = atr_high - atr_m15
            
            zone = {
                'name': 'ATR_High',
                'level': atr_high,
                'high': zone_high,
                'low': zone_low,
                'zone_size': zone_high - zone_low,
                'type': 'resistance',
                'center': atr_high,
                'distance': atr_high - current_price,
                'distance_pct': ((atr_high - current_price) / current_price * 100) if current_price > 0 else 0
            }
            zones.append(zone)
            logger.debug(f"Created ATR High Zone: {zone_low:.2f} - {zone_high:.2f}")
        
        # Create ATR Low Zone (support zone)
        if atr_low and atr_low > 0:
            zone_high = atr_low + atr_m15
            zone_low = atr_low - atr_m15
            
            zone = {
                'name': 'ATR_Low',
                'level': atr_low,
                'high': zone_high,
                'low': zone_low,
                'zone_size': zone_high - zone_low,
                'type': 'support',
                'center': atr_low,
                'distance': current_price - atr_low,
                'distance_pct': ((current_price - atr_low) / current_price * 100) if current_price > 0 else 0
            }
            zones.append(zone)
            logger.debug(f"Created ATR Low Zone: {zone_low:.2f} - {zone_high:.2f}")
        
        return zones