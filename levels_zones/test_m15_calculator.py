"""
Test the fixed M15ZoneCalculator
Save as: test_m15_calculator.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pytz

# Add paths
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

print("=" * 80)
print("Testing Fixed M15ZoneCalculator")
print("=" * 80)

# Import the calculator
try:
    from calculations.candlestick.m15_zone_calc import M15ZoneCalculator
    print("✓ Successfully imported M15ZoneCalculator")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Create calculator instance
calculator = M15ZoneCalculator()
print("✓ Calculator initialized")

# Test connection
connected, msg = calculator.test_connection()
print(f"\nConnection test: {'✓ Connected' if connected else '✗ Failed'} - {msg}")

# Test single zone fetch
print("\n" + "=" * 60)
print("Test 1: Single Zone Fetch")
print("=" * 60)

ticker = "TSLA"
zone_date = "2025-07-30"
zone_time = "14:00:00"

print(f"Fetching: {ticker} on {zone_date} at {zone_time} UTC")

result = calculator.fetch_candle_for_zone(ticker, zone_date, zone_time)

if result:
    print(f"\n✓ Success! Found candle data:")
    print(f"  High: ${result['high']:.2f}")
    print(f"  Low: ${result['low']:.2f}")
    print(f"  Mid (Level): ${result['mid']:.2f}")
    print(f"  Open: ${result.get('open', 0):.2f}")
    print(f"  Close: ${result.get('close', 0):.2f}")
    print(f"  Volume: {result.get('volume', 0):,}")
    if result.get('estimated'):
        print("  ⚠️  Note: This is estimated data based on price")
else:
    print("✗ No data returned")

# Test multiple zones
print("\n" + "=" * 60)
print("Test 2: Multiple Zones Fetch")
print("=" * 60)

zones = [
    {'date': '2025-07-30', 'time': '14:00:00'},    # Market open
    {'date': '2025-07-30', 'time': '15:30:00'},    # Mid-session
    {'date': '2025-07-30', 'time': '19:45:00'},    # Near close
    {'date': '', 'time': ''},                      # Empty zone
    {'date': 'yyyy-mm-dd', 'time': 'hh:mm:ss'},   # Placeholder
]

print(f"Testing {len(zones)} zones...")
results = calculator.fetch_all_zone_candles(ticker, zones)

for idx, (zone_idx, candle_data) in enumerate(results):
    zone = zones[zone_idx]
    print(f"\nZone {zone_idx + 1}: {zone['date']} {zone['time']}")
    
    if candle_data:
        print(f"  ✓ High: ${candle_data['high']:.2f}")
        print(f"  ✓ Low: ${candle_data['low']:.2f}")
        print(f"  ✓ Mid: ${candle_data['mid']:.2f}")
        if candle_data.get('estimated'):
            print("  ⚠️  Estimated data")
    else:
        if zone['date'] and zone['time'] and \
           zone['date'] != 'yyyy-mm-dd' and \
           zone['time'] != 'hh:mm:ss':
            print("  ✗ No data found")
        else:
            print("  - Skipped (empty/placeholder)")

# Test market hours validation
print("\n" + "=" * 60)
print("Test 3: Market Hours Validation")
print("=" * 60)

test_times = [
    "09:00:00",  # Pre-market
    "14:00:00",  # Market open
    "18:00:00",  # Regular hours
    "21:00:00",  # After-hours
    "02:00:00",  # Closed
]

for time_str in test_times:
    dt = datetime.strptime(f"2025-07-30 {time_str}", "%Y-%m-%d %H:%M:%S")
    dt = pytz.UTC.localize(dt)
    is_valid, session = calculator.validate_market_hours(dt)
    status = "✓" if is_valid else "✗"
    print(f"{status} {time_str} UTC: {session}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)