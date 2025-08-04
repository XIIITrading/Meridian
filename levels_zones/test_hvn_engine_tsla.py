"""
Test script for HVN_Engine - TSLA 2025-08-04 12:30:00 UTC
This bypasses the confluence engine to show raw HVN results
Save as: test_hvn_engine_tsla.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz

# Add paths for imports
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Import required modules
from data.polygon_bridge import PolygonBridge
from calculations.volume.hvn_engine import HVNEngine
from calculations.volume.volume_profile import VolumeProfile

print("=" * 80)
print("HVN Engine Test - Raw Results Without Confluence")
print("=" * 80)

# Test parameters
ticker = "TSLA"
analysis_datetime = datetime(2025, 8, 4, 12, 30, 0, tzinfo=pytz.UTC)
print(f"\nTarget: {ticker} at {analysis_datetime} UTC")
print(f"Current date (today): {datetime.now().strftime('%Y-%m-%d')}")

# Initialize components
print("\nInitializing components...")
bridge = PolygonBridge()
hvn_engine = HVNEngine(levels=100)  # 100 price levels for volume profile

# Test connection
connected, msg = bridge.test_connection()
print(f"Polygon connection: {'✓ Connected' if connected else '✗ Failed'} - {msg}")

if not connected:
    print("\nERROR: Cannot connect to Polygon REST API")
    print("Make sure the Polygon REST API server is running:")
    print("cd polygon && python run_server.py")
    sys.exit(1)

# Fetch historical data
print(f"\nFetching historical data for HVN analysis...")
end_date = analysis_datetime.date()
start_date = end_date - timedelta(days=120)  # Get enough for 30-day analysis

print(f"Date range: {start_date} to {end_date}")

try:
    # Fetch 5-minute data
    data_5min = bridge.get_historical_bars(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        timeframe='5min'
    )
    
    if data_5min.empty:
        raise ValueError(f"No data returned for {ticker}")
    
    # Ensure we have the required timestamp column
    if 'timestamp' not in data_5min.columns:
        data_5min['timestamp'] = data_5min.index
    
    print(f"✓ Fetched {len(data_5min)} bars of 5-minute data")
    print(f"  Date range in data: {data_5min.index[0]} to {data_5min.index[-1]}")
    
except Exception as e:
    print(f"\nERROR fetching data: {e}")
    sys.exit(1)

# Run HVN analysis for each timeframe
print("\n" + "=" * 80)
print("Running HVN Analysis")
print("=" * 80)

timeframes = [7, 14, 30]
results = {}

for days in timeframes:
    print(f"\n📊 Analyzing {days}-day timeframe...")
    
    try:
        # Run analysis
        result = hvn_engine.analyze_timeframe(
            data_5min,
            timeframe_days=days,
            include_pre=True,
            include_post=True
        )
        
        results[days] = result
        
        # Display summary
        print(f"  ✓ Analysis complete")
        print(f"  Price range: ${result.price_range[0]:.2f} - ${result.price_range[1]:.2f}")
        print(f"  Data points analyzed: {result.data_points:,} bars")
        print(f"  Peaks found: {len(result.peaks)}")
        
    except Exception as e:
        print(f"  ✗ Error in {days}-day analysis: {e}")
        results[days] = None

# Display detailed results
print("\n" + "=" * 80)
print("DETAILED HVN RESULTS")
print("=" * 80)

# Get current price for reference
current_price = float(data_5min['close'].iloc[-1])
print(f"\nReference price (last close): ${current_price:.2f}")

for days, result in results.items():
    print(f"\n{'='*60}")
    print(f"{days}-DAY HVN ANALYSIS - TOP 10 ZONES")
    print(f"{'='*60}")
    
    if result is None:
        print("  No results available (error during analysis)")
        continue
    
    if not result.peaks:
        print("  No volume peaks found")
        continue
    
    # Show top 10 peaks
    print(f"\n{'Rank':<6} {'Price':<12} {'Volume %':<10} {'Distance':<12} {'Direction'}")
    print("-" * 60)
    
    for i, peak in enumerate(result.peaks[:10]):
        # Calculate distance from current price
        distance = peak.price - current_price
        distance_pct = (distance / current_price) * 100
        direction = "↑ Above" if distance > 0 else "↓ Below"
        
        print(f"#{i+1:<5} ${peak.price:<11.2f} {peak.volume_percent:<9.2f}% "
              f"{abs(distance_pct):<11.2f}% {direction}")
    
    # Additional analysis
    print(f"\nZone Analysis:")
    
    # Find support zones (below current price)
    support_peaks = [p for p in result.peaks if p.price < current_price]
    if support_peaks:
        nearest_support = max(support_peaks, key=lambda p: p.price)
        print(f"  Nearest Support: ${nearest_support.price:.2f} "
              f"({nearest_support.volume_percent:.1f}% volume)")
    
    # Find resistance zones (above current price)
    resistance_peaks = [p for p in result.peaks if p.price > current_price]
    if resistance_peaks:
        nearest_resistance = min(resistance_peaks, key=lambda p: p.price)
        print(f"  Nearest Resistance: ${nearest_resistance.price:.2f} "
              f"({nearest_resistance.volume_percent:.1f}% volume)")

# Volume Profile visualization (text-based)
print("\n" + "=" * 80)
print("VOLUME PROFILE VISUALIZATION")
print("=" * 80)

# Show a simple text visualization for the 7-day profile
if results.get(7) and results[7].peaks:
    print("\n7-Day Volume Profile (Top 10 levels):")
    print("Price         Volume Bar")
    print("-" * 40)
    
    # Get max volume for scaling
    max_vol = max(p.volume_percent for p in results[7].peaks[:10])
    
    for peak in sorted(results[7].peaks[:10], key=lambda p: p.price, reverse=True):
        # Create bar
        bar_length = int((peak.volume_percent / max_vol) * 30)
        bar = "█" * bar_length
        
        # Mark if near current price
        marker = " ← Current" if abs(peak.price - current_price) < 1 else ""
        
        print(f"${peak.price:>8.2f}  {bar:<30} {peak.volume_percent:>5.1f}%{marker}")

# Export results to CSV for further analysis
print("\n" + "=" * 80)
print("EXPORTING RESULTS")
print("=" * 80)

try:
    # Create a DataFrame with all peaks
    all_peaks = []
    for days, result in results.items():
        if result and result.peaks:
            for peak in result.peaks[:10]:
                all_peaks.append({
                    'timeframe_days': days,
                    'rank': peak.rank,
                    'price': peak.price,
                    'volume_percent': peak.volume_percent,
                    'distance_from_current': peak.price - current_price,
                    'distance_percent': ((peak.price - current_price) / current_price) * 100
                })
    
    if all_peaks:
        df_peaks = pd.DataFrame(all_peaks)
        output_file = f"hvn_results_{ticker}_{analysis_datetime.strftime('%Y%m%d_%H%M%S')}.csv"
        df_peaks.to_csv(output_file, index=False)
        print(f"✓ Results exported to: {output_file}")
    
except Exception as e:
    print(f"✗ Error exporting results: {e}")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

print(f"\nAnalysis Summary for {ticker}:")
print(f"  Analysis datetime: {analysis_datetime}")
print(f"  Current/reference price: ${current_price:.2f}")

for days, result in results.items():
    if result and result.peaks:
        avg_volume = sum(p.volume_percent for p in result.peaks) / len(result.peaks)
        print(f"\n  {days}-Day Analysis:")
        print(f"    Total peaks found: {len(result.peaks)}")
        print(f"    Average peak volume: {avg_volume:.2f}%")
        print(f"    Highest volume peak: {result.peaks[0].volume_percent:.2f}% at ${result.peaks[0].price:.2f}")

# Debug information
print("\n" + "=" * 80)
print("DEBUG INFORMATION")
print("=" * 80)

print("\nIf you're seeing confluence errors, here's what's happening:")
print("1. HVN Engine successfully identifies volume peaks")
print("2. Confluence calculator tries to group peaks from different timeframes")
print("3. The error might be in the confluence grouping logic")
print("\nThe raw HVN results above are what the confluence engine receives as input.")

# Show the first few bars of data for verification
print(f"\nFirst 5 bars of data (for verification):")
print(data_5min.head())

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)