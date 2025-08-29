markdown# Fractal Engine Module Documentation

## Overview
The Fractal Engine identifies significant swing highs and lows in market data using a ZigZag-style algorithm with ATR-based validation.

## Module Structure
fractal_engine/
├── init.py           # Module initialization
├── config.py            # Configuration parameters
├── data_fetcher.py      # Polygon data fetching
├── detector.py          # Core fractal detection logic
└── orchestrator.py      # High-level coordination

## Key Components

### 1. FractalOrchestrator
Main interface for fractal detection operations.

```python
from fractal_engine.orchestrator import FractalOrchestrator

orchestrator = FractalOrchestrator()
results = orchestrator.run_detection(
    symbol="SPY",
    analysis_time=datetime.utcnow(),  # Optional, defaults to now
    lookback_days=30,                  # Optional, defaults to config
    fractal_length=11,                 # Optional, defaults to config
    min_atr_distance=1.0               # Optional, defaults to config
)
2. FractalDetector
Core detection algorithm that identifies swing points.
Key Methods:

detect_fractals(df, start_time) - Main detection method
_find_zigzag_swings(df, end_idx) - ZigZag algorithm implementation
_apply_overlap_filter(swings, df) - Filter overlapping swings

3. DataFetcher
Handles connection to Polygon server for market data.
Key Methods:

fetch_bars(ticker, end_date, lookback_days) - Fetch historical data
test_connection() - Verify server connectivity

Configuration Parameters
Located in config.py:

FRACTAL_LENGTH (default: 11) - Bars on each side of pivot
MIN_FRACTAL_DISTANCE_ATR (default: 1.0) - Minimum ATR between swings
LOOKBACK_DAYS (default: 30) - Historical data period
CHECK_PRICE_OVERLAP (default: True) - Filter overlapping swings
ATR_PERIOD (default: 14) - ATR calculation period

Results Structure
The run_detection() method returns:
python{
    'symbol': 'SPY',
    'analysis_time': datetime,
    'fractals': {
        'highs': [
            {
                'datetime': datetime,
                'price': float,
                'atr': float,
                'index': int,
                'bar_high': float,
                'bar_low': float,
                'bar_open': float,
                'bar_close': float,
                'bar_volume': float
            },
            # ... more highs
        ],
        'lows': [
            # ... similar structure
        ]
    },
    'parameters': {
        'fractal_length': 11,
        'min_atr_distance': 1.0,
        'lookback_days': 30,
        'overlap_filter': True
    },
    'statistics': {
        'total_highs': int,
        'total_lows': int,
        'date_range': {
            'start': datetime,
            'end': datetime
        }
    },
    'structure': {
        'trend': 'UPTREND|DOWNTREND|EXPANDING|CONTRACTING|MIXED',
        'description': str,
        'recent_high': float,
        'recent_low': float,
        'range': float
    }
}
Usage Examples
Basic Usage
pythonfrom fractal_engine.orchestrator import FractalOrchestrator

# Initialize
orchestrator = FractalOrchestrator()

# Detect fractals
results = orchestrator.run_detection("AAPL")

# Access results
for high in results['fractals']['highs']:
    print(f"High: {high['datetime']} @ ${high['price']:.2f}")
Custom Parameters
pythonresults = orchestrator.run_detection(
    symbol="TSLA",
    lookback_days=60,      # Look back 60 days
    fractal_length=21,     # Use 10 bars on each side
    min_atr_distance=2.0   # Require 2x ATR distance
)
Get Latest Fractals
pythonlatest = orchestrator.get_latest_fractals("SPY", count=10)
print(f"Market trend: {latest['structure']['trend']}")
Integration Points
This module integrates with:

Confluence Scanner - Provides fractal levels for confluence analysis
Zone Identification - Converts fractals to trading zones
Results Engine - Formats fractals for display/export

Dependencies

pandas
numpy
requests
Local Polygon server (for live data)
Python 3.7+

Error Handling
The module handles:

Server connection failures
Missing/invalid data
Insufficient data for fractal detection
Configuration errors

Performance Notes

Processing 30 days of 15-minute data typically takes <1 second
ATR calculation is optimized using rolling windows
Overlap filtering can be disabled for speed via config

Future Enhancements
Planned improvements:

Multiple timeframe fractal detection
Adaptive ATR multipliers
Volume-weighted fractal significance
Real-time fractal updates