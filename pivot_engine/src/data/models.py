"""
Data models for Meridian Trading System
Defines all data structures used throughout the application
UPDATED: Pure Pivot Confluence System - M15 zones removed
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
class PivotConfluenceData:
    """Container for pivot confluence analysis results and settings"""
    # Daily Camarilla pivot prices (base zones)
    daily_cam_r6_price: Optional[Decimal] = None
    daily_cam_r4_price: Optional[Decimal] = None
    daily_cam_r3_price: Optional[Decimal] = None
    daily_cam_s3_price: Optional[Decimal] = None
    daily_cam_s4_price: Optional[Decimal] = None
    daily_cam_s6_price: Optional[Decimal] = None
    
    # Zone ranges (pivot ± 5min ATR)
    daily_cam_r6_zone_low: Optional[Decimal] = None
    daily_cam_r6_zone_high: Optional[Decimal] = None
    daily_cam_r4_zone_low: Optional[Decimal] = None
    daily_cam_r4_zone_high: Optional[Decimal] = None
    daily_cam_r3_zone_low: Optional[Decimal] = None
    daily_cam_r3_zone_high: Optional[Decimal] = None
    daily_cam_s3_zone_low: Optional[Decimal] = None
    daily_cam_s3_zone_high: Optional[Decimal] = None
    daily_cam_s4_zone_low: Optional[Decimal] = None
    daily_cam_s4_zone_high: Optional[Decimal] = None
    daily_cam_s6_zone_low: Optional[Decimal] = None
    daily_cam_s6_zone_high: Optional[Decimal] = None
    
    # Confluence scores and levels
    daily_cam_r6_confluence_score: Optional[Decimal] = None
    daily_cam_r6_confluence_level: Optional[str] = None
    daily_cam_r6_confluence_count: Optional[int] = None
    daily_cam_r4_confluence_score: Optional[Decimal] = None
    daily_cam_r4_confluence_level: Optional[str] = None
    daily_cam_r4_confluence_count: Optional[int] = None
    daily_cam_r3_confluence_score: Optional[Decimal] = None
    daily_cam_r3_confluence_level: Optional[str] = None
    daily_cam_r3_confluence_count: Optional[int] = None
    daily_cam_s3_confluence_score: Optional[Decimal] = None
    daily_cam_s3_confluence_level: Optional[str] = None
    daily_cam_s3_confluence_count: Optional[int] = None
    daily_cam_s4_confluence_score: Optional[Decimal] = None
    daily_cam_s4_confluence_level: Optional[str] = None
    daily_cam_s4_confluence_count: Optional[int] = None
    daily_cam_s6_confluence_score: Optional[Decimal] = None
    daily_cam_s6_confluence_level: Optional[str] = None
    daily_cam_s6_confluence_count: Optional[int] = None
    
    # Settings and results
    pivot_confluence_settings: Optional[str] = None  # JSON string
    pivot_confluence_text: Optional[str] = None  # Formatted display text
    
    def __post_init__(self):
        """Convert all price fields to Decimal"""
        for field_name in self.__annotations__:
            if field_name.endswith('_price') or field_name.endswith('_low') or field_name.endswith('_high') or field_name.endswith('_score'):
                value = getattr(self, field_name)
                if value is not None:
                    setattr(self, field_name, Decimal(str(value)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        for field_name, value in asdict(self).items():
            if isinstance(value, Decimal):
                result[field_name] = str(value)
            else:
                result[field_name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PivotConfluenceData':
        """Create from dictionary"""
        instance = cls()
        for field_name, value in data.items():
            if hasattr(instance, field_name) and value is not None:
                if field_name.endswith('_price') or field_name.endswith('_low') or field_name.endswith('_high') or field_name.endswith('_score'):
                    setattr(instance, field_name, Decimal(str(value)))
                else:
                    setattr(instance, field_name, value)
        return instance


@dataclass
class TradingSession:
    """Complete trading session data - Pure Pivot Confluence System"""
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
    
    # Pivot confluence data (NEW - replaces M15 levels)
    pivot_confluence_data: Optional[PivotConfluenceData] = None
    
    # Metrics (all stored as Decimal for precision)
    pre_market_price: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_5min: Decimal = field(default_factory=lambda: Decimal("0.00"))  # CRITICAL for pivot zones
    atr_2hour: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_15min: Decimal = field(default_factory=lambda: Decimal("0.00"))
    daily_atr: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    # Calculated fields
    atr_high: Decimal = field(default_factory=lambda: Decimal("0.00"))
    atr_low: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    # Analysis results (transient - not stored in database)
    pivot_confluence_results: Optional[Any] = field(default=None, init=False)  # Raw analysis object
    pivot_confluence_settings: Optional[str] = field(default=None, init=False)  # UI settings JSON
    pivot_confluence_text: Optional[str] = field(default=None, init=False)  # Formatted display text
    
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
        self.atr_2hour = Decimal(str(self.atr_2hour))
        self.atr_15min = Decimal(str(self.atr_15min))
        self.daily_atr = Decimal(str(self.daily_atr))
        self.atr_high = Decimal(str(self.atr_high))
        self.atr_low = Decimal(str(self.atr_low))

    def calculate_atr_bands(self):
        """Calculate ATR high and low bands"""
        if self.pre_market_price > 0 and self.daily_atr > 0:
            self.atr_high = self.pre_market_price + self.daily_atr
            self.atr_low = self.pre_market_price - self.daily_atr
        else:
            # Don't calculate if we don't have the required data
            self.atr_high = Decimal("0.00")
            self.atr_low = Decimal("0.00")
    
    def get_pivot_levels_sorted_by_price(self, ascending: bool = True) -> List[tuple]:
        """Get all pivot levels sorted by price (level_name, price)"""
        if not self.pivot_confluence_data:
            return []
        
        levels = []
        level_fields = [
            ('R6', self.pivot_confluence_data.daily_cam_r6_price),
            ('R4', self.pivot_confluence_data.daily_cam_r4_price),
            ('R3', self.pivot_confluence_data.daily_cam_r3_price),
            ('S3', self.pivot_confluence_data.daily_cam_s3_price),
            ('S4', self.pivot_confluence_data.daily_cam_s4_price),
            ('S6', self.pivot_confluence_data.daily_cam_s6_price)
        ]
        
        for level_name, price in level_fields:
            if price and price > 0:
                levels.append((level_name, price))
        
        return sorted(levels, key=lambda x: x[1], reverse=not ascending)
    
    def get_pivot_levels_above_price(self, price: Decimal) -> List[tuple]:
        """Get pivot levels above a given price"""
        all_levels = self.get_pivot_levels_sorted_by_price()
        return [(name, p) for name, p in all_levels if p > price]
    
    def get_pivot_levels_below_price(self, price: Decimal) -> List[tuple]:
        """Get pivot levels below a given price"""
        all_levels = self.get_pivot_levels_sorted_by_price()
        return [(name, p) for name, p in all_levels if p < price]
    
    def get_pivot_confluence_summary(self) -> Dict[str, Any]:
        """Get summary of pivot confluence data"""
        if not self.pivot_confluence_data:
            return {'pivot_count': 0, 'zones_with_confluence': 0}
        
        pivot_count = 0
        zones_with_confluence = 0
        
        levels = ['r6', 'r4', 'r3', 's3', 's4', 's6']
        for level in levels:
            price_attr = f'daily_cam_{level}_price'
            score_attr = f'daily_cam_{level}_confluence_score'
            
            if (hasattr(self.pivot_confluence_data, price_attr) and 
                getattr(self.pivot_confluence_data, price_attr)):
                pivot_count += 1
                
                if (hasattr(self.pivot_confluence_data, score_attr) and 
                    getattr(self.pivot_confluence_data, score_attr) and
                    getattr(self.pivot_confluence_data, score_attr) > 0):
                    zones_with_confluence += 1
        
        return {
            'pivot_count': pivot_count,
            'zones_with_confluence': zones_with_confluence
        }
    
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
            'pivot_confluence_data': self.pivot_confluence_data.to_dict() if self.pivot_confluence_data else None,
            'pre_market_price': str(self.pre_market_price),
            'atr_5min': str(self.atr_5min),
            'atr_2hour': str(self.atr_2hour),
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
        if data.get('pivot_confluence_data'):
            session.pivot_confluence_data = PivotConfluenceData.from_dict(data['pivot_confluence_data'])
        
        # Set metrics
        session.pre_market_price = Decimal(data.get('pre_market_price', '0'))
        session.atr_5min = Decimal(data.get('atr_5min', '0'))
        session.atr_2hour = Decimal(data.get('atr_2hour', '0'))
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


@dataclass
class PivotCalculatedMetrics:
    """Container for calculated pivot confluence metrics"""
    session_id: str
    hvn_zones: List[Dict[str, Any]] = field(default_factory=list)
    camarilla_pivots: Dict[str, Decimal] = field(default_factory=dict)
    pivot_confluence_zones: List[Dict[str, Any]] = field(default_factory=list)
    confluence_sources: Dict[str, int] = field(default_factory=dict)  # Source counts
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'hvn_zones': self.hvn_zones,
            'camarilla_pivots': {k: str(v) for k, v in self.camarilla_pivots.items()},
            'pivot_confluence_zones': self.pivot_confluence_zones,
            'confluence_sources': self.confluence_sources,
            'calculated_at': self.calculated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PivotCalculatedMetrics':
        """Create from dictionary"""
        return cls(
            session_id=data['session_id'],
            hvn_zones=data.get('hvn_zones', []),
            camarilla_pivots={k: Decimal(v) for k, v in data.get('camarilla_pivots', {}).items()},
            pivot_confluence_zones=data.get('pivot_confluence_zones', []),
            confluence_sources=data.get('confluence_sources', {}),
            calculated_at=datetime.fromisoformat(data.get('calculated_at', datetime.now().isoformat()))
        )


# Utility functions for pivot confluence
def create_pivot_confluence_summary(session: TradingSession) -> Dict[str, Any]:
    """Create a summary of pivot confluence data for reporting"""
    if not session.pivot_confluence_data:
        return {'error': 'No pivot confluence data available'}
    
    summary = {
        'ticker': session.ticker,
        'date': session.date.isoformat(),
        'pivot_levels': {},
        'confluence_summary': session.get_pivot_confluence_summary()
    }
    
    # Add individual pivot data
    levels = [
        ('R6', 'daily_cam_r6_price', 'daily_cam_r6_confluence_score', 'daily_cam_r6_confluence_level'),
        ('R4', 'daily_cam_r4_price', 'daily_cam_r4_confluence_score', 'daily_cam_r4_confluence_level'),
        ('R3', 'daily_cam_r3_price', 'daily_cam_r3_confluence_score', 'daily_cam_r3_confluence_level'),
        ('S3', 'daily_cam_s3_price', 'daily_cam_s3_confluence_score', 'daily_cam_s3_confluence_level'),
        ('S4', 'daily_cam_s4_price', 'daily_cam_s4_confluence_score', 'daily_cam_s4_confluence_level'),
        ('S6', 'daily_cam_s6_price', 'daily_cam_s6_confluence_score', 'daily_cam_s6_confluence_level')
    ]
    
    for level_name, price_attr, score_attr, level_attr in levels:
        price = getattr(session.pivot_confluence_data, price_attr, None)
        score = getattr(session.pivot_confluence_data, score_attr, None)
        level = getattr(session.pivot_confluence_data, level_attr, None)
        
        if price:
            summary['pivot_levels'][level_name] = {
                'price': str(price),
                'confluence_score': str(score) if score else '0',
                'confluence_level': level or 'L1'
            }
    
    return summary


def validate_pivot_confluence_data(data: PivotConfluenceData) -> tuple[bool, List[str]]:
    """Validate pivot confluence data integrity"""
    errors = []
    
    # Check that we have at least some pivot prices
    pivot_prices = [
        data.daily_cam_r6_price, data.daily_cam_r4_price, data.daily_cam_r3_price,
        data.daily_cam_s3_price, data.daily_cam_s4_price, data.daily_cam_s6_price
    ]
    
    valid_prices = [p for p in pivot_prices if p and p > 0]
    if not valid_prices:
        errors.append("No valid pivot prices found")
    
    # Check price ordering (R6 > R4 > R3 and S3 > S4 > S6)
    resistance_prices = [
        (data.daily_cam_r6_price, 'R6'),
        (data.daily_cam_r4_price, 'R4'),
        (data.daily_cam_r3_price, 'R3')
    ]
    
    valid_resistance = [(p, n) for p, n in resistance_prices if p and p > 0]
    if len(valid_resistance) >= 2:
        valid_resistance.sort(key=lambda x: x[0], reverse=True)
        expected_order = ['R6', 'R4', 'R3']
        actual_order = [n for p, n in valid_resistance]
        
        # Check if they follow the expected descending order
        for i, level in enumerate(actual_order):
            if level in expected_order:
                expected_idx = expected_order.index(level)
                if i < expected_idx:
                    errors.append(f"Resistance levels out of order: {level} should not be higher than previous levels")
    
    support_prices = [
        (data.daily_cam_s3_price, 'S3'),
        (data.daily_cam_s4_price, 'S4'),
        (data.daily_cam_s6_price, 'S6')
    ]
    
    valid_support = [(p, n) for p, n in support_prices if p and p > 0]
    if len(valid_support) >= 2:
        valid_support.sort(key=lambda x: x[0], reverse=True)
        expected_order = ['S3', 'S4', 'S6']
        actual_order = [n for p, n in valid_support]
        
        # Check if they follow the expected descending order
        for i, level in enumerate(actual_order):
            if level in expected_order:
                expected_idx = expected_order.index(level)
                if i < expected_idx:
                    errors.append(f"Support levels out of order: {level} should not be higher than previous levels")
    
    return len(errors) == 0, errors