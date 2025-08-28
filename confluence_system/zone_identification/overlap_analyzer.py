"""
Core overlap analysis between fractals and confluence zones
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from .models import TradingLevel

logger = logging.getLogger(__name__)


class OverlapAnalyzer:
    """
    Analyzes overlap between fractal candlesticks and confluence zones
    """
    
    def __init__(self, overlap_threshold: float = 0.2):
        """
        Args:
            overlap_threshold: Minimum overlap percentage to consider (0.2 = 20%)
        """
        self.overlap_threshold = overlap_threshold
        
    def calculate_overlap(self, 
                         fractal_high: float, 
                         fractal_low: float,
                         zone_high: float, 
                         zone_low: float) -> float:
        """
        Calculate percentage overlap between fractal candle and zone
        
        Returns:
            Overlap percentage (0-1)
        """
        # Find overlap boundaries
        overlap_high = min(fractal_high, zone_high)
        overlap_low = max(fractal_low, zone_low)
        
        # No overlap if boundaries don't intersect
        if overlap_high <= overlap_low:
            return 0.0
            
        # Calculate overlap range
        overlap_range = overlap_high - overlap_low
        fractal_range = fractal_high - fractal_low
        
        # Handle point fractals (high = low)
        if fractal_range == 0:
            # Check if point is within zone
            if zone_low <= fractal_high <= zone_high:
                return 1.0
            return 0.0
            
        # Calculate percentage
        return overlap_range / fractal_range
        
    def analyze_fractal_zone_overlap(self,
                                    fractal: Dict,
                                    zone: any) -> Optional[Dict]:
        """
        Analyze overlap between a single fractal and zone
        
        Args:
            fractal: Fractal data from fractal_engine
            zone: Zone object from confluence_scanner
            
        Returns:
            Overlap details or None if below threshold
        """
        # Get fractal boundaries
        fractal_high = fractal.get('bar_high', fractal['price'])
        fractal_low = fractal.get('bar_low', fractal['price'])
        
        # Calculate overlap
        overlap_pct = self.calculate_overlap(
            fractal_high, fractal_low,
            zone.zone_high, zone.zone_low
        )
        
        # Check threshold
        if overlap_pct < self.overlap_threshold:
            return None
            
        # Extract confluence sources from zone
        confluence_factors = self._extract_confluence_factors(zone)
        
        return {
            'overlap_percentage': overlap_pct,
            'zone_id': zone.zone_id,
            'zone_score': zone.confluence_score,
            'zone_level': zone.confluence_level,
            'zone_sources': zone.confluent_sources,
            'confluence_factors': confluence_factors
        }
        
    def _extract_confluence_factors(self, zone: any) -> Dict[str, bool]:
        """
        Extract boolean flags for confluence factors present in zone
        """
        factors = {
            'has_hvn': False,
            'has_camarilla': False,
            'has_weekly': False,
            'has_daily': False,
            'has_atr': False,
            'has_multiple_timeframes': False
        }
        
        timeframes = set()
        
        for source in zone.confluent_sources:
            source_type = source.get('type', '')
            
            # Check HVN
            if 'hvn' in source_type:
                factors['has_hvn'] = True
                # Extract timeframe from type (e.g., 'hvn-30d')
                if '-' in source_type:
                    timeframes.add(source_type.split('-')[1])
                    
            # Check Camarilla
            elif 'cam' in source_type:
                factors['has_camarilla'] = True
                if '-' in source_type:
                    timeframes.add(source_type.split('-')[1])
                    
            # Check weekly
            elif 'weekly' in source_type:
                factors['has_weekly'] = True
                
            # Check daily
            elif 'daily' in source_type:
                factors['has_daily'] = True
                
            # Check ATR
            elif 'atr' in source_type:
                factors['has_atr'] = True
                
        # Check multiple timeframes
        if len(timeframes) > 1:
            factors['has_multiple_timeframes'] = True
            
        return factors
        
    def find_overlapping_zones(self,
                              fractal: Dict,
                              zones: List[any]) -> List[Dict]:
        """
        Find all zones that overlap with a fractal
        
        Args:
            fractal: Fractal data
            zones: List of zones from confluence_scanner
            
        Returns:
            List of overlap details for qualifying zones
        """
        overlaps = []
        
        for zone in zones:
            overlap = self.analyze_fractal_zone_overlap(fractal, zone)
            if overlap:
                overlaps.append(overlap)
                
        # Sort by overlap percentage and zone score
        overlaps.sort(key=lambda x: (x['overlap_percentage'], x['zone_score']), reverse=True)
        
        return overlaps