"""
Maps trades to M15 zones and calculates confluence
"""
from typing import Optional, List, Dict
from datetime import datetime

from core.models import ManualTradeEntry, ZoneMatch, ZoneDetail, TradeDirection
from core.confluence_reconstructor import ConfluenceReconstructor
from backtest_config import BACKTEST_CONFIG

class ZoneAlignmentAnalyzer:
    """Analyzes trade alignment with M15 zones"""
    
    def __init__(self, confluence_reconstructor: ConfluenceReconstructor):
        self.reconstructor = confluence_reconstructor
        self.max_distance_ticks = BACKTEST_CONFIG['MAX_ZONE_DISTANCE_TICKS']
        self.tick_size = 0.01  # For AMD, adjust per ticker
    
    def find_entry_zone(self, 
                       entry_price: float, 
                       zones: List[ZoneDetail],
                       direction: TradeDirection) -> Optional[ZoneMatch]:
        """
        Identify which M15 zone was traded
        
        Args:
            entry_price: Trade entry price
            zones: List of available zones
            direction: Trade direction (long/short)
            
        Returns:
            ZoneMatch if found, None otherwise
        """
        best_match = None
        min_distance = float('inf')
        
        for zone in zones:
            # Skip if no zone data
            if not zone.high or not zone.low:
                continue
            
            # Check zone type matches trade direction
            zone_type = self._determine_zone_type(zone, entry_price)
            
            if direction == TradeDirection.LONG and zone_type != 'support':
                continue
            elif direction == TradeDirection.SHORT and zone_type != 'resistance':
                continue
            
            # Calculate distance from zone
            distance_ticks = self._calculate_distance_from_zone(
                entry_price, zone.high, zone.low
            )
            
            # Check if within acceptable distance
            if abs(distance_ticks) <= self.max_distance_ticks:
                if abs(distance_ticks) < min_distance:
                    min_distance = abs(distance_ticks)
                    
                    # Extract confluence details
                    confluence_sources = self._extract_confluence_sources(zone)
                    
                    best_match = ZoneMatch(
                        zone_number=zone.zone_number,
                        zone_type=zone_type,
                        zone_high=zone.high,
                        zone_low=zone.low,
                        confluence_level=str(zone.confluence_level.value) if zone.confluence_level else "NONE",
                        confluence_score=zone.confluence_score,
                        confluence_sources=confluence_sources,
                        distance_from_zone_ticks=distance_ticks,
                        is_valid_entry=abs(distance_ticks) <= 5  # Tighter criteria for "valid"
                    )
        
        return best_match
    
    def _determine_zone_type(self, zone: ZoneDetail, current_price: float) -> str:
        """
        Determine if zone is support or resistance relative to current price
        
        Args:
            zone: Zone to analyze
            current_price: Current market price
            
        Returns:
            'support' or 'resistance'
        """
        zone_mid = (zone.high + zone.low) / 2
        return 'support' if current_price > zone_mid else 'resistance'
    
    def _calculate_distance_from_zone(self, 
                                     price: float, 
                                     zone_high: float, 
                                     zone_low: float) -> int:
        """
        Calculate distance from price to nearest zone edge in ticks
        
        Args:
            price: Price to measure from
            zone_high: Upper zone boundary
            zone_low: Lower zone boundary
            
        Returns:
            Distance in ticks (negative if below zone, positive if above)
        """
        if price >= zone_low and price <= zone_high:
            # Price is within zone
            return 0
        elif price < zone_low:
            # Price is below zone
            distance = zone_low - price
            return -int(distance / self.tick_size)
        else:
            # Price is above zone
            distance = price - zone_high
            return int(distance / self.tick_size)
    
    def _extract_confluence_sources(self, zone: ZoneDetail) -> List[str]:
        """
        Extract list of confluence sources from zone
        
        Args:
            zone: Zone with confluence data
            
        Returns:
            List of confluence source names
        """
        sources = []
        
        # Get from confluent_inputs if available
        if hasattr(zone, 'confluent_inputs') and zone.confluent_inputs:
            for inp in zone.confluent_inputs:
                sources.append(inp.source_name)
        
        return sources
    
    def validate_zone_trade(self, 
                          trade: ManualTradeEntry, 
                          zone: ZoneMatch) -> Dict[str, any]:
        """
        Validate that trade setup aligns with zone characteristics
        
        Args:
            trade: Trade to validate
            zone: Matched zone
            
        Returns:
            Dictionary with validation details
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'quality_score': 0
        }
        
        # Check confluence level
        confluence_num = int(zone.confluence_level[1]) if zone.confluence_level and zone.confluence_level != "NONE" else 0
        
        if confluence_num < 2:
            validation['issues'].append("Low confluence zone (L1)")
            validation['quality_score'] -= 2
        elif confluence_num >= 4:
            validation['quality_score'] += 2
        
        # Check distance from zone
        if abs(zone.distance_from_zone_ticks) > 5:
            validation['issues'].append(f"Entry far from zone: {zone.distance_from_zone_ticks} ticks")
            validation['quality_score'] -= 1
        elif abs(zone.distance_from_zone_ticks) <= 2:
            validation['quality_score'] += 1
        
        # Check zone type alignment
        if trade.trade_direction == TradeDirection.LONG and zone.zone_type != 'support':
            validation['issues'].append("Long trade at resistance zone")
            validation['is_valid'] = False
        elif trade.trade_direction == TradeDirection.SHORT and zone.zone_type != 'resistance':
            validation['issues'].append("Short trade at support zone")
            validation['is_valid'] = False
        
        # Check stop placement
        if trade.trade_direction == TradeDirection.LONG:
            if trade.stop_price > zone.zone_low:
                validation['issues'].append("Stop inside zone for long trade")
        else:
            if trade.stop_price < zone.zone_high:
                validation['issues'].append("Stop inside zone for short trade")
        
        # Calculate final quality score (0-10 scale)
        base_score = 5 + confluence_num
        validation['quality_score'] = max(0, min(10, base_score + validation['quality_score']))
        
        return validation
    
    def get_zone_analysis_summary(self, zone: ZoneMatch) -> str:
        """
        Create formatted summary of zone analysis
        
        Args:
            zone: Zone match results
            
        Returns:
            Formatted string summary
        """
        summary = f"""
Zone Analysis
=============
Zone #{zone.zone_number} ({zone.zone_type.upper()})
Range: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}

Confluence: {zone.confluence_level} (Score: {zone.confluence_score:.2f})
Sources: {', '.join(zone.confluence_sources) if zone.confluence_sources else 'None'}

Entry Distance: {zone.distance_from_zone_ticks} ticks from zone
Valid Entry: {'Yes' if zone.is_valid_entry else 'No'}
"""
        return summary