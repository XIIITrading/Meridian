"""
Data models for pattern recognition
Supports both discovered and user-defined patterns
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class PatternSource(Enum):
    """Source of pattern definition"""
    DISCOVERED = "discovered"
    USER_DEFINED = "user_defined"
    HYBRID = "hybrid"  # User-defined but system-refined

class PatternType(Enum):
    """Types of patterns"""
    CONFLUENCE = "confluence"
    SEQUENCE = "sequence"
    TIMING = "timing"
    FAILURE = "failure"
    COMBINATION = "combination"
    CUSTOM = "custom"

@dataclass
class PatternCondition:
    """Single condition within a pattern"""
    field: str  # Column name in trades_df
    operator: str  # '==', '>', '<', 'in', 'between'
    value: Any  # Value to compare
    description: str = ""

@dataclass
class PatternDefinition:
    """Complete pattern definition (user or system)"""
    pattern_id: str
    name: str
    source: PatternSource
    pattern_type: PatternType
    conditions: List[PatternCondition]
    hypothesis: Optional[str] = None  # For user-defined
    discovery_method: Optional[str] = None  # For discovered
    created_date: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None  # User ID for user-defined

@dataclass
class PatternMatch:
    """Result of pattern matching on trades"""
    pattern_id: str
    pattern_name: str
    matching_trades: List[str]  # Trade IDs
    total_matches: int
    total_opportunities: int  # Total trades checked
    match_rate: float  # Percentage of trades matching

@dataclass
class PatternPerformance:
    """Performance metrics for a pattern"""
    pattern_id: str
    win_rate: float
    avg_r_multiple: float
    total_r: float
    profit_factor: float
    best_trade: float
    worst_trade: float
    stddev_r: float
    sharpe_ratio: float

@dataclass
class PatternAnalysis:
    """Complete analysis of a pattern"""
    definition: PatternDefinition
    match: PatternMatch
    performance: PatternPerformance
    statistical_significance: float  # p-value
    confidence_score: float  # 0-100
    strength_score: float  # Composite score
    sample_size_sufficient: bool
    recommendations: List[str]

@dataclass
class PatternRule:
    """Actionable trading rule from pattern"""
    rule_id: str
    pattern_ids: List[str]  # Can combine multiple patterns
    name: str
    conditions_text: str  # Human readable
    expected_win_rate: float
    expected_r_multiple: float
    confidence: float
    min_sample_size: int
    active: bool = True
    
@dataclass
class UserPatternRequest:
    """User request to test a specific pattern"""
    name: str
    hypothesis: str
    conditions: Dict[str, Any]  # Flexible format
    success_criteria: Optional[Dict[str, float]] = None  # e.g., {'win_rate': 60}
    user_id: Optional[str] = None
    notes: Optional[str] = None