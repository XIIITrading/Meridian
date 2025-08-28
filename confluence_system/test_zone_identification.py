"""
Fixed-time test for TSLA at 2025-08-28 12:30 UTC
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json

sys.path.insert(0, str(Path(__file__).parent))

def test_zone_identification_fixed_time():
    """Test with fixed time for chart comparison"""
    
    # FIXED PARAMETERS
    symbol = "TSLA"
    # Use UTC timezone for display but naive for processing
    analysis_time_utc = datetime(2025, 8, 28, 12, 30, 0, tzinfo=timezone.utc)
    analysis_time_naive = datetime(2025, 8, 28, 12, 30, 0)  # No timezone for fractal engine
    
    print("=" * 80)
    print(f"ZONE IDENTIFICATION - {symbol}")
    print(f"Analysis Time: {analysis_time_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 80)
    
    # Get TSLA price at this exact time
    from confluence_scanner.data.polygon_client import PolygonClient
    client = PolygonClient()
    
    # Fetch bars for the day
    bars = client.fetch_bars(
        symbol, 
        "2025-08-28", 
        "2025-08-28", 
        "15min"
    )
    
    current_price = None
    if bars is not None and not bars.empty:
        # Find the 12:30 UTC bar (naive datetime)
        target_time = analysis_time_naive
        
        try:
            if target_time in bars.index:
                current_price = bars.loc[target_time, 'close']
            else:
                # Find nearest time
                time_diff = abs(bars.index - target_time)
                closest_idx = time_diff.argmin()
                closest_bar = bars.iloc[closest_idx]
                current_price = closest_bar['close']
                print(f"Using bar at {bars.index[closest_idx]}: ${current_price:.2f}")
        except Exception as e:
            print(f"Error finding bar: {e}")
    
    if current_price is None:
        print("Warning: Could not fetch exact price, using approximate")
        current_price = 349.76  # From your output
    else:
        print(f"\nPrice at {analysis_time_utc.strftime('%H:%M UTC')}: ${current_price:.2f}")
    
    # Run full analysis
    from fractal_engine.orchestrator import FractalOrchestrator
    from confluence_scanner.orchestrator import ConfluenceOrchestrator
    from zone_identification.orchestrator import ZoneIdentificationOrchestrator
    
    # 1. FRACTALS - use naive datetime
    print("\n" + "="*40)
    print("DETECTING FRACTALS")
    print("="*40)
    
    fractal_orch = FractalOrchestrator()
    fractal_results = fractal_orch.run_detection(
        symbol=symbol,
        analysis_time=analysis_time_naive,  # Use naive datetime here
        lookback_days=30
    )
    
    print(f"Found {len(fractal_results['fractals']['highs'])} highs, "
          f"{len(fractal_results['fractals']['lows'])} lows")
    
    # 2. CONFLUENCE - use naive datetime
    print("\n" + "="*40)
    print("FINDING CONFLUENCE")
    print("="*40)
    
    confluence_orch = ConfluenceOrchestrator()
    confluence_orch.initialize()
    
    # Test levels for TSLA
    weekly_levels = [340.0, 335.0, 330.0, 325.0]
    daily_levels = [345.0, 342.0, 338.0, 335.0, 332.0, 328.0]
    
    confluence_result = confluence_orch.run_analysis(
        symbol=symbol,
        analysis_datetime=analysis_time_naive,  # Use naive datetime here
        fractal_data=fractal_results,
        weekly_levels=weekly_levels,
        daily_levels=daily_levels,
        lookback_days=30,
        merge_overlapping=True,
        merge_identical=False
    )
    
    print(f"Found {len(confluence_result.zones)} zones")
    
    # Count by level
    level_counts = {}
    for zone in confluence_result.zones:
        level = zone.confluence_level
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level in ['L5', 'L4', 'L3', 'L2', 'L1', 'L0']:
        if level in level_counts:
            print(f"  {level}: {level_counts[level]} zones")
    
    # 3. ZONE IDENTIFICATION
    print("\n" + "="*40)
    print("IDENTIFYING TRADING LEVELS")
    print("="*40)
    
    zone_id_orch = ZoneIdentificationOrchestrator()
    zone_id_orch.initialize(current_price)
    
    atr_daily = confluence_result.metrics['atr_daily']
    atr_filter = atr_daily * 2
    
    trading_levels = zone_id_orch.identify_trading_levels(
        fractal_data=fractal_results,
        confluence_zones=confluence_result.zones,
        atr_filter=atr_filter
    )
    
    print(f"Identified {len(trading_levels)} trading levels")
    
    # OUTPUT FOR CHART COMPARISON
    print("\n" + "="*80)
    print("LEVELS FOR CHART (Copy these to compare)")
    print("="*80)
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"Time: {analysis_time_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print("-" * 40)
    
    # Group by confluence level
    by_level = {}
    for level in trading_levels:
        conf = level.confluence_level
        if conf not in by_level:
            by_level[conf] = []
        by_level[conf].append(level)
    
    # Print levels for charting
    print("\n[HIGH PRIORITY LEVELS]")
    for conf_level in ['L5', 'L4']:
        if conf_level in by_level:
            print(f"\n{conf_level} Levels:")
            for level in sorted(by_level[conf_level], key=lambda x: x.low_price):
                direction = "RES" if level.low_price > current_price else "SUP"
                print(f"  {direction} ${level.low_price:.2f}-${level.high_price:.2f} "
                      f"({abs(level.distance_percentage):.1f}% away)")
    
    print("\n[MEDIUM PRIORITY LEVELS]")
    for conf_level in ['L3', 'L2']:
        if conf_level in by_level:
            print(f"\n{conf_level} Levels:")
            for level in sorted(by_level[conf_level], key=lambda x: x.low_price):
                direction = "RES" if level.low_price > current_price else "SUP"
                print(f"  {direction} ${level.low_price:.2f}-${level.high_price:.2f} "
                      f"({abs(level.distance_percentage):.1f}% away)")
    
    # Summary
    print("\n" + "="*40)
    print("SUMMARY")
    print("="*40)
    print(f"Total Trading Levels: {len(trading_levels)}")
    
    # Save for external use
    output_data = {
        'symbol': symbol,
        'analysis_time': analysis_time_utc.isoformat(),
        'current_price': current_price,
        'levels': []
    }
    
    for level in sorted(trading_levels, key=lambda x: x.priority_score, reverse=True)[:10]:
        output_data['levels'].append({
            'low': level.low_price,
            'high': level.high_price,
            'confluence': level.confluence_level,
            'score': level.confluence_score,
            'distance_pct': level.distance_percentage,
            'type': level.fractal_type,
            'priority': level.priority_score
        })
    
    with open('tsla_levels.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✓ Levels saved to tsla_levels.json")
    print(f"✓ Current Price: ${current_price:.2f}")
    
    return trading_levels

if __name__ == "__main__":
    levels = test_zone_identification_fixed_time()
    print("\n" + "="*80)
    print("TEST COMPLETE - Check the levels on your chart")
    print("="*80)