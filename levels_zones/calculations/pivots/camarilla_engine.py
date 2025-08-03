"""
Camarilla pivot calculator engine
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd


@dataclass
class CamarillaPivot:
    level_name: str
    price: float
    strength: int
    timeframe: str


@dataclass
class CamarillaResult:
    timeframe: str
    close: float
    high: float
    low: float
    pivots: List[CamarillaPivot]
    range_type: str
    central_pivot: float


class CamarillaEngine:
    """
    Camarilla pivot point calculator
    """
    
    def calculate_from_data(self, data: pd.DataFrame, timeframe: str) -> CamarillaResult:
        """
        Calculate Camarilla pivots from OHLC data
        
        Args:
            data: DataFrame with OHLC data
            timeframe: Timeframe string ('daily', 'weekly', 'monthly')
            
        Returns:
            CamarillaResult with calculated pivots
        """
        if data.empty:
            return None
            
        # Get the last complete period
        last_bar = data.iloc[-1]
        high = float(last_bar['high'])
        low = float(last_bar['low'])
        close = float(last_bar['close'])
        
        # Calculate range
        range_val = high - low
        
        # Calculate pivot point (central pivot)
        pivot = (high + low + close) / 3
        
        # Calculate Camarilla levels
        pivots = []
        
        # Resistance levels
        r1 = close + range_val * 1.1 / 12
        r2 = close + range_val * 1.1 / 6
        r3 = close + range_val * 1.1 / 4
        r4 = close + range_val * 1.1 / 2
        r5 = (high / low) * close
        r6 = r5 + 1.168 * (r5 - r4)
        
        # Support levels
        s1 = close - range_val * 1.1 / 12
        s2 = close - range_val * 1.1 / 6
        s3 = close - range_val * 1.1 / 4
        s4 = close - range_val * 1.1 / 2
        s5 = close - (r5 - close)
        s6 = close - (r6 - close)
        
        # Add pivots with strength scores
        pivots.extend([
            CamarillaPivot('R6', r6, 6, timeframe),
            CamarillaPivot('R5', r5, 5, timeframe),
            CamarillaPivot('R4', r4, 4, timeframe),
            CamarillaPivot('R3', r3, 3, timeframe),
            CamarillaPivot('R2', r2, 2, timeframe),
            CamarillaPivot('R1', r1, 1, timeframe),
            CamarillaPivot('S1', s1, 1, timeframe),
            CamarillaPivot('S2', s2, 2, timeframe),
            CamarillaPivot('S3', s3, 3, timeframe),
            CamarillaPivot('S4', s4, 4, timeframe),
            CamarillaPivot('S5', s5, 5, timeframe),
            CamarillaPivot('S6', s6, 6, timeframe),
        ])
        
        # Determine range type
        if close > pivot:
            range_type = 'higher'
        elif close < pivot:
            range_type = 'lower'
        else:
            range_type = 'neutral'
        
        return CamarillaResult(
            timeframe=timeframe,
            close=close,
            high=high,
            low=low,
            pivots=pivots,
            range_type=range_type,
            central_pivot=pivot
        )