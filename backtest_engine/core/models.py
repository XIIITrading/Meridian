# core/models.py
"""
Data models for the backtesting engine
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import json
from decimal import Decimal
import uuid

# Constants for confluence scoring (from your M15 widget)
CONFLUENCE_THRESHOLDS = {
    'L5': 12.0,   # Highest
    'L4': 8.0,    # High
    'L3': 5.0,    # Medium
    'L2': 2.5,    # Low
    'L1': 0.0     # Minimal
}

TICK_SIZE = 0.01  # For equities

# Enums for standardization
class ConfluenceLevel(Enum):
    L5 = "L5"  # Highest (12+)
    L4 = "L4"  # High (8-12)
    L3 = "L3"  # Medium (5-8)
    L2 = "L2"  # Low (2.5-5)
    L1 = "L1"  # Minimal (<2.5)
    NONE = "NONE"
    
    @classmethod
    def from_score(cls, score: float) -> 'ConfluenceLevel':
        """Get confluence level from score"""
        if score >= 12:
            return cls.L5
        elif score >= 8:
            return cls.L4
        elif score >= 5:
            return cls.L3
        elif score >= 2.5:
            return cls.L2
        elif score > 0:
            return cls.L1
        else:
            return cls.NONE

class ConfluenceSource(Enum):
    """Types of confluence sources"""
    HVN_7DAY = "HVN_7DAY"
    HVN_14DAY = "HVN_14DAY"
    HVN_30DAY = "HVN_30DAY"
    CAMARILLA_MONTHLY = "CAMARILLA_MONTHLY"
    CAMARILLA_WEEKLY = "CAMARILLA_WEEKLY"
    CAMARILLA_DAILY = "CAMARILLA_DAILY"
    WEEKLY_ZONES = "WEEKLY_ZONES"
    DAILY_ZONES = "DAILY_ZONES"
    ATR_ZONES = "ATR_ZONES"
    DAILY_LEVELS = "DAILY_LEVELS"
    ATR_LEVELS = "ATR_LEVELS"
    REFERENCE_PRICES = "REFERENCE_PRICES"
    WEEKLY_LEVEL = "WEEKLY_LEVEL"  # WL1-4
    DAILY_LEVEL = "DAILY_LEVEL"    # DL1-6
    M15_OVERLAP = "M15_OVERLAP"    # Zone overlap

class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"

class SignalType(Enum):
    PIVOT_HIGH = "pivot_high"
    PIVOT_LOW = "pivot_low"
    ZONE_TOUCH = "zone_touch"

class ExitReason(Enum):
    STOP_LOSS = "stop_loss"
    STOP_HIT = "stop_hit" 
    TARGET1 = "target1"
    TARGET_HIT = "target_hit"
    TARGET2 = "target2"
    TARGET3 = "target3"
    TIME_EXIT = "time_exit"
    MANUAL = "manual"
    MANUAL_EXIT = "manual_exit"
    UNKNOWN = "unknown"

@dataclass
class ConfluenceInput:
    """Single confluence source for a zone"""
    source_type: ConfluenceSource
    source_name: str  # e.g., "WL1", "DL3", "Zone 2"
    source_value: float  # Price level
    overlap_percentage: float  # How much it overlaps with zone
    score_contribution: float  # How much it adds to total score
    
    def to_dict(self) -> Dict:
        return {
            'source_type': self.source_type.value,
            'source_name': self.source_name,
            'source_value': self.source_value,
            'overlap_percentage': self.overlap_percentage,
            'score_contribution': self.score_contribution
        }

@dataclass
class ZoneDetail:
    """Detailed information about a single M15 zone"""
    zone_number: int  # 1-6
    level: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    zone_date: Optional[date] = None
    zone_time: Optional[time] = None
    
    # Confluence tracking
    confluent_inputs: List[ConfluenceInput] = field(default_factory=list)
    confluence_score: float = 0.0
    confluence_level: ConfluenceLevel = ConfluenceLevel.NONE
    confluence_count: int = 0
    
    # Distance metrics
    distance_from_price: Optional[float] = None
    distance_in_ticks: Optional[float] = None
    distance_in_atr: Optional[float] = None
    
    # Behavior tracking
    zone_tested: bool = False
    zone_held: bool = False
    penetration_depth: Optional[float] = None
    time_at_zone: Optional[int] = None  # seconds
    
    @property
    def zone_center(self) -> float:
        """Calculate zone center price"""
        if self.high and self.low:
            return (self.high + self.low) / 2
        return self.level or 0.0
    
    @property
    def zone_height(self) -> float:
        """Calculate zone height in price"""
        if self.high and self.low:
            return self.high - self.low
        return 0.0
    
    @property
    def zone_height_ticks(self) -> float:
        """Calculate zone height in ticks"""
        return self.zone_height / TICK_SIZE
    
    def calculate_confluence_score(self) -> float:
        """Calculate total confluence score from inputs"""
        self.confluence_score = sum(inp.score_contribution for inp in self.confluent_inputs)
        self.confluence_level = ConfluenceLevel.from_score(self.confluence_score)
        self.confluence_count = len(self.confluent_inputs)
        return self.confluence_score
    
    def add_confluence(self, source_type: ConfluenceSource, source_name: str, 
                      source_value: float, score_contribution: float = 1.0):
        """Add a confluence source to this zone"""
        # Calculate overlap percentage
        if self.high and self.low:
            if self.low <= source_value <= self.high:
                overlap = 100.0
            else:
                # Calculate distance-based overlap
                if source_value < self.low:
                    distance = self.low - source_value
                else:
                    distance = source_value - self.high
                overlap = max(0, 100 - (distance / self.zone_height * 100)) if self.zone_height > 0 else 0
        else:
            overlap = 0.0
        
        confluence = ConfluenceInput(
            source_type=source_type,
            source_name=source_name,
            source_value=source_value,
            overlap_percentage=overlap,
            score_contribution=score_contribution
        )
        
        self.confluent_inputs.append(confluence)
        self.calculate_confluence_score()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert enums
        data['confluence_level'] = self.confluence_level.value
        data['confluent_inputs'] = [inp.to_dict() for inp in self.confluent_inputs]
        return data
    
    @classmethod
    def from_levels_zones(cls, record: Dict, zone_num: int) -> 'ZoneDetail':
        """Create from levels_zones record"""
        prefix = f"m15_zone{zone_num}_"
        
        zone = cls(
            zone_number=zone_num,
            level=record.get(f"{prefix}level"),
            high=record.get(f"{prefix}high"),
            low=record.get(f"{prefix}low"),
            zone_date=record.get(f"{prefix}date"),
            zone_time=record.get(f"{prefix}time")
        )
        
        # Set stored confluence if available
        if record.get(f"{prefix}confluence_score"):
            zone.confluence_score = float(record.get(f"{prefix}confluence_score"))
            zone.confluence_level = ConfluenceLevel(record.get(f"{prefix}confluence_level", "NONE"))
            zone.confluence_count = record.get(f"{prefix}confluence_count", 0)
        
        return zone

@dataclass
class LevelsData:
    """Store all levels from levels_zones record"""
    # Weekly levels
    wl1: Optional[float] = None
    wl2: Optional[float] = None
    wl3: Optional[float] = None
    wl4: Optional[float] = None
    
    # Daily levels
    dl1: Optional[float] = None
    dl2: Optional[float] = None
    dl3: Optional[float] = None
    dl4: Optional[float] = None
    dl5: Optional[float] = None
    dl6: Optional[float] = None
    
    @classmethod
    def from_levels_zones(cls, record: Dict) -> 'LevelsData':
        """Create from levels_zones record"""
        return cls(
            wl1=record.get('weekly_wl1'),
            wl2=record.get('weekly_wl2'),
            wl3=record.get('weekly_wl3'),
            wl4=record.get('weekly_wl4'),
            dl1=record.get('daily_dl1'),
            dl2=record.get('daily_dl2'),
            dl3=record.get('daily_dl3'),
            dl4=record.get('daily_dl4'),
            dl5=record.get('daily_dl5'),
            dl6=record.get('daily_dl6')
        )
    
    def get_weekly_levels(self) -> List[Tuple[str, float]]:
        """Get list of weekly levels with names"""
        levels = []
        for i in range(1, 5):
            val = getattr(self, f'wl{i}')
            if val is not None:
                levels.append((f'WL{i}', val))
        return levels
    
    def get_daily_levels(self) -> List[Tuple[str, float]]:
        """Get list of daily levels with names"""
        levels = []
        for i in range(1, 7):
            val = getattr(self, f'dl{i}')
            if val is not None:
                levels.append((f'DL{i}', val))
        return levels

@dataclass
class MarketContext:
    """Market structure and context at time of analysis"""
    # Weekly context
    weekly_trend: Optional[str] = None
    weekly_internal_trend: Optional[str] = None
    weekly_position_structure: Optional[float] = None
    weekly_eow_bias: Optional[str] = None
    
    # Daily context
    daily_trend: Optional[str] = None
    daily_internal_trend: Optional[str] = None
    daily_position_structure: Optional[float] = None
    daily_eod_bias: Optional[str] = None
    
    # Price context
    pre_market_price: Optional[float] = None
    current_price: Optional[float] = None
    
    # ATR values
    atr_5min: Optional[float] = None
    atr_15min: Optional[float] = None
    atr_2hour: Optional[float] = None
    daily_atr: Optional[float] = None
    
    # Levels data
    levels: Optional[LevelsData] = None
    
    def is_trend_aligned(self) -> bool:
        """Check if weekly and daily trends are aligned"""
        if self.weekly_trend and self.daily_trend:
            return self.weekly_trend == self.daily_trend
        return False
    
    def get_structure_strength(self) -> float:
        """Get average structure position strength"""
        positions = []
        if self.weekly_position_structure is not None:
            positions.append(self.weekly_position_structure)
        if self.daily_position_structure is not None:
            positions.append(self.daily_position_structure)
        return sum(positions) / len(positions) if positions else 0.0
    
    @classmethod
    def from_levels_zones(cls, record: Dict) -> 'MarketContext':
        """Create from levels_zones record"""
        return cls(
            weekly_trend=record.get('weekly_trend_direction'),
            weekly_internal_trend=record.get('weekly_internal_trend'),
            weekly_position_structure=record.get('weekly_position_structure'),
            weekly_eow_bias=record.get('weekly_eow_bias'),
            daily_trend=record.get('daily_trend_direction'),
            daily_internal_trend=record.get('daily_internal_trend'),
            daily_position_structure=record.get('daily_position_structure'),
            daily_eod_bias=record.get('daily_eod_bias'),
            pre_market_price=record.get('pre_market_price'),
            current_price=record.get('current_price'),
            atr_5min=record.get('atr_5min'),
            atr_15min=record.get('atr_15min'),
            atr_2hour=record.get('atr_2hour'),
            daily_atr=record.get('daily_atr'),
            levels=LevelsData.from_levels_zones(record)
        )

# Remove the comment line and add these classes:

@dataclass
class BacktestSession:
    """Represents a complete backtesting session"""
    id: Optional[str] = None
    levels_zones_id: str = None
    ticker: str = None
    session_date: date = None
    strategy_name: str = "M5_Pivot"
    strategy_version: str = "1.0.0"
    
    # Strategy parameters
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    # Configuration
    start_time: time = time(9, 30)
    end_time: time = time(16, 0)
    use_premarket: bool = False
    use_afterhours: bool = False
    
    # Risk parameters
    stop_multiplier: float = 1.5
    target_zones: int = 2
    max_trades_per_session: int = 10
    position_size_mode: str = "fixed"
    
    # Status
    status: str = "pending"
    completion_percentage: float = 0.0
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    created_by: Optional[str] = None
    notes: Optional[str] = None
    
    # Runtime data (not stored in DB)
    zones: List[ZoneDetail] = field(default_factory=list)
    market_context: Optional[MarketContext] = None
    
    def to_db_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'levels_zones_id': self.levels_zones_id,
            'ticker': self.ticker,
            'session_date': self.session_date,
            'strategy_name': self.strategy_name,
            'strategy_version': self.strategy_version,
            'strategy_params': json.dumps(self.strategy_params),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'use_premarket': self.use_premarket,
            'use_afterhours': self.use_afterhours,
            'stop_multiplier': self.stop_multiplier,
            'target_zones': self.target_zones,
            'max_trades_per_session': self.max_trades_per_session,
            'position_size_mode': self.position_size_mode,
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'error_message': self.error_message,
            'created_by': self.created_by,
            'notes': self.notes
        }

@dataclass
class EntrySignal:
    """Represents a potential entry signal"""
    id: Optional[str] = None
    session_id: str = None
    
    # Signal details
    signal_timestamp: datetime = None
    signal_type: SignalType = None
    pivot_strength: Optional[int] = None  # 1-3
    
    # M5 candle data
    m5_open: Optional[float] = None
    m5_high: Optional[float] = None
    m5_low: Optional[float] = None
    m5_close: Optional[float] = None
    m5_volume: Optional[int] = None
    m5_vwap: Optional[float] = None
    
    # Zone association
    zone_number: Optional[int] = None
    zone_high: Optional[float] = None
    zone_low: Optional[float] = None
    zone_confluence_level: Optional[str] = None
    zone_confluence_score: Optional[float] = None
    distance_to_zone_ticks: Optional[float] = None
    
    # Validation
    is_valid: bool = True
    validation_reason: Optional[str] = None
    user_marked: bool = False
    
    # Additional calculations
    calculation_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeSetup:
    """Entry criteria and risk parameters for a trade"""
    entry_signal: EntrySignal
    zone_detail: ZoneDetail
    
    # Entry rules
    entry_price: float = None
    entry_time: datetime = None
    direction: TradeDirection = None
    
    # Risk management
    stop_price: float = None
    stop_distance_ticks: float = None
    stop_distance_atr: float = None
    
    # Targets
    target_prices: List[float] = field(default_factory=list)
    target_zones: List[int] = field(default_factory=list)
    
    # Position sizing
    position_size: int = 100
    risk_amount: float = None
    
    # Validation
    meets_criteria: bool = False
    criteria_details: Dict[str, bool] = field(default_factory=dict)

@dataclass
class TradeExecution:
    """Actual trade execution with results"""
    id: Optional[str] = None
    session_id: str = None
    entry_signal_id: Optional[str] = None
    
    # Trade identification
    trade_number: int = None
    trade_direction: str = None
    
    # Entry
    entry_timestamp: datetime = None
    entry_price: float = None
    entry_zone_number: Optional[int] = None
    entry_confluence_level: Optional[str] = None
    entry_confluence_score: Optional[float] = None
    entry_slippage: float = 0.0
    
    # Position
    position_size: int = None
    risk_amount: Optional[float] = None
    
    # Stops and targets
    initial_stop_price: float = None
    current_stop_price: Optional[float] = None
    target_prices: List[float] = field(default_factory=list)
    
    # Exit
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    exit_slippage: float = 0.0
    
    # Results
    pnl_dollars: Optional[float] = None
    pnl_ticks: Optional[float] = None
    pnl_r_multiple: Optional[float] = None
    commission: float = 0.0
    duration_minutes: Optional[int] = None
    
    # MFE/MAE
    mfe_price: Optional[float] = None
    mfe_r_multiple: Optional[float] = None
    mae_price: Optional[float] = None
    mae_r_multiple: Optional[float] = None
    
    # Status
    status: str = "open"
    is_winner: Optional[bool] = None
    
    # Bar-by-bar tracking
    bar_data: List[Dict] = field(default_factory=list)

@dataclass  
class PerformanceMetrics:
    """Aggregate performance metrics for analysis"""
    session_id: str
    
    # Basic statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L metrics
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # R-multiple metrics
    avg_win_r: float = 0.0
    avg_loss_r: float = 0.0
    total_r: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    # Confluence analysis
    performance_by_confluence: Dict[str, Dict] = field(default_factory=dict)
    
    # Time analysis
    performance_by_hour: Dict[int, Dict] = field(default_factory=dict)
    
    # Additional metrics
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)

# ============= ADD THESE PHASE 3 MODELS TO YOUR EXISTING FILE =============

@dataclass
class ManualTradeEntry:
    """Model for semi-automated trade entries"""
    # User inputs
    entry_candle_time: datetime
    exit_candle_time: datetime
    trade_direction: TradeDirection
    entry_price: float
    stop_price: float
    target_price: float
    exit_price: float
    
    # Optional fields
    ticker: str = "AMD"
    fixed_risk: float = 250.0
    notes: Optional[str] = None
    
    # Calculated fields (set after creation)
    trade_id: Optional[str] = None
    ticker_id: Optional[str] = None
    shares: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived fields after initialization"""
        # Calculate position size
        if self.stop_price and self.entry_price:
            risk_per_share = abs(self.entry_price - self.stop_price)
            if risk_per_share > 0:
                self.shares = round(self.fixed_risk / risk_per_share, 2)
        
        # Calculate risk/reward ratio
        if self.target_price and self.entry_price and self.stop_price:
            potential_profit = abs(self.target_price - self.entry_price)
            potential_loss = abs(self.entry_price - self.stop_price)
            if potential_loss > 0:
                self.risk_reward_ratio = round(potential_profit / potential_loss, 2)

@dataclass
class ZoneMatch:
    """Result of matching a trade to a zone"""
    zone_number: int
    zone_type: str  # 'resistance' or 'support'
    zone_high: float
    zone_low: float
    confluence_level: str  # L1-L5
    confluence_score: float
    confluence_sources: List[str]
    distance_from_zone_ticks: int
    is_valid_entry: bool

@dataclass
class MinuteBarData:
    """1-minute OHLCV data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None

@dataclass
class TradeMetrics:
    """Comprehensive trade analysis metrics for manual trades"""
    # Price extremes
    max_favorable_excursion: float
    max_adverse_excursion: float
    mfe_r_multiple: float
    mae_r_multiple: float
    
    # Exit analysis
    actual_exit_time: datetime
    exit_reason: ExitReason
    minutes_to_target: Optional[int]
    minutes_to_stop: Optional[int]
    minutes_to_exit: int
    
    # Performance
    trade_result: float
    r_multiple: float
    efficiency_ratio: float
    
    # Price levels
    highest_price: float
    lowest_price: float
    first_profitable_minute: Optional[int]
    first_negative_minute: Optional[int]
    total_minutes_in_trade: Optional[int] = None
    pivot_strength: Optional[int] = None

@dataclass
class ValidationResult:
    """Trade input validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)