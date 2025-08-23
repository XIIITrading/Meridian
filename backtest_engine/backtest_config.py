"""
Backtest Engine Configuration
Inherits from main Meridian system with backtesting-specific additions
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import json
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from {env_path}")
else:
    print(f"⚠️ No .env file found at {env_path}")

# Base paths
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
POLYGON_CACHE_DIR = CACHE_DIR / "polygon_data"

@dataclass
class BacktestConfig:
    """Backtesting-specific configuration"""
    
    # Trading Hours (in UTC)
    BACKTEST_START_HOUR: float = 14.5  # 2:30 PM UTC (9:30 AM ET Standard)
    BACKTEST_END_HOUR: float = 21.0    # 9:00 PM UTC (4:00 PM ET Standard)
    BACKTEST_START_HOUR_DST: float = 13.5  # 1:30 PM UTC (9:30 AM EDT)
    BACKTEST_END_HOUR_DST: float = 20.0    # 8:00 PM UTC (4:00 PM EDT)
    PRE_MARKET_START_HOUR: float = 9.0  # 9:00 AM UTC (4:00 AM ET Standard)
    AFTER_HOURS_END_HOUR: float = 1.0   # 1:00 AM UTC next day (8:00 PM ET)
    
    # Risk Management Defaults
    FIXED_RISK_AMOUNT: float = 250.0  # Fixed risk per trade
    DEFAULT_STOP_MULTIPLIER: float = 1.5  # 1.5x ATR for stop loss
    DEFAULT_TARGET_ZONES: int = 2  # Target next 2 confluence zones
    MAX_TRADE_DURATION_HOURS: float = 6.5  # Maximum time in trade
    DEFAULT_POSITION_SIZE: int = 100  # Default shares per trade
    
    # Entry Criteria
    MAX_DISTANCE_TO_ZONE_TICKS: float = 5.0  # Maximum ticks from zone for valid entry
    MIN_CONFLUENCE_LEVEL: str = "L3"  # Minimum confluence for entry
    MIN_PIVOT_STRENGTH: int = 1  # Minimum pivot strength (1-3)
    
    # Exit Rules
    BREAKEVEN_AFTER_R: float = 1.0  # Move stop to breakeven after 1R profit
    TRAIL_STOP_AFTER_TARGET1: bool = True  # Trail stop after first target
    TIME_EXIT_MINUTES_BEFORE_CLOSE: int = 10  # Exit 10 minutes before close
    
    # Performance Thresholds
    MIN_WIN_RATE_FOR_LIVE: float = 0.40  # 40% win rate minimum
    MIN_PROFIT_FACTOR: float = 1.2  # Minimum profit factor
    MIN_TRADES_FOR_VALIDATION: int = 30  # Minimum trades for statistical significance
    
    # Cache Settings
    CACHE_DIRECTORY: str = str(POLYGON_CACHE_DIR)
    CACHE_EXPIRY_DAYS: int = 30  # Keep cached data for 30 days
    USE_CACHE: bool = True  # Use local cache for Polygon data
    
    # Processing Settings
    PARALLEL_PROCESSING: bool = True  # Use multiprocessing for batch operations
    MAX_WORKERS: int = 4  # Maximum parallel workers
    BATCH_SIZE: int = 100  # Trades per batch for processing
    
    # Timezone settings
    DATA_TIMEZONE: str = "UTC"  # All data stored in UTC
    DISPLAY_TIMEZONE: str = "America/New_York"  # For UI display
    
    # UI Settings
    CHART_CANDLE_COUNT: int = 78  # Number of M5 candles to show (6.5 hours)
    ZONE_COLORS: dict = None  # Will be set in __post_init__
    
    def __post_init__(self):
        """Initialize complex default values"""
        if self.ZONE_COLORS is None:
            self.ZONE_COLORS = {
                "L1": "#ffcccc",  # Light red
                "L2": "#ffaaaa",  # 
                "L3": "#ff8888",  # Medium red
                "L4": "#ff6666",  # 
                "L5": "#ff4444",  # Strong red
            }
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def save(self, filepath: str = "backtest_config.json"):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, filepath: str = "backtest_config.json") -> 'BacktestConfig':
        """Load configuration from JSON file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


class MeridianConfig:
    """
    Main Meridian system configuration
    This should be imported/adapted from your main system
    """
    
    # Database Configuration (from environment variables)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Polygon.io Configuration
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    
    # System Settings
    TIMEZONE: str = "America/New_York"
    LOG_LEVEL: str = "INFO"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = ["SUPABASE_URL", "SUPABASE_KEY", "POLYGON_API_KEY"]
        missing = []
        
        for field in required:
            if not getattr(cls, field):
                missing.append(field)
        
        if missing:
            print(f"❌ Missing required configuration: {', '.join(missing)}")
            print("Please set these environment variables or update config.py")
            return False
        
        return True


# Create singleton instances
backtest_config = BacktestConfig()
meridian_config = MeridianConfig()

# Add BACKTEST_CONFIG dictionary for backward compatibility
BACKTEST_CONFIG = {
    'FIXED_RISK_AMOUNT': backtest_config.FIXED_RISK_AMOUNT,
    'DEFAULT_COMMISSION': 0.00,
    'DEFAULT_SLIPPAGE_TICKS': 0,
    'MARKET_OPEN': '14:30',  # UTC
    'MARKET_CLOSE': '21:00',  # UTC
    'MINUTE_DATA_BUFFER': 5,
    'MAX_ZONE_DISTANCE_TICKS': backtest_config.MAX_DISTANCE_TO_ZONE_TICKS,
    'MIN_CONFLUENCE_LEVEL': 2,
    'MIN_TRADES_FOR_SIGNIFICANCE': backtest_config.MIN_TRADES_FOR_VALIDATION,
    'CACHE_DIRECTORY': Path(backtest_config.CACHE_DIRECTORY) / 'minute_data',
    'CACHE_EXPIRY_DAYS': backtest_config.CACHE_EXPIRY_DAYS,
    'DATA_TIMEZONE': 'UTC',
}

# Validate on import
if not meridian_config.validate():
    print("⚠️ Warning: Some configuration values are missing")

# Create cache directories if they don't exist
CACHE_DIR.mkdir(exist_ok=True)
POLYGON_CACHE_DIR.mkdir(exist_ok=True)
(Path(backtest_config.CACHE_DIRECTORY) / 'minute_data').mkdir(parents=True, exist_ok=True)

print(f"✅ Configuration loaded. Cache directory: {POLYGON_CACHE_DIR}")