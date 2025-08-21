"""
Pivot Confluence Engine for Meridian Trading System
Calculates confluence scores for Daily Camarilla pivot zones
Replaces the M15-based confluence system
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


class ConfluenceSource(Enum):
    """Types of confluence sources for pivot zones"""
    HVN_7DAY = "hvn_7day"
    HVN_14DAY = "hvn_14day" 
    HVN_30DAY = "hvn_30day"
    MONTHLY_PIVOTS = "monthly_pivots"
    WEEKLY_PIVOTS = "weekly_pivots"
    WEEKLY_ZONES = "weekly_zones"
    DAILY_ZONES = "daily_zones"
    ATR_ZONES = "atr_zones"


class PivotLevel(Enum):
    """Camarilla pivot level designations"""
    L1 = 1  # Lowest confluence
    L2 = 2  # Low confluence
    L3 = 3  # Medium confluence
    L4 = 4  # High confluence
    L5 = 5  # Highest confluence


@dataclass(frozen=True)
class ConfluenceCheck:
    """Represents a confluence source that aligns with a pivot zone"""
    source: ConfluenceSource
    source_name: str  # e.g., "Peak_1", "WR4", "Weekly_Zone_1"
    price: Decimal
    weight: float = 1.0
    is_zone: bool = False
    zone_low: Optional[Decimal] = None
    zone_high: Optional[Decimal] = None


@dataclass
class PivotZone:
    """Represents a Daily Camarilla pivot level with its confluence zone"""
    level_name: str  # "R6", "R4", "R3", "S3", "S4", "S6"
    pivot_price: Decimal
    zone_low: Decimal  # pivot_price - 5min_atr
    zone_high: Decimal  # pivot_price + 5min_atr
    zone_width: Decimal
    
    # Confluence tracking
    confluence_sources: List[ConfluenceCheck] = field(default_factory=list)
    confluence_count: int = 0
    confluence_score: float = 0.0
    level_designation: PivotLevel = PivotLevel.L1
    
    # Configuration flags (for UI checkboxes)
    check_hvn_7day: bool = True
    check_hvn_14day: bool = True
    check_hvn_30day: bool = True
    check_monthly_pivots: bool = True
    check_weekly_pivots: bool = True
    check_weekly_zones: bool = True
    check_daily_zones: bool = True
    check_atr_zones: bool = True
    
    def __post_init__(self):
        """Validate zone data"""
        if self.zone_high <= self.zone_low:
            raise ValueError(f"Zone high must be > zone low for {self.level_name}")
        if self.zone_width != (self.zone_high - self.zone_low):
            object.__setattr__(self, 'zone_width', self.zone_high - self.zone_low)
    
    @property
    def zone_center(self) -> Decimal:
        """Get zone center price"""
        return (self.zone_high + self.zone_low) / 2
    
    @property
    def is_resistance(self) -> bool:
        """Check if this is a resistance level"""
        return self.level_name in ['R6', 'R4', 'R3']
    
    @property
    def is_support(self) -> bool:
        """Check if this is a support level"""
        return self.level_name in ['S3', 'S4', 'S6']
    
    def contains_price(self, price: Decimal) -> bool:
        """Check if a price falls within this zone"""
        return self.zone_low <= price <= self.zone_high
    
    def overlaps_zone(self, zone_low: Decimal, zone_high: Decimal, 
                     overlap_threshold: float = 0.2) -> bool:
        """Check if another zone overlaps with this zone"""
        overlap_low = max(self.zone_low, zone_low)
        overlap_high = min(self.zone_high, zone_high)
        
        if overlap_high <= overlap_low:
            return False
        
        overlap_width = overlap_high - overlap_low
        overlap_pct = float(overlap_width / self.zone_width)
        
        return overlap_pct >= overlap_threshold
    
    def add_confluence(self, confluence_check: ConfluenceCheck, 
                      source_weight: float = 1.0) -> None:
        """Add a confluence source to this zone"""
        if confluence_check.is_zone:
            # Zone overlap
            if self.overlaps_zone(confluence_check.zone_low, confluence_check.zone_high):
                self.confluence_sources.append(confluence_check)
                self.confluence_score += confluence_check.weight * source_weight * 1.5  # Zone bonus
        else:
            # Point level
            if self.contains_price(confluence_check.price):
                self.confluence_sources.append(confluence_check)
                self.confluence_score += confluence_check.weight * source_weight
        
        self.confluence_count = len(self.confluence_sources)
        self._update_level_designation()
    
    def _update_level_designation(self) -> None:
        """Update level designation based on score"""
        if self.confluence_score >= 12:
            self.level_designation = PivotLevel.L5
        elif self.confluence_score >= 8:
            self.level_designation = PivotLevel.L4
        elif self.confluence_score >= 5:
            self.level_designation = PivotLevel.L3
        elif self.confluence_score >= 2:
            self.level_designation = PivotLevel.L2
        else:
            self.level_designation = PivotLevel.L1


@dataclass
class PivotConfluenceResult:
    """Complete Camarilla pivot confluence analysis results"""
    pivot_zones: List[PivotZone] = field(default_factory=list)
    current_price: Optional[Decimal] = None
    atr_5min: Optional[Decimal] = None
    total_confluence_sources: int = 0
    zones_with_confluence: int = 0
    highest_confluence_zone: Optional[str] = None  # level_name
    source_summary: Dict[ConfluenceSource, int] = field(default_factory=dict)
    
    def get_ranked_zones(self) -> List[PivotZone]:
        """Get zones ranked by confluence score (highest first)"""
        return sorted(
            self.pivot_zones,
            key=lambda z: (z.confluence_score, float(z.pivot_price)),
            reverse=True
        )
    
    def get_zones_by_level(self, level: PivotLevel) -> List[PivotZone]:
        """Get all zones at a specific level designation"""
        return [zone for zone in self.pivot_zones if zone.level_designation == level]
    
    def get_resistance_zones(self) -> List[PivotZone]:
        """Get resistance zones (R6, R4, R3)"""
        return [z for z in self.pivot_zones if z.level_name in ['R6', 'R4', 'R3']]
    
    def get_support_zones(self) -> List[PivotZone]:
        """Get support zones (S3, S4, S6)"""
        return [z for z in self.pivot_zones if z.level_name in ['S3', 'S4', 'S6']]


@dataclass
class ConfluenceWeights:
    """Configurable weights for different confluence sources"""
    # Starting with equal weights as requested, but maintaining priority order structure
    hvn_30day: float = 1.0      # Can be configured to higher values later
    monthly_pivots: float = 1.0
    hvn_14day: float = 1.0
    weekly_zones: float = 1.0
    weekly_pivots: float = 1.0
    hvn_7day: float = 1.0
    daily_zones: float = 1.0
    atr_zones: float = 1.0
    
    def get_weight(self, source: ConfluenceSource) -> float:
        """Get weight for a confluence source"""
        weight_map = {
            ConfluenceSource.HVN_30DAY: self.hvn_30day,
            ConfluenceSource.MONTHLY_PIVOTS: self.monthly_pivots,
            ConfluenceSource.HVN_14DAY: self.hvn_14day,
            ConfluenceSource.WEEKLY_ZONES: self.weekly_zones,
            ConfluenceSource.WEEKLY_PIVOTS: self.weekly_pivots,
            ConfluenceSource.HVN_7DAY: self.hvn_7day,
            ConfluenceSource.DAILY_ZONES: self.daily_zones,
            ConfluenceSource.ATR_ZONES: self.atr_zones,
        }
        return weight_map.get(source, 1.0)


class PivotConfluenceEngine:
    """
    Calculates confluence scores for Daily Camarilla pivot zones.
    
    This engine takes Daily Camarilla pivots (R6, R4, R3, S3, S4, S6) and creates
    zones around each pivot using 5min ATR. It then checks how many other technical
    analysis levels fall within each zone's price range.
    """
    
    def __init__(self, weights: Optional[ConfluenceWeights] = None):
        """Initialize pivot confluence engine"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.weights = weights or ConfluenceWeights()
        
    def calculate_confluence(
        self,
        daily_camarilla: CamarillaResult,
        atr_5min: float,
        current_price: Optional[float] = None,
        hvn_results: Optional[Dict[int, TimeframeResult]] = None,
        camarilla_results: Optional[Dict[str, CamarillaResult]] = None,
        weekly_zones: Optional[List[Dict[str, Any]]] = None,
        daily_zones: Optional[List[Dict[str, Any]]] = None,
        atr_zones: Optional[List[Dict[str, Any]]] = None
    ) -> PivotConfluenceResult:
        """
        Calculate confluence for Daily Camarilla pivot zones.
        
        Args:
            daily_camarilla: Daily Camarilla pivot results
            atr_5min: 5-minute ATR value for zone creation
            current_price: Current market price
            hvn_results: Dictionary mapping timeframe days to HVN results
            camarilla_results: Dictionary mapping timeframes to Camarilla results (weekly/monthly)
            weekly_zones: List of weekly zone dictionaries
            daily_zones: List of daily zone dictionaries  
            atr_zones: List of ATR zone dictionaries
            
        Returns:
            PivotConfluenceResult with scored and ranked zones
        """
        self.logger.info("Starting pivot confluence calculation")
        
        # Step 1: Create pivot zones from Daily Camarilla results
        pivot_zones = self._create_pivot_zones(daily_camarilla, atr_5min)
        if not pivot_zones:
            self.logger.warning("No valid Daily Camarilla pivots found")
            return PivotConfluenceResult()
        
        # Step 2: Collect all confluence sources
        all_confluence_sources = self._collect_all_confluence_sources(
            hvn_results=hvn_results,
            camarilla_results=camarilla_results,
            weekly_zones=weekly_zones,
            daily_zones=daily_zones,
            atr_zones=atr_zones
        )
        
        self.logger.info(f"Collected {len(all_confluence_sources)} confluence sources")
        
        # Step 3: Check each confluence source against each pivot zone
        for confluence_source in all_confluence_sources:
            source_weight = self.weights.get_weight(confluence_source.source)
            
            for pivot_zone in pivot_zones:
                # Check if this source type is enabled for this zone
                if self._is_source_enabled(pivot_zone, confluence_source.source):
                    pivot_zone.add_confluence(confluence_source, source_weight)
        
        # Step 4: Create result summary
        result = PivotConfluenceResult(
            pivot_zones=pivot_zones,
            current_price=Decimal(str(current_price)) if current_price else None,
            atr_5min=Decimal(str(atr_5min)),
            total_confluence_sources=len(all_confluence_sources),
            zones_with_confluence=sum(1 for z in pivot_zones if z.confluence_count > 0),
            source_summary=self._create_source_summary(all_confluence_sources)
        )
        
        # Find highest confluence zone
        if result.pivot_zones:
            highest_zone = max(result.pivot_zones, key=lambda z: z.confluence_score)
            result.highest_confluence_zone = highest_zone.level_name
        
        self.logger.info(f"Pivot confluence calculation complete: {result.zones_with_confluence}/{len(pivot_zones)} zones have confluence")
        
        return result
    
    def _create_pivot_zones(self, daily_camarilla: CamarillaResult, atr_5min: float) -> List[PivotZone]:
        """Create pivot zones from Daily Camarilla results"""
        pivot_zones = []
        atr_decimal = Decimal(str(atr_5min))
        
        # Focus on key levels only: R6, R4, R3, S3, S4, S6
        key_levels = {'R6', 'R4', 'R3', 'S3', 'S4', 'S6'}
        
        for pivot in daily_camarilla.pivots:
            if pivot.level_name in key_levels:
                try:
                    pivot_price = Decimal(str(pivot.price))
                    zone_low = pivot_price - atr_decimal
                    zone_high = pivot_price + atr_decimal
                    zone_width = zone_high - zone_low
                    
                    pivot_zone = PivotZone(
                        level_name=pivot.level_name,
                        pivot_price=pivot_price,
                        zone_low=zone_low,
                        zone_high=zone_high,
                        zone_width=zone_width
                    )
                    pivot_zones.append(pivot_zone)
                    
                    self.logger.debug(f"Created zone {pivot.level_name}: ${zone_low:.2f}-${zone_high:.2f}")
                    
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error creating zone for {pivot.level_name}: {e}")
                    continue
        
        return pivot_zones
    
    def _collect_all_confluence_sources(
        self,
        hvn_results: Optional[Dict[int, TimeframeResult]] = None,
        camarilla_results: Optional[Dict[str, CamarillaResult]] = None,
        weekly_zones: Optional[List[Dict[str, Any]]] = None,
        daily_zones: Optional[List[Dict[str, Any]]] = None,
        atr_zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[ConfluenceCheck]:
        """Collect all confluence sources"""
        all_sources = []
        
        if hvn_results:
            all_sources.extend(self._collect_hvn_sources(hvn_results))
        
        if camarilla_results:
            all_sources.extend(self._collect_camarilla_sources(camarilla_results))
        
        if weekly_zones:
            all_sources.extend(self._collect_weekly_zone_sources(weekly_zones))
        
        if daily_zones:
            all_sources.extend(self._collect_daily_zone_sources(daily_zones))
        
        if atr_zones:
            all_sources.extend(self._collect_atr_zone_sources(atr_zones))
        
        return all_sources
    
    def _collect_hvn_sources(self, hvn_results: Dict[int, TimeframeResult]) -> List[ConfluenceCheck]:
        """Collect HVN peak prices as confluence sources"""
        sources = []
        
        timeframe_map = {
            7: ConfluenceSource.HVN_7DAY,
            14: ConfluenceSource.HVN_14DAY,
            30: ConfluenceSource.HVN_30DAY
        }
        
        for days, result in hvn_results.items():
            if not result or not result.peaks:
                continue
                
            source_type = timeframe_map.get(days)
            if not source_type:
                continue
            
            for i, peak in enumerate(result.peaks[:10]):  # Top 10 peaks
                try:
                    sources.append(ConfluenceCheck(
                        source=source_type,
                        source_name=f"Peak_{i+1}",
                        price=Decimal(str(peak.price)),
                        weight=1.0
                    ))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid HVN peak: {e}")
                    continue
        
        return sources
    
    def _collect_camarilla_sources(self, camarilla_results: Dict[str, CamarillaResult]) -> List[ConfluenceCheck]:
        """Collect Weekly and Monthly Camarilla pivots as confluence sources"""
        sources = []
        
        timeframe_map = {
            'weekly': ConfluenceSource.WEEKLY_PIVOTS,
            'monthly': ConfluenceSource.MONTHLY_PIVOTS
        }
        
        for timeframe, result in camarilla_results.items():
            if not result or not result.pivots or timeframe == 'daily':
                continue  # Skip daily as that's our base
                
            source_type = timeframe_map.get(timeframe)
            if not source_type:
                continue
            
            # Use key levels from weekly/monthly
            key_levels = {'R6', 'R4', 'R3', 'S3', 'S4', 'S6'}
            
            for pivot in result.pivots:
                if pivot.level_name in key_levels:
                    try:
                        sources.append(ConfluenceCheck(
                            source=source_type,
                            source_name=pivot.level_name,
                            price=Decimal(str(pivot.price)),
                            weight=1.0
                        ))
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Skipping invalid Camarilla level: {e}")
                        continue
        
        return sources
    
    def _collect_weekly_zone_sources(self, weekly_zones: List[Dict[str, Any]]) -> List[ConfluenceCheck]:
        """Collect weekly zones as confluence sources"""
        sources = []
        
        for zone in weekly_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    sources.append(ConfluenceCheck(
                        source=ConfluenceSource.WEEKLY_ZONES,
                        source_name=zone_name,
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.0
                    ))
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid weekly zone: {e}")
                continue
        
        return sources
    
    def _collect_daily_zone_sources(self, daily_zones: List[Dict[str, Any]]) -> List[ConfluenceCheck]:
        """Collect daily zones as confluence sources"""
        sources = []
        
        for zone in daily_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    sources.append(ConfluenceCheck(
                        source=ConfluenceSource.DAILY_ZONES,
                        source_name=zone_name,
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.0
                    ))
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid daily zone: {e}")
                continue
        
        return sources
    
    def _collect_atr_zone_sources(self, atr_zones: List[Dict[str, Any]]) -> List[ConfluenceCheck]:
        """Collect ATR zones as confluence sources"""
        sources = []
        
        for zone in atr_zones:
            try:
                zone_name = zone.get('name', 'Unknown')
                zone_low = zone.get('low', 0)
                zone_high = zone.get('high', 0)
                zone_center = zone.get('level', zone.get('center', 0))
                
                if zone_low and zone_high and zone_low > 0 and zone_high > 0:
                    sources.append(ConfluenceCheck(
                        source=ConfluenceSource.ATR_ZONES,
                        source_name=zone_name,
                        price=Decimal(str(zone_center if zone_center else (zone_low + zone_high) / 2)),
                        zone_low=Decimal(str(zone_low)),
                        zone_high=Decimal(str(zone_high)),
                        is_zone=True,
                        weight=1.0
                    ))
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Skipping invalid ATR zone: {e}")
                continue
        
        return sources
    
    def _is_source_enabled(self, pivot_zone: PivotZone, source: ConfluenceSource) -> bool:
        """Check if a confluence source is enabled for a pivot zone"""
        source_flag_map = {
            ConfluenceSource.HVN_7DAY: pivot_zone.check_hvn_7day,
            ConfluenceSource.HVN_14DAY: pivot_zone.check_hvn_14day,
            ConfluenceSource.HVN_30DAY: pivot_zone.check_hvn_30day,
            ConfluenceSource.MONTHLY_PIVOTS: pivot_zone.check_monthly_pivots,
            ConfluenceSource.WEEKLY_PIVOTS: pivot_zone.check_weekly_pivots,
            ConfluenceSource.WEEKLY_ZONES: pivot_zone.check_weekly_zones,
            ConfluenceSource.DAILY_ZONES: pivot_zone.check_daily_zones,
            ConfluenceSource.ATR_ZONES: pivot_zone.check_atr_zones,
        }
        return source_flag_map.get(source, True)
    
    def _create_source_summary(self, all_sources: List[ConfluenceCheck]) -> Dict[ConfluenceSource, int]:
        """Create summary of sources by type"""
        summary = {}
        for source in all_sources:
            summary[source.source] = summary.get(source.source, 0) + 1
        return summary
    
    def format_confluence_result(self, result: PivotConfluenceResult) -> str:
        """Format confluence results for display"""
        if not result.pivot_zones:
            return "No Daily Camarilla pivots available for confluence analysis"
        
        output = []
        output.append("CAMARILLA PIVOT CONFLUENCE RANKING")
        output.append("=" * 50)
        
        if result.current_price:
            output.append(f"Current Price: ${result.current_price:.2f}")
        
        if result.atr_5min:
            output.append(f"5min ATR: ${result.atr_5min:.2f}")
        
        output.append(f"Total Sources Checked: {result.total_confluence_sources}")
        output.append(f"Zones with Confluence: {result.zones_with_confluence}/{len(result.pivot_zones)}")
        
        if result.source_summary:
            output.append(f"\nConfluence Sources:")
            for source_type, count in result.source_summary.items():
                source_name = source_type.value.replace('_', ' ').title()
                if source_type in [ConfluenceSource.WEEKLY_ZONES, ConfluenceSource.DAILY_ZONES, ConfluenceSource.ATR_ZONES]:
                    output.append(f"  • {source_name}: {count} zones")
                else:
                    output.append(f"  • {source_name}: {count} levels")
        
        output.append(f"\nRanked Pivot Zones (by Score):")
        output.append("-" * 60)
        
        # Separate resistance and support
        resistance_zones = [z for z in result.get_ranked_zones() if z.is_resistance]
        support_zones = [z for z in result.get_ranked_zones() if z.is_support]
        
        if resistance_zones:
            output.append("\n📈 RESISTANCE ZONES:")
            for zone in resistance_zones:
                output.append(self._format_zone_line(zone, result.current_price))
        
        if support_zones:
            output.append("\n📉 SUPPORT ZONES:")
            for zone in support_zones:
                output.append(self._format_zone_line(zone, result.current_price))
        
        output.append("\n" + "-" * 60)
        output.append("Legend: L1=Minimal, L2=Low, L3=Medium, L4=High, L5=Highest")
        output.append("🔄 = Zone Overlap (higher weight)")
        output.append("\nScoring: L5(12+), L4(8-12), L3(5-8), L2(2-5), L1(<2)")
        
        return "\n".join(output)
    
    def _format_zone_line(self, zone: PivotZone, current_price: Optional[Decimal]) -> str:
        """Format a single zone line for display"""
        # Score-based stars
        if zone.confluence_score >= 12:
            stars = "⭐⭐⭐⭐⭐"
        elif zone.confluence_score >= 8:
            stars = "⭐⭐⭐⭐"
        elif zone.confluence_score >= 5:
            stars = "⭐⭐⭐"
        elif zone.confluence_score >= 2:
            stars = "⭐⭐"
        elif zone.confluence_score > 0:
            stars = "⭐"
        else:
            stars = ""
        
        direction = ""
        if current_price:
            if zone.pivot_price > current_price:
                direction = " ↑ Above"
            elif zone.pivot_price < current_price:
                direction = " ↓ Below"
            else:
                direction = " ← At Price"
        
        zone_line = f"\n{zone.level_name} (L{zone.level_designation.value}): "
        zone_line += f"${zone.zone_low:.2f}-${zone.zone_high:.2f} - "
        zone_line += f"Score: {zone.confluence_score:.1f} {stars}{direction}"
        
        if zone.confluence_sources:
            by_source = {}
            for source in zone.confluence_sources:
                if source.source not in by_source:
                    by_source[source.source] = []
                by_source[source.source].append(source)
            
            for source_type, sources in by_source.items():
                source_name = source_type.value.replace('_', ' ').title()
                
                if source_type in [ConfluenceSource.WEEKLY_ZONES, ConfluenceSource.DAILY_ZONES, ConfluenceSource.ATR_ZONES]:
                    zone_details = []
                    for source in sources:
                        if source.is_zone:
                            zone_details.append(f"{source.source_name} (${source.zone_low:.2f}-${source.zone_high:.2f})")
                        else:
                            zone_details.append(source.source_name)
                    zone_line += f"\n  • {source_name}: {', '.join(zone_details)} 🔄"
                else:
                    source_names = [source.source_name for source in sources]
                    zone_line += f"\n  • {source_name}: {', '.join(source_names)}"
        
        return zone_line


# Example usage and testing
if __name__ == "__main__":
    print("Pivot Confluence Engine - Test Mode")
    
    # This would be used with real data from the analysis thread
    from calculations.pivots.camarilla_engine import CamarillaResult, CamarillaPivot
    
    # Mock Daily Camarilla result for testing
    mock_daily_camarilla = CamarillaResult(
        timeframe='daily',
        close=220.0,
        high=222.0,
        low=218.0,
        pivots=[
            CamarillaPivot(level_name='R6', price=224.04, strength=6, timeframe='daily'),
            CamarillaPivot(level_name='R4', price=222.20, strength=4, timeframe='daily'),
            CamarillaPivot(level_name='R3', price=221.10, strength=3, timeframe='daily'),
            CamarillaPivot(level_name='S3', price=218.90, strength=3, timeframe='daily'),
            CamarillaPivot(level_name='S4', price=217.80, strength=4, timeframe='daily'),
            CamarillaPivot(level_name='S6', price=215.96, strength=6, timeframe='daily'),
        ],
        range_type='higher',
        central_pivot=220.0
    )
    
    engine = PivotConfluenceEngine()
    result = engine.calculate_confluence(
        daily_camarilla=mock_daily_camarilla,
        atr_5min=0.25,
        current_price=220.5
    )
    
    print(engine.format_confluence_result(result))