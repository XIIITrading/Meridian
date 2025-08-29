"""
Fractal Integration Module
Integrates fractals from fractal_engine as the primary candle data for zones
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FractalCandle:
    """Fractal data formatted as candle for zone association"""
    datetime: datetime
    type: str  # 'high' or 'low'
    price: float
    high: float
    low: float
    open: float
    close: float
    volume: float
    zone_id: Optional[int] = None
    zone_level: Optional[str] = None
    distance_to_zone: Optional[float] = None
    
    @classmethod
    def from_fractal(cls, fractal: Dict, fractal_type: str):
        """Create from fractal engine output"""
        return cls(
            datetime=fractal['datetime'],
            type=fractal_type,
            price=fractal['price'],
            high=fractal.get('bar_high', fractal['price']),
            low=fractal.get('bar_low', fractal['price']),
            open=fractal.get('bar_open', fractal['price']),
            close=fractal.get('bar_close', fractal['price']),
            volume=fractal.get('bar_volume', 0)
        )

class FractalIntegrator:
    """
    Integrates fractals with discovered zones
    Replaces the complex candle_selector with direct fractal usage
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def associate_fractals_with_zones(self, 
                                     zones: List[Any],
                                     fractals: Dict) -> Dict[int, FractalCandle]:
        """
        Associate fractals with zones based on price proximity
        
        Args:
            zones: List of discovered zones
            fractals: Dict with 'highs' and 'lows' from fractal_engine
            
        Returns:
            Dict mapping zone_id to best matching FractalCandle
        """
        if not zones:
            return {}
            
        # Convert fractals to FractalCandle objects
        fractal_candles = []
        
        for high in fractals.get('highs', []):
            fractal_candles.append(FractalCandle.from_fractal(high, 'high'))
            
        for low in fractals.get('lows', []):
            fractal_candles.append(FractalCandle.from_fractal(low, 'low'))
            
        if not fractal_candles:
            logger.warning("No fractals provided for zone association")
            return {}
            
        # Sort by datetime for recency preference
        fractal_candles.sort(key=lambda x: x.datetime, reverse=True)
        
        # Associate each zone with the closest fractal
        zone_associations = {}
        
        for zone in zones:
            best_fractal = self._find_best_fractal_for_zone(zone, fractal_candles)
            
            if best_fractal:
                # Update fractal with zone info
                best_fractal.zone_id = zone.zone_id
                best_fractal.zone_level = zone.confluence_level
                zone_associations[zone.zone_id] = best_fractal
                
                # Update zone with fractal data
                zone.best_candle = {
                    'datetime': best_fractal.datetime,
                    'high': best_fractal.high,
                    'low': best_fractal.low,
                    'open': best_fractal.open,
                    'close': best_fractal.close,
                    'volume': best_fractal.volume,
                    'overlap_pct': self._calculate_overlap(best_fractal, zone),
                    'zone_id': zone.zone_id,
                    'zone_level': zone.confluence_level
                }
                
                logger.debug(f"Zone {zone.zone_id} associated with fractal at "
                           f"{best_fractal.datetime} (distance: {best_fractal.distance_to_zone:.2f})")
                
        logger.info(f"Associated {len(zone_associations)} zones with fractals")
        return zone_associations
        
    def _find_best_fractal_for_zone(self, zone: Any, fractal_candles: List[FractalCandle]) -> Optional[FractalCandle]:
        """
        Find the best fractal for a zone based on:
        1. Price proximity to zone
        2. Type match (high fractal for resistance, low for support)
        3. Recency (prefer more recent fractals)
        """
        zone_center = (zone.zone_high + zone.zone_low) / 2
        zone_width = zone.zone_high - zone.zone_low
        
        # Filter fractals that are reasonably close to the zone
        max_distance = zone_width * 2  # Within 2x zone width
        
        candidates = []
        for fractal in fractal_candles:
            # Check if fractal overlaps or is near the zone
            if fractal.high >= zone.zone_low and fractal.low <= zone.zone_high:
                # Direct overlap - highest priority
                distance = 0
            else:
                # Calculate distance to zone
                if fractal.price > zone.zone_high:
                    distance = fractal.price - zone.zone_high
                elif fractal.price < zone.zone_low:
                    distance = zone.zone_low - fractal.price
                else:
                    distance = abs(fractal.price - zone_center)
                    
            if distance <= max_distance:
                fractal_copy = FractalCandle(
                    datetime=fractal.datetime,
                    type=fractal.type,
                    price=fractal.price,
                    high=fractal.high,
                    low=fractal.low,
                    open=fractal.open,
                    close=fractal.close,
                    volume=fractal.volume,
                    distance_to_zone=distance
                )
                
                # Score bonus for type match
                type_match_bonus = 0
                if zone.zone_type == 'resistance' and fractal.type == 'high':
                    type_match_bonus = -zone_width * 0.5  # Reduce effective distance
                elif zone.zone_type == 'support' and fractal.type == 'low':
                    type_match_bonus = -zone_width * 0.5
                    
                fractal_copy.distance_to_zone = max(0, distance + type_match_bonus)
                candidates.append(fractal_copy)
                
        if not candidates:
            return None
            
        # Sort by distance (closest first), then by recency
        candidates.sort(key=lambda x: (x.distance_to_zone, -x.datetime.timestamp()))
        
        return candidates[0]
        
    def _calculate_overlap(self, fractal: FractalCandle, zone: Any) -> float:
        """Calculate overlap percentage between fractal candle and zone"""
        candle_range = fractal.high - fractal.low
        if candle_range == 0:
            # Point fractal
            if zone.zone_low <= fractal.price <= zone.zone_high:
                return 100.0
            return 0.0
            
        # Calculate overlap
        overlap_low = max(fractal.low, zone.zone_low)
        overlap_high = min(fractal.high, zone.zone_high)
        
        if overlap_high <= overlap_low:
            return 0.0
            
        overlap_range = overlap_high - overlap_low
        return (overlap_range / candle_range) * 100
        
    def add_fractals_as_confluence(self, 
                              confluence_sources: Dict,
                              fractals: Dict,
                              atr_15min: float) -> Dict:
        """Add fractals as a confluence source for zone discovery"""
        fractal_items = []
        
        # Add swing highs as resistance levels
        for high in fractals.get('highs', []):
            fractal_items.append({
                'name': f'FractalHigh_{high["datetime"].strftime("%m%d_%H%M")}',
                'level': high['price'],
                'low': high.get('bar_low', high['price']),  # Use actual candle boundaries
                'high': high.get('bar_high', high['price']),  # Use actual candle boundaries
                'type': 'fractal_high',
                'datetime': high['datetime']
            })
            
        # Add swing lows as support levels  
        for low in fractals.get('lows', []):
            fractal_items.append({
                'name': f'FractalLow_{low["datetime"].strftime("%m%d_%H%M")}',
                'level': low['price'],
                'low': low.get('bar_low', low['price']),  # Use actual candle boundaries
                'high': low.get('bar_high', low['price']),  # Use actual candle boundaries
                'type': 'fractal_low',
                'datetime': low['datetime']
            })
            
        if fractal_items:
            confluence_sources['fractals'] = fractal_items
            logger.info(f"Added {len(fractal_items)} fractals as confluence source")
            
        return confluence_sources