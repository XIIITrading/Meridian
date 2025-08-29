"""
Zone Discovery Engine with configurable overlap logic
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Zone:
    """Zone with confluence information"""
    zone_id: int
    zone_low: float
    zone_high: float
    center_price: float
    zone_width: float
    zone_type: str  # 'support' or 'resistance'
    confluence_level: str  # L1-L5
    confluence_score: float
    confluent_sources: List[Dict]
    distance_from_price: float
    distance_percentage: float
    best_candle: Optional[Dict] = None
    recency_score: float = 1.0


class ZoneDiscoveryEngine:
    """
    Zone discovery with configurable overlap merging
    """
    
    def __init__(self, merge_overlapping: bool = False, merge_identical: bool = True):
        """
        Initialize zone discovery engine
        
        Args:
            merge_overlapping: If True, merge zones that overlap. If False, keep all zones separate
            merge_identical: If True, merge items at identical prices (within $0.10)
        """
        self.merge_overlapping = merge_overlapping
        self.merge_identical = merge_identical
        self.identical_threshold = 0.10  # Consider prices within $0.10 as identical
        logger.info(f"ZoneDiscoveryEngine initialized - Merge overlapping: {merge_overlapping}, "
                   f"Merge identical: {merge_identical}")
    
    def discover_zones(self,
                      scan_low: float,
                      scan_high: float,
                      current_price: float,
                      atr_15min: float,
                      confluence_sources: Dict[str, List[Dict]]) -> List[Zone]:
        """
        Discover zones from confluence sources
        
        Args:
            scan_low: Lower bound of scan range
            scan_high: Upper bound of scan range
            current_price: Current market price
            atr_15min: 15-minute ATR (not used for merging, only for info)
            confluence_sources: Dictionary of source type to items
            
        Returns:
            List of Zone objects
        """
        # Flatten all confluence items
        all_items = []
        for source_type, items in confluence_sources.items():
            for item in items:
                if scan_low <= item.get('level', 0) <= scan_high:
                    all_items.append(item)
        
        if not all_items:
            logger.warning("No confluence items within scan range")
            return []
        
        logger.info(f"Processing {len(all_items)} confluence items")
        
        # Create initial zones based on configuration
        if not self.merge_overlapping and not self.merge_identical:
            # Each item becomes its own zone
            zones = self._create_individual_zones(all_items, current_price)
        elif self.merge_identical and not self.merge_overlapping:
            # Merge only identical prices
            zones = self._create_zones_merge_identical(all_items, current_price)
        else:
            # Full overlap merging (original logic)
            zones = self._create_zones_merge_overlapping(all_items, current_price)
        
        # Calculate confluence scores and levels
        for zone in zones:
            zone.confluence_score = self._calculate_confluence_score(zone)
            zone.confluence_level = self._determine_confluence_level(len(zone.confluent_sources))
        
        # Sort by score
        zones.sort(key=lambda x: x.confluence_score, reverse=True)
        
        logger.info(f"Discovered {len(zones)} zones")
        return zones
    
    def _create_individual_zones(self, items: List[Dict], current_price: float) -> List[Zone]:
        """
        Create individual zones - no merging at all
        Each confluence item becomes its own zone
        """
        zones = []
        
        for idx, item in enumerate(items):
            zone_low = item.get('low', item['level'])
            zone_high = item.get('high', item['level'])
            center = item['level']
            
            zone = Zone(
                zone_id=idx,
                zone_low=zone_low,
                zone_high=zone_high,
                center_price=center,
                zone_width=zone_high - zone_low,
                zone_type='resistance' if center > current_price else 'support',
                confluence_level='L1',  # Will be updated
                confluence_score=0,  # Will be calculated
                confluent_sources=[item],
                distance_from_price=abs(center - current_price),
                distance_percentage=abs(center - current_price) / current_price * 100
            )
            zones.append(zone)
        
        logger.info(f"Created {len(zones)} individual zones (no merging)")
        return zones
    
    def _create_zones_merge_identical(self, items: List[Dict], current_price: float) -> List[Zone]:
        """
        Merge only items at identical price levels (within threshold)
        Different from full overlap - only merges if prices are essentially the same
        """
        # Group by price level
        price_groups = {}
        
        for item in items:
            level = item['level']
            # Find if there's an existing group within threshold
            found_group = False
            for group_price in price_groups:
                if abs(level - group_price) <= self.identical_threshold:
                    price_groups[group_price].append(item)
                    found_group = True
                    break
            
            if not found_group:
                price_groups[level] = [item]
        
        # Create zones from groups
        zones = []
        for idx, (price, group_items) in enumerate(price_groups.items()):
            # Calculate zone boundaries from all items in group
            zone_low = min(item.get('low', item['level']) for item in group_items)
            zone_high = max(item.get('high', item['level']) for item in group_items)
            center = sum(item['level'] for item in group_items) / len(group_items)
            
            zone = Zone(
                zone_id=idx,
                zone_low=zone_low,
                zone_high=zone_high,
                center_price=center,
                zone_width=zone_high - zone_low,
                zone_type='resistance' if center > current_price else 'support',
                confluence_level='L1',  # Will be updated
                confluence_score=0,  # Will be calculated
                confluent_sources=group_items,
                distance_from_price=abs(center - current_price),
                distance_percentage=abs(center - current_price) / current_price * 100
            )
            zones.append(zone)
        
        logger.info(f"Created {len(zones)} zones from {len(items)} items (identical price merging)")
        return zones
    
    def _create_zones_merge_overlapping(self, items: List[Dict], current_price: float) -> List[Zone]:
        """
        Original logic - merge zones that overlap
        Pure overlap based on actual high/low boundaries, no ATR buffers
        """
        # Sort items by level
        sorted_items = sorted(items, key=lambda x: x['level'])
        
        # Create initial clusters
        clusters = []
        for item in sorted_items:
            item_low = item.get('low', item['level'])
            item_high = item.get('high', item['level'])
            
            # Find overlapping cluster
            merged = False
            for cluster in clusters:
                cluster_low = min(i.get('low', i['level']) for i in cluster)
                cluster_high = max(i.get('high', i['level']) for i in cluster)
                
                # Check for overlap (pure geometric overlap)
                if item_low <= cluster_high and item_high >= cluster_low:
                    # They overlap - add to cluster
                    cluster.append(item)
                    merged = True
                    break
            
            if not merged:
                # Start new cluster
                clusters.append([item])
        
        # Convert clusters to zones
        zones = []
        for idx, cluster in enumerate(clusters):
            zone_low = min(item.get('low', item['level']) for item in cluster)
            zone_high = max(item.get('high', item['level']) for item in cluster)
            
            # Calculate weighted center if items have strength/volume
            total_weight = 0
            weighted_sum = 0
            for item in cluster:
                weight = item.get('strength', 1.0)
                weighted_sum += item['level'] * weight
                total_weight += weight
            
            center = weighted_sum / total_weight if total_weight > 0 else (zone_high + zone_low) / 2
            
            zone = Zone(
                zone_id=idx,
                zone_low=zone_low,
                zone_high=zone_high,
                center_price=center,
                zone_width=zone_high - zone_low,
                zone_type='resistance' if center > current_price else 'support',
                confluence_level='L1',  # Will be updated
                confluence_score=0,  # Will be calculated
                confluent_sources=cluster,
                distance_from_price=abs(center - current_price),
                distance_percentage=abs(center - current_price) / current_price * 100
            )
            zones.append(zone)
        
        logger.info(f"Created {len(zones)} zones from {len(items)} items (overlap merging)")
        return zones
    
    def _calculate_confluence_score(self, zone: Zone) -> float:
        """Calculate confluence score for a zone"""
        base_score = len(zone.confluent_sources) * 2.0
        
        # Strength multiplier
        total_strength = sum(s.get('strength', 1.0) for s in zone.confluent_sources)
        avg_strength = total_strength / len(zone.confluent_sources) if zone.confluent_sources else 1.0
        strength_multiplier = avg_strength / 5.0 if avg_strength > 0 else 1.0
        
        # Source diversity bonus
        unique_types = len(set(s.get('type', 'unknown') for s in zone.confluent_sources))
        diversity_bonus = 1.0 + (unique_types - 1) * 0.1
        
        return base_score * strength_multiplier * diversity_bonus * zone.recency_score
    
    def _determine_confluence_level(self, source_count: int) -> str:
        """Determine confluence level based on source count"""
        if source_count >= 10:
            return 'L5'
        elif source_count >= 8:
            return 'L4'
        elif source_count >= 6:
            return 'L3'
        elif source_count >= 4:
            return 'L2'
        elif source_count >= 2:
            return 'L1'
        else:
            return 'L0'
    
    def set_merge_mode(self, merge_overlapping: bool, merge_identical: bool):
        """
        Change merge mode at runtime
        
        Args:
            merge_overlapping: Enable/disable overlap merging
            merge_identical: Enable/disable identical price merging
        """
        self.merge_overlapping = merge_overlapping
        self.merge_identical = merge_identical
        logger.info(f"Merge mode changed - Overlapping: {merge_overlapping}, Identical: {merge_identical}")