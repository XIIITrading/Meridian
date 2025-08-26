# debug_zones.py
from datetime import datetime
from scanner.zone_scanner import ZoneScanner
from discovery.zone_discovery import ZoneDiscoveryEngine

# Setup
scanner = ZoneScanner()
ticker = "AMD"
analysis_datetime = datetime(2025, 8, 26, 12, 30, 0)
weekly_levels = [177.7, 171.1, 158.7, 147.5]
daily_levels = [184.5, 175.0, 173.2, 170.0, 166.5, 162.8]

# Get metrics
metrics = scanner.metrics_calculator.calculate_metrics(ticker, analysis_datetime)
print(f"Current Price: ${metrics.current_price:.2f}")
print(f"Daily ATR: ${metrics.atr_daily:.2f}")
print(f"M15 ATR: ${metrics.atr_m15:.2f}")

# Calculate scan bounds
scan_low = metrics.current_price - (2 * metrics.atr_daily)
scan_high = metrics.current_price + (2 * metrics.atr_daily)
print(f"\nScan Range: ${scan_low:.2f} - ${scan_high:.2f}")

# Show what confluence sources we're building
confluence_sources = {}
if weekly_levels:
    confluence_sources['weekly_zones'] = [
        {'name': f'WL{i+1}', 'level': level, 'low': level - 0.5, 'high': level + 0.5}
        for i, level in enumerate(weekly_levels) if level
    ]
if daily_levels:
    confluence_sources['daily_levels'] = daily_levels

print(f"\nConfluence sources provided:")
for key, value in confluence_sources.items():
    print(f"  {key}: {len(value)} items")

# Now let's manually test the discovery engine
engine = ZoneDiscoveryEngine()

# Check what the engine expects
print("\nZone Discovery Engine expects these confluence sources:")
print("  - hvn_peaks")
print("  - camarilla_pivots") 
print("  - weekly_zones")
print("  - daily_zones")
print("  - atr_zones")
print("  - daily_levels")

print("\nWe're only providing:")
print(f"  - weekly_zones: {len(confluence_sources.get('weekly_zones', []))} items")
print(f"  - daily_levels: {len(confluence_sources.get('daily_levels', []))} items")

# Test discovery
zones = engine.discover_zones(
    scan_low=scan_low,
    scan_high=scan_high,
    current_price=metrics.current_price,
    atr_15min=metrics.atr_m15,
    confluence_sources=confluence_sources
)

print(f"\nZones discovered: {len(zones)}")

# Let's check the confluence thresholds
print(f"\nConfluence thresholds (from config):")
print(f"  L3 (minimum for discovery): {engine.confluence_thresholds.get('L3', 'unknown')}")
print(f"  L4: {engine.confluence_thresholds.get('L4', 'unknown')}")
print(f"  L5: {engine.confluence_thresholds.get('L5', 'unknown')}")

# Let's calculate max possible score with our sources
max_score = 0
if 'weekly_zones' in confluence_sources:
    max_score += engine.confluence_weights.get('weekly_zones', 1.0) * 1.5  # with overlap
if 'daily_levels' in confluence_sources:
    max_score += engine.confluence_weights.get('daily_levels', 1.0) * len(daily_levels)

print(f"\nMax possible confluence score with provided sources: {max_score}")
print("This explains why no zones are found - not enough confluence sources!")