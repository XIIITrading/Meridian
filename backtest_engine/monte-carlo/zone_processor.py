"""
Zone processing and merging logic
"""
import pandas as pd
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ZoneProcessor:
    def __init__(self, merge_threshold: float = 0.10):
        """
        Initialize zone processor
        
        Args:
            merge_threshold: Price threshold for merging overlapping zones
        """
        self.merge_threshold = merge_threshold
    
    def zones_overlap(self, zone1: Dict, zone2: Dict) -> bool:
        """
        Check if two zones overlap
        
        Args:
            zone1: First zone dictionary
            zone2: Second zone dictionary
            
        Returns:
            True if zones overlap
        """
        return not (zone1['high'] < zone2['low'] or zone2['high'] < zone1['low'])
    
    def merge_zones(self, zone1: Dict, zone2: Dict) -> Dict:
        """
        Merge two overlapping zones
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            Merged zone
        """
        return {
            'id': f"{zone1['id']}_{zone2['id']}",
            'datetime': min(zone1['datetime'], zone2['datetime']),
            'date': min(zone1['date'], zone2['date']),
            'high': max(zone1['high'], zone2['high']),
            'low': min(zone1['low'], zone2['low']),
            'type': zone1['type']  # Keep first zone's type
        }
    
    def merge_overlapping_zones(self, zones: List[Dict]) -> List[Dict]:
        """
        Merge all overlapping zones in list
        
        Args:
            zones: List of zone dictionaries
            
        Returns:
            List of merged zones
        """
        if not zones:
            return []
        
        # Sort zones by date and low price
        zones_sorted = sorted(zones, key=lambda x: (x['date'], x['low']))
        
        merged = []
        current = zones_sorted[0].copy()
        
        for zone in zones_sorted[1:]:
            if zone['date'] == current['date'] and self.zones_overlap(current, zone):
                # Merge with current
                current = self.merge_zones(current, zone)
            else:
                # Save current and start new
                merged.append(current)
                current = zone.copy()
        
        # Don't forget the last zone
        merged.append(current)
        
        logger.info(f"Merged {len(zones)} zones into {len(merged)} zones")
        return merged
    
    def validate_zone(self, zone: Dict) -> bool:
        """
        Validate that a zone is tradeable
        
        Args:
            zone: Zone dictionary
            
        Returns:
            True if zone is valid for trading
        """
        # Check that high > low
        if zone['high'] <= zone['low']:
            return False
        
        # Check zone size
        zone_size = zone['high'] - zone['low']
        if zone_size < 0.10 or zone_size > 5.00:
            return False
        
        return True
    
    def filter_valid_zones(self, zones: List[Dict]) -> List[Dict]:
        """
        Filter zones to only valid ones
        
        Args:
            zones: List of zones
            
        Returns:
            List of valid zones
        """
        valid = [z for z in zones if self.validate_zone(z)]
        logger.info(f"Filtered to {len(valid)} valid zones from {len(zones)} total")
        return valid