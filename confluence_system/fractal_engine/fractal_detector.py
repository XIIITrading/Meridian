"""
Core Fractal Detection Engine
Identifies significant swing highs and lows using ZigZag-style logic
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from . import config

class FractalDetector:
    def __init__(self, fractal_length: int = None, min_atr_distance: float = None):
        """
        Initialize the Fractal Detector
        
        Args:
            fractal_length: Number of bars to check on each side (uses config if not specified)
            min_atr_distance: Minimum ATR multiples for significant swing (uses config if not specified)
        """
        # Use config values if not overridden
        self.fractal_length = fractal_length if fractal_length is not None else config.FRACTAL_LENGTH
        self.min_atr_distance = min_atr_distance if min_atr_distance is not None else config.MIN_FRACTAL_DISTANCE_ATR
        self.atr_period = config.ATR_PERIOD
        
        if self.fractal_length % 2 == 0:
            raise ValueError("Fractal length must be odd (3, 5, 7, 9, 11, etc.)")
        
        self.lookback = self.fractal_length // 2
        self.fractals = {'highs': [], 'lows': []}
        
    def detect_fractals(self, df: pd.DataFrame, start_time: datetime) -> Dict:
        """
        Detect significant swing patterns using ZigZag logic
        
        Args:
            df: DataFrame with columns ['datetime', 'open', 'high', 'low', 'close', 'volume']
            start_time: Starting point for backward analysis (UTC)
            
        Returns:
            Dictionary containing detected fractal highs and lows
        """
        # Ensure data is sorted by datetime
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # Calculate ATR for distance validation using config period
        df['atr'] = self._calculate_atr(df, period=self.atr_period)
        
        # Find starting index
        start_idx = self._find_start_index(df, start_time)
        if start_idx is None:
            raise ValueError(f"Start time {start_time} UTC not found in data")
        
        print(f"\n  Using Configuration:")
        print(f"  Fractal Length: {self.fractal_length} bars ({self.lookback} on each side)")
        print(f"  ATR Period: {self.atr_period}")
        print(f"  Min Distance: {self.min_atr_distance} ATRs")
        
        # Use ZigZag logic to find significant swings
        swings = self._find_zigzag_swings(df, end_idx=start_idx)
        
        # Separate into highs and lows
        self.fractals['highs'] = [s for s in swings if s['type'] == 'high']
        self.fractals['lows'] = [s for s in swings if s['type'] == 'low']
        
        print(f"  Found {len(self.fractals['highs'])} significant highs and {len(self.fractals['lows'])} significant lows")
        
        return self.fractals
    
    def _find_zigzag_swings(self, df: pd.DataFrame, end_idx: int) -> List[Dict]:
        """
        Find significant swings using ZigZag algorithm
        This ensures we get alternating highs and lows with significant moves between them
        """
        swings = []
        
        # Calculate the minimum price change required (using ATR from config)
        atr_series = df['atr'].dropna()
        if len(atr_series) > 0:
            avg_atr = atr_series.mean()
            min_move = avg_atr * self.min_atr_distance  # Use config value
            print(f"\n  ZigZag Parameters:")
            print(f"  Average ATR: ${avg_atr:.2f}")
            print(f"  Minimum move required: ${min_move:.2f} ({self.min_atr_distance} ATRs)")
        else:
            # Fallback to percentage if no ATR available
            avg_price = df['close'].mean()
            min_move = avg_price * 0.02  # 2% minimum move
            print(f"  Using 2% minimum move: ${min_move:.2f}")
        
        # Start from the beginning and work forward
        current_idx = self.lookback  # Start after we have enough bars for fractal detection
        last_swing = None
        
        # Find initial swing (could be high or low)
        while current_idx <= end_idx and last_swing is None:
            if self._is_swing_high_at(df, current_idx):
                last_swing = {
                    'index': current_idx,
                    'datetime': df.loc[current_idx, 'datetime'],
                    'type': 'high',
                    'price': df.loc[current_idx, 'high'],
                    'atr': df.loc[current_idx, 'atr']
                }
                swings.append(last_swing)
            elif self._is_swing_low_at(df, current_idx):
                last_swing = {
                    'index': current_idx,
                    'datetime': df.loc[current_idx, 'datetime'],
                    'type': 'low',
                    'price': df.loc[current_idx, 'low'],
                    'atr': df.loc[current_idx, 'atr']
                }
                swings.append(last_swing)
            current_idx += 1
        
        # Now find alternating swings
        while current_idx <= end_idx:
            if last_swing['type'] == 'high':
                # Look for next significant low
                potential_low = self._find_next_significant_low(
                    df, last_swing['index'] + 1, end_idx, last_swing['price'], min_move
                )
                if potential_low:
                    swings.append(potential_low)
                    last_swing = potential_low
                    current_idx = potential_low['index'] + 1
                else:
                    break
            else:  # last_swing['type'] == 'low'
                # Look for next significant high
                potential_high = self._find_next_significant_high(
                    df, last_swing['index'] + 1, end_idx, last_swing['price'], min_move
                )
                if potential_high:
                    swings.append(potential_high)
                    last_swing = potential_high
                    current_idx = potential_high['index'] + 1
                else:
                    break
        
        # Post-process to ensure quality
        swings = self._refine_swings(swings, df, min_move)
        
        return swings
    
    def _find_next_significant_high(self, df: pd.DataFrame, start_idx: int, end_idx: int, 
                                   last_price: float, min_move: float) -> Optional[Dict]:
        """Find the next significant high after a low"""
        best_high = None
        best_high_price = last_price
        
        for idx in range(start_idx + self.lookback, min(end_idx + 1, len(df) - self.lookback)):
            current_high = df.loc[idx, 'high']
            
            # Check if this could be a swing high
            if self._is_swing_high_at(df, idx):
                # Check if it's significant enough
                if current_high - last_price >= min_move:
                    # Check if it's higher than our current best
                    if current_high > best_high_price:
                        best_high = {
                            'index': idx,
                            'datetime': df.loc[idx, 'datetime'],
                            'type': 'high',
                            'price': current_high,
                            'atr': df.loc[idx, 'atr']
                        }
                        best_high_price = current_high
            
            # If price drops significantly below our best high, we've found our swing
            if best_high and best_high_price - df.loc[idx, 'low'] >= min_move:
                return best_high
        
        # Return the best high we found (if any)
        return best_high
    
    def _find_next_significant_low(self, df: pd.DataFrame, start_idx: int, end_idx: int,
                                  last_price: float, min_move: float) -> Optional[Dict]:
        """Find the next significant low after a high"""
        best_low = None
        best_low_price = last_price
        
        for idx in range(start_idx + self.lookback, min(end_idx + 1, len(df) - self.lookback)):
            current_low = df.loc[idx, 'low']
            
            # Check if this could be a swing low
            if self._is_swing_low_at(df, idx):
                # Check if it's significant enough
                if last_price - current_low >= min_move:
                    # Check if it's lower than our current best
                    if current_low < best_low_price:
                        best_low = {
                            'index': idx,
                            'datetime': df.loc[idx, 'datetime'],
                            'type': 'low',
                            'price': current_low,
                            'atr': df.loc[idx, 'atr']
                        }
                        best_low_price = current_low
            
            # If price rises significantly above our best low, we've found our swing
            if best_low and df.loc[idx, 'high'] - best_low_price >= min_move:
                return best_low
        
        # Return the best low we found (if any)
        return best_low
    
    def _refine_swings(self, swings: List[Dict], df: pd.DataFrame, min_move: float) -> List[Dict]:
        """
        Refine swings to ensure they alternate and are significant
        Remove any consecutive highs or lows
        """
        if len(swings) < 2:
            return swings
        
        refined = [swings[0]]
        
        for i in range(1, len(swings)):
            current = swings[i]
            last = refined[-1]
            
            # Ensure alternation
            if current['type'] != last['type']:
                # Check significance
                price_diff = abs(current['price'] - last['price'])
                if price_diff >= min_move:
                    refined.append(current)
            else:
                # Same type - keep the more extreme one
                if current['type'] == 'high':
                    if current['price'] > last['price']:
                        refined[-1] = current  # Replace with higher high
                else:  # low
                    if current['price'] < last['price']:
                        refined[-1] = current  # Replace with lower low
        
        return refined
    
    def get_bar_data(self, df: pd.DataFrame, swing: Dict) -> Dict:
        """
        Get the full bar data for a swing point
        
        Args:
            df: DataFrame with price data
            swing: Swing dictionary with index
            
        Returns:
            Dictionary with high and low of the bar
        """
        idx = swing.get('index')
        if idx is not None and idx < len(df):
            return {
                'high': df.loc[idx, 'high'],
                'low': df.loc[idx, 'low'],
                'open': df.loc[idx, 'open'],
                'close': df.loc[idx, 'close']
            }
        return {'high': swing['price'], 'low': swing['price']}
    
    def _is_swing_high_at(self, df: pd.DataFrame, idx: int) -> bool:
        """Check if a specific index is a swing high"""
        if idx < self.lookback or idx >= len(df) - self.lookback:
            return False
        
        pivot_high = df.loc[idx, 'high']
        
        # Check surrounding bars (using config fractal_length)
        for i in range(1, self.lookback + 1):
            if df.loc[idx - i, 'high'] >= pivot_high or df.loc[idx + i, 'high'] >= pivot_high:
                return False
        
        return True
    
    def _is_swing_low_at(self, df: pd.DataFrame, idx: int) -> bool:
        """Check if a specific index is a swing low"""
        if idx < self.lookback or idx >= len(df) - self.lookback:
            return False
        
        pivot_low = df.loc[idx, 'low']
        
        # Check surrounding bars (using config fractal_length)
        for i in range(1, self.lookback + 1):
            if df.loc[idx - i, 'low'] <= pivot_low or df.loc[idx + i, 'low'] <= pivot_low:
                return False
        
        return True
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = None) -> pd.Series:
        """Calculate Average True Range using config period"""
        if period is None:
            period = self.atr_period
            
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate true range
        hl = high - low
        hc = abs(high - close.shift(1))
        lc = abs(low - close.shift(1))
        
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = tr.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    def _is_swing_high(self, df: pd.DataFrame, idx: int) -> bool:
        """Legacy method for compatibility"""
        return self._is_swing_high_at(df, idx)
    
    def _is_swing_low(self, df: pd.DataFrame, idx: int) -> bool:
        """Legacy method for compatibility"""
        return self._is_swing_low_at(df, idx)
    
    def _find_start_index(self, df: pd.DataFrame, start_time: datetime) -> Optional[int]:
        """Find the index of the start time in the dataframe"""
        if isinstance(start_time, str):
            start_time = pd.to_datetime(start_time)
        
        time_diff = abs(df['datetime'] - start_time)
        if time_diff.min() > pd.Timedelta(minutes=15):
            return None
        
        return time_diff.idxmin()