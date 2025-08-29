# calculations/volume/hvn_engine.py - Updated for confluence_scanner

"""
Module: HVN (High Volume Node) Peak Detection Engine
Purpose: Identify volume peaks in price profiles across multiple timeframes
Performance Target: Complete multi-timeframe analysis in <3 seconds
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

# Import from same package
from .volume_profile import VolumeProfile, PriceLevel


@dataclass
class HVNCluster:
    """Container for HVN cluster information"""
    levels: List[PriceLevel]
    cluster_high: float
    cluster_low: float
    center_price: float
    total_volume: float
    total_percent: float
    highest_volume_level: PriceLevel


@dataclass
class HVNResult:
    """Complete HVN analysis result"""
    hvn_unit: float
    price_range: Tuple[float, float]
    clusters: List[HVNCluster]
    ranked_levels: List[PriceLevel]  # All levels with rank
    filtered_levels: List[PriceLevel]  # Levels above threshold


@dataclass
class VolumePeak:
    """Single volume peak information"""
    price: float
    rank: int  # 1 = highest volume peak within timeframe
    volume_percent: float
    level_index: int  # Original level index in volume profile


@dataclass
class TimeframeResult:
    """HVN analysis result for a single timeframe"""
    timeframe_days: int
    price_range: Tuple[float, float]  # High/Low of timeframe
    total_levels: int
    peaks: List[VolumePeak]  # Sorted by rank (volume)
    data_points: int  # Number of bars analyzed


class HVNEngine:
    """
    HVN Peak Detection Engine - adapted for confluence_scanner.
    Identifies absolute peaks in volume profiles across multiple timeframes.
    """
    
    def __init__(self, 
                 levels: int = 100,
                 percentile_threshold: float = 80.0,
                 prominence_threshold: float = 0.5,
                 min_peak_distance: int = 3,
                 proximity_atr_minutes: int = 30):
        """
        Initialize HVN Engine.
        
        Args:
            levels: Number of price levels for volume profile
            percentile_threshold: Percentile threshold for HVN identification
            prominence_threshold: Minimum prominence as % of max volume
            min_peak_distance: Minimum distance between peaks (in levels)
            proximity_atr_minutes: ATR in minutes for proximity alerts
        """
        self.levels = levels
        self.percentile_threshold = percentile_threshold
        self.prominence_threshold = prominence_threshold
        self.min_peak_distance = min_peak_distance
        self.proximity_atr_minutes = proximity_atr_minutes
        self.volume_profile = VolumeProfile(levels=levels)
    
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for volume profile analysis.
        Ensures 'timestamp' column exists.
        
        Args:
            data: OHLCV DataFrame (may have timestamp as index)
            
        Returns:
            DataFrame with timestamp column
        """
        df = data.copy()
        
        # If timestamp is not a column, create it from index
        if 'timestamp' not in df.columns:
            df['timestamp'] = df.index
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # If timestamp has no timezone, assume UTC
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
        return df
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range.
        
        Args:
            data: OHLCV DataFrame
            period: ATR period (default 14)
            
        Returns:
            ATR value
        """
        if len(data) < period + 1:
            return 0.0
            
        high = data['high']
        low = data['low']
        close = data['close'].shift(1)
        
        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else 0.0
    
    def rank_levels(self, levels: List[PriceLevel]) -> List[PriceLevel]:
        """
        Rank levels from 1-100 based on volume percentage.
        100 = highest volume, 1 = lowest volume.
        For ties, closer to current price gets higher rank.
        
        Args:
            levels: List of PriceLevel objects
            
        Returns:
            List of PriceLevel objects with rank attribute added
        """
        if not levels:
            return []
        
        # Get current price (using last level's center as proxy)
        current_price = levels[-1].center
        
        # Sort by volume percentage (descending) and distance to current price (ascending)
        sorted_levels = sorted(
            levels,
            key=lambda x: (-x.percent_of_total, abs(x.center - current_price))
        )
        
        # Assign ranks (1-100 scale)
        total_levels = len(sorted_levels)
        for i, level in enumerate(sorted_levels):
            # Scale rank to 1-100 range
            level.rank = int(100 - (i * 99 / (total_levels - 1))) if total_levels > 1 else 100
            
        return sorted_levels
    
    def filter_by_percentile(self, ranked_levels: List[PriceLevel]) -> List[PriceLevel]:
        """
        Filter levels that are in the top X percentile.
        
        Args:
            ranked_levels: Levels already ranked 1-100
            
        Returns:
            Levels with rank >= percentile_threshold
        """
        return [level for level in ranked_levels 
                if level.rank >= self.percentile_threshold]
    
    def identify_contiguous_clusters(self, 
                                   filtered_levels: List[PriceLevel],
                                   all_levels: List[PriceLevel]) -> List[HVNCluster]:
        """
        Identify clusters of contiguous high-volume levels.
        Checks if adjacent levels are also above threshold.
        
        Args:
            filtered_levels: Levels above percentile threshold
            all_levels: All levels (for checking adjacent)
            
        Returns:
            List of HVNCluster objects
        """
        if not filtered_levels:
            return []
        
        # Create a set of indices for quick lookup
        filtered_indices = {level.index for level in filtered_levels}
        
        # Create index map for all levels
        level_by_index = {level.index: level for level in all_levels}
        
        # Sort filtered levels by index (price order)
        sorted_levels = sorted(filtered_levels, key=lambda x: x.index)
        
        clusters = []
        used_indices = set()
        
        for level in sorted_levels:
            if level.index in used_indices:
                continue
                
            # Start new cluster
            cluster_levels = [level]
            used_indices.add(level.index)
            
            # Check upward (higher prices)
            current_idx = level.index
            while True:
                next_idx = current_idx + 1
                if next_idx in filtered_indices and next_idx not in used_indices:
                    if next_idx in level_by_index:  # Safety check
                        cluster_levels.append(level_by_index[next_idx])
                        used_indices.add(next_idx)
                        current_idx = next_idx
                else:
                    break
            
            # Check downward (lower prices)
            current_idx = level.index
            while True:
                prev_idx = current_idx - 1
                if prev_idx in filtered_indices and prev_idx not in used_indices:
                    if prev_idx in level_by_index:  # Safety check
                        cluster_levels.append(level_by_index[prev_idx])
                        used_indices.add(prev_idx)
                        current_idx = prev_idx
                else:
                    break
            
            # Create cluster
            cluster = self._create_cluster(cluster_levels)
            clusters.append(cluster)
        
        return sorted(clusters, key=lambda x: x.total_percent, reverse=True)
    
    def _create_cluster(self, levels: List[PriceLevel]) -> HVNCluster:
        """Helper to create HVNCluster from levels."""
        total_volume = sum(l.volume for l in levels)
        
        if total_volume == 0:
            total_volume = 1  # Avoid division by zero
        
        return HVNCluster(
            levels=sorted(levels, key=lambda x: x.index),
            cluster_high=max(l.high for l in levels),
            cluster_low=min(l.low for l in levels),
            center_price=sum(l.center * l.volume for l in levels) / total_volume,
            total_volume=total_volume,
            total_percent=sum(l.percent_of_total for l in levels),
            highest_volume_level=max(levels, key=lambda x: x.volume)
        )
    
    def analyze(self, 
                data: pd.DataFrame,
                include_pre: bool = True,
                include_post: bool = True) -> HVNResult:
        """
        Run complete HVN analysis.
        
        Args:
            data: OHLCV DataFrame
            include_pre: Include pre-market data
            include_post: Include post-market data
            
        Returns:
            HVNResult with all calculations
        """
        # Prepare data
        prepared_data = self.prepare_data(data)
        
        # Build volume profile
        profile_levels = self.volume_profile.build_volume_profile(
            prepared_data, include_pre, include_post
        )
        
        if not profile_levels:
            return HVNResult(
                hvn_unit=0,
                price_range=(0, 0),
                clusters=[],
                ranked_levels=[],
                filtered_levels=[]
            )
        
        # Calculate ATR
        atr = self.calculate_atr(data)
        
        # Rank all levels
        ranked_levels = self.rank_levels(profile_levels)
        
        # Filter levels by percentile (top 20% if threshold=80)
        filtered_levels = self.filter_by_percentile(ranked_levels)
        
        # Identify contiguous clusters
        clusters = self.identify_contiguous_clusters(filtered_levels, profile_levels)

        # Extract POCs for zone anchoring
        pocs = self.volume_profile.get_multiple_pocs(count=12)  # Get top 12 POCs
        
        return HVNResult(
            hvn_unit=self.volume_profile.hvn_unit,
            price_range=self.volume_profile.price_range,
            clusters=clusters,
            ranked_levels=ranked_levels,
            filtered_levels=filtered_levels
        )
    
    def create_poc_anchor_zones(self, 
                           data: pd.DataFrame,
                           timeframe_days: int = 7,
                           zone_width_atr: float = None,
                           min_zones: int = 6) -> Dict:
        """
        Create anchor zones from POCs for HVN-based zone discovery
        
        Args:
            data: OHLCV DataFrame
            timeframe_days: Days to analyze (default 7)
            zone_width_atr: Zone width in ATR units (e.g., 5-min ATR)
            min_zones: Minimum zones to create
            
        Returns:
            Dictionary with POC zones and metadata
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Filter data for timeframe
        current_date = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else pd.Timestamp.now()
        start_date = current_date - timedelta(days=timeframe_days)
        timeframe_data = data[data.index >= start_date].copy()
        
        # Prepare and build volume profile
        prepared_data = self.prepare_data(timeframe_data)
        profile_levels = self.volume_profile.build_volume_profile(
            prepared_data, 
            include_pre=True, 
            include_post=True
        )
        
        if not profile_levels:
            logger.warning(f"No volume profile levels for {timeframe_days}-day HVN")
            return {'poc_zones': [], 'metadata': {}}
        
        # Get POCs
        pocs = self.volume_profile.get_multiple_pocs(count=min_zones * 2)  # Get extra for filtering
        
        if not pocs:
            logger.warning("No POCs identified")
            return {'poc_zones': [], 'metadata': {}}
        
        # Create zones from POCs
        poc_zones = []
        for i, poc in enumerate(pocs):
            zone = {
                'zone_id': f'hvn_poc_{timeframe_days}d_{i}',
                'poc_price': poc.center,
                'poc_volume_pct': poc.percent_of_total,
                'zone_low': poc.center - (zone_width_atr / 2) if zone_width_atr else poc.low,
                'zone_high': poc.center + (zone_width_atr / 2) if zone_width_atr else poc.high,
                'zone_width': zone_width_atr if zone_width_atr else (poc.high - poc.low),
                'timeframe_days': timeframe_days,
                'rank': i + 1,  # 1 = highest volume
                'type': 'hvn_poc_anchor',
                'source': f'hvn_{timeframe_days}d_poc'
            }
            poc_zones.append(zone)
        
        logger.info(f"Created {len(poc_zones)} POC anchor zones from {timeframe_days}-day HVN")
        
        return {
            'poc_zones': poc_zones,
            'metadata': {
                'timeframe_days': timeframe_days,
                'total_pocs': len(pocs),
                'price_range': self.volume_profile.price_range,
                'zone_width_atr': zone_width_atr
            }
        }
    
    def identify_volume_peaks(self, 
                            levels: List[PriceLevel], 
                            percentile_filter: float = 70.0) -> List[PriceLevel]:
        """
        Identify local peaks in the volume profile.
        
        Args:
            levels: All price levels from volume profile
            percentile_filter: Only consider levels above this percentile
            
        Returns:
            List of PriceLevel objects that are peaks
        """
        if not levels:
            return []
        
        # Sort levels by price
        sorted_levels = sorted(levels, key=lambda x: x.center)
        volumes = np.array([level.percent_of_total for level in sorted_levels])
        
        if len(volumes) == 0:
            return []
        
        # Calculate thresholds
        max_volume = np.max(volumes)
        if max_volume == 0:
            return []
            
        min_prominence = max_volume * self.prominence_threshold / 100
        height_threshold = np.percentile(volumes, percentile_filter)
        
        # Find peaks
        try:
            peak_indices, properties = find_peaks(
                volumes,
                prominence=min_prominence,
                distance=self.min_peak_distance,
                height=height_threshold
            )
        except Exception:
            # If find_peaks fails, return empty list
            return []
        
        # Extract peak levels
        peak_levels = [sorted_levels[i] for i in peak_indices]
        
        return peak_levels
    
    def analyze_timeframe(self, 
                         data: pd.DataFrame,
                         timeframe_days: int,
                         include_pre: bool = True,
                         include_post: bool = True) -> TimeframeResult:
        """
        Run HVN peak analysis for a single timeframe.
        
        Args:
            data: Complete OHLCV DataFrame
            timeframe_days: Number of days to analyze
            include_pre: Include pre-market data
            include_post: Include post-market data
            
        Returns:
            TimeframeResult with detected peaks
        """
        # Filter data for timeframe
        current_date = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else pd.Timestamp.now()
        start_date = current_date - timedelta(days=timeframe_days)
        timeframe_data = data[data.index >= start_date].copy()
        
        # Prepare data
        prepared_data = self.prepare_data(timeframe_data)
        
        # Build volume profile
        profile_levels = self.volume_profile.build_volume_profile(
            prepared_data, include_pre, include_post
        )
        
        if not profile_levels:
            return TimeframeResult(
                timeframe_days=timeframe_days,
                price_range=(0, 0),
                total_levels=0,
                peaks=[],
                data_points=len(timeframe_data)
            )
        
        # Identify peaks
        peak_levels = self.identify_volume_peaks(profile_levels)
        
        # Sort peaks by volume and create VolumePeak objects
        sorted_peaks = sorted(peak_levels, key=lambda x: x.percent_of_total, reverse=True)
        volume_peaks = [
            VolumePeak(
                price=peak.center,
                rank=idx + 1,
                volume_percent=peak.percent_of_total,
                level_index=peak.index
            )
            for idx, peak in enumerate(sorted_peaks)
        ]
        
        return TimeframeResult(
            timeframe_days=timeframe_days,
            price_range=self.volume_profile.price_range,
            total_levels=len(profile_levels),
            peaks=volume_peaks,
            data_points=len(timeframe_data)
        )
    
    def analyze_multi_timeframe(self, 
                               data: pd.DataFrame,
                               timeframes: List[int] = [30, 14, 7],  # Changed default to your preferred
                               include_pre: bool = True,
                               include_post: bool = True) -> Dict[int, TimeframeResult]:
        """
        Run HVN analysis for multiple timeframes.
        
        Args:
            data: Complete OHLCV DataFrame
            timeframes: List of lookback days
            include_pre: Include pre-market data
            include_post: Include post-market data
            
        Returns:
            Dictionary mapping timeframe to TimeframeResult
        """
        results = {}
        
        for days in timeframes:
            try:
                results[days] = self.analyze_timeframe(
                    data, days, include_pre, include_post
                )
            except Exception as e:
                # If a timeframe fails, create empty result
                results[days] = TimeframeResult(
                    timeframe_days=days,
                    price_range=(0, 0),
                    total_levels=0,
                    peaks=[],
                    data_points=0
                )
        
        return results
    
    def get_all_peaks_dataframe(self, results: Dict[int, TimeframeResult]) -> pd.DataFrame:
        """
        Convert results to a clean DataFrame for easy access.
        
        Returns DataFrame with columns:
            - timeframe: 30, 14, or 7
            - price: Peak price
            - rank: Rank within timeframe
            - volume_pct: Volume percentage
        """
        rows = []
        
        for days, result in results.items():
            for peak in result.peaks:
                rows.append({
                    'timeframe': days,
                    'price': peak.price,
                    'rank': peak.rank,
                    'volume_pct': peak.volume_percent
                })
        
        return pd.DataFrame(rows)
    
    def get_peaks_summary(self, results: Dict[int, TimeframeResult]) -> Dict:
        """
        Get a clean summary of peaks grouped by timeframe.
        
        Returns:
            {
                30: [{'price': 456.25, 'rank': 1, 'volume_pct': 8.5}, ...],
                14: [{'price': 465.50, 'rank': 1, 'volume_pct': 9.2}, ...],
                7: [{'price': 464.25, 'rank': 1, 'volume_pct': 11.5}, ...]
            }
        """
        summary = {}
        
        for days, result in results.items():
            summary[days] = [
                {
                    'price': peak.price,
                    'rank': peak.rank,
                    'volume_pct': round(peak.volume_percent, 2)
                }
                for peak in result.peaks
            ]
        
        return summary
    
    def print_results(self, results: Dict[int, TimeframeResult], symbol: str = ""):
        """
        Pretty print the results to console.
        """
        print(f"\n{'='*60}")
        print(f"HVN PEAK ANALYSIS{f' - {symbol}' if symbol else ''}")
        print(f"{'='*60}")
        
        for days in sorted(results.keys(), reverse=True):
            result = results[days]
            print(f"\n📊 {days}-Day Timeframe")
            print(f"   Price Range: ${result.price_range[0]:.2f} - ${result.price_range[1]:.2f}")
            print(f"   Data Points: {result.data_points:,} bars")
            print(f"   Total Peaks: {len(result.peaks)}")
            
            if result.peaks:
                print(f"\n   Top Volume Peaks:")
                print(f"   {'Rank':<6} {'Price':<10} {'Volume %'}")
                print(f"   {'-'*6} {'-'*10} {'-'*10}")
                
                for peak in result.peaks[:5]:  # Show top 5
                    print(f"   #{peak.rank:<5} ${peak.price:<9.2f} {peak.volume_percent:.2f}%")