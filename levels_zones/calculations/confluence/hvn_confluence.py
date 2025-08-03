# market_review/calculations/confluence/hvn_confluence.py
"""
Module: HVN Confluence Calculator
Purpose: Identify confluence zones where multiple timeframe peaks align
Features: Zone detection, strength analysis, distance calculation, recency bias
Updated: Prioritizes 15-day analysis for trending stocks
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

from calculations.volume.hvn_engine import TimeframeResult


@dataclass
class ConfluenceZone:
    """Represents a confluence zone where multiple timeframe peaks align"""
    zone_id: int
    center_price: float
    zone_high: float
    zone_low: float
    zone_width: float
    timeframes: List[int]
    peaks: List[Tuple[int, float, float]]  # (timeframe, price, volume_pct)
    total_volume_weight: float
    average_volume: float
    distance_from_current: float
    distance_percentage: float
    strength: str  # 'Strong', 'Moderate', 'Weak'
    strength_score: float  # Numerical strength score
    
    def contains_price(self, price: float) -> bool:
        """Check if a price is within this zone"""
        return self.zone_low <= price <= self.zone_high


@dataclass
class ConfluenceAnalysis:
    """Complete confluence analysis results"""
    current_price: float
    analysis_time: datetime
    zones: List[ConfluenceZone]
    total_zones_found: int
    strongest_zone: Optional[ConfluenceZone]
    nearest_zone: Optional[ConfluenceZone]
    price_in_zone: Optional[ConfluenceZone]  # Zone containing current price
    
    def get_zones_by_distance(self, max_distance_pct: float = 5.0) -> List[ConfluenceZone]:
        """Get zones within a certain percentage distance from current price"""
        return [z for z in self.zones if z.distance_percentage <= max_distance_pct]
    
    def get_zones_by_strength(self, min_strength: str = 'Moderate') -> List[ConfluenceZone]:
        """Get zones meeting minimum strength criteria"""
        strength_order = {'Weak': 1, 'Moderate': 2, 'Strong': 3}
        min_level = strength_order.get(min_strength, 2)
        return [z for z in self.zones if strength_order.get(z.strength, 0) >= min_level]


class HVNConfluenceCalculator:
    """
    Calculates confluence zones from multi-timeframe HVN analysis results.
    
    Confluence zones are areas where peaks from multiple timeframes align,
    suggesting stronger support/resistance levels.
    
    Updated to prioritize 15-day analysis for trending stocks.
    """
    
    def __init__(self,
                 confluence_threshold_percent: float = 0.5,
                 min_peaks_for_zone: int = 2,
                 max_peaks_per_timeframe: int = 10,
                 strength_weights: Optional[Dict[int, float]] = None,
                 use_recency_bias: bool = True):
        """
        Initialize confluence calculator.
        
        Args:
            confluence_threshold_percent: Max price difference as % to group peaks
            min_peaks_for_zone: Minimum peaks required to form a zone
            max_peaks_per_timeframe: Max peaks to consider from each timeframe
            strength_weights: Weight multipliers for each timeframe
            use_recency_bias: Whether to apply recency bias to prioritize recent data
        """
        self.confluence_threshold_percent = confluence_threshold_percent
        self.min_peaks_for_zone = min_peaks_for_zone
        self.max_peaks_per_timeframe = max_peaks_per_timeframe
        self.use_recency_bias = use_recency_bias
        
        # Updated weights to strongly favor shorter timeframes
        self.strength_weights = strength_weights or {
            120: 0.5,   # Reduced from 0.8
            60: 0.8,    # Reduced from 1.0
            15: 1.5     # Increased from 1.2
        }
        
        # Differentiate max peaks by timeframe
        self.max_peaks_by_timeframe = {
            15: 10,  # Allow more from recent timeframe
            60: 7,
            120: 5   # Limit peaks from longest timeframe
        }
        
        # Recency multipliers for volume weighting
        self.recency_multipliers = {
            15: 2.0,   # Double weight for 15-day
            60: 1.5,   # 1.5x weight for 60-day
            120: 1.0   # Base weight for 120-day
        }
        
    def calculate(self,
                  results: Dict[int, TimeframeResult],
                  current_price: float,
                  max_zones: int = 10) -> ConfluenceAnalysis:
        """
        Calculate confluence zones from multi-timeframe results.
        
        Args:
            results: Dictionary of timeframe -> TimeframeResult
            current_price: Current market price
            max_zones: Maximum number of zones to return
            
        Returns:
            ConfluenceAnalysis with identified zones
        """
        # Collect all peaks with metadata
        all_peaks = self._collect_peaks(results)
        
        if not all_peaks:
            return self._empty_analysis(current_price)
        
        # Find confluence zones with 15-day priority
        zones = self._identify_zones(all_peaks, current_price)
        
        # Calculate zone metrics
        zones = self._calculate_zone_metrics(zones, current_price)
        
        # Sort by distance and limit to max_zones
        zones.sort(key=lambda z: z.distance_from_current)
        zones = zones[:max_zones]
        
        # Assign zone IDs
        for i, zone in enumerate(zones):
            zone.zone_id = i + 1
        
        # Create analysis summary
        return self._create_analysis(zones, current_price)
        
    def _collect_peaks(self, results: Dict[int, TimeframeResult]) -> List[Tuple[int, float, float]]:
        """Collect all peaks from results with timeframe-based decay"""
        all_peaks = []
        
        for timeframe, result in results.items():
            # Use timeframe-specific max peaks
            max_peaks = self.max_peaks_by_timeframe.get(
                timeframe, 
                self.max_peaks_per_timeframe
            )
            
            # Apply decay based on timeframe
            decay_factor = {15: 1.0, 60: 0.8, 120: 0.6}.get(timeframe, 1.0)
            
            # Take top N peaks from each timeframe
            for i, peak in enumerate(result.peaks[:max_peaks]):
                if self.use_recency_bias:
                    # Further decay peaks by rank within timeframe
                    rank_decay = 1.0 - (i * 0.1)  # 10% decay per rank
                    adjusted_volume = peak.volume_percent * decay_factor * rank_decay
                else:
                    adjusted_volume = peak.volume_percent
                    
                all_peaks.append((timeframe, peak.price, adjusted_volume))
                
        return all_peaks
    
    def _identify_zones(self, 
                       all_peaks: List[Tuple[int, float, float]], 
                       current_price: float) -> List[ConfluenceZone]:
        """Identify confluence zones with 15-day priority"""
        zones = []
        used_peaks = set()
        confluence_threshold = current_price * (self.confluence_threshold_percent / 100)
        
        # Process peaks by timeframe priority (15-day first)
        for timeframe_priority in [15, 60, 120]:
            # Get peaks for this timeframe that haven't been used
            timeframe_peaks = [
                (i, peak) for i, peak in enumerate(all_peaks) 
                if peak[0] == timeframe_priority and i not in used_peaks
            ]
            
            # Sort by price
            timeframe_peaks.sort(key=lambda x: x[1][1])
            
            for idx1, (tf1, price1, vol1) in timeframe_peaks:
                if idx1 in used_peaks:
                    continue
                    
                # Start new zone anchored by this peak
                zone_peaks = [(tf1, price1, vol1)]
                zone_indices = {idx1}
                
                # Look for nearby peaks from all timeframes
                for idx2, (tf2, price2, vol2) in enumerate(all_peaks):
                    if idx2 in used_peaks or idx2 == idx1:
                        continue
                        
                    # Check if within threshold of any peak in current zone
                    if any(abs(price2 - p[1]) <= confluence_threshold for p in zone_peaks):
                        zone_peaks.append((tf2, price2, vol2))
                        zone_indices.add(idx2)
                
                # Create zone if it meets criteria
                if self._is_valid_zone(zone_peaks):
                    used_peaks.update(zone_indices)
                    zone = self._create_zone(zone_peaks, current_price)
                    zones.append(zone)
                    
        return zones
    
    def _is_valid_zone(self, peaks: List[Tuple[int, float, float]]) -> bool:
        """Check if peaks form a valid confluence zone"""
        if len(peaks) < self.min_peaks_for_zone:
            return False
            
        # Check for multiple timeframes or significant volume
        unique_timeframes = len(set(p[0] for p in peaks))
        total_volume = sum(p[2] for p in peaks)
        
        # Prioritize zones with 15-day peaks
        has_15_day = any(p[0] == 15 for p in peaks)
        
        # Valid if has 15-day peak OR multiple timeframes OR high volume
        return has_15_day or unique_timeframes > 1 or (len(peaks) >= 3 and total_volume > 15.0)
    
    def _create_zone(self, 
                    peaks: List[Tuple[int, float, float]], 
                    current_price: float) -> ConfluenceZone:
        """Create a confluence zone with recency-biased center calculation"""
        prices = [p[1] for p in peaks]
        volumes = [p[2] for p in peaks]
        timeframes = list(set(p[0] for p in peaks))
        
        if self.use_recency_bias:
            # Apply recency bias to volumes based on timeframe
            recency_weighted_peaks = []
            for tf, price, vol in peaks:
                recency_multiplier = self.recency_multipliers.get(tf, 1.0)
                recency_weighted_peaks.append((price, vol * recency_multiplier))
            
            # Calculate weighted center with recency bias
            weighted_sum = sum(p * v for p, v in recency_weighted_peaks)
            total_weight = sum(v for _, v in recency_weighted_peaks)
            center_price = weighted_sum / total_weight if total_weight > 0 else np.mean(prices)
        else:
            # Original calculation
            weighted_sum = sum(p * v for p, v in zip(prices, volumes))
            total_volume = sum(volumes)
            center_price = weighted_sum / total_volume if total_volume > 0 else np.mean(prices)
        
        zone = ConfluenceZone(
            zone_id=0,  # Will be assigned later
            center_price=center_price,
            zone_high=max(prices),
            zone_low=min(prices),
            zone_width=max(prices) - min(prices),
            timeframes=sorted(timeframes),
            peaks=sorted(peaks, key=lambda x: x[0]),  # Sort by timeframe
            total_volume_weight=sum(volumes),
            average_volume=sum(volumes) / len(peaks),
            distance_from_current=abs(center_price - current_price),
            distance_percentage=0,  # Will be calculated
            strength='',  # Will be calculated
            strength_score=0  # Will be calculated
        )
        
        return zone
    
    def _calculate_zone_metrics(self, 
                               zones: List[ConfluenceZone], 
                               current_price: float) -> List[ConfluenceZone]:
        """Calculate additional metrics for each zone"""
        for zone in zones:
            # Distance percentage
            zone.distance_percentage = (zone.distance_from_current / current_price) * 100
            
            # Strength calculation
            zone.strength_score = self._calculate_strength_score(zone)
            zone.strength = self._classify_strength(zone.strength_score)
            
        return zones
    
    def _calculate_strength_score(self, zone: ConfluenceZone) -> float:
        """Calculate numerical strength score with maximum weight approach"""
        score = 0.0
        
        # Factor 1: Number of timeframes (0-3 points)
        timeframe_score = len(zone.timeframes) * 1.0
        score += timeframe_score
        
        # Factor 2: Volume weight (0-3 points)
        volume_score = min(zone.total_volume_weight / 20.0, 1.0) * 3.0
        score += volume_score
        
        # Factor 3: Zone tightness (0-2 points)
        tightness_score = max(0, 2.0 - (zone.zone_width / zone.center_price * 100))
        score += tightness_score
        
        # Factor 4: Timeframe weights - USE MAXIMUM WEIGHT, NOT AVERAGE
        # This ensures zones containing 15-day peaks get the full 1.5x multiplier
        weight_multiplier = max(self.strength_weights.get(tf, 1.0) for tf in zone.timeframes)
        
        # Bonus for having 15-day peak
        if 15 in zone.timeframes:
            score += 1.0  # Additional bonus for recency
        
        return score * weight_multiplier
    
    def _classify_strength(self, score: float) -> str:
        """Classify zone strength based on score"""
        if score >= 6.0:
            return 'Strong'
        elif score >= 4.0:
            return 'Moderate'
        else:
            return 'Weak'
    
    def _create_analysis(self, 
                        zones: List[ConfluenceZone], 
                        current_price: float) -> ConfluenceAnalysis:
        """Create complete analysis summary"""
        # Find special zones
        strongest_zone = max(zones, key=lambda z: z.strength_score) if zones else None
        nearest_zone = min(zones, key=lambda z: z.distance_from_current) if zones else None
        price_in_zone = next((z for z in zones if z.contains_price(current_price)), None)
        
        return ConfluenceAnalysis(
            current_price=current_price,
            analysis_time=datetime.now(),
            zones=zones,
            total_zones_found=len(zones),
            strongest_zone=strongest_zone,
            nearest_zone=nearest_zone,
            price_in_zone=price_in_zone
        )
    
    def _empty_analysis(self, current_price: float) -> ConfluenceAnalysis:
        """Return empty analysis when no peaks found"""
        return ConfluenceAnalysis(
            current_price=current_price,
            analysis_time=datetime.now(),
            zones=[],
            total_zones_found=0,
            strongest_zone=None,
            nearest_zone=None,
            price_in_zone=None
        )
    
    def format_zone_summary(self, zone: ConfluenceZone, current_price: float) -> str:
        """Format a zone for display"""
        direction = "above" if zone.center_price > current_price else "below"
        
        summary = f"Zone #{zone.zone_id} - {zone.strength}\n"
        summary += f"  Center: ${zone.center_price:.2f} ({zone.distance_percentage:.2f}% {direction})\n"
        summary += f"  Range: ${zone.zone_low:.2f} - ${zone.zone_high:.2f} (width: ${zone.zone_width:.2f})\n"
        summary += f"  Timeframes: {', '.join(f'{tf}d' for tf in zone.timeframes)}\n"
        summary += f"  Combined Volume: {zone.total_volume_weight:.2f}%\n"
        summary += f"  Peaks:\n"
        
        for tf, price, vol in zone.peaks:
            # Show original volume for transparency
            original_vol = vol
            if self.use_recency_bias and tf in [15, 60, 120]:
                # Reverse the decay to show original
                decay_factor = {15: 1.0, 60: 0.8, 120: 0.6}.get(tf, 1.0)
                original_vol = vol / decay_factor
            summary += f"    - {tf}d: ${price:.2f} ({original_vol:.2f}%)\n"
            
        return summary


# Example usage
if __name__ == "__main__":
    # This would normally come from HVN analysis
    from market_review.calculations.volume.hvn_engine import VolumePeak, TimeframeResult
    
    # Mock some results for testing with trending stock scenario
    mock_results = {
        120: TimeframeResult(
            timeframe_days=120,
            price_range=(200.0, 250.0),
            total_levels=100,
            peaks=[
                VolumePeak(price=220.50, rank=1, volume_percent=3.5, level_index=0),
                VolumePeak(price=235.25, rank=2, volume_percent=2.8, level_index=0),
                VolumePeak(price=215.00, rank=3, volume_percent=2.5, level_index=0),
            ],
            data_points=1000
        ),
        60: TimeframeResult(
            timeframe_days=60,
            price_range=(210.0, 240.0),
            total_levels=100,
            peaks=[
                VolumePeak(price=220.75, rank=1, volume_percent=4.2, level_index=0),
                VolumePeak(price=230.00, rank=2, volume_percent=3.1, level_index=0),
            ],
            data_points=500
        ),
        15: TimeframeResult(
            timeframe_days=15,
            price_range=(225.0, 245.0),  # Trending higher
            total_levels=100,
            peaks=[
                VolumePeak(price=240.25, rank=1, volume_percent=5.5, level_index=0),
                VolumePeak(price=235.50, rank=2, volume_percent=4.0, level_index=0),
                VolumePeak(price=242.00, rank=3, volume_percent=3.8, level_index=0),
            ],
            data_points=200
        )
    }
    
    # Calculate confluence with recency bias
    calculator = HVNConfluenceCalculator(use_recency_bias=True)
    analysis = calculator.calculate(mock_results, current_price=241.0)
    
    # Print results
    print(f"Current Price: ${analysis.current_price:.2f}")
    print(f"Total Zones Found: {analysis.total_zones_found}")
    print(f"\nTop 5 Confluence Zones (with 15-day priority):")
    
    for zone in analysis.zones[:5]:
        print(f"\n{calculator.format_zone_summary(zone, analysis.current_price)}")