# calculations/volume/volume_profile.py - Updated for confluence_scanner

"""
Module: Volume Profile Calculation
Purpose: Aggregate volume by price levels for HVN analysis
Time Handling: All timestamps in UTC, no conversions
Performance Target: Process 14 days of 1-min data in <1 second
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass

@dataclass
class PriceLevel:
    """Container for price level information"""
    index: int
    low: float
    high: float
    center: float
    volume: float
    percent_of_total: float = 0.0
    rank: int = 0  # Add rank attribute for HVNEngine compatibility

class VolumeProfile:
    """
    Calculate volume profile from OHLCV data.
    All timestamps must be in UTC.
    """
    
    def __init__(self, levels: int = 100):
        """
        Initialize Volume Profile calculator.
        
        Args:
            levels: Number of price levels to divide the range into
        """
        self.levels = levels
        self.pre_market_start = 8  # 08:00 UTC
        self.pre_market_end = 13.5  # 13:30 UTC
        self.post_market_start = 20  # 20:00 UTC
        self.post_market_end = 24  # 00:00 UTC (next day)
        
        # Store the profile results
        self.price_levels: List[PriceLevel] = []
        self.hvn_unit: float = 0.0
        self.price_range: Tuple[float, float] = (0.0, 0.0)
    
    def calculate_price_levels(self, high: float, low: float) -> Tuple[np.ndarray, float]:
        """
        Calculate price levels and unit size.
        
        Args:
            high: Highest price in range
            low: Lowest price in range
            
        Returns:
            (price_boundaries, hvn_unit)
        """
        if high <= low:
            # Invalid range, return defaults
            return np.array([low, high]), 0.0
            
        price_range = high - low
        hvn_unit = price_range / self.levels if self.levels > 0 else 0.0
        
        # Create price level boundaries
        price_boundaries = np.linspace(low, high, self.levels + 1)
        
        # Store for later use
        self.hvn_unit = hvn_unit
        self.price_range = (low, high)
        
        return price_boundaries, hvn_unit
    
    def is_market_hours(self, timestamp: pd.Timestamp, 
                       include_pre: bool = True, 
                       include_post: bool = True) -> bool:
        """
        Check if timestamp is within desired market hours (UTC).
        
        Args:
            timestamp: UTC timestamp to check
            include_pre: Include pre-market hours
            include_post: Include post-market hours
        """
        try:
            # Handle both Timestamp and datetime objects
            if hasattr(timestamp, 'hour'):
                hour = timestamp.hour + timestamp.minute / 60.0
            else:
                # Convert to Timestamp if needed
                ts = pd.Timestamp(timestamp)
                hour = ts.hour + ts.minute / 60.0
        except:
            # If timestamp parsing fails, include the data point
            return True
        
        # Regular market hours (13:30 - 20:00 UTC)
        if 13.5 <= hour < 20:
            return True
            
        # Pre-market hours
        if include_pre and 8 <= hour < 13.5:
            return True
            
        # Post-market hours
        if include_post and 20 <= hour <= 24:
            return True
            
        return False
    
    def build_volume_profile(self, 
                           data: pd.DataFrame,
                           include_pre: bool = True,
                           include_post: bool = True) -> List[PriceLevel]:
        """
        Build complete volume profile with price level associations.
        
        Args:
            data: DataFrame with columns: open, high, low, close, volume
                  Must have either 'timestamp' column or datetime index
            include_pre: Include pre-market volume
            include_post: Include post-market volume
            
        Returns:
            List of PriceLevel objects sorted by level index
        """
        if data.empty:
            return []
        
        # Handle timestamp column/index
        working_data = data.copy()
        
        # Create timestamp column if it doesn't exist
        if 'timestamp' not in working_data.columns:
            working_data['timestamp'] = working_data.index
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(working_data['timestamp']):
            try:
                working_data['timestamp'] = pd.to_datetime(working_data['timestamp'])
            except:
                # If timestamp conversion fails, use all data
                pass
        
        # Add timezone if missing
        if pd.api.types.is_datetime64_any_dtype(working_data['timestamp']):
            if working_data['timestamp'].dt.tz is None:
                working_data['timestamp'] = working_data['timestamp'].dt.tz_localize('UTC')
        
        # Filter for market hours
        try:
            mask = working_data['timestamp'].apply(
                lambda x: self.is_market_hours(x, include_pre, include_post)
            )
            filtered_data = working_data[mask]
        except:
            # If filtering fails, use all data
            filtered_data = working_data
        
        if filtered_data.empty:
            return []
        
        # Calculate price levels
        high = filtered_data['high'].max()
        low = filtered_data['low'].min()
        
        if high <= low or pd.isna(high) or pd.isna(low):
            return []
            
        price_boundaries, hvn_unit = self.calculate_price_levels(high, low)
        
        if hvn_unit == 0:
            return []
        
        # Initialize volume array
        volume_by_level = np.zeros(self.levels)
        
        # Aggregate volume
        for _, row in filtered_data.iterrows():
            try:
                bar_low = float(row['low'])
                bar_high = float(row['high'])
                bar_volume = float(row.get('volume', 0))
                
                if bar_volume <= 0 or pd.isna(bar_volume):
                    continue
                
                # Find which levels this bar touches
                low_idx = np.searchsorted(price_boundaries, bar_low, side='left')
                high_idx = np.searchsorted(price_boundaries, bar_high, side='right')
                
                # Distribute volume evenly across touched levels
                if high_idx > low_idx:
                    levels_touched = high_idx - low_idx
                    volume_per_level = bar_volume / levels_touched
                    
                    for i in range(max(0, low_idx), min(self.levels, high_idx)):
                        volume_by_level[i] += volume_per_level
            except:
                # Skip invalid rows
                continue
        
        # Calculate total volume for percentages
        total_volume = np.sum(volume_by_level)
        
        if total_volume == 0:
            return []
        
        # Build PriceLevel objects
        self.price_levels = []
        for i in range(self.levels):
            if volume_by_level[i] > 0:  # Only include levels with volume
                level = PriceLevel(
                    index=i,
                    low=price_boundaries[i],
                    high=price_boundaries[i + 1] if i + 1 < len(price_boundaries) else price_boundaries[i],
                    center=(price_boundaries[i] + price_boundaries[min(i + 1, len(price_boundaries) - 1)]) / 2,
                    volume=volume_by_level[i],
                    percent_of_total=(volume_by_level[i] / total_volume) * 100
                )
                self.price_levels.append(level)
        
        return self.price_levels
    
    def get_level_by_price(self, price: float) -> Optional[PriceLevel]:
        """
        Find the price level containing a given price.
        
        Args:
            price: The price to look up
            
        Returns:
            PriceLevel object or None if price is outside range
        """
        for level in self.price_levels:
            if level.low <= price <= level.high:
                return level
        return None
    
    def get_top_levels(self, n: int = 10) -> List[PriceLevel]:
        """
        Get top N levels by volume percentage.
        
        Args:
            n: Number of top levels to return
            
        Returns:
            List of PriceLevel objects sorted by volume percentage (descending)
        """
        return sorted(self.price_levels, 
                     key=lambda x: x.percent_of_total, 
                     reverse=True)[:n]
    
    def get_levels_above_threshold(self, threshold: float) -> List[PriceLevel]:
        """
        Get all levels above a volume percentage threshold.
        
        Args:
            threshold: Minimum percentage of total volume (e.g., 2.0 for 2%)
            
        Returns:
            List of PriceLevel objects meeting the threshold
        """
        return [level for level in self.price_levels 
                if level.percent_of_total >= threshold]