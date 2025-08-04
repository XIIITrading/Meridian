"""
Test script to query TSLA 15-minute candle using PolygonBridge methods
Testing for: TSLA - 2025-07-30 14:00:00 UTC
"""

import sys
from pathlib import Path
from datetime import datetime
import pytz
from decimal import Decimal

# Add paths
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

print("=" * 80)
print("Polygon M15 Candle Query Test - Using PolygonBridge Methods")
print("=" * 80)

# Import PolygonBridge
from data.polygon_bridge import PolygonBridge

# Test parameters
ticker = "TSLA"
target_datetime = datetime(2025, 7, 30, 14, 0, 0, tzinfo=pytz.UTC)

print(f"\nTarget: {ticker} at {target_datetime}")

# Initialize bridge
bridge = PolygonBridge()
print("✓ PolygonBridge initialized")

# Test 1: get_candle_at_datetime (most likely the right method)
print("\n" + "=" * 60)
print("Test 1: Using get_candle_at_datetime")
print("=" * 60)

try:
    candle = bridge.get_candle_at_datetime(ticker, target_datetime)
    
    if candle:
        print(f"\n✓ Found candle data:")
        print(f"  Candle: {candle}")
        
        # Extract values depending on the format returned
        if isinstance(candle, dict):
            high = candle.get('h', candle.get('high', 0))
            low = candle.get('l', candle.get('low', 0))
            open_price = candle.get('o', candle.get('open', 0))
            close = candle.get('c', candle.get('close', 0))
            
            # Calculate midpoint
            high_decimal = Decimal(str(high))
            low_decimal = Decimal(str(low))
            midpoint = (high_decimal + low_decimal) / 2
            
            print(f"\n📊 Results for M15 Zone:")
            print(f"  Level (Midpoint): ${midpoint:.2f}")
            print(f"  Zone High: ${high:.2f}")
            print(f"  Zone Low: ${low:.2f}")
            print(f"  Open: ${open_price:.2f}")
            print(f"  Close: ${close:.2f}")
    else:
        print("✗ No candle data returned")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: get_price_at_datetime (alternative)
print("\n" + "=" * 60)
print("Test 2: Using get_price_at_datetime")
print("=" * 60)

try:
    price = bridge.get_price_at_datetime(ticker, target_datetime)
    print(f"Price at {target_datetime}: ${price}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: fetch_bars (might work with specific parameters)
print("\n" + "=" * 60)
print("Test 3: Using fetch_bars")
print("=" * 60)

try:
    # Try to fetch with 15-minute timeframe
    bars = bridge.fetch_bars(
        ticker=ticker,
        date=target_datetime.date(),  # This might be the issue - it only takes date
        timeframe='15Min'  # or '15' or 'minute' with multiplier
    )
    
    if bars:
        print(f"✓ Got {len(bars)} bars")
        # Find the bar at 14:00
        for bar in bars[:5]:  # Show first 5
            print(f"  Bar: {bar}")
    else:
        print("✗ No bars returned")
        
except Exception as e:
    print(f"✗ Error: {e}")
    # This might show us the correct parameter names
    import traceback
    traceback.print_exc()

# Test 4: get_historical_bars
print("\n" + "=" * 60)
print("Test 4: Using get_historical_bars")
print("=" * 60)

try:
    # This might accept datetime parameters
    bars = bridge.get_historical_bars(
        ticker=ticker,
        start_date=target_datetime.date(),
        end_date=target_datetime.date(),
        timeframe='15Min'
    )
    
    if bars:
        print(f"✓ Got {len(bars)} bars")
        # Look for the 14:00 bar
        target_hour = 14
        for bar in bars:
            # Check if this bar is at our target time
            bar_time = bar.get('t', bar.get('timestamp', 0))
            if isinstance(bar_time, (int, float)):
                bar_dt = datetime.fromtimestamp(bar_time / 1000, tz=pytz.UTC)
                if bar_dt.hour == target_hour and bar_dt.minute == 0:
                    print(f"\n✓ Found 14:00 UTC candle:")
                    print(f"  Time: {bar_dt}")
                    print(f"  High: ${bar.get('h', 0):.2f}")
                    print(f"  Low: ${bar.get('l', 0):.2f}")
                    print(f"  Midpoint: ${(bar.get('h', 0) + bar.get('l', 0)) / 2:.2f}")
                    break
    else:
        print("✗ No bars returned")
        
except Exception as e:
    print(f"✗ Error: {e}")

# Debug: Check what m15_zone_calc.py might be doing wrong
print("\n" + "=" * 60)
print("Debug: M15ZoneCalculator Issue")
print("=" * 60)

print("\nBased on the error, it seems the calculator is passing:")
print("  start_date=2025-07-30T00:00:00+00:00")
print("  end_date=2025-07-30T00:00:00+00:00")

print("\nThis suggests the code might be doing something like:")
print("  start_date = datetime.combine(zone_date, datetime.min.time())")
print("  end_date = datetime.combine(zone_date, datetime.max.time())")

print("\nOr it might be using .date() which strips the time:")
print("  bridge.method(ticker, target_datetime.date(), target_datetime.date())")

print("\n" + "=" * 80)
print("Recommendation: Check m15_zone_calc.py for date/datetime handling")
print("=" * 80)