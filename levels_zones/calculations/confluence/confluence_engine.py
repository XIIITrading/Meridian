"""
Confluence Engine for Meridian Trading System
Calculates confluence scores for M15 zones based on alignment with other technical levels
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from enum import Enum
import logging

# Import existing data structures
from calculations.volume.hvn_engine import TimeframeResult
from calculations.pivots.camarilla_engine import CamarillaResult

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of confluence input sources"""
    HVN_7DAY = "hvn_7day"
    HVN_14DAY = "hvn_14day" 
    HVN_30DAY = "hvn_30day"
    CAMARILLA_DAILY = "camarilla_daily"
    CAMARILLA_WEEKLY = "camarilla_weekly"
    CAMARILLA_MONTHLY = "camarilla_monthly"
    DAILY_LEVELS = "daily_levels"
    WEEKLY_ZONES = "weekly_zones" 
    DAILY_ZONES = "daily_zones"
    ATR_ZONES = "atr_zones"  
    ATR_LEVELS = "atr_levels"
    REFERENCE_PRICES = "reference_prices"


class ConfluenceLevel(Enum):
    """M15 zone confluence ranking levels"""
    L1 = "L1"  # Minimal confluence (0-1 points)
    L2 = "L2"  # Low confluence (2-3 points)
    L3 = "L3"  # Medium confluence (4-5 points)
    L4 = "L4"  # High confluence (6-7 points)
    L5 = "L5"  # Highest confluence (8+ points)


@dataclass(frozen=True, kw_only=True)
class ConfluenceInput:
    """Represents a single confluence input (price level or zone from any source)"""
    price: Decimal
    source_type: SourceType
    level_name: str  # e.g., "Peak_1", "R3", "Daily_A1", "ATR_High", "Weekly_WL1"
    weight: float = 1.0  # For future weighted scoring enhancement
    # NEW: Add zone boundaries for zone-based inputs
    zone_low: Optional[Decimal] = None
    zone_high: Optional[Decimal] = None
    is_zone: bool = False  # Flag to indicate if this is a zone rather than a level
    
    def __post_init__(self):
        """Validate input data"""
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
        if not self.level_name.strip():
            raise ValueError("Level name cannot be empty")
        # Validate zone data if it's a zone
        if self.is_zone:
            if not self.zone_low or not self.zone_high:
                raise ValueError("Zone inputs must have zone_low and zone_high")
            if self.zone_high <= self.zone_low:
                raise ValueError(f"Zone high ({self.zone_high}) must be > zone low ({self.zone_low})")


@dataclass(kw_only=True)
class M15ZoneScore:
    """Represents confluence scoring for a single M15 zone"""
    zone_number: int
    zone_low: Decimal
    zone_high: Decimal
    confluence_count: int = 0
    confluent_inputs: List[ConfluenceInput] = field(default_factory=list)
    confluence_level: ConfluenceLevel = ConfluenceLevel.L1
    score: float = 0.0  # NEW: Add numerical score for more granular ranking
    
    def __post_init__(self):
        """Validate zone data"""
        if not 1 <= self.zone_number <= 6:
            raise ValueError(f"Zone number must be 1-6, got {self.zone_number}")
        if self.zone_high <= self.zone_low:
            raise ValueError(f"Zone high ({self.zone_high}) must be > zone low ({self.zone_low})")
    
    @property
    def zone_center(self) -> Decimal:
        """Calculate zone center price"""
        return (self.zone_high + self.zone_low) / 2
    
    @property
    def zone_width(self) -> Decimal:
        """Calculate zone width"""
        return self.zone_high - self.zone_low
    
    def contains_price(self, price: Decimal) -> bool:
        """Check if a price falls within this zone"""
        return self.zone_low <= price <= self.zone_high
    
    def overlaps_zone(self, zone_low: Decimal, zone_high: Decimal, 
                     overlap_threshold: float = 0.2) -> bool:
        """
        Check if another zone overlaps with this zone
        
        Args:
            zone_low: Low boundary of the other zone
            zone_high: High boundary of the other zone
            overlap_threshold: Minimum overlap percentage to count as overlap (0.2 = 20%)
        
        Returns:
            True if zones overlap by at least the threshold percentage
        """
        # Calculate overlap
        overlap_low = max(self.zone_low, zone_low)
        overlap_high = min(self.zone_high, zone_high)
        
        if overlap_high <= overlap_low:
            return False  # No overlap
        
        # Calculate overlap percentage relative to this zone's width
        overlap_width = overlap_high - overlap_low
        overlap_pct = float(overlap_width / self.zone_width)
        
        return overlap_pct >= overlap_threshold
    
    def add_confluence(self, confluence_input: ConfluenceInput, 
                      weight_multiplier: float = 1.0) -> None:
        """
        Add a confluence input to this zone
        
        Args:
            confluence_input: The confluence input to add
            weight_multiplier: Additional weight multiplier for this input
        """
        # Check if it's a zone input or level input
        if confluence_input.is_zone:
            # For zone inputs, check overlap
            if self.overlaps_zone(confluence_input.zone_low, confluence_input.zone_high):
                self.confluent_inputs.append(confluence_input)
                self.confluence_count = len(self.confluent_inputs)
                # Zones get higher scores
                self.score += confluence_input.weight * weight_multiplier * 2.0
                self._update_confluence_level()
        else:
            # For level inputs, check if price is within zone
            if self.contains_price(confluence_input.price):
                self.confluent_inputs.append(confluence_input)
                self.confluence_count = len(self.confluent_inputs)
                self.score += confluence_input.weight * weight_multiplier
                self._update_confluence_level()
    
    def _update_confluence_level(self) -> None:
        """Update confluence level based on score"""
        # Using score-based levels for better granularity
        if self.score >= 16:
            self.confluence_level = ConfluenceLevel.L5
        elif self.score >= 12:
            self.confluence_level = ConfluenceLevel.L4
        elif self.score >= 8:
            self.confluence_level = ConfluenceLevel.L3
        elif self.score >= 4:
            self.confluence_level = ConfluenceLevel.L2
        else:
            self.confluence_level = ConfluenceLevel.L1


@dataclass(kw_only=True)
class ConfluenceResult:
    """Complete confluence analysis results"""
    zone_scores: List[M15ZoneScore] = field(default_factory=list)
    total_inputs_checked: int = 0
    zones_with_confluence: int = 0
    highest_confluence_zone: Optional[int] = None
    input_summary: Dict[SourceType, int] = field(default_factory=dict)
    
    def get_ranked_zones(self) -> List[M15ZoneScore]:
        """Get zones ranked by score (highest first)"""
        return sorted(
            self.zone_scores,
            key=lambda z: (z.score, float(z.zone_center)),
            reverse=True
        )
    
    def get_zones_by_level(self, level: ConfluenceLevel) -> List[M15ZoneScore]:
        """Get all zones at a specific confluence level"""
        return [zone for zone in self.zone_scores if zone.confluence_level == level]


class ConfluenceEngine:
    """
    Calculates confluence scores for M15 zones based on alignment with other technical levels.
    
    This engine takes M15 zone data and checks how many other technical analysis levels
    (HVN peaks, Camarilla pivots, daily levels, weekly zones, ATR levels) fall within 
    each zone's price range. Zone overlaps are weighted higher than single level confluences.
    """
    
    def __init__(self):
        """Initialize confluence engine"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Define scoring weights for different sources

        self.source_weights = {
            # Major structural levels (8.0-10.0) - Game changers
            SourceType.CAMARILLA_MONTHLY: 10.0,  # Monthly pivots - major institutions watch these
            SourceType.HVN_30DAY: 8.0,           # Month of volume accumulation
            
            # Important swing levels (4.0-5.0) - Multi-day significance  
            SourceType.WEEKLY_ZONES: 5.0,        # Weekly structure 
            SourceType.CAMARILLA_WEEKLY: 4.5,    # Weekly pivots
            SourceType.HVN_14DAY: 4.0,           # Two weeks of volume
            
            # Intraday context (1.5-2.5) - Day trading levels
            SourceType.DAILY_ZONES: 2.5,         # Today's structure
            SourceType.ATR_ZONES: 2.0,           # Dynamic volatility zones
            SourceType.HVN_7DAY: 1.5,            # Recent week's volume
            
            # Minor levels (0.5-1.0) - Supporting information
            SourceType.DAILY_LEVELS: 1.0,        # Basic support/resistance
            SourceType.ATR_LEVELS: 1.0,          # ATR targets
            SourceType.CAMARILLA_DAILY: 0.5,     # Too granular for primary use
            SourceType.REFERENCE_PRICES: 0.25    # Just reference points
        }
        
    def calculate_confluence(
        self,
        m15_zones: List[Dict[str, Any]],
        hvn_results: Optional[Dict[int, TimeframeResult]] = None,
        camarilla_results: Optional[Dict[str, CamarillaResult]] = None,
        daily_levels: Optional[List[float]] = None,
        weekly_zones: Optional[List[Dict[str, Any]]] = None,
        daily_zones: Optional[List[Dict[str, Any]]] = None,
        atr_zones: Optional[List[Dict[str, Any]]] = None,    # NEW: Add ATR zones parameter
        metrics: Optional[Dict[str, float]] = None
    ) -> ConfluenceResult:
        """
        Calculate confluence for M15 zones against all available technical levels.
        
        Args:
            m15_zones: List of M15 zone dictionaries with 'zone_number', 'high', 'low'
            hvn_results: Dictionary mapping timeframe days to HVN results
            camarilla_results: Dictionary mapping timeframes to Camarilla results  
            daily_levels: List of 6 daily price levels (3 above, 3 below)
            weekly_zones: List of weekly zone dictionaries with 'name', 'high', 'low', etc.
            daily_zones: List of daily zone dictionaries with 'name', 'high', 'low', etc.
            atr_zones: List of ATR zone dictionaries with 'name', 'high', 'low', etc.
            metrics: Dictionary with ATR and price metrics
            
        Returns:
            ConfluenceResult with scored and ranked zones
        """
        self.logger.info("Starting confluence calculation")
        
        # Step 1: Validate and prepare M15 zones
        zone_scores = self._prepare_m15_zones(m15_zones)
        if not zone_scores:
            self.logger.warning("No valid M15 zones provided")
            return ConfluenceResult()
        
        # Step 2: Collect all confluence inputs
        all_inputs = self._collect_all_inputs(
            hvn_results=hvn_results,
            camarilla_results=camarilla_results,
            daily_levels=daily_levels,
            weekly_zones=weekly_zones,
            daily_zones=daily_zones,
            atr_zones=atr_zones,           # NEW: Pass ATR zones
            metrics=metrics
        )
        
        self.logger.info(f"Collected {len(all_inputs)} confluence inputs from {len(set(inp.source_type for inp in all_inputs))} sources")
        
        # Step 3: Check each input against each zone with weighted scoring
        for confluence_input in all_inputs:
            weight = self.source_weights.get(confluence_input.source_type, 1.0)
            for zone_score in zone_scores:
                zone_score.add_confluence(confluence_input, weight_multiplier=weight)
        
        # Step 4: Create summary statistics
        result = ConfluenceResult(
            zone_scores=zone_scores,
            total_inputs_checked=len(all_inputs),
            zones_with_confluence=sum(1 for z in zone_scores if z.confluence_count > 0),
            input_summary=self._create_input_summary(all_inputs)
        )
        
        # Find highest confluence zone
        if result.zone_scores:
            highest_zone = max(result.zone_scores, key=lambda z: z.score)
            result.highest_confluence_zone = highest_zone.zone_number
        
        self.logger.info(f"Confluence calculation complete: {result.zones_with_confluence}/{len(zone_scores)} zones have confluence")
        
        return result
    
    def _prepare_m15_zones(self, m15_zones: List[Dict[str, Any]]) -> List[M15ZoneScore]:
        """Convert M15 zone data to M15ZoneScore objects"""
        zone_scores = []
        
        for zone_data in m15_zones:
            try:
                # Extract zone number
                zone_number = zone_data.get('zone_number', 0)
                if not 1 <= zone_number <= 6:
                    continue
                
                # Extract and validate prices
                high_str = zone_data.get('high', '0')
                low_str = zone_data.get('low', '0')
                
                if not high_str or not low_str or high_str == '0' or low_str == '0':
                    self.logger.debug(f"Skipping zone {zone_number}: missing high/low prices")
                    continue
                
                zone_high = Decimal(str(high_str))
                zone_low = Decimal(str(low_str))
                
                if zone_high <= zone_low:
                    self.logger.warning(f"Skipping zone {zone_number}: invalid price range ({zone_low} to {zone_high})")
                    continue
                
                zone_score = M15ZoneScore(
                    zone_number=zone_number,
                    zone_low=zone_low,
                    zone_high=zone_high
                )
                zone_scores.append(zone_score)
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Error processing zone {zone_data}: {e}")
                continue
        
        return zone_scores
    
    def _collect_all_inputs(
        self,
        hvn_results: Optional[Dict[int, TimeframeResult]] = None,
        camarilla_results: Optional[Dict[str, CamarillaResult]] = None,
        daily_levels: Optional[List[float]] = None,
        weekly_zones: Optional[List[Dict[str, Any]]] = None,
        daily_zones: Optional[List[Dict[str, Any]]] = None,
        atr_zones: Optional[List[Dict[str, Any]]] = None,    # NEW: Add ATR zones parameter
        metrics: Optional[Dict[str, float]] = None
    ) -> List[ConfluenceInput]:
        """Collect all confluence inputs from various sources"""
        all_inputs = []
        
        # Collect HVN inputs
        if hvn_results:
            all_inputs.extend(self._collect_hvn_inputs(hvn_results))
        
        # Collect Camarilla inputs  
        if camarilla_results:
            all_inputs.extend(self._collect_camarilla_inputs(camarilla_results))
        
        # Collect daily level inputs
        if daily_levels:
            all_inputs.extend(self._collect_daily_level_inputs(daily_levels))

        # Collect weekly zone inputs
        if weekly_zones:
            all_inputs.extend(self._collect_weekly_zone_inputs(weekly_zones))

        # Collect daily zone inputs
        if daily_zones:
            all_inputs.extend(self._collect_daily_zone_inputs(daily_zones))

        # NEW: Collect ATR zone inputs
        if atr_zones:
            all_inputs.extend(self._collect_atr_zone_inputs(atr_zones))

        # Collect ATR and reference price inputs
        if metrics:
            all_inputs.extend(self._collect_metrics_inputs(metrics))
        
        return all_inputs
    
    def _collect_weekly_zone_inputs(self, weekly_zones: List[Dict[str, Any]]) -> List[ConfluenceInput]:
        """
        Collect weekly zones as confluence inputs
        These are zones, not single levels, so they have high/low boundaries
        """
        inputs = []
        
        for zone in weekly_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    # Create a zone-based confluence input
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        source_type=SourceType.WEEKLY_ZONES,
                        level_name=zone_name,
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.5  # Weekly zones get higher base weight
                    ))
                    self.logger.debug(f"Added weekly zone {zone_name}: {zone_low:.2f}-{zone_high:.2f}")
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid weekly zone: {e}")
                continue
        
        self.logger.info(f"Collected {len(inputs)} weekly zones for confluence")
        return inputs
    
    def _collect_daily_zone_inputs(self, daily_zones: List[Dict[str, Any]]) -> List[ConfluenceInput]:
        """
        Collect daily zones as confluence inputs
        These are zones with high/low boundaries based on 15-min ATR
        """
        inputs = []
        
        for zone in daily_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    # Create a zone-based confluence input
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        source_type=SourceType.DAILY_ZONES,
                        level_name=zone_name,
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.2  # Daily zones get moderate base weight (lower than weekly)
                    ))
                    self.logger.debug(f"Added daily zone {zone_name}: {zone_low:.2f}-{zone_high:.2f}")
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid daily zone: {e}")
                continue
        
        self.logger.info(f"Collected {len(inputs)} daily zones for confluence")
        return inputs
    
    def _collect_atr_zone_inputs(self, atr_zones: List[Dict[str, Any]]) -> List[ConfluenceInput]:
        """
        NEW: Collect ATR zones as confluence inputs
        These are dynamic volatility-based zones with high/low boundaries
        """
        inputs = []
        
        for zone in atr_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    # Create a zone-based confluence input
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        source_type=SourceType.ATR_ZONES,
                        level_name=zone_name,
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.0  # ATR zones get moderate base weight
                    ))
                    self.logger.debug(f"Added ATR zone {zone_name}: {zone_low:.2f}-{zone_high:.2f}")
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid ATR zone: {e}")
                continue
        
        self.logger.info(f"Collected {len(inputs)} ATR zones for confluence")
        return inputs
    
    def _collect_hvn_inputs(self, hvn_results: Dict[int, TimeframeResult]) -> List[ConfluenceInput]:
        """Collect HVN peak prices as confluence inputs"""
        inputs = []
        
        # Map timeframe days to source types
        timeframe_map = {
            7: SourceType.HVN_7DAY,
            14: SourceType.HVN_14DAY,
            30: SourceType.HVN_30DAY
        }
        
        for days, result in hvn_results.items():
            if not result or not result.peaks:
                continue
                
            source_type = timeframe_map.get(days)
            if not source_type:
                continue
            
            # Take top 10 peaks from each timeframe
            for i, peak in enumerate(result.peaks[:10]):
                try:
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(peak.price)),
                        source_type=source_type,
                        level_name=f"Peak_{i+1}"
                    ))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid HVN peak: {e}")
                    continue
        
        return inputs
    
    def _collect_camarilla_inputs(self, camarilla_results: Dict[str, CamarillaResult]) -> List[ConfluenceInput]:
        """Collect Camarilla pivot levels as confluence inputs"""
        inputs = []
        
        # Map timeframes to source types
        timeframe_map = {
            'daily': SourceType.CAMARILLA_DAILY,
            'weekly': SourceType.CAMARILLA_WEEKLY,
            'monthly': SourceType.CAMARILLA_MONTHLY
        }
        
        for timeframe, result in camarilla_results.items():
            if not result or not result.pivots:
                continue
                
            source_type = timeframe_map.get(timeframe)
            if not source_type:
                continue
            
            # Collect key pivot levels (R6, R4, R3, S3, S4, S6)
            key_levels = {'R6', 'R4', 'R3', 'S3', 'S4', 'S6'}
            
            for pivot in result.pivots:
                if pivot.level_name in key_levels:
                    try:
                        inputs.append(ConfluenceInput(
                            price=Decimal(str(pivot.price)),
                            source_type=source_type,
                            level_name=pivot.level_name
                        ))
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Skipping invalid Camarilla level: {e}")
                        continue
        
        return inputs
    
    def _collect_daily_level_inputs(self, daily_levels: List[float]) -> List[ConfluenceInput]:
        """Collect daily analysis price levels as confluence inputs"""
        inputs = []
        
        for i, level in enumerate(daily_levels):
            if level and level > 0:
                try:
                    # Label as A1-A3 (above) or B1-B3 (below)
                    if i < 3:
                        level_name = f"A{i+1}"
                    else:
                        level_name = f"B{i-2}"
                    
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(level)),
                        source_type=SourceType.DAILY_LEVELS,
                        level_name=level_name
                    ))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid daily level: {e}")
                    continue
        
        return inputs
    
    def _collect_metrics_inputs(self, metrics: Dict[str, float]) -> List[ConfluenceInput]:
        """Collect ATR and reference price inputs"""
        inputs = []
        
        # ATR levels
        atr_levels = [
            ('atr_high', 'ATR_High'),
            ('atr_low', 'ATR_Low')
        ]
        
        for metric_key, level_name in atr_levels:
            value = metrics.get(metric_key)
            if value and value > 0:
                try:
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(value)),
                        source_type=SourceType.ATR_LEVELS,
                        level_name=level_name
                    ))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid ATR level: {e}")
                    continue
        
        # Reference prices
        reference_prices = [
            ('current_price', 'Current_Price'),
            ('open_price', 'Open_Price'),
            ('pre_market_price', 'PreMarket_Price')
        ]
        
        for metric_key, level_name in reference_prices:
            value = metrics.get(metric_key)
            if value and value > 0:
                try:
                    inputs.append(ConfluenceInput(
                        price=Decimal(str(value)),
                        source_type=SourceType.REFERENCE_PRICES,
                        level_name=level_name
                    ))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid reference price: {e}")
                    continue
        
        return inputs
    
    def _create_input_summary(self, all_inputs: List[ConfluenceInput]) -> Dict[SourceType, int]:
        """Create summary of inputs by source type"""
        summary = {}
        for input_item in all_inputs:
            summary[input_item.source_type] = summary.get(input_item.source_type, 0) + 1
        return summary
    
    def format_confluence_result(self, result: ConfluenceResult, current_price: Optional[float] = None) -> str:
        """Format confluence results for display"""
        if not result.zone_scores:
            return "No M15 zones available for confluence analysis"
        
        output = []
        output.append("M15 ZONES CONFLUENCE RANKING")
        output.append("=" * 50)
        
        if current_price:
            output.append(f"Current Price: ${current_price:.2f}")
        
        output.append(f"Total Inputs Checked: {result.total_inputs_checked}")
        output.append(f"Zones with Confluence: {result.zones_with_confluence}/{len(result.zone_scores)}")
        
        # Input summary
        if result.input_summary:
            output.append(f"\nInput Sources:")
            for source_type, count in result.input_summary.items():
                source_name = source_type.value.replace('_', ' ').title()
                # Handle zone vs level terminology - UPDATED to include ATR_ZONES
                if source_type in [SourceType.WEEKLY_ZONES, SourceType.DAILY_ZONES, SourceType.ATR_ZONES]:
                    output.append(f"  • {source_name}: {count} zones")
                else:
                    output.append(f"  • {source_name}: {count} levels")
        
        output.append(f"\nRanked Zones (by Score):")
        output.append("-" * 60)
        
        # Show ranked zones
        ranked_zones = result.get_ranked_zones()
        for zone in ranked_zones:
            # Show score-based stars
            if zone.score >= 16:
                stars = "⭐⭐⭐⭐⭐"
            elif zone.score >= 12:
                stars = "⭐⭐⭐⭐"
            elif zone.score >= 8:
                stars = "⭐⭐⭐"
            elif zone.score >= 4:
                stars = "⭐⭐"
            elif zone.score > 0:
                stars = "⭐"
            else:
                stars = ""
            
            direction = ""
            if current_price:
                if zone.zone_center > current_price:
                    direction = " ↑ Above"
                elif zone.zone_center < current_price:
                    direction = " ↓ Below"
                else:
                    direction = " ← At Price"
            
            output.append(f"\nZone {zone.zone_number} ({zone.confluence_level.value}): "
                         f"${zone.zone_low:.2f}-${zone.zone_high:.2f} - "
                         f"Score: {zone.score:.1f} {stars}{direction}")
            
            # Show confluent inputs, highlighting zones
            if zone.confluent_inputs:
                # Group by source type for cleaner display
                by_source = {}
                for inp in zone.confluent_inputs:
                    if inp.source_type not in by_source:
                        by_source[inp.source_type] = []
                    by_source[inp.source_type].append(inp)
                
                for source_type, inputs in by_source.items():
                    source_name = source_type.value.replace('_', ' ').title()
                    
                    # Special formatting for zone types to show overlap
                    if source_type in [SourceType.WEEKLY_ZONES, SourceType.DAILY_ZONES, SourceType.ATR_ZONES]:
                        zone_details = []
                        for inp in inputs:
                            if inp.is_zone:
                                zone_details.append(f"{inp.level_name} (${inp.zone_low:.2f}-${inp.zone_high:.2f})")
                            else:
                                zone_details.append(inp.level_name)
                        output.append(f"  • {source_name}: {', '.join(zone_details)} 🔄")  # 🔄 indicates zone overlap
                    else:
                        input_names = [inp.level_name for inp in inputs]
                        output.append(f"  • {source_name}: {', '.join(input_names)}")
        
        # Add legend
        output.append("\n" + "-" * 60)
        output.append("Legend: L1=Minimal, L2=Low, L3=Medium, L4=High, L5=Highest")
        output.append("🔄 = Zone Overlap (higher weight)")
        
        return "\n".join(output)


# Example usage and testing
if __name__ == "__main__":
    # This would normally be called from analysis_thread.py
    print("Confluence Engine - Test Mode")
    
    # Mock data for testing
    mock_zones = [
        {'zone_number': 1, 'high': '250.50', 'low': '248.75'},
        {'zone_number': 2, 'high': '245.25', 'low': '243.80'},
        {'zone_number': 3, 'high': '255.10', 'low': '253.40'},
    ]
    
    # Mock weekly zones
    mock_weekly_zones = [
        {'name': 'Weekly_WL1', 'high': 251.00, 'low': 248.00, 'level': 249.50},
        {'name': 'Weekly_WL2', 'high': 246.00, 'low': 243.00, 'level': 244.50},
    ]
    
    # Mock ATR zones
    mock_atr_zones = [
        {'name': 'ATR_High_Zone', 'high': 252.18, 'low': 251.82, 'level': 252.00},
        {'name': 'ATR_Low_Zone', 'high': 243.18, 'low': 242.82, 'level': 243.00},
    ]
    
    mock_metrics = {
        'current_price': 247.50,
        'atr_high': 250.25,
        'atr_low': 244.75,
        'open_price': 246.80
    }
    
    # Test the engine
    engine = ConfluenceEngine()
    result = engine.calculate_confluence(
        m15_zones=mock_zones,
        weekly_zones=mock_weekly_zones,
        atr_zones=mock_atr_zones,  # Include ATR zones
        metrics=mock_metrics
    )
    
    print(engine.format_confluence_result(result, 247.50))