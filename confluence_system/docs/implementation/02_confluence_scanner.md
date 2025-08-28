Confluence Scanner Technical Documentation
Overview
The Confluence Scanner is a market analysis module designed to identify high-probability price zones where multiple technical indicators converge. It processes fractal swing points, volume profiles, pivot calculations, and ATR-based levels to discover zones with significant technical confluence.
Architecture
Module Structure
confluence_scanner/
├── orchestrator.py              # Main coordination and API entry point
├── scanner/
│   └── zone_scanner.py         # Core scanning engine
├── calculations/               # Technical calculation engines
│   ├── fractals/              # Fractal integration
│   │   └── fractal_integration.py
│   ├── pivots/                # Pivot calculations
│   │   └── camarilla_engine.py
│   ├── volume/                # Volume profile analysis
│   │   ├── hvn_engine.py
│   │   └── volume_profile.py
│   └── zones/                 # Zone calculations
│       ├── atr_zone_calc.py
│       ├── daily_zone_calc.py
│       └── weekly_zone_calc.py
├── discovery/                  # Zone discovery engine
│   ├── zone_discovery.py
│   └── zone_validation.py
├── data/                      # Data interfaces
│   ├── polygon_client.py
│   └── market_metrics.py
└── config.py                  # Configuration settings
Data Flow
Input Sources → Confluence Items → Zone Discovery → Validation → Output
     ↓              ↓                    ↓              ↓          ↓
  Fractals      Standardized        Clustering     M15 Candle   Scored
  HVN Peaks      Price Zones         Algorithm     Association   Zones
  Pivots                                            Recency
  Levels                                            Scoring
Core Components
1. Confluence Orchestrator
Primary interface for external systems. Manages initialization, coordinates sub-components, and handles fractal integration.
pythonfrom confluence_scanner.orchestrator import ConfluenceOrchestrator

orchestrator = ConfluenceOrchestrator()
orchestrator.initialize()

result = orchestrator.run_analysis(
    symbol="SPY",
    analysis_datetime=datetime(2025, 8, 27, 14, 30, 0),
    fractal_data=fractal_results,  # From fractal_engine
    weekly_levels=[450.0, 445.0, 440.0],
    daily_levels=[455.0, 452.0, 448.0]
)
2. Zone Scanner
Core scanning engine that collects confluence items from multiple sources and coordinates zone discovery.
Key responsibilities:

Fetches market data via Polygon client
Calculates metrics (ATR values, scan range)
Collects confluence items from all calculation engines
Triggers zone discovery algorithm
Associates zones with M15 candles for validation

3. Calculation Engines
HVN Engine (High Volume Nodes)
Identifies volume peaks in price profiles across multiple timeframes.
Configuration:

Levels: 100 price levels for volume distribution
Timeframes: 30-day, 14-day, 7-day analysis
Peak detection: Scipy signal processing with prominence filtering
Market hours: Includes pre/post market data

Camarilla Pivot Engine
Calculates traditional Camarilla pivot points for daily, weekly, and monthly timeframes.
Key levels tracked:

R6, R5, R4, R3 (Resistance levels)
S3, S4, S5, S6 (Support levels)
Zone width varies by timeframe (0.5x to 2x M15 ATR)

Fractal Integration
Converts fractal swing points into confluence items.
Process:

Receives fractals from fractal_engine
Creates zones using 0.5x M15 ATR around each fractal price
Maintains fractal type (high/low) for zone association
Associates fractals with discovered zones post-discovery

4. Zone Discovery Engine
Discovery Algorithm
python# Simplified algorithm flow
1. Group confluence items by price proximity
2. Cluster items within 0.5x M15 ATR distance
3. Calculate confluence score:
   score = count * strength_multiplier * recency_boost
4. Filter zones by minimum confluence (≥2 sources)
5. Rank zones by score and distance to current price
Confluence Levels

L1 (Low): 2-3 confluence sources
L2 (Medium-Low): 4-5 sources
L3 (Medium): 6-7 sources
L4 (Medium-High): 8-9 sources
L5 (High): 10+ sources

Zone Validation
Zones are validated through M15 candle association:

Searches 30 days of 15-minute bars
Calculates overlap percentage
Applies recency scoring (5-day: 2x, 10-day: 1.5x, 20-day: 1.2x)
Filters for minimum 20% overlap

Configuration
Scanner Configuration (config.py)
pythonclass ScannerConfig:
    # Zone Discovery
    MIN_CONFLUENCE_SOURCES = 2
    ZONE_CLUSTER_THRESHOLD = 0.5  # x M15 ATR
    
    # Scan Range
    SCAN_RANGE_MULTIPLIER = 2.0  # x Daily ATR
    
    # HVN Settings
    HVN_LEVELS = 100
    HVN_PERCENTILE_THRESHOLD = 80.0
    HVN_TIMEFRAMES = [30, 14, 7]
    
    # Camarilla Settings
    CAMARILLA_KEY_LEVELS = {'R6', 'R5', 'R4', 'R3', 'S3', 'S4', 'S5', 'S6'}
    
    # M15 Candle Validation
    MIN_OVERLAP_PERCENT = 20.0
    CANDLE_LOOKBACK_DAYS = 30
    
    # Recency Multipliers
    RECENCY_5_DAY = 2.0
    RECENCY_10_DAY = 1.5
    RECENCY_20_DAY = 1.2
API Reference
ConfluenceOrchestrator.run_analysis()
pythondef run_analysis(
    symbol: str,
    analysis_datetime: Optional[datetime] = None,
    fractal_data: Optional[Dict] = None,
    weekly_levels: Optional[List[float]] = None,
    daily_levels: Optional[List[float]] = None,
    lookback_days: int = 30
) -> ScanResult
Parameters:

symbol: Stock ticker symbol
analysis_datetime: Analysis timestamp (UTC)
fractal_data: Dictionary containing 'fractals' key with highs/lows arrays
weekly_levels: List of weekly price levels (WL1-WL4)
daily_levels: List of daily price levels (DL1-DL6)
lookback_days: Days to search for M15 candle validation

Returns: ScanResult dataclass containing:

zones: List of Zone objects sorted by confluence score
confluence_counts: Dictionary of source type → item count
total_confluence_items: Total number of confluence items
metrics: Market metrics (ATR values, current price)

Zone Object Structure
pythonclass Zone:
    zone_id: int                    # Unique identifier
    zone_low: float                 # Lower boundary
    zone_high: float                # Upper boundary
    center_price: float             # Zone center
    zone_width: float               # Zone size
    zone_type: str                  # 'support' or 'resistance'
    confluence_level: str           # L1-L5 rating
    confluence_score: float         # Numerical score
    confluent_sources: List[Dict]   # Contributing items
    distance_percentage: float      # Distance from current price
    best_candle: Optional[Dict]     # Associated M15 candle
Usage Examples
Basic Confluence Scan
pythonfrom confluence_scanner.orchestrator import ConfluenceOrchestrator
from datetime import datetime

orchestrator = ConfluenceOrchestrator()
orchestrator.initialize()

result = orchestrator.run_analysis(
    symbol="AAPL",
    analysis_datetime=datetime.utcnow()
)

for zone in result.zones[:5]:
    print(f"Zone: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}")
    print(f"  Confluence: {zone.confluence_level} ({len(zone.confluent_sources)} sources)")
    print(f"  Type: {zone.zone_type}")
Integration with Fractal Engine
pythonfrom fractal_engine.orchestrator import FractalOrchestrator
from confluence_scanner.orchestrator import ConfluenceOrchestrator

# Detect fractals
fractal_orch = FractalOrchestrator()
fractal_results = fractal_orch.run_detection("SPY", lookback_days=30)

# Run confluence with fractals
confluence_orch = ConfluenceOrchestrator()
confluence_orch.initialize()

result = confluence_orch.run_analysis(
    symbol="SPY",
    fractal_data=fractal_results,
    weekly_levels=[450.0, 445.0],
    daily_levels=[455.0, 452.0]
)

# Check fractal participation
fractal_count = result.confluence_counts.get('fractals', 0)
print(f"Fractals contributed {fractal_count} confluence items")
Accessing Calculation Engines Directly
pythonorchestrator = ConfluenceOrchestrator()
orchestrator.initialize()

engines = orchestrator.get_calculation_engines()
hvn_engine = engines['hvn_engine']
camarilla_engine = engines['camarilla_engine']

# Run HVN analysis independently
import pandas as pd
df = pd.DataFrame(market_data)  # Your OHLCV data
hvn_results = hvn_engine.analyze_multi_timeframe(df)
Performance Specifications
Computational Complexity

Zone Discovery: O(n²) where n = confluence items
M15 Candle Search: O(m × z) where m = bars, z = zones
Typical execution: 2-5 seconds for complete analysis

Memory Requirements

Base: ~50MB for module and dependencies
Runtime: ~100MB for 30 days of 5-minute data
Scales linearly with lookback period

Data Requirements

Minimum: 14 days of data for valid ATR calculation
Recommended: 30+ days for robust HVN analysis
M15 candle validation: Requires 15-minute bar data

Polygon Server Requirements
The scanner requires a Polygon data server running at http://localhost:8200 with the following endpoints:
GET /api/v1/test
GET /api/v1/bars
  Parameters:
    symbol: string
    timeframe: string (5min, 15min, 1day, etc.)
    start_date: string (YYYY-MM-DD)
    end_date: string (YYYY-MM-DD)
Confluence Source Specifications
Source Weighting
Each confluence source type contributes equally to zone discovery. No inherent bias exists between source types.
Active Scan Range
Zones are only discovered within 2x Daily ATR of current price. This focuses analysis on actionable price levels.
Confluence Item Format
All confluence sources are standardized to:
python{
    'name': str,          # Unique identifier
    'level': float,       # Center price
    'low': float,         # Zone lower boundary
    'high': float,        # Zone upper boundary
    'type': str,          # Source type identifier
    'strength': float     # Optional: source-specific weight
}
Zone Clustering Algorithm
The discovery engine uses a proximity-based clustering approach:

Initial Grouping: Items are grouped if within 0.5x M15 ATR
Cluster Merging: Adjacent clusters merge if boundaries overlap
Zone Creation: Each cluster becomes a zone with:

Boundaries: Min/max of all items
Center: Volume-weighted average if available, else arithmetic mean
Type: 'resistance' if above current price, else 'support'



Scoring Mechanism
Zone scores combine three factors:
pythonbase_score = source_count * 2.0

# Strength multiplier (if sources provide strength values)
strength_mult = average(source.strength) / 5.0

# Recency boost (from M15 candle association)
recency_mult = 2.0 if days < 5 else 1.5 if days < 10 else 1.2

final_score = base_score * strength_mult * recency_mult
Error Handling
The scanner implements graceful degradation:

Missing data sources: Continue with available sources
Polygon connection failure: Log warning, proceed with cached data
Calculation engine errors: Skip that source, continue analysis
No zones found: Return empty zone list with metrics

Logging
Uses Python standard logging with namespace confluence_scanner:
pythonimport logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('confluence_scanner')
Log levels:

DEBUG: Detailed calculation steps
INFO: Major operations and results
WARNING: Data issues, fallback behavior
ERROR: Calculation failures

Testing
Run integration test:
bashpython test_fractal_confluence.py
Run minimal test:
bashpython test_minimal.py
Dependencies

pandas >= 1.5.0
numpy >= 1.24.0
scipy >= 1.10.0 (for signal processing)
pytz (for timezone handling)
dataclasses (Python 3.7+)

Future Enhancements
Planned improvements:

Configurable source weights
Machine learning-based zone ranking
Historical zone performance tracking
Real-time streaming updates
Additional pivot calculation methods
Support for futures and forex symbols

License
Proprietary - XIII Trading Systems
Support
For issues or questions, reference the implementation plan document and test scripts provided in the confluence_system directory.