# debug_zone_calculation.py
from datetime import datetime
from scanner.zone_scanner import ZoneScanner
from discovery.zone_discovery import ZoneDiscoveryEngine
import numpy as np

# Setup
scanner = ZoneScanner()
ticker = "AMD"
analysis_datetime = datetime(2025, 8, 26, 12, 30, 0)
weekly_levels = [177.7, 171.1, 158.7, 147.5]
daily_levels = [184.5, 175.0, 173.2, 170.0, 166.5, 162.8]

# Get metrics
metrics = scanner.metrics_calculator.calculate_metrics(ticker, analysis_datetime)
current_price = metrics.current_price
atr_15min = metrics.atr_m15

print(f"Current Price: ${current_price:.2f}")
print(f"M15 ATR: ${atr_15min:.2f}")

# Build confluence sources
confluence_sources = {
    'weekly_zones': [
        {'name': f'WL{i+1}', 'level': level, 'low': level - 0.5, 'high': level + 0.5}
        for i, level in enumerate(weekly_levels)
    ],
    'daily_levels': daily_levels
}

# Create engine and test some theoretical zones
engine = ZoneDiscoveryEngine()
zone_half_width = atr_15min * engine.zone_size_multiplier

print(f"\nZone width: ${zone_half_width * 2:.2f} (M15 ATR * {engine.zone_size_multiplier} * 2)")

# Test zones around our daily levels to see if they score
print("\nTesting zones around daily levels:")
for i, level in enumerate(daily_levels):
    # Create a theoretical zone at this level
    from discovery.zone_discovery import TheoreticalZone
    zone = TheoreticalZone(
        center_price=level,
        zone_high=level + zone_half_width,
        zone_low=level - zone_half_width,
        zone_width=zone_half_width * 2,
        grid_index=i
    )
    
    score, sources = engine._calculate_zone_confluence(zone, confluence_sources)
    print(f"\nZone at ${level:.2f} (${zone.zone_low:.2f}-${zone.zone_high:.2f}):")
    print(f"  Score: {score:.1f}")
    print(f"  Sources found: {len(sources)}")
    if sources:
        for s in sources[:3]:  # Show first 3
            print(f"    - {s['type']}: {s.get('price', s.get('zone', 'N/A'))}")

# The fix: Add more confluence sources OR adjust the config
print("\n" + "="*50)
print("SOLUTIONS:")
print("1. Add HVN and Camarilla calculations to increase confluence")
print("2. Lower the L3 threshold in config.py")
print("3. Increase zone width multiplier to capture more levels")