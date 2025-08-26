# discovery/zone_discovery.py - Complete working version

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
import pytz

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredZone:
    """A discovered zone with confluence"""
    zone_id: int
    zone_high: float
    zone_low: float
    center_price: float
    zone_width: float
    confluence_score: float
    confluence_level: str
    confluent_sources: List[Dict]
    best_candle: Optional[Dict] = None
    candle_score: float = 0.0
    distance_from_current: float = 0.0
    distance_percentage: float = 0.0
    zone_type: str = ''
    recency_score: float = 0.0

class ZoneDiscoveryEngine:
    """Enhanced zone discovery supporting all confluence types with M15 validation"""
    
    def __init__(self, config=None):
        self.config = config
        if not config:
            from config import ScannerConfig
            self.config = ScannerConfig()
        
        # Configuration
        self.cluster_distance_atr = getattr(self.config, 'CLUSTER_DISTANCE_ATR', 1.5)
        self.min_confluence_score = getattr(self.config, 'MIN_CONFLUENCE_SCORE', 2.0)
        
        # Weights for different confluence types
        self.confluence_weights = {
            'hvn-30d': 3.0,
            'hvn-14d': 2.5,
            'hvn-7d': 2.0,
            'cam-monthly': 3.0,
            'cam-weekly': 2.5,
            'cam-daily': 1.5,
            'weekly': 2.5,
            'daily-zone': 1.5,
            'daily-level': 1.0,
            'atr': 1.5,
        }
    
    def discover_zones(self,
                      scan_low: float,
                      scan_high: float,
                      current_price: float,
                      atr_15min: float,
                      confluence_sources: Dict[str, List[Dict]]) -> List[DiscoveredZone]:
        """Main discovery method - finds zones where multiple levels cluster"""
        
        logger.info(f"Zone discovery: ${scan_low:.2f} - ${scan_high:.2f}")
        logger.info(f"Current price: ${current_price:.2f}, M15 ATR: ${atr_15min:.2f}")
        
        # Collect all items from all sources
        all_items = []
        for source_type, items in confluence_sources.items():
            if isinstance(items, list):
                for item in items:
                    if 'level' in item:
                        item_copy = item.copy()
                        item_copy['source_type'] = source_type
                        item_type = item.get('type', source_type)
                        item_copy['weight'] = self.confluence_weights.get(item_type, 1.0)
                        all_items.append(item_copy)
        
        if not all_items:
            logger.warning("No confluence items to process")
            return []
        
        logger.info(f"Processing {len(all_items)} confluence items from {len(confluence_sources)} sources")
        
        # Sort by price level
        all_items.sort(key=lambda x: x['level'])
        
        # Find clusters
        clusters = self._find_clusters(all_items, atr_15min)
        
        # Create zones from clusters
        zones = []
        zone_id = 1
        
        for cluster in clusters:
            score = sum(item['weight'] for item in cluster)
            
            if score >= self.min_confluence_score:
                zone = self._create_zone_from_cluster(
                    cluster, zone_id, current_price, atr_15min
                )
                zones.append(zone)
                zone_id += 1
        
        logger.info(f"Found {len(zones)} zones from {len(clusters)} clusters")
        
        # Sort zones by distance from current price
        zones.sort(key=lambda z: z.distance_from_current)
        
        # Refine final range to 1 ATR 15-Minute
        zones = self.refine_zones_to_m15_atr(zones, atr_15min)
        logger.info(f"Refined {len(zones)} zones to 1x M15 ATR width (${atr_15min:.2f})")
        
        return zones
    
    def _find_clusters(self, items: List[Dict], atr_15min: float) -> List[List[Dict]]:
        """Find clusters of nearby items"""
        
        if not items:
            return []
        
        cluster_distance = atr_15min * self.cluster_distance_atr
        clusters = []
        current_cluster = [items[0]]
        
        for item in items[1:]:
            if item['level'] - current_cluster[-1]['level'] <= cluster_distance:
                current_cluster.append(item)
            else:
                if current_cluster:
                    clusters.append(current_cluster)
                current_cluster = [item]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        return clusters
    
    def _create_zone_from_cluster(self,
                                 cluster: List[Dict],
                                 zone_id: int,
                                 current_price: float,
                                 atr_15min: float) -> DiscoveredZone:
        """Create a zone from a cluster of confluence items with width constraint"""
        
        prices = [item['level'] for item in cluster]
        weights = [item['weight'] for item in cluster]
        total_weight = sum(weights)
        
        # Calculate weighted center first
        zone_center = sum(p * w for p, w in zip(prices, weights)) / total_weight
        
        # Initial zone boundaries from cluster
        initial_low = min(prices) - (atr_15min * 0.25)
        initial_high = max(prices) + (atr_15min * 0.25)
        initial_width = initial_high - initial_low
        
        # Maximum zone width constraint (3x M15 ATR)
        max_zone_width = atr_15min * 3.0
        
        # Apply width constraint if needed
        if initial_width > max_zone_width:
            zone_low = zone_center - (max_zone_width / 2)
            zone_high = zone_center + (max_zone_width / 2)
            logger.debug(f"Zone {zone_id} width capped: {initial_width:.2f} -> {max_zone_width:.2f}")
        else:
            zone_low = initial_low
            zone_high = initial_high
        
        # Calculate confluence score
        confluence_score = total_weight
        
        # Bonus for multiple different types
        unique_types = set(item.get('type', item.get('source_type', '')) for item in cluster)
        if len(unique_types) > 1:
            confluence_score *= (1 + 0.1 * (len(unique_types) - 1))
        
        # Penalty for overly wide initial clusters
        if initial_width > (atr_15min * 2):
            width_ratio = initial_width / (atr_15min * 2)
            confluence_score = confluence_score / (1 + (width_ratio - 1) * 0.5)
            logger.debug(f"Zone {zone_id} score reduced due to width: {width_ratio:.2f}x expected")
        
        # Cap extreme scores
        if confluence_score > 50:
            confluence_score = 50 + (confluence_score - 50) * 0.1
        
        # Determine confluence level
        if confluence_score >= 10:
            level = 'L5'
        elif confluence_score >= 7:
            level = 'L4'
        elif confluence_score >= 5:
            level = 'L3'
        elif confluence_score >= 3:
            level = 'L2'
        else:
            level = 'L1'
        
        # Prepare confluent sources info
        confluent_sources = []
        for item in cluster:
            confluent_sources.append({
                'type': item.get('type', item.get('source_type', 'unknown')),
                'name': item.get('name', 'unnamed'),
                'price': item['level'],
                'weight': item['weight']
            })
        
        return DiscoveredZone(
            zone_id=zone_id,
            zone_high=zone_high,
            zone_low=zone_low,
            center_price=zone_center,
            zone_width=zone_high - zone_low,
            confluence_score=confluence_score,
            confluence_level=level,
            confluent_sources=confluent_sources,
            distance_from_current=abs(zone_center - current_price),
            distance_percentage=abs(zone_center - current_price) / current_price * 100,
            zone_type='resistance' if zone_center > current_price else 'support'
        )
    
    def refine_zones_to_m15_atr(self, zones: List[DiscoveredZone], atr_15min: float) -> List[DiscoveredZone]:
        """Refine zones to exactly 1x M15 ATR width centered on highest confluence point"""
        
        refined_zones = []
        
        for zone in zones:
            # Find the price with highest weight concentration
            price_weights = {}
            for source in zone.confluent_sources:
                price = source['price']
                weight = source['weight']
                if price not in price_weights:
                    price_weights[price] = 0
                price_weights[price] += weight
            
            # Find peak confluence point
            if price_weights:
                peak_price = max(price_weights.keys(), key=lambda p: price_weights[p])
            else:
                peak_price = zone.center_price
            
            # Create refined zone of exactly 1x M15 ATR
            refined_zone = DiscoveredZone(
                zone_id=zone.zone_id,
                zone_low=peak_price - (atr_15min * 0.5),
                zone_high=peak_price + (atr_15min * 0.5),
                center_price=peak_price,
                zone_width=atr_15min,
                confluence_score=zone.confluence_score,
                confluence_level=zone.confluence_level,
                confluent_sources=zone.confluent_sources,
                best_candle=zone.best_candle if hasattr(zone, 'best_candle') else None,
                candle_score=zone.candle_score if hasattr(zone, 'candle_score') else 0.0,
                distance_from_current=zone.distance_from_current,
                distance_percentage=zone.distance_percentage,
                zone_type=zone.zone_type,
                recency_score=zone.recency_score if hasattr(zone, 'recency_score') else 0.0
            )
            
            refined_zones.append(refined_zone)
        
        return refined_zones
    
    def find_best_candles_for_zones(self,
                                   zones: List[DiscoveredZone],
                                   symbol: str,
                                   polygon_client,
                                   lookback_days: int = 30) -> None:
        """Find M15 candle with highest overlap and calculate recency scores"""
        
        logger.info(f"Finding best M15 candles for {len(zones)} zones")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        df = polygon_client.fetch_bars(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            '15min'
        )
        
        if df is None or df.empty:
            logger.warning("No M15 data available")
            return
        
        current_time_utc = datetime.now(pytz.UTC)
        
        for zone in zones:
            best_candle = None
            best_overlap = 0
            
            for idx, row in df.iterrows():
                candle_high = row['high']
                candle_low = row['low']
                
                # Calculate overlap
                overlap_low = max(candle_low, zone.zone_low)
                overlap_high = min(candle_high, zone.zone_high)
                
                if overlap_high > overlap_low:
                    candle_range = candle_high - candle_low
                    if candle_range > 0:
                        overlap_pct = (overlap_high - overlap_low) / candle_range
                        
                        if overlap_pct > best_overlap:
                            best_overlap = overlap_pct
                            best_candle = {
                                'datetime': idx,
                                'high': candle_high,
                                'low': candle_low,
                                'open': row['open'],
                                'close': row['close'],
                                'volume': row.get('volume', 0),
                                'overlap_pct': overlap_pct * 100,
                                'zone_id': zone.zone_id,
                                'zone_level': zone.confluence_level
                            }
            
            if best_candle:
                zone.best_candle = best_candle
                zone.candle_score = best_overlap * 100
                
                # Calculate recency with proper timezone handling
                candle_datetime = best_candle['datetime']
                
                if hasattr(candle_datetime, 'tzinfo'):
                    if candle_datetime.tzinfo is None:
                        candle_dt = pytz.UTC.localize(candle_datetime)
                    else:
                        candle_dt = candle_datetime
                else:
                    candle_dt = pytz.UTC.localize(candle_datetime)
                
                time_diff = current_time_utc - candle_dt
                days_old = time_diff.days
                
                # Apply recency boost
                if days_old <= 5:
                    zone.recency_score = 1.2
                    zone.confluence_score *= 1.2
                elif days_old <= 10:
                    zone.recency_score = 1.1
                    zone.confluence_score *= 1.1
                else:
                    zone.recency_score = 1.0
                
                logger.debug(f"Zone {zone.zone_id}: Best candle {best_overlap:.1%} overlap, {days_old} days old")