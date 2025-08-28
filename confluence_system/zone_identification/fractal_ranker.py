"""
Ranking and prioritization of fractal candlesticks
"""

import logging
from typing import List, Dict
from datetime import datetime
from .models import TradingLevel

logger = logging.getLogger(__name__)


class FractalRanker:
    """
    Ranks and prioritizes fractal candlesticks based on confluence
    """
    
    def __init__(self, current_price: float):
        """
        Args:
            current_price: Current market price for distance calculations
        """
        self.current_price = current_price
        
    def create_trading_level(self,
                           fractal: Dict,
                           overlaps: List[Dict]) -> TradingLevel:
        """
        Create a TradingLevel from fractal and its overlapping zones
        
        Args:
            fractal: Fractal data
            overlaps: List of overlapping zone details
            
        Returns:
            TradingLevel object
        """
        # Get best overlap (highest score)
        if not overlaps:
            # No confluence - minimal score
            confluence_score = 0.0
            confluence_level = "L0"
            confluence_factors = {}
        else:
            best_overlap = overlaps[0]
            confluence_score = best_overlap['zone_score']
            confluence_level = best_overlap['zone_level']
            confluence_factors = best_overlap['confluence_factors']
            
        # Calculate distance from current price
        fractal_price = fractal['price']
        distance = abs(fractal_price - self.current_price)
        distance_pct = (distance / self.current_price) * 100
        
        # Calculate priority score
        # Higher confluence + closer to price = higher priority
        proximity_factor = max(0, 10 - distance_pct) / 10  # 0-1, closer is better
        priority_score = confluence_score * (1 + proximity_factor)
        
        return TradingLevel(
            datetime=fractal['datetime'],
            fractal_type=fractal.get('type', 'unknown'),
            high_price=fractal.get('bar_high', fractal['price']),
            low_price=fractal.get('bar_low', fractal['price']),
            open_price=fractal.get('bar_open', fractal['price']),
            close_price=fractal.get('bar_close', fractal['price']),
            volume=fractal.get('bar_volume', 0),
            confluence_score=confluence_score,
            confluence_level=confluence_level,
            overlapping_zones=overlaps,
            has_hvn=confluence_factors.get('has_hvn', False),
            has_camarilla=confluence_factors.get('has_camarilla', False),
            has_weekly=confluence_factors.get('has_weekly', False),
            has_daily=confluence_factors.get('has_daily', False),
            has_atr=confluence_factors.get('has_atr', False),
            has_multiple_timeframes=confluence_factors.get('has_multiple_timeframes', False),
            distance_from_price=distance,
            distance_percentage=distance_pct,
            priority_score=priority_score
        )
        
    def rank_trading_levels(self,
                          trading_levels: List[TradingLevel]) -> List[TradingLevel]:
        """
        Rank trading levels by priority
        
        Ranking order:
        1. Confluence level (L5 > L4 > L3 > L2 > L1)
        2. Confluence score (higher is better)
        3. Proximity to current price (closer is better)
        
        Args:
            trading_levels: List of TradingLevel objects
            
        Returns:
            Sorted list of trading levels
        """
        # Define level order
        level_order = {'L5': 5, 'L4': 4, 'L3': 3, 'L2': 2, 'L1': 1, 'L0': 0}
        
        # Sort by multiple criteria
        sorted_levels = sorted(
            trading_levels,
            key=lambda x: (
                level_order.get(x.confluence_level, 0),  # Level (L5 first)
                x.confluence_score,                       # Score (higher first)
                -x.distance_percentage                    # Distance (closer first)
            ),
            reverse=True
        )
        
        return sorted_levels
        
    def filter_by_proximity(self,
                           trading_levels: List[TradingLevel],
                           max_distance_pct: float = 5.0) -> List[TradingLevel]:
        """
        Filter levels within trading range
        
        Args:
            trading_levels: List of trading levels
            max_distance_pct: Maximum distance from current price (%)
            
        Returns:
            Filtered list within range
        """
        return [
            level for level in trading_levels
            if level.distance_percentage <= max_distance_pct
        ]
        
    def deduplicate_overlapping_fractals(self,
                                        trading_levels: List[TradingLevel],
                                        price_threshold: float = 0.5) -> List[TradingLevel]:
        """
        Remove duplicate fractals at similar price levels
        Keeps the highest scoring fractal when duplicates exist
        
        Args:
            trading_levels: List of trading levels
            price_threshold: Price difference threshold (in points)
            
        Returns:
            Deduplicated list
        """
        if not trading_levels:
            return []
            
        # Sort by price for efficient comparison
        sorted_by_price = sorted(trading_levels, key=lambda x: x.low_price)
        
        kept_levels = []
        skip_indices = set()
        
        for i, level in enumerate(sorted_by_price):
            if i in skip_indices:
                continue
                
            # Find all levels within threshold
            similar_levels = [level]
            for j in range(i + 1, len(sorted_by_price)):
                if j in skip_indices:
                    continue
                    
                other = sorted_by_price[j]
                price_diff = abs(level.low_price - other.low_price)
                
                if price_diff <= price_threshold:
                    similar_levels.append(other)
                    skip_indices.add(j)
                elif other.low_price > level.high_price + price_threshold:
                    # No more overlaps possible
                    break
                    
            # Keep the best from similar levels
            best = max(similar_levels, key=lambda x: x.priority_score)
            kept_levels.append(best)
            
        return kept_levels