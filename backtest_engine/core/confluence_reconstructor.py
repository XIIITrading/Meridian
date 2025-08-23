# core/confluence_reconstructor.py
"""
Confluence reconstruction from levels_zones records
Mimics the M15 confluence widget logic
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, time
from decimal import Decimal

from core.models import (
    ZoneDetail, MarketContext, LevelsData, 
    ConfluenceLevel, ConfluenceSource, ConfluenceInput,
    TICK_SIZE
)

logger = logging.getLogger(__name__)

class ConfluenceReconstructor:
    """Reconstruct confluence scores from levels_zones data"""
    
    # Scoring weights for different confluence sources
    SCORING_WEIGHTS = {
        ConfluenceSource.WEEKLY_LEVEL: 2.0,      # Weekly levels get double weight
        ConfluenceSource.DAILY_LEVEL: 1.5,       # Daily levels get 1.5x weight
        ConfluenceSource.M15_OVERLAP: 1.0,       # Zone overlap normal weight
        'DEFAULT': 1.0                           # Default weight
    }
    
    # Proximity thresholds (in ticks)
    PROXIMITY_THRESHOLD_TICKS = 10  # Consider levels within 10 ticks as confluent
    
    def __init__(self):
        """Initialize the reconstructor"""
        self.zones: List[ZoneDetail] = []
        self.market_context: Optional[MarketContext] = None
        self.levels: Optional[LevelsData] = None
    
    def parse_levels_zones_record(self, record: Dict) -> Tuple[List[ZoneDetail], MarketContext]:
        """
        Parse a levels_zones record and extract all zone and context data
        
        Args:
            record: Dictionary from levels_zones table
            
        Returns:
            Tuple of (zones list, market context)
        """
        # Extract market context
        self.market_context = MarketContext.from_levels_zones(record)
        
        # Extract all 6 M15 zones
        self.zones = []
        for zone_num in range(1, 7):
            zone = ZoneDetail.from_levels_zones(record, zone_num)
            
            # Only add zones that have valid data
            if zone.high is not None and zone.low is not None:
                self.zones.append(zone)
        
        # Sort zones by price (highest first)
        self.zones.sort(key=lambda z: z.zone_center, reverse=True)
        
        logger.info(f"Parsed {len(self.zones)} valid zones from record")
        
        return self.zones, self.market_context
    
    def identify_confluence_sources(self, zone: ZoneDetail, full_record: Dict) -> Dict[str, List[ConfluenceInput]]:
        """
        Identify all confluence sources for a specific zone
        
        Args:
            zone: The zone to analyze
            full_record: Complete levels_zones record
            
        Returns:
            Dictionary of confluence sources by type
        """
        confluences = {
            'weekly_levels': [],
            'daily_levels': [],
            'zone_overlaps': [],
            'other_sources': []
        }
        
        # Check weekly levels (WL1-4)
        for level_name, level_value in self.market_context.levels.get_weekly_levels():
            if level_value and self._is_level_confluent_with_zone(level_value, zone):
                weight = self.SCORING_WEIGHTS[ConfluenceSource.WEEKLY_LEVEL]
                zone.add_confluence(
                    ConfluenceSource.WEEKLY_LEVEL,
                    level_name,
                    level_value,
                    score_contribution=weight
                )
                confluences['weekly_levels'].append(level_name)
        
        # Check daily levels (DL1-6)
        for level_name, level_value in self.market_context.levels.get_daily_levels():
            if level_value and self._is_level_confluent_with_zone(level_value, zone):
                weight = self.SCORING_WEIGHTS[ConfluenceSource.DAILY_LEVEL]
                zone.add_confluence(
                    ConfluenceSource.DAILY_LEVEL,
                    level_name,
                    level_value,
                    score_contribution=weight
                )
                confluences['daily_levels'].append(level_name)
        
        # Check for overlaps with other M15 zones
        for other_zone in self.zones:
            if other_zone.zone_number != zone.zone_number:
                if self._zones_overlap(zone, other_zone):
                    weight = self.SCORING_WEIGHTS[ConfluenceSource.M15_OVERLAP]
                    zone.add_confluence(
                        ConfluenceSource.M15_OVERLAP,
                        f"Zone {other_zone.zone_number}",
                        other_zone.zone_center,
                        score_contribution=weight
                    )
                    confluences['zone_overlaps'].append(other_zone.zone_number)
        
        # Note: Additional confluence sources (HVN, Camarilla, etc.) would be added here
        # if they were stored in the levels_zones record
        
        return confluences
    
    def _is_level_confluent_with_zone(self, level: float, zone: ZoneDetail) -> bool:
        """
        Check if a price level is confluent with a zone
        
        Args:
            level: Price level to check
            zone: Zone to check against
            
        Returns:
            True if level is within or near the zone
        """
        if not zone.high or not zone.low:
            return False
        
        # Check if level is within zone
        if zone.low <= level <= zone.high:
            return True
        
        # Check proximity (within threshold ticks)
        distance_ticks = 0
        if level < zone.low:
            distance_ticks = (zone.low - level) / TICK_SIZE
        elif level > zone.high:
            distance_ticks = (level - zone.high) / TICK_SIZE
        
        return distance_ticks <= self.PROXIMITY_THRESHOLD_TICKS
    
    def _zones_overlap(self, zone1: ZoneDetail, zone2: ZoneDetail) -> bool:
        """
        Check if two zones overlap
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            True if zones overlap
        """
        if not all([zone1.high, zone1.low, zone2.high, zone2.low]):
            return False
        
        # Check for overlap
        return not (zone1.high < zone2.low or zone2.high < zone1.low)
    
    def reconstruct_all_confluence(self, record: Dict) -> List[ZoneDetail]:
        """
        Complete confluence reconstruction for all zones
        
        Args:
            record: Complete levels_zones record
            
        Returns:
            List of zones with calculated confluence
        """
        # Parse the record
        zones, context = self.parse_levels_zones_record(record)
        
        # Calculate confluence for each zone
        for zone in zones:
            # Identify all confluence sources
            confluences = self.identify_confluence_sources(zone, record)
            
            # The score is already calculated by add_confluence calls
            zone.calculate_confluence_score()
            
            logger.debug(f"Zone {zone.zone_number}: "
                        f"Score={zone.confluence_score:.1f}, "
                        f"Level={zone.confluence_level.value}, "
                        f"Sources={zone.confluence_count}")
        
        # Sort zones by confluence score (highest first)
        zones.sort(key=lambda z: z.confluence_score, reverse=True)
        
        return zones
    
    def reconstruct_market_context(self, record: Dict) -> MarketContext:
        """
        Reconstruct market context with trend and structure analysis
        
        Args:
            record: Complete levels_zones record
            
        Returns:
            Market context object
        """
        context = MarketContext.from_levels_zones(record)
        
        # Add calculated fields
        context.trend_aligned = context.is_trend_aligned()
        context.structure_strength = context.get_structure_strength()
        
        return context
    
    def calculate_zone_quality_score(self, zone: ZoneDetail, context: MarketContext) -> float:
        """
        Calculate an enhanced quality score considering market context
        
        Args:
            zone: Zone to score
            context: Market context
            
        Returns:
            Quality score (can be higher than confluence score)
        """
        base_score = zone.confluence_score
        
        # Trend alignment bonus (up to 2 points)
        if context.is_trend_aligned():
            base_score += 2.0
        
        # Structure position bonus (up to 3 points based on strength)
        structure_bonus = context.get_structure_strength() / 100 * 3
        base_score += structure_bonus
        
        # Zone tested bonus (if we had historical data)
        if zone.zone_tested and zone.zone_held:
            base_score += 1.5
        
        return base_score
    
    def get_confluence_summary(self, zones: List[ZoneDetail]) -> Dict[str, Any]:
        """
        Get a summary of confluence analysis
        
        Args:
            zones: List of analyzed zones
            
        Returns:
            Summary dictionary
        """
        if not zones:
            return {'error': 'No zones to analyze'}
        
        summary = {
            'total_zones': len(zones),
            'zones_by_level': {},
            'top_zone': None,
            'average_score': 0
        }
        
        # Count zones by confluence level
        for level in ConfluenceLevel:
            if level != ConfluenceLevel.NONE:
                count = sum(1 for z in zones if z.confluence_level == level)
                if count > 0:
                    summary['zones_by_level'][level.value] = count
        
        # Top zone
        if zones:
            top_zone = zones[0]
            summary['top_zone'] = {
                'number': top_zone.zone_number,
                'range': f"${top_zone.low:.2f}-${top_zone.high:.2f}",
                'score': top_zone.confluence_score,
                'level': top_zone.confluence_level.value,
                'sources': top_zone.confluence_count
            }
        
        # Average score
        summary['average_score'] = sum(z.confluence_score for z in zones) / len(zones)
        
        return summary

def validate_reconstruction(original_scores: Dict, reconstructed_zones: List[ZoneDetail]) -> bool:
    """
    Validate that reconstruction matches original scores
    
    Args:
        original_scores: Original confluence scores from levels_zones
        reconstructed_zones: Reconstructed zones with calculated scores
        
    Returns:
        True if reconstruction matches (within tolerance)
    """
    tolerance = 0.1  # Allow 0.1 point difference
    
    for zone in reconstructed_zones:
        original_key = f"m15_zone{zone.zone_number}_confluence_score"
        if original_key in original_scores:
            original = float(original_scores[original_key] or 0)
            reconstructed = zone.confluence_score
            
            if abs(original - reconstructed) > tolerance:
                logger.warning(f"Zone {zone.zone_number} mismatch: "
                             f"Original={original}, Reconstructed={reconstructed}")
                return False
    
    return True