# debug_full.py
import sys
import traceback
from datetime import datetime

print("="*80)
print("COMPREHENSIVE DEBUG - Testing each component")
print("="*80)

# Test 1: Can we import everything?
print("\n[TEST 1] Imports")
print("-"*40)
try:
    from data.polygon_client import PolygonClient
    print("✓ PolygonClient imported")
except Exception as e:
    print(f"✗ PolygonClient import failed: {e}")
    sys.exit(1)

try:
    from data.market_metrics import MetricsCalculator
    print("✓ MetricsCalculator imported")
except Exception as e:
    print(f"✗ MetricsCalculator import failed: {e}")
    sys.exit(1)

try:
    from discovery.zone_discovery import ZoneDiscoveryEngine
    print("✓ ZoneDiscoveryEngine imported")
except Exception as e:
    print(f"✗ ZoneDiscoveryEngine import failed: {e}")
    sys.exit(1)

try:
    from scanner.zone_scanner import ZoneScanner
    print("✓ ZoneScanner imported")
except Exception as e:
    print(f"✗ ZoneScanner import failed: {e}")
    sys.exit(1)

# Test 2: Can we connect to Polygon?
print("\n[TEST 2] Polygon Connection")
print("-"*40)
try:
    client = PolygonClient(base_url="http://localhost:8200/api/v1")
    success, msg = client.test_connection()
    if success:
        print(f"✓ {msg}")
    else:
        print(f"✗ {msg}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Connection test failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Can we fetch data?
print("\n[TEST 3] Data Fetching")
print("-"*40)
try:
    df = client.fetch_bars("AMD", "2025-08-20", "2025-08-26", "1day")
    if df is not None and not df.empty:
        print(f"✓ Fetched {len(df)} daily bars")
    else:
        print("✗ No daily data returned")
except Exception as e:
    print(f"✗ Fetch failed: {e}")
    traceback.print_exc()

# Test 4: Can we calculate metrics?
print("\n[TEST 4] Metrics Calculation")
print("-"*40)
try:
    calc = MetricsCalculator(client)
    metrics = calc.calculate_metrics("AMD", datetime(2025, 8, 26, 12, 30))
    if metrics:
        print(f"✓ Metrics calculated:")
        print(f"  Current Price: ${metrics.current_price:.2f}")
        print(f"  Daily ATR: ${metrics.atr_daily:.2f}")
        print(f"  M15 ATR: ${metrics.atr_m15:.2f}")
    else:
        print("✗ Metrics calculation returned None")
except Exception as e:
    print(f"✗ Metrics calculation failed: {e}")
    traceback.print_exc()

# Test 5: Check scanner initialization
print("\n[TEST 5] Scanner Initialization")
print("-"*40)
try:
    scanner = ZoneScanner()
    print("✓ Scanner created")
    
    # Check what methods it has
    methods = [m for m in dir(scanner) if not m.startswith('_')]
    print(f"  Available methods: {methods}")
    
    # Check initialize method
    if hasattr(scanner, 'initialize'):
        result = scanner.initialize()
        print(f"  initialize() returns: {result}")
    else:
        print("  ✗ No initialize() method")
    
    # Check scan method signature
    import inspect
    if hasattr(scanner, 'scan'):
        sig = inspect.signature(scanner.scan)
        print(f"  scan() signature: {sig}")
        print(f"  scan() parameters: {list(sig.parameters.keys())}")
    else:
        print("  ✗ No scan() method")
        
except Exception as e:
    print(f"✗ Scanner initialization failed: {e}")
    traceback.print_exc()

# Test 6: Try calling scan with different parameter names
print("\n[TEST 6] Scanner.scan() Parameters")
print("-"*40)
if 'scanner' in locals():
    # Try with 'symbol'
    try:
        result = scanner.scan(symbol="AMD")
        print("✓ scan(symbol='AMD') works")
    except TypeError as e:
        print(f"✗ scan(symbol='AMD') failed: {e}")
    
    # Try with 'ticker' (what CLI uses)
    try:
        result = scanner.scan(ticker="AMD")
        print("✓ scan(ticker='AMD') works")
    except TypeError as e:
        print(f"✗ scan(ticker='AMD') failed: {e}")
    
    # Show what CLI is trying to pass
    print("\n  CLI is trying to call with:")
    print("    ticker='AMD'")
    print("    analysis_datetime=datetime")
    print("    weekly_levels=[...]")
    print("    daily_levels=[...]")

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)