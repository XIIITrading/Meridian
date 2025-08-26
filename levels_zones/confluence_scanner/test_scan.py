# test_scan.py
import sys
from datetime import datetime
import traceback

print("Testing actual scan execution...\n")

try:
    from scanner.zone_scanner import ZoneScanner
    
    # Create scanner
    scanner = ZoneScanner()
    
    # Test data
    ticker = "AMD"
    analysis_datetime = datetime(2025, 8, 26, 12, 30, 0)
    weekly_levels = [177.70, 171.10, 158.70, 147.50]
    daily_levels = [184.50, 175.00, 173.20, 170.00, 166.50, 162.80]
    
    print(f"Calling scan with:")
    print(f"  ticker={ticker}")
    print(f"  analysis_datetime={analysis_datetime}")
    print(f"  weekly_levels={weekly_levels}")
    print(f"  daily_levels={daily_levels}")
    print()
    
    # Call scan exactly as CLI would
    result = scanner.scan(
        ticker=ticker,
        analysis_datetime=analysis_datetime,
        weekly_levels=weekly_levels,
        daily_levels=daily_levels
    )
    
    print("Scan completed!")
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    
    if 'error' in result:
        print(f"ERROR in result: {result['error']}")
    else:
        print(f"Symbol: {result.get('symbol')}")
        if 'metrics' in result:
            print(f"Metrics: Price=${result['metrics'].get('current_price')}")
        if 'zones' in result:
            print(f"Zones found: {len(result['zones'])}")
            
except Exception as e:
    print(f"\nFAILED: {e}")
    print("\nFull traceback:")
    traceback.print_exc()