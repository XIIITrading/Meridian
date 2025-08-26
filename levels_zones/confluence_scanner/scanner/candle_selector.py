# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\scanner\candle_selector.py

"""
Candle Selector Module
Sophisticated candle selection and scoring for discovered zones
Finds the best M15 candle to represent each high-confluence zone
NO SYNTHETIC CANDLES - only real price action
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CandleScore:
    """Detailed scoring for a candle within a zone"""
    datetime: datetime
    total_score: float
    overlap_score: float
    confluence_score: float
    volume_score: float
    structure_score: float
    recency_score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredCandle:
    """A candle with comprehensive scoring information"""
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    mid_point: float
    zone_id: int
    zone_level: str
    scoring: CandleScore
    overlap_percentage: float
    touches_confluence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display"""
        return {
            'datetime': self.datetime.isoformat(),
            'high': self.high,
            'low': self.low,
            'open': self.open,
            'close': self.close,
            'mid': self.mid_point,
            'volume': self.volume,
            'score': self.scoring.total_score,
            'zone_id': self.zone_id,
            'zone_level': self.zone_level,
            'overlap_pct': self.overlap_percentage,
            'confluences': self.touches_confluence
        }


class CandleSelector:
    """
    Advanced candle selection for discovered zones
    Scores candles based on multiple criteria to find the best representative
    ONLY uses real historical candles - no synthetic data
    """
    
    def __init__(self, config=None):
        """
        Initialize candle selector
        
        Args:
            config: ScannerConfig instance
        """
        self.config = config
        if not config:
            from config import ScannerConfig
            self.config = ScannerConfig()
        
        # Scoring weights
        self.weights = {
            'overlap': 0.30,      # 30% - How much candle overlaps zone
            'confluence': 0.25,   # 25% - Touches specific confluence levels
            'volume': 0.20,       # 20% - Volume relative to others
            'structure': 0.15,    # 15% - Price action structure
            'recency': 0.10       # 10% - How recent the candle is
        }
        
        # Cache for M15 data
        self.candle_cache = {}
        
    def select_best_candles(self,
                           zones: List[Any],  # DiscoveredZone objects
                           symbol: str,
                           polygon_client,
                           lookback_days: int = 30,
                           analysis_datetime: Optional[datetime] = None) -> Dict[int, ScoredCandle]:
        """
        Select the best M15 candle for each discovered zone
        Returns only zones that have real candles
        
        Args:
            zones: List of discovered zones
            symbol: Stock ticker
            polygon_client: PolygonClient instance
            lookback_days: Days to look back for candles
            analysis_datetime: Analysis datetime (default: now)
            
        Returns:
            Dictionary mapping zone_id to best ScoredCandle
            Only includes zones with real candles
        """
        if not zones:
            logger.warning("No zones provided for candle selection")
            return {}
        
        if analysis_datetime is None:
            analysis_datetime = datetime.now()
        
        logger.info(f"Selecting best candles for {len(zones)} zones")
        
        # Step 1: Fetch M15 data
        m15_data = self._fetch_m15_data(
            symbol, 
            polygon_client,
            analysis_datetime,
            lookback_days
        )
        
        if m15_data is None or m15_data.empty:
            logger.warning("No M15 data available for candle selection")
            logger.warning("Cannot proceed without real candle data")
            return {}
        
        # Step 2: Process each zone
        best_candles = {}
        zones_without_candles = []
        
        for zone in zones:
            # Find overlapping candles
            overlapping = self._find_overlapping_candles(m15_data, zone)
            
            if not overlapping:
                logger.debug(f"Zone {zone.zone_id}: No overlapping candles found - skipping zone")
                zones_without_candles.append(zone.zone_id)
                continue  # Skip this zone entirely
            
            # Score all overlapping candles
            scored_candles = self._score_candles(
                overlapping,
                zone,
                m15_data
            )
            
            # Select the best
            if scored_candles:
                best = max(scored_candles, key=lambda c: c.scoring.total_score)
                best_candles[zone.zone_id] = best
                
                logger.info(f"Zone {zone.zone_id} ({zone.confluence_level}): "
                          f"Selected candle from {best.datetime} "
                          f"(score: {best.scoring.total_score:.2f})")
        
        # Log summary
        logger.info(f"Found real candles for {len(best_candles)}/{len(zones)} zones")
        if zones_without_candles:
            logger.info(f"Zones without candles (excluded): {zones_without_candles}")
        
        return best_candles
    
    def _fetch_m15_data(self,
                       symbol: str,
                       polygon_client,
                       analysis_datetime: datetime,
                       lookback_days: int) -> Optional[pd.DataFrame]:
        """
        Fetch M15 data with caching
        
        Args:
            symbol: Stock ticker
            polygon_client: PolygonClient instance
            analysis_datetime: Analysis datetime
            lookback_days: Days to look back
            
        Returns:
            DataFrame with M15 data
        """
        cache_key = f"{symbol}_{analysis_datetime.date()}_{lookback_days}"
        
        if cache_key in self.candle_cache:
            logger.debug(f"Using cached M15 data for {symbol}")
            return self.candle_cache[cache_key]
        
        try:
            end_date = analysis_datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            logger.info(f"Fetching M15 data for {symbol}: "
                       f"{start_date.date()} to {end_date.date()}")
            
            df = polygon_client.fetch_bars(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                '15min'
            )
            
            if df is not None and not df.empty:
                # Add calculated fields
                df['mid'] = (df['high'] + df['low']) / 2
                df['range'] = df['high'] - df['low']
                df['body'] = abs(df['close'] - df['open'])
                df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
                df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
                
                # Cache the data
                self.candle_cache[cache_key] = df
                
                logger.info(f"Fetched {len(df)} M15 candles")
                return df
            else:
                logger.warning(f"No M15 data returned for {symbol}")
                return None
            
        except Exception as e:
            logger.error(f"Error fetching M15 data: {e}")
            return None
    
    def _find_overlapping_candles(self,
                                 m15_data: pd.DataFrame,
                                 zone: Any) -> List[pd.Series]:
        """
        Find all candles that overlap with a zone
        
        Args:
            m15_data: DataFrame with M15 data
            zone: DiscoveredZone object
            
        Returns:
            List of overlapping candle rows
        """
        overlapping = []
        
        for idx, row in m15_data.iterrows():
            # Check if candle overlaps with zone
            if not (row['high'] < zone.zone_low or row['low'] > zone.zone_high):
                overlapping.append(row)
        
        return overlapping
    
    def _score_candles(self,
                      candles: List[pd.Series],
                      zone: Any,
                      all_m15_data: pd.DataFrame) -> List[ScoredCandle]:
        """
        Score all overlapping candles for a zone
        
        Args:
            candles: List of overlapping candles
            zone: DiscoveredZone object
            all_m15_data: All M15 data for context
            
        Returns:
            List of ScoredCandle objects
        """
        scored_candles = []
        
        # Pre-calculate some statistics for relative scoring
        all_volumes = [c['volume'] for c in candles if c['volume'] > 0]
        max_volume = max(all_volumes) if all_volumes else 1
        avg_volume = np.mean(all_volumes) if all_volumes else 1
        
        # Get earliest and latest times for recency scoring
        if candles:
            earliest_time = min(c.name for c in candles)
            latest_time = max(c.name for c in candles)
            time_range = (latest_time - earliest_time).total_seconds()
            if time_range == 0:
                time_range = 1
        else:
            time_range = 1
        
        for candle in candles:
            # Create scoring object
            scoring = CandleScore(
                datetime=candle.name,
                total_score=0,
                overlap_score=0,
                confluence_score=0,
                volume_score=0,
                structure_score=0,
                recency_score=0
            )
            
            # 1. Calculate overlap score (0-100)
            overlap_pct = self._calculate_overlap_percentage(candle, zone)
            scoring.overlap_score = overlap_pct * 100
            scoring.details['overlap_pct'] = overlap_pct
            
            # 2. Calculate confluence touch score (0-100)
            touches = self._check_confluence_touches(candle, zone.confluent_sources)
            scoring.confluence_score = min(len(touches) * 20, 100)  # 20 points per touch, max 100
            scoring.details['touches'] = touches
            
            # 3. Calculate volume score (0-100)
            if candle['volume'] > 0 and max_volume > 0:
                # Relative volume
                rel_volume = candle['volume'] / max_volume
                # Above average bonus
                above_avg = candle['volume'] / avg_volume if avg_volume > 0 else 1
                scoring.volume_score = (rel_volume * 50) + min(above_avg * 25, 50)
            else:
                scoring.volume_score = 0
            scoring.details['volume'] = candle['volume']
            
            # 4. Calculate structure score (0-100)
            structure_score = self._calculate_structure_score(candle, zone)
            scoring.structure_score = structure_score
            
            # 5. Calculate recency score (0-100)
            if time_range > 0:
                time_from_earliest = (candle.name - earliest_time).total_seconds()
                recency_ratio = time_from_earliest / time_range
                scoring.recency_score = recency_ratio * 100
            else:
                scoring.recency_score = 100
            
            # Calculate weighted total score
            scoring.total_score = (
                scoring.overlap_score * self.weights['overlap'] +
                scoring.confluence_score * self.weights['confluence'] +
                scoring.volume_score * self.weights['volume'] +
                scoring.structure_score * self.weights['structure'] +
                scoring.recency_score * self.weights['recency']
            )
            
            # Create ScoredCandle object
            scored_candle = ScoredCandle(
                datetime=candle.name,
                open=candle['open'],
                high=candle['high'],
                low=candle['low'],
                close=candle['close'],
                volume=int(candle['volume']),
                mid_point=candle['mid'],
                zone_id=zone.zone_id,
                zone_level=zone.confluence_level,
                scoring=scoring,
                overlap_percentage=overlap_pct,
                touches_confluence=touches
            )
            
            scored_candles.append(scored_candle)
        
        return scored_candles
    
    def _calculate_overlap_percentage(self,
                                     candle: pd.Series,
                                     zone: Any) -> float:
        """
        Calculate how much of the candle overlaps with the zone
        
        Args:
            candle: Candle data
            zone: DiscoveredZone object
            
        Returns:
            Overlap percentage (0-1)
        """
        candle_range = candle['high'] - candle['low']
        if candle_range == 0:
            # Single price candle
            if zone.zone_low <= candle['low'] <= zone.zone_high:
                return 1.0
            return 0.0
        
        # Calculate overlap
        overlap_low = max(candle['low'], zone.zone_low)
        overlap_high = min(candle['high'], zone.zone_high)
        
        if overlap_high <= overlap_low:
            return 0.0
        
        overlap_range = overlap_high - overlap_low
        return overlap_range / candle_range
    
    def _check_confluence_touches(self,
                                 candle: pd.Series,
                                 confluent_sources: List[Dict]) -> List[str]:
        """
        Check which confluence sources the candle touches
        
        Args:
            candle: Candle data
            confluent_sources: List of confluence sources for the zone
            
        Returns:
            List of touched confluence source names
        """
        touches = []
        
        for source in confluent_sources:
            # Check if candle touches this confluence
            if 'price' in source:
                # Point confluence (pivot, level)
                if candle['low'] <= source['price'] <= candle['high']:
                    touches.append(f"{source['type']}:{source.get('name', source.get('level', ''))}")
            
            elif 'zone' in source and source.get('overlap'):
                # Zone confluence - already overlapping
                touches.append(f"{source['type']}:{source['name']}")
        
        return touches
    
    def _calculate_structure_score(self,
                                  candle: pd.Series,
                                  zone: Any) -> float:
        """
        Calculate structure score based on price action characteristics
        
        Args:
            candle: Candle data
            zone: DiscoveredZone object
            
        Returns:
            Structure score (0-100)
        """
        score = 0.0
        
        # 1. Rejection wicks (40 points max)
        candle_range = candle['high'] - candle['low']
        if candle_range > 0:
            # Check for rejection from zone boundaries
            if zone.zone_type == 'resistance':
                # Upper wick rejection
                upper_wick_ratio = candle['upper_wick'] / candle_range
                if upper_wick_ratio > 0.5:  # Strong rejection
                    score += 40
                elif upper_wick_ratio > 0.3:  # Moderate rejection
                    score += 25
                elif upper_wick_ratio > 0.1:  # Weak rejection
                    score += 10
                    
            else:  # Support zone
                # Lower wick rejection
                lower_wick_ratio = candle['lower_wick'] / candle_range
                if lower_wick_ratio > 0.5:  # Strong rejection
                    score += 40
                elif lower_wick_ratio > 0.3:  # Moderate rejection
                    score += 25
                elif lower_wick_ratio > 0.1:  # Weak rejection
                    score += 10
        
        # 2. Body position (30 points max)
        body_center = (candle['open'] + candle['close']) / 2
        zone_center = (zone.zone_high + zone.zone_low) / 2
        
        # Distance from body center to zone center
        distance = abs(body_center - zone_center)
        zone_width = zone.zone_high - zone.zone_low
        
        if zone_width > 0:
            proximity_ratio = 1 - (distance / zone_width)
            score += max(0, proximity_ratio * 30)
        
        # 3. Candle type bonus (30 points max)
        body_size = abs(candle['close'] - candle['open'])
        
        if candle_range > 0:
            body_ratio = body_size / candle_range
            
            # Doji or spinning top (high indecision)
            if body_ratio < 0.1:
                score += 30
            # Hammer or shooting star
            elif body_ratio < 0.3:
                if zone.zone_type == 'resistance' and candle['upper_wick'] > body_size * 2:
                    score += 25  # Shooting star at resistance
                elif zone.zone_type == 'support' and candle['lower_wick'] > body_size * 2:
                    score += 25  # Hammer at support
                else:
                    score += 15
            # Regular candle
            else:
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def format_candle_summary(self, candle: ScoredCandle) -> str:
        """
        Format a candle for display
        
        Args:
            candle: ScoredCandle object
            
        Returns:
            Formatted string
        """
        output = []
        output.append(f"Zone {candle.zone_id} ({candle.zone_level})")
        output.append(f"  DateTime: {candle.datetime}")
        output.append(f"  Range: ${candle.low:.2f} - ${candle.high:.2f}")
        output.append(f"  Open: ${candle.open:.2f}, Close: ${candle.close:.2f}")
        output.append(f"  Volume: {candle.volume:,}")
        output.append(f"  Total Score: {candle.scoring.total_score:.1f}/100")
        output.append(f"  Scoring Breakdown:")
        output.append(f"    - Overlap: {candle.scoring.overlap_score:.1f}")
        output.append(f"    - Confluence: {candle.scoring.confluence_score:.1f}")
        output.append(f"    - Volume: {candle.scoring.volume_score:.1f}")
        output.append(f"    - Structure: {candle.scoring.structure_score:.1f}")
        output.append(f"    - Recency: {candle.scoring.recency_score:.1f}")
        
        if candle.touches_confluence:
            output.append(f"  Touches: {', '.join(candle.touches_confluence)}")
        
        return '\n'.join(output)
    
    def export_to_m15_format(self, 
                            best_candles: Dict[int, ScoredCandle],
                            max_zones: int = 6) -> List[Dict]:
        """
        Export selected candles to M15 table format
        Only exports zones with real candles
        
        Args:
            best_candles: Dictionary of best candles by zone
            max_zones: Maximum zones to export
            
        Returns:
            List of dictionaries for M15 table
        """
        if not best_candles:
            logger.warning("No candles to export")
            return []
        
        # Sort by score and take top zones
        sorted_candles = sorted(
            best_candles.values(),
            key=lambda c: c.scoring.total_score,
            reverse=True
        )[:max_zones]
        
        m15_data = []
        for i, candle in enumerate(sorted_candles, 1):
            m15_data.append({
                'zone_number': i,
                'date': candle.datetime.strftime('%Y-%m-%d'),
                'time': candle.datetime.strftime('%H:%M:%S'),
                'level': round((candle.high + candle.low) / 2, 2),
                'high': round(candle.high, 2),
                'low': round(candle.low, 2),
                'original_zone_id': candle.zone_id,
                'confluence_level': candle.zone_level,
                'score': round(candle.scoring.total_score, 1)
            })
        
        return m15_data