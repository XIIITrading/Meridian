Consolidated Polygon Client Requirements
Overview
Create a single, unified Polygon client that serves all three trading tools (Confluence Scanner, Fractal Engine, HVN Engine) with consistent interfaces and error handling.
Core Configuration
pythonclass PolygonClientConfig:
    """Centralized configuration"""
    BASE_URL = "http://localhost:8200"
    API_VERSION = "/api/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF = 1.0
    
    # Standardized timeframe mappings
    TIMEFRAME_MAPPINGS = {
        # Input variants -> Standard format
        '1min': '1min',
        '1minute': '1min',
        '5min': '5min',
        '5minute': '5min',
        '5minutes': '5min',
        '10min': '10min',
        '10minute': '10min',
        '15min': '15min',
        '15minute': '15min',
        '15minutes': '15min',
        '30min': '30min',
        '30minute': '30min',
        '60min': '60min',
        '1hour': '60min',
        '120min': '120min',
        '2hour': '120min',
        '2hours': '120min',
        'day': '1day',
        '1day': '1day',
        'daily': '1day'
    }
Input Requirements
1. Connection Management
pythondef __init__(self, 
             base_url: str = None,
             timeout: int = None,
             max_retries: int = None,
             enable_caching: bool = True):
    """
    Args:
        base_url: Override default base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        enable_caching: Enable response caching
    """
2. Core Data Fetching
pythondef fetch_bars(self,
               symbol: str,
               start_date: Union[str, date, datetime],
               end_date: Union[str, date, datetime],
               timeframe: str,
               limit: Optional[int] = None,
               include_extended: bool = True,
               use_cache: bool = True) -> pd.DataFrame:
    """
    Unified bar fetching method
    
    Args:
        symbol: Stock ticker (automatically uppercased)
        start_date: Start date (handles multiple formats)
        end_date: End date (handles multiple formats)
        timeframe: Bar timeframe (automatically standardized)
        limit: Maximum bars to return
        include_extended: Include pre/post market data
        use_cache: Use cached data if available
    
    Returns:
        DataFrame with columns: [open, high, low, close, volume, timestamp]
        Index: timestamp (timezone-aware UTC)
    """
3. Specialized Endpoints
pythondef validate_ticker(self, symbol: str) -> bool:
    """Validate if ticker symbol exists"""

def get_latest_price(self, symbol: str) -> Optional[Decimal]:
    """Get most recent price for symbol"""

def get_candle_at_datetime(self, 
                           symbol: str,
                           target_datetime: datetime,
                           timeframe: str = '15min',
                           tolerance_minutes: int = 30) -> Optional[Dict]:
    """Get specific candle nearest to target datetime"""

def search_symbols(self, 
                  query: str,
                  active_only: bool = True) -> List[Dict]:
    """Search for symbols by name or ticker"""

def clear_cache(self, symbol: Optional[str] = None) -> bool:
    """Clear cache for specific symbol or all"""
Output Format Specifications
1. Standard Bar Data Output
python# DataFrame format
{
    'timestamp': pd.DatetimeIndex,  # UTC timezone-aware
    'open': float,
    'high': float,
    'low': float,
    'close': float,
    'volume': int
}
2. Candle Data Output
python{
    'datetime': datetime,  # UTC
    'open': Decimal,
    'high': Decimal,
    'low': Decimal,
    'close': Decimal,
    'volume': int,
    'vwap': Optional[Decimal]  # Volume-weighted average price
}
3. Session Data Output
python{
    'symbol': str,
    'session_datetime': datetime,
    'current_price': Decimal,
    'pre_market_price': Optional[Decimal],
    'open_price': Optional[Decimal],
    'atr_5min': Decimal,
    'atr_2hour': Decimal,  # Changed from atr_10min
    'atr_15min': Decimal,
    'daily_atr': Decimal,
    'atr_high': Decimal,
    'atr_low': Decimal,
    'error': Optional[str]
}
REST API Endpoints
Required Server Endpoints
pythonENDPOINTS = {
    # Connection & Validation
    'rate_limit': 'GET /api/v1/rate-limit',
    'validate': 'POST /api/v1/validate',
    
    # Market Data
    'bars': 'POST /api/v1/bars',
    'latest_price': 'GET /api/v1/latest/{symbol}',
    
    # Search & Discovery
    'search': 'GET /api/v1/search',
    
    # Cache Management
    'clear_cache': 'DELETE /api/v1/cache'
}
Request/Response Formats
Bars Request
python{
    "symbol": "AAPL",
    "timeframe": "5min",  # Standardized format
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "limit": 5000,
    "use_cache": true,
    "validate": false
}
Bars Response
python{
    "data": [
        {
            "timestamp": "2024-01-01T09:30:00Z",
            "open": 189.50,
            "high": 190.25,
            "low": 189.25,
            "close": 190.00,
            "volume": 1250000
        }
    ],
    "metadata": {
        "symbol": "AAPL",
        "timeframe": "5min",
        "count": 390
    }
}
Error Handling
pythonclass PolygonClientError(Exception):
    """Base exception for Polygon client"""
    pass

class ConnectionError(PolygonClientError):
    """Failed to connect to Polygon server"""
    pass

class DataFetchError(PolygonClientError):
    """Failed to fetch market data"""
    pass

class ValidationError(PolygonClientError):
    """Invalid input parameters"""
    pass
Caching Strategy
pythonclass CacheManager:
    """LRU cache with TTL"""
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 5):
        self.cache = {}  # key: (data, timestamp)
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get_cache_key(self, symbol: str, timeframe: str, 
                      start: str, end: str) -> str:
        return f"{symbol}_{timeframe}_{start}_{end}"
Performance Requirements

Concurrent Requests: Support parallel data fetching for multiple timeframes
Retry Logic: Exponential backoff with jitter for failed requests
Rate Limiting: Respect server rate limits (track remaining calls)
Connection Pooling: Reuse HTTP sessions for efficiency

Integration Points
The unified client should seamlessly integrate with:

Confluence Scanner: Zone discovery and validation
Fractal Engine: Swing point detection
HVN Engine: Volume profile analysis
Camarilla Engine: Pivot calculations
Zone Calculators: Weekly/Daily/ATR zones

Implementation Priority
Phase 1: Core Consolidation

Unified data fetching
Standardized timeframe handling
Consistent error handling

Phase 2: Optimization

Implement caching layer
Add parallel processing
Performance monitoring

Phase 3: Advanced Features

Streaming data support
WebSocket integration
Historical data management