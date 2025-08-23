"""
Data models for analysis results
All dataclasses used across analysis modules
"""
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class ConfluenceAnalysis:
    """Results from confluence level analysis"""
    level: str
    trade_count: int
    win_rate: float
    avg_r_multiple: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]

@dataclass
class TimePatternAnalysis:
    """Results from time-based pattern analysis"""
    pattern_name: str
    description: str
    occurrence_count: int
    win_rate: float
    avg_r_multiple: float
    p_value: float
    is_significant: bool

@dataclass
class EdgeFactor:
    """Identified edge in trading performance"""
    factor_name: str
    condition: str
    baseline_winrate: float
    edge_winrate: float
    improvement: float
    sample_size: int
    confidence: float
    actionable_insight: str

@dataclass
class ZoneDistanceResult:
    """Results from zone distance analysis"""
    category: str
    trade_count: int
    win_rate: float
    avg_r_multiple: float
    avg_mfe_r: float
    avg_mae_r: float

@dataclass
class BasicStatistics:
    """Basic trading statistics"""
    total_trades: int
    winners: int
    losers: int
    win_rate: float
    avg_r_multiple: float
    total_r: float
    avg_winner_r: float
    avg_loser_r: float
    best_trade_r: float
    worst_trade_r: float
    profit_factor: float
    expectancy: float