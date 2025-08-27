Step 2: Confluence Engine - Enhanced Specification
2.1 Purpose & Overview
The Confluence Engine aggregates multiple technical indicators to identify high-probability trading zones where various market factors converge. It processes fractal zones from Step 1 and overlays additional confluence sources to score and rank potential trading areas.
2.2 Input Requirements
pythonRequired Inputs:
- fractal_zones: Dict         # Output from Step 1 Fractal Engine
- ticker: str                 # Stock symbol
- analysis_datetime: datetime # Analysis point (UTC)
- manual_levels: Dict         # User-provided levels
  - weekly_levels: List[float]  # 4 weekly levels (WL1-WL4)
  - daily_levels: List[float]   # 6 daily levels (DL1-DL6)
- lookback_days: int          # Historical data range (default: 30)

From Fractal Engine:
- valid_fractals: List of non-overlapping swing zones
- fractal_metadata: Analysis parameters and statistics
- cache_key: For data persistence
2.3 Core Metrics Calculation
pythonMarket Metrics Required:
- current_price: float        # Latest price at analysis time
- daily_atr: float           # 14-period daily ATR
- atr_15min: float           # 14-period M15 ATR
- atr_5min: float            # 14-period 5-minute ATR
- adr_percent: float         # Average Daily Range as percentage
- daily_high/low/open: float # Current day's OHLC values
- pre_market_price: float    # Pre-market reference price

Active Range Definition:
- scan_low: current_price - (2 × daily_atr)
- scan_high: current_price + (2 × daily_atr)
- This defines the boundary for all confluence calculations
2.4 Confluence Source Components
2.4.1 HVN (High Volume Node) Analysis
pythonHVN Configuration:
- Timeframes: [30-day, 14-day, 7-day]
- Price levels: 100 (default)
- Percentile threshold: 80th percentile
- Peak detection: scipy.signal.find_peaks with prominence

Process:
1. Build volume profile for each timeframe
2. Identify volume peaks using statistical analysis
3. Rank peaks 1-100 based on volume percentage
4. Filter to top 20% (80th percentile and above)
5. Create zones around peaks using 0.3 × M15_ATR

Output per timeframe:
{
    'timeframe': 30,  # days
    'peaks': [
        {
            'price': 456.25,
            'rank': 1,  # 1 = highest volume in timeframe
            'volume_pct': 8.5,
            'zone_width': atr_15min * 0.3
        }
    ]
}
2.4.2 Camarilla Pivots
pythonCamarilla Calculation:
- Timeframes: [Daily, Weekly, Monthly]
- Key levels: R6, R5, R4, R3, S3, S4, S5, S6 (skip minor levels)
- Formula basis: Previous period's high, low, close

Zone widths by timeframe:
- Monthly: 2.0 × M15_ATR
- Weekly: 1.5 × M15_ATR  
- Daily: 0.5 × M15_ATR

Output structure:
{
    'type': 'cam-monthly',
    'level_name': 'MR4',
    'price': 465.50,
    'strength': 4,  # 1-6 based on level
    'zone_width': calculated_width
}
2.4.3 Manual Level Integration
pythonWeekly Zones (WL1-WL4):
- Zone width: 2.0 × M15_ATR
- Higher weight in confluence scoring
- Type: 'weekly'

Daily Zones (DL1-DL6):
- Dual representation:
  1. As levels: minimal width (0.1)
  2. As zones: 1.0 × M15_ATR width
- Type: 'daily-level' and 'daily-zone'
2.4.4 ATR Dynamic Zones
pythonATR Zones:
- ATR High: current_price + daily_atr ± M15_ATR
- ATR Low: current_price - daily_atr ± M15_ATR
- Dynamic adjustment based on volatility
- Type: 'atr'
2.4.5 Market Structure Levels
pythonStructure Levels (with 5min_ATR zones):
- Previous Day High (PDH)
- Previous Day Low (PDL)
- Previous Day Close (PDC)
- Overnight High (ONH) - 20:00 UTC to analysis time
- Overnight Low (ONL) - 20:00 UTC to analysis time
2.5 Confluence Scoring Algorithm
pythonWeight Configuration:
confluence_weights = {
    'hvn-30d': 3.0,      # Highest weight for 30-day volume
    'hvn-14d': 2.5,      
    'hvn-7d': 2.0,       
    'cam-monthly': 3.0,   # Monthly pivots
    'cam-weekly': 2.5,    
    'cam-daily': 1.5,    
    'weekly': 2.5,        # Weekly manual levels
    'daily-zone': 1.5,    
    'daily-level': 1.0,   
    'atr': 1.5,          
    'market-structure': 1.0
}

Scoring Process:
1. Identify all confluence items within active range
2. Cluster nearby items (within 1.5 × M15_ATR)
3. Calculate weighted score for each cluster
4. Apply multi-type bonus (10% per additional type)
5. Apply width penalty if cluster > 2 × M15_ATR
6. Cap extreme scores at 50 (with logarithmic scaling above)

Confluence Levels:
- L5: Score ≥ 12.0 (Extreme confluence)
- L4: Score ≥ 8.0  (High confluence)
- L3: Score ≥ 5.0  (Significant confluence)
- L2: Score ≥ 2.5  (Moderate confluence)
- L1: Score < 2.5  (Low confluence)
2.6 Zone Discovery Process
pythonDiscovery Algorithm:
1. Collect all confluence items in active range
2. Sort by price level
3. Find clusters using distance threshold (1.5 × M15_ATR)
4. For each cluster:
   - Calculate weighted center
   - Determine zone boundaries
   - Apply width constraint (max 3 × M15_ATR)
   - Calculate confluence score
   - Assign confluence level
5. Refine zones to exactly 1 × M15_ATR width
6. Sort by distance from current price
2.7 Zone Refinement & Validation
pythonZone Refinement:
1. Find peak confluence point within cluster
2. Center refined zone on peak
3. Set zone width to exactly 1 × M15_ATR
4. Preserve all confluence sources and scores

Quality Filters:
- Minimum confluence score: 2.0
- Maximum initial cluster width: 3 × M15_ATR
- Overlap handling: Merge zones with >50% overlap
- Distance filter: Prioritize zones within 1 × daily_ATR
2.8 Output Data Structure
pythonConfluence Engine Output:
{
    'metadata': {
        'ticker': str,
        'analysis_datetime': datetime,
        'metrics': {
            'current_price': float,
            'daily_atr': float,
            'atr_15min': float,
            'atr_5min': float,
            'scan_range': (scan_low, scan_high)
        }
    },
    'confluence_sources': {
        'hvn_peaks': List[Dict],        # All HVN peaks found
        'camarilla_pivots': List[Dict], # All Camarilla levels
        'weekly_zones': List[Dict],     # Manual weekly zones
        'daily_zones': List[Dict],      # Manual daily zones
        'atr_zones': List[Dict],        # Dynamic ATR zones
        'market_structure': List[Dict]  # PDH, PDL, etc.
    },
    'discovered_zones': [
        {
            'zone_id': int,
            'zone_high': float,
            'zone_low': float,
            'center_price': float,
            'zone_width': float,  # Exactly 1 × M15_ATR
            'confluence_score': float,
            'confluence_level': str,  # L1-L5
            'confluent_sources': [
                {
                    'type': str,
                    'name': str,
                    'price': float,
                    'weight': float
                }
            ],
            'distance_from_current': float,
            'distance_percentage': float,
            'zone_type': 'support' | 'resistance'
        }
    ],
    'statistics': {
        'total_confluence_items': int,
        'zones_discovered': int,
        'zones_above_l3': int,
        'average_confluence_score': float
    }
}
2.9 Integration with Fractal Zones
pythonFractal Integration:
1. Add fractal zones to confluence sources with weight 2.0
2. Check overlap between discovered zones and fractals
3. Boost score by 20% if zone contains fractal
4. Mark zones with fractal overlap for priority

Enhanced Scoring:
if zone overlaps with fractal:
    zone.confluence_score *= 1.2
    zone.confluent_sources.append({
        'type': 'fractal',
        'name': f'Fractal_{fractal.type}',
        'price': fractal.price,
        'weight': 2.0,
        'datetime': fractal.datetime
    })
2.10 Performance Optimization
pythonOptimization Strategies:
1. Data Caching:
   - Cache all market data with 15-minute TTL
   - Cache HVN calculations by timeframe
   - Cache Camarilla pivots by period
   
2. Parallel Processing:
   - Calculate HVN timeframes concurrently
   - Process Camarilla timeframes in parallel
   - Batch confluence item processing
   
3. Early Termination:
   - Stop clustering if max zones reached
   - Skip sources outside active range
   - Prune low-scoring clusters early

Performance Targets:
- Complete confluence analysis: < 3 seconds
- HVN calculation per timeframe: < 1 second
- Zone discovery: < 500ms
- Memory usage: < 500MB for 30-day analysis
2.11 Configuration Parameters
pythonConfigurable Parameters:
{
    # Clustering
    'CLUSTER_DISTANCE_ATR': 1.5,     # Cluster items within this distance
    'MIN_CONFLUENCE_SCORE': 2.0,     # Minimum score to create zone
    
    # Zone constraints
    'MAX_ZONE_WIDTH_ATR': 3.0,       # Maximum initial zone width
    'REFINED_ZONE_WIDTH_ATR': 1.0,   # Final zone width (exactly)
    
    # HVN settings
    'HVN_LEVELS': 100,                # Price levels for volume profile
    'HVN_PERCENTILE': 80,             # Top percentile for peaks
    'HVN_TIMEFRAMES': [30, 14, 7],    # Days to analyze
    
    # Display limits
    'MIN_CONFLUENCE_LEVEL': 'L3',     # Minimum level to report
    'MAX_ZONES_TO_DISPLAY': 6,        # Top zones to show
    
    # Active range
    'ATR_SCAN_MULTIPLIER': 2.0        # Scan within N × daily_ATR
}
2.12 Error Handling & Validation
pythonRequired Validations:
1. Data Availability:
   - Verify sufficient historical data for each timeframe
   - Handle missing data gracefully
   - Validate ATR calculations (non-zero)
   
2. Confluence Sources:
   - Minimum 2 different source types required
   - Validate price levels within reasonable range
   - Check for NaN/Inf values
   
3. Zone Quality:
   - Verify zone boundaries (high > low)
   - Ensure zones within active range
   - Validate confluence scores are positive

Error Recovery:
- Missing HVN data: Continue with other sources
- Invalid Camarilla: Skip that timeframe
- No zones found: Return empty list with explanation
2.13 Testing Requirements
pythonTest Coverage:
□ All confluence sources calculate correctly
□ Clustering algorithm groups items properly
□ Scoring weights applied accurately
□ Zone refinement produces 1 × M15_ATR zones
□ Integration with fractal zones works
□ Performance meets targets
□ Edge cases handled (no data, single item, etc.)
2.14 Example Integration Flow
python# Step 2 receives output from Step 1
fractal_output = step1_fractal_engine_output

# Initialize Confluence Engine
confluence_engine = ConfluenceEngine()

# Run confluence analysis
confluence_result = confluence_engine.analyze(
    fractal_zones=fractal_output['fractals'],
    ticker="SPY",
    analysis_datetime=datetime.now(),
    manual_levels={
        'weekly': [450.0, 445.0, 440.0, 435.0],
        'daily': [452.0, 448.0, 447.0, 446.0, 444.0, 442.0]
    },
    lookback_days=30
)

# Enhanced zones ready for Step 3
zones_for_filtering = confluence_result['discovered_zones']
This enhanced specification provides comprehensive implementation details for the Confluence Engine, ensuring proper integration with the Fractal Engine output and preparation for subsequent zone filtering and M15 candle analysis steps.