Step 1: Fractal Engine - Enhanced Specification
1.1 Purpose & Overview
The Fractal Engine identifies significant market structure points (swing highs/lows) using a ZigZag-style algorithm on 15-minute candlestick data. These fractals serve as the foundation for all subsequent confluence analysis and zone filtering.
1.2 Input Requirements
pythonRequired Inputs:
- ticker: str           # Stock symbol (e.g., 'SPY', 'AAPL')
- analysis_datetime: datetime  # Analysis point (UTC) - format: YYYY-MM-DD HH:MM
- fractal_length: int   # Odd number (default: 11) - bars on each side to evaluate
- min_atr_distance: float  # ATR multiples for swing validation (default: 1.0)

Data Source:
- Local Polygon server at http://localhost:8200
- Endpoint: /api/v1/bars (POST method preferred, GET fallback)
- Authentication: API key in headers
1.3 Data Retrieval Process
pythonData Fetch Specifications:
- Timeframe: 15-minute bars (M15)
- Lookback Period: 90 days from analysis_datetime
- Caching: Enabled for efficiency
- Timezone: All timestamps in UTC (timezone-naive for consistency)
- Required Fields: datetime, open, high, low, close, volume
1.4 Core Algorithm - ZigZag Fractal Detection
Phase 1: ATR Calculation
pythonATR Calculation:
- Period: 14 bars (configurable)
- Formula: Average of True Range over period
- True Range = max(high-low, |high-prev_close|, |low-prev_close|)
- Purpose: Dynamic threshold for significant price movements
Phase 2: Fractal Identification
pythonFractal Detection Logic:
1. For each bar (starting from fractal_length/2 to end):
   - Swing High: Current bar high > all highs within ±fractal_length/2 bars
   - Swing Low: Current bar low < all lows within ±fractal_length/2 bars
   
2. ZigZag Validation:
   - Must alternate between highs and lows
   - Minimum distance between swings: avg_ATR × min_atr_distance
   - Price move threshold: Ensures significant price movement between swings
Phase 3: Zone Creation from Fractals
pythonFor each validated fractal:
{
    'type': 'high' | 'low',
    'datetime': timestamp (UTC),
    'price': swing_high or swing_low value,
    'zone': {
        'high': candle_high,  # Upper bound of fractal zone
        'low': candle_low,    # Lower bound of fractal zone
    },
    'atr': current_atr_value,
    'index': bar_index,
    'status': 'valid' | 'overlap' | 'invalid'
}
1.5 Overlap Prevention Logic
pythonOverlap Check Algorithm:
1. Sort fractals by datetime (oldest to newest)
2. For each fractal:
   - Compare zone boundaries with previously validated fractals
   - Overlap exists if: current_low <= previous_high AND current_high >= previous_low
   - If overlap detected: Mark as 'overlap' status and exclude
   - If no overlap: Add to valid_fractals list
1.6 Output Data Structure
pythonOutput Format:
{
    'metadata': {
        'ticker': str,
        'analysis_datetime': datetime,
        'data_range': {
            'start': datetime,  # 90 days before analysis
            'end': datetime     # analysis_datetime
        },
        'parameters': {
            'fractal_length': int,
            'min_atr_distance': float,
            'atr_period': int
        },
        'statistics': {
            'total_bars_analyzed': int,
            'fractals_detected': int,
            'valid_fractals': int
        }
    },
    'fractals': {
        'highs': [
            {
                'datetime': datetime,
                'price': float,      # Exact swing high
                'zone_high': float,  # Bar high
                'zone_low': float,   # Bar low
                'atr': float,
                'index': int,        # Bar index in dataset
                'distance_from_previous': float  # Price distance
            }
        ],
        'lows': [
            # Same structure as highs
        ]
    },
    'cache_key': str  # For data persistence between steps
}
1.7 Integration Points for Next Steps
pythonKey Outputs for Confluence Engine:
1. valid_fractals: List of non-overlapping swing zones
2. active_range_bounds: To be calculated in Step 3 using current_price ± 2×daily_ATR
3. zone_boundaries: High/low of each fractal candle for overlap analysis
4. temporal_data: Datetime stamps for time-based filtering
1.8 Error Handling Requirements
pythonRequired Error Handling:
1. Connection Errors:
   - Test server connection before data fetch
   - Implement retry logic with exponential backoff
   - Fallback to cached data if available

2. Data Validation:
   - Verify minimum bars available (fractal_length × 2)
   - Check for missing OHLCV data
   - Validate datetime continuity (no large gaps)

3. Algorithm Failures:
   - Handle case where no fractals found
   - Manage edge cases at data boundaries
   - Validate ATR calculation (handle zero/null values)
1.9 Performance Optimizations
pythonOptimization Strategies:
1. Caching:
   - Cache 90-day bar data with TTL of 15 minutes
   - Cache fractal calculations by hash(ticker, datetime, parameters)
   
2. Computation:
   - Vectorized operations for ATR calculation
   - Early termination if sufficient fractals found
   - Sliding window approach for fractal detection
   
3. Memory:
   - Process data in chunks if dataset > 10,000 bars
   - Release intermediate calculations after validation
1.10 Configuration & Flexibility
pythonConfigurable Parameters:
{
    'FRACTAL_LENGTH': 11,        # Must be odd, range: 3-21
    'LOOKBACK_DAYS': 90,        # Range: 30-365
    'MIN_FRACTAL_DISTANCE_ATR': 1.0,  # Range: 0.5-3.0
    'ATR_PERIOD': 14,           # Range: 10-20
    'CHECK_PRICE_OVERLAP': True,  # Enable/disable overlap filtering
    'MAX_FRACTALS_TO_PROCESS': 100,  # Limit for performance
    'AGGREGATION_MULTIPLIER': 15,  # For M15 bars
    'SERVER_TIMEOUT': 30,       # Seconds
    'CACHE_TTL': 900           # 15 minutes in seconds
}
1.11 Testing & Validation Checklist
pythonValidation Requirements:
□ Verify fractals alternate between highs and lows
□ Confirm minimum ATR distance between swings
□ Check zone overlap prevention working correctly
□ Validate all timestamps are in UTC
□ Ensure cache key generation is deterministic
□ Test edge cases (market gaps, low liquidity periods)
□ Verify handling of pre/post market data
1.12 Example Usage Pattern
python# Integration example for next steps
fractal_engine_output = run_fractal_engine(
    ticker="SPY",
    analysis_datetime="2025-01-15 14:30",
    fractal_length=11,
    min_atr_distance=1.0
)

# Pass to Step 2: Confluence Engine
confluence_input = {
    'fractal_zones': fractal_engine_output['fractals'],
    'metadata': fractal_engine_output['metadata'],
    'cache_key': fractal_engine_output['cache_key']
}
This enhanced specification provides clear implementation details while maintaining flexibility for integration with the subsequent steps in your trading system. The structure ensures that the confluence engine (Step 2) receives properly formatted and validated swing zones for further analysis.