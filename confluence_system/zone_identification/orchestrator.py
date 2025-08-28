"""
Zone Identification Orchestrator
Coordinates overlap analysis between fractals and confluence zones
Includes fallback for high-confluence zones without fractals
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .overlap_analyzer import OverlapAnalyzer
from .fractal_ranker import FractalRanker
from .models import TradingLevel

logger = logging.getLogger(__name__)


class ZoneIdentificationOrchestrator:
    """
    Main orchestrator for zone identification module
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.overlap_analyzer = None
        self.fractal_ranker = None
        self.is_initialized = False
        self.atr_5min = 0.3  # Default, should be calculated from data
        
    def initialize(self, current_price: float, atr_5min: Optional[float] = None):
        """
        Initialize components with market context
        
        Args:
            current_price: Current market price
            atr_5min: Optional 5-minute ATR for synthetic levels
        """
        self.overlap_analyzer = OverlapAnalyzer(overlap_threshold=0.2)
        self.fractal_ranker = FractalRanker(current_price)
        self.current_price = current_price
        if atr_5min:
            self.atr_5min = atr_5min
        self.is_initialized = True
        logger.info(f"Zone Identification initialized with price ${current_price:.2f}")
        
    def identify_trading_levels(self,
                              fractal_data: Dict,
                              confluence_zones: List[any],
                              atr_filter: Optional[float] = None,
                              ensure_coverage: bool = True,
                              min_above: int = 3,
                              min_below: int = 3) -> List[TradingLevel]:
        """
        Main entry point - identify tradeable fractal levels with fallback
        
        Args:
            fractal_data: Output from fractal_engine
            confluence_zones: Zones from confluence_scanner
            atr_filter: Optional ATR multiplier for range filtering
            ensure_coverage: Whether to ensure minimum levels above/below price
            min_above: Minimum levels above current price
            min_below: Minimum levels below current price
            
        Returns:
            List of ranked TradingLevel objects
        """
        if not self.is_initialized:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
            
        logger.info(f"Processing {len(fractal_data.get('fractals', {}).get('highs', []))} highs and "
                   f"{len(fractal_data.get('fractals', {}).get('lows', []))} lows against "
                   f"{len(confluence_zones)} confluence zones")
        
        trading_levels = []
        
        # Process swing highs
        for high in fractal_data.get('fractals', {}).get('highs', []):
            high['type'] = 'high'
            overlaps = self.overlap_analyzer.find_overlapping_zones(high, confluence_zones)
            
            if overlaps or self._should_include_no_confluence(high):
                level = self.fractal_ranker.create_trading_level(high, overlaps)
                trading_levels.append(level)
                
        # Process swing lows
        for low in fractal_data.get('fractals', {}).get('lows', []):
            low['type'] = 'low'
            overlaps = self.overlap_analyzer.find_overlapping_zones(low, confluence_zones)
            
            if overlaps or self._should_include_no_confluence(low):
                level = self.fractal_ranker.create_trading_level(low, overlaps)
                trading_levels.append(level)
                
        logger.info(f"Created {len(trading_levels)} trading levels from fractals")
        
        # Apply fallback for high-confluence zones without fractals
        high_conf_zones = [z for z in confluence_zones 
                          if z.confluence_level in ['L5', 'L4', 'L3']]
        
        # Track which zones already have fractal coverage
        zones_with_fractals = set()
        for level in trading_levels:
            if level.overlapping_zones:
                for overlap in level.overlapping_zones:
                    # Try to get zone_id, use zone object id as fallback
                    zone_id = overlap.get('zone_id')
                    if zone_id:
                        zones_with_fractals.add(zone_id)
        
        # Find L3-L5 zones without fractal coverage
        synthetic_count = 0
        for zone in high_conf_zones:
            zone_id = getattr(zone, 'zone_id', id(zone))
            
            # Check if this zone has fractal coverage
            has_coverage = False
            if zone_id in zones_with_fractals:
                has_coverage = True
            else:
                # Double-check by comparing zones directly
                for level in trading_levels:
                    if level.overlapping_zones:
                        for overlap in level.overlapping_zones:
                            if abs(overlap.get('zone_score', 0) - zone.confluence_score) < 0.01:
                                has_coverage = True
                                break
            
            if not has_coverage:
                # Create synthetic trading level
                synthetic_level = self._create_synthetic_level(zone)
                trading_levels.append(synthetic_level)
                synthetic_count += 1
                logger.info(f"Created synthetic level for {zone.confluence_level} zone at "
                          f"${zone.zone_low:.2f}-${zone.zone_high:.2f}")
        
        if synthetic_count > 0:
            logger.info(f"Added {synthetic_count} synthetic levels for high-confluence zones")
        
        # Apply filters
        if atr_filter:
            max_distance_pct = (atr_filter / self.current_price) * 100
            trading_levels = self.fractal_ranker.filter_by_proximity(
                trading_levels, max_distance_pct
            )
            logger.info(f"Filtered to {len(trading_levels)} levels within {atr_filter:.2f} ATR")
            
        # Remove duplicates
        trading_levels = self.fractal_ranker.deduplicate_overlapping_fractals(trading_levels)
        logger.info(f"After deduplication: {len(trading_levels)} unique levels")
        
        # Ensure minimum coverage if requested
        if ensure_coverage:
            trading_levels = self._ensure_minimum_coverage(
                trading_levels, confluence_zones, min_above, min_below
            )
        
        # Rank final levels
        ranked_levels = self.fractal_ranker.rank_trading_levels(trading_levels)
        
        logger.info(f"Zone identification complete: {len(ranked_levels)} trading levels")
        
        return ranked_levels
        
    def _should_include_no_confluence(self, fractal: Dict) -> bool:
        """
        Determine if a fractal with no confluence should be included
        
        Current logic: Include if within 2% of current price
        """
        distance_pct = abs(fractal['price'] - self.current_price) / self.current_price * 100
        return distance_pct <= 2.0
        
    def _create_synthetic_level(self, zone: any) -> TradingLevel:
        """
        Create synthetic trading level for high-confluence zones without fractals
        
        Args:
            zone: Confluence zone object
            
        Returns:
            TradingLevel object representing the zone
        """
        # Use zone center with 5-minute ATR width
        center = (zone.zone_high + zone.zone_low) / 2
        
        # Extract confluence factors from zone sources
        has_hvn = False
        has_camarilla = False
        has_weekly = False
        has_daily = False
        has_atr = False
        timeframes = set()
        
        for source in zone.confluent_sources:
            source_type = source.get('type', '')
            
            if 'hvn' in source_type:
                has_hvn = True
                if '-' in source_type:
                    timeframes.add(source_type.split('-')[1])
            elif 'cam' in source_type:
                has_camarilla = True
                if '-' in source_type:
                    timeframes.add(source_type.split('-')[1])
            elif 'weekly' in source_type:
                has_weekly = True
            elif 'daily' in source_type:
                has_daily = True
            elif 'atr' in source_type:
                has_atr = True
        
        has_multiple_timeframes = len(timeframes) > 1
        
        # Determine type based on zone position
        fractal_type = 'zone_resistance' if center > self.current_price else 'zone_support'
        
        # Calculate distances
        distance = abs(center - self.current_price)
        distance_pct = (distance / self.current_price) * 100
        
        # Priority score with bonus for synthetic high-confluence zones
        proximity_factor = max(0, 10 - distance_pct) / 10
        priority_score = zone.confluence_score * (1 + proximity_factor) * 1.2  # 20% bonus
        
        return TradingLevel(
            datetime=datetime.now(),
            fractal_type=fractal_type,
            high_price=center + self.atr_5min,
            low_price=center - self.atr_5min,
            open_price=center,
            close_price=center,
            volume=0,
            confluence_score=zone.confluence_score,
            confluence_level=zone.confluence_level,
            overlapping_zones=[{
                'zone_id': getattr(zone, 'zone_id', 0),
                'zone_score': zone.confluence_score,
                'zone_level': zone.confluence_level,
                'overlap_percentage': 1.0,  # Full overlap since it's synthetic
                'zone_sources': zone.confluent_sources,
                'confluence_factors': {
                    'has_hvn': has_hvn,
                    'has_camarilla': has_camarilla,
                    'has_weekly': has_weekly,
                    'has_daily': has_daily,
                    'has_atr': has_atr,
                    'has_multiple_timeframes': has_multiple_timeframes
                }
            }],
            distance_from_price=distance,
            distance_percentage=distance_pct,
            priority_score=priority_score,
            has_hvn=has_hvn,
            has_camarilla=has_camarilla,
            has_weekly=has_weekly,
            has_daily=has_daily,
            has_atr=has_atr,
            has_multiple_timeframes=has_multiple_timeframes
        )
        
    def _ensure_minimum_coverage(self,
                                trading_levels: List[TradingLevel],
                                confluence_zones: List[any],
                                min_above: int,
                                min_below: int) -> List[TradingLevel]:
        """
        Ensure minimum number of levels above and below current price
        
        Args:
            trading_levels: Current list of trading levels
            confluence_zones: All confluence zones
            min_above: Minimum levels needed above price
            min_below: Minimum levels needed below price
            
        Returns:
            Updated list with minimum coverage
        """
        levels_above = [l for l in trading_levels if l.low_price > self.current_price]
        levels_below = [l for l in trading_levels if l.high_price < self.current_price]
        
        # If we have enough, return as is
        if len(levels_above) >= min_above and len(levels_below) >= min_below:
            return trading_levels
            
        # Need to add more levels
        if len(levels_above) < min_above:
            needed_above = min_above - len(levels_above)
            zones_above = [z for z in confluence_zones 
                          if (z.zone_low + z.zone_high) / 2 > self.current_price]
            
            # Sort by confluence score
            zones_above.sort(key=lambda x: x.confluence_score, reverse=True)
            
            # Add best zones that aren't already covered
            added = 0
            for zone in zones_above:
                if added >= needed_above:
                    break
                    
                # Check if already covered
                already_covered = False
                zone_center = (zone.zone_low + zone.zone_high) / 2
                for level in levels_above:
                    if abs(level.low_price - zone_center) < self.atr_5min * 2:
                        already_covered = True
                        break
                        
                if not already_covered:
                    synthetic = self._create_synthetic_level(zone)
                    trading_levels.append(synthetic)
                    added += 1
                    logger.info(f"Added synthetic level above for coverage: {zone.confluence_level}")
        
        # Similar logic for below levels
        if len(levels_below) < min_below:
            needed_below = min_below - len(levels_below)
            zones_below = [z for z in confluence_zones 
                          if (z.zone_low + z.zone_high) / 2 < self.current_price]
            
            zones_below.sort(key=lambda x: x.confluence_score, reverse=True)
            
            added = 0
            for zone in zones_below:
                if added >= needed_below:
                    break
                    
                already_covered = False
                zone_center = (zone.zone_low + zone.zone_high) / 2
                for level in levels_below:
                    if abs(level.high_price - zone_center) < self.atr_5min * 2:
                        already_covered = True
                        break
                        
                if not already_covered:
                    synthetic = self._create_synthetic_level(zone)
                    trading_levels.append(synthetic)
                    added += 1
                    logger.info(f"Added synthetic level below for coverage: {zone.confluence_level}")
        
        return trading_levels
        
    def format_results(self, trading_levels: List[TradingLevel]) -> str:
        """
        Format trading levels for display
        """
        if not trading_levels:
            return "No trading levels identified"
            
        output = []
        output.append("=" * 60)
        output.append("IDENTIFIED TRADING LEVELS")
        output.append("=" * 60)
        
        # Group by level
        by_level = {}
        for level in trading_levels:
            if level.confluence_level not in by_level:
                by_level[level.confluence_level] = []
            by_level[level.confluence_level].append(level)
            
        # Display by confluence level
        for conf_level in ['L5', 'L4', 'L3', 'L2', 'L1', 'L0']:
            if conf_level not in by_level:
                continue
                
            output.append(f"\n{conf_level} LEVELS ({len(by_level[conf_level])} levels)")
            output.append("-" * 40)
            
            for level in by_level[conf_level][:5]:  # Show top 5 per level
                level_type = level.fractal_type.upper()
                if 'zone' in level.fractal_type:
                    level_type = f"{level_type} (SYNTHETIC)"
                    
                output.append(f"\n{level_type} @ ${level.low_price:.2f}-${level.high_price:.2f}")
                output.append(f"  Time: {level.datetime}")
                output.append(f"  Score: {level.confluence_score:.1f}")
                output.append(f"  Distance: {level.distance_percentage:.1f}%")
                
                # Show confluence factors
                factors = []
                if level.has_hvn: factors.append("HVN")
                if level.has_camarilla: factors.append("Camarilla")
                if level.has_weekly: factors.append("Weekly")
                if level.has_daily: factors.append("Daily")
                if level.has_atr: factors.append("ATR")
                if level.has_multiple_timeframes: factors.append("Multi-TF")
                
                if factors:
                    output.append(f"  Factors: {', '.join(factors)}")
                    
        return "\n".join(output)