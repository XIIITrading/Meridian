"""
Data models for Meridian Trading System
Defines all data structures used throughout the application
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class TrendDirection(Enum):
    """Market trend direction enumeration"""
    BULL = "Bull"
    BEAR = "Bear"
    RANGE = "Range"
    
    @classmethod
    def from_string(cls, value: str) -> 'TrendDirection':
        """Create enum from string value"""
        value_upper = value.upper()
        for trend in cls:
            if trend.name == value_upper:
                return trend
        raise ValueError(f"Invalid trend direction: {value}")


@dataclass
class PriceLevel:
    """Represents a significant price level"""
    line_price: Decimal
    candle_datetime: datetime
    candle_high: Decimal
    candle_low: Decimal
    level_id: str  # UID format: TICKER_ID_L001, TICKER_ID_L002, etc.
    
    def __post_init__(self):
        """Validate price level data"""
        # Convert to Decimal if needed
        self.line_price = Decimal(str(self.line_price))
        self.candle_high = Decimal(str(self.candle_high))
        self.candle_low = Decimal(str(self.candle_low))
        
        # Validate high/low relationship
        if self.candle_high < self.candle_low:
            raise ValueError("Candle high must be >= candle low")
        
        # Validate level_id format (optional)
        if not self.level_id or '_L' not in self.level_id:
            raise ValueError(f"Invalid level_id format: {self.level_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'line_price': str(self.line_price),
            'candle_datetime': self.candle_datetime.isoformat(),
            'candle_high': str(self.candle_high),
            'candle_low': str(self.candle_low),
            'level_id': self.level_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceLevel':
        """Create from dictionary"""
        return cls(
            line_price=Decimal(data['line_price']),
            candle_datetime=datetime.fromisoformat(data['candle_datetime']),
            candle_high=Decimal(data['candle_high']),
            candle_low=Decimal(data['candle_low']),
            level_id=data['level_id']
        )


@dataclass
class WeeklyData:
    """Weekly analysis data"""
    trend_direction: TrendDirection
    internal_trend: TrendDirection
    position_structure: float  # Percentage (0-100)
    eow_bias: TrendDirection  # End of Week bias
    price_levels: List[Decimal] = field(default_factory=list)  # For wl1-wl4
    notes: str = ""
    
    def __post_init__(self):
        """Validate weekly data"""
        # Validate position structure percentage
        if not 0 <= self.position_structure <= 100:
            raise ValueError("Position structure must be between 0 and 100")
        
        # Convert price levels to Decimal
        self.price_levels = [Decimal(str(level)) for level in self.price_levels if level]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'trend_direction': self.trend_direction.value,
            'internal_trend': self.internal_trend.value,
            'position_structure': self.position_structure,
            'eow_bias': self.eow_bias.value,
            'price_levels': [str(level) for level in self.price_levels],
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklyData':
        """Create from dictionary"""
        return cls(
            trend_direction=TrendDirection(data['trend_direction']),
            internal_trend=TrendDirection(data['internal_trend']),
            position_structure=float(data['position_structure']),
            eow_bias=TrendDirection(data['eow_bias']),
            price_levels=[Decimal(level) for level in data.get('price_levels', [])],
            notes=data.get('notes', '')
        )


@dataclass
class DailyData:
    """Daily analysis data"""
    trend_direction: TrendDirection
    internal_trend: TrendDirection
    position_structure: float  # Percentage (0-100)
    eod_bias: TrendDirection  # End of Day bias
    price_levels: List[Decimal] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """Validate daily data"""
        # Validate position structure percentage
        if not 0 <= self.position_structure <= 100:
            raise ValueError("Position structure must be between 0 and 100")
        
        # Convert price levels to Decimal
        self.price_levels = [Decimal(str(level)) for level in self.price_levels]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'trend_direction': self.trend_direction.value,
            'internal_trend': self.internal_trend.value,
            'position_structure': self.position_structure,
            'eod_bias': self.eod_bias.value,
            'price_levels': [str(level) for level in self.price_levels],
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyData':
        """Create from dictionary"""
        return cls(
            trend_direction=TrendDirection(data['trend_direction']),
            internal_trend=TrendDirection(data['internal_trend']),
            position_structure=float(data['position_structure']),
            eod_bias=TrendDirection(data['eod_bias']),
            price_levels=[Decimal(level) for level in data.get('price_levels', [])],
            notes=data.get('notes', '')
        )


@dataclass
class TradingSession:
    """Complete trading session data"""
    # Identification
    ticker: str
    date: date
    ticker_id: str = field(init=False)  # Generated: TICKER.MMDDYY
    
    # Session type
    is_live: bool = True
    historical_date: Optional[date] = None
    historical_time: Optional[time] = None
    
    # Analysis data
    weekly_data: Optional[WeeklyData] = None
    daily_data: Optional[DailyData] = None
    m15_levels: List[PriceLevel] = field(default_factory=list)
    
    # Metrics (all stored as strings for Decimal precision)
    pre_market_price: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_5min: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_2hour: Decimal = field(default_factory=lambda: Decimal("0.00"))  # CHANGED from atr_10min
    atr_15min: Decimal = field(default_factory=lambda: Decimal("0.00"))
    daily_atr: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    # Calculated fields
    atr_high: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_low: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Generate ticker_id and validate data"""
        # Generate ticker_id
        self.ticker_id = f"{self.ticker.upper()}.{self.date.strftime('%m%d%y')}"
        
        # Validate ticker
        if not self.ticker or len(self.ticker) > 10:
            raise ValueError("Invalid ticker symbol")
        
        # Convert all price fields to Decimal
        self.pre_market_price = Decimal(str(self.pre_market_price))
        self.atr_5min = Decimal(str(self.atr_5min))
        self.atr_2hour = Decimal(str(self.atr_2hour))  # CHANGED from atr_10min
        self.atr_15min = Decimal(str(self.atr_15min))
        self.daily_atr = Decimal(str(self.daily_atr))
        self.atr_high = Decimal(str(self.atr_high))
        self.atr_low = Decimal(str(self.atr_low))
        
        # Validate M15 levels count (max 6: 3 above, 3 below)
        if len(self.m15_levels) > 6:
            raise ValueError("Maximum 6 M15 levels allowed (3 above, 3 below)")

    def calculate_atr_bands(self):
        """Calculate ATR high and low bands"""
        if self.pre_market_price > 0 and self.daily_atr > 0:
            self.atr_high = self.pre_market_price + self.daily_atr
            self.atr_low = self.pre_market_price - self.daily_atr
        else:
            # Don't calculate if we don't have the required data
            self.atr_high = Decimal("0.00")
            self.atr_low = Decimal("0.00")
    
    def get_levels_sorted_by_price(self, ascending: bool = True) -> List[PriceLevel]:
        """Get all price levels sorted by price"""
        return sorted(
            self.m15_levels,
            key=lambda x: x.line_price,
            reverse=not ascending
        )
    
    def get_levels_above_price(self, price: Decimal) -> List[PriceLevel]:
        """Get price levels above a given price"""
        return sorted(
            [level for level in self.m15_levels if level.line_price > price],
            key=lambda x: x.line_price
        )
    
    def get_levels_below_price(self, price: Decimal) -> List[PriceLevel]:
        """Get price levels below a given price"""
        return sorted(
            [level for level in self.m15_levels if level.line_price < price],
            key=lambda x: x.line_price,
            reverse=True
        )
    
    def generate_level_id(self, level_count: int) -> str:
        """Generate a unique level ID for a new price level"""
        return f"{self.ticker_id}_L{str(level_count + 1).zfill(3)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ticker': self.ticker,
            'date': self.date.isoformat(),
            'ticker_id': self.ticker_id,
            'is_live': self.is_live,
            'historical_date': self.historical_date.isoformat() if self.historical_date else None,
            'historical_time': self.historical_time.isoformat() if self.historical_time else None,
            'weekly_data': self.weekly_data.to_dict() if self.weekly_data else None,
            'daily_data': self.daily_data.to_dict() if self.daily_data else None,
            'm15_levels': [level.to_dict() for level in self.m15_levels],
            'pre_market_price': str(self.pre_market_price),
            'atr_5min': str(self.atr_5min),
            'atr_2hour': str(self.atr_2hour),  # CHANGED from atr_10min
            'atr_15min': str(self.atr_15min),
            'daily_atr': str(self.daily_atr),
            'atr_high': str(self.atr_high),
            'atr_low': str(self.atr_low),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingSession':
        """Create from dictionary"""
        session = cls(
            ticker=data['ticker'],
            date=date.fromisoformat(data['date']),
            is_live=data.get('is_live', True)
        )
        
        # Set optional dates
        if data.get('historical_date'):
            session.historical_date = date.fromisoformat(data['historical_date'])
        if data.get('historical_time'):
            session.historical_time = time.fromisoformat(data['historical_time'])
        
        # Set analysis data
        if data.get('weekly_data'):
            session.weekly_data = WeeklyData.from_dict(data['weekly_data'])
        if data.get('daily_data'):
            session.daily_data = DailyData.from_dict(data['daily_data'])
        
        # Set M15 levels
        session.m15_levels = [
            PriceLevel.from_dict(level) for level in data.get('m15_levels', [])
        ]
        
        # Set metrics
        session.pre_market_price = Decimal(data.get('pre_market_price', '0'))
        session.atr_5min = Decimal(data.get('atr_5min', '0'))
        session.atr_2hour = Decimal(data.get('atr_2hour', '0'))  # CHANGED from atr_10min
        session.atr_15min = Decimal(data.get('atr_15min', '0'))
        session.daily_atr = Decimal(data.get('daily_atr', '0'))
        session.atr_high = Decimal(data.get('atr_high', '0'))
        session.atr_low = Decimal(data.get('atr_low', '0'))
        
        # Set timestamps
        if data.get('created_at'):
            session.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            session.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return session


# Additional model for calculated metrics
@dataclass
class CalculatedMetrics:
    """Container for calculated metrics"""
    session_id: str
    hvn_zones: List[Dict[str, Any]] = field(default_factory=list)
    camarilla_pivots: Dict[str, Decimal] = field(default_factory=dict)
    confluence_scores: List[Dict[str, Any]] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'hvn_zones': self.hvn_zones,
            'camarilla_pivots': {k: str(v) for k, v in self.camarilla_pivots.items()},
            'confluence_scores': self.confluence_scores,
            'calculated_at': self.calculated_at.isoformat()
        }