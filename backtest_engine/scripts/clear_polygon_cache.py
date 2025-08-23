"""
Clear Polygon API server cache
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import requests
from data.polygon_fetcher import PolygonBacktestFetcher

def clear_cache(symbol=None):
    """Clear the Polygon REST API cache"""
    print("\n" + "="*60)
    print("CLEARING POLYGON API CACHE")
    print("="*60)
    
    fetcher = PolygonBacktestFetcher()
    
    if symbol:
        print(f"Clearing cache for {symbol}...")
        success = fetcher.clear_cache(symbol)
    else:
        print("Clearing entire cache...")
        success = fetcher.clear_cache()
    
    if success:
        print("✓ Cache cleared successfully")
    else:
        print("✗ Failed to clear cache")
    
    # Also try direct DELETE request
    try:
        base_url = "http://localhost:8200/api/v1"
        if symbol:
            response = requests.delete(f"{base_url}/cache?symbol={symbol}")
        else:
            response = requests.delete(f"{base_url}/cache")
        
        if response.status_code == 200:
            print("✓ Direct cache clear successful")
        else:
            print(f"Direct cache clear returned: {response.status_code}")
    except Exception as e:
        print(f"Direct cache clear failed: {e}")

def test_fresh_fetch(symbol="NVDA", date="2025-08-19"):
    """Test fetching fresh data"""
    print("\n" + "="*60)
    print("TESTING FRESH DATA FETCH")
    print("="*60)
    
    fetcher = PolygonBacktestFetcher()
    
    # Fetch WITHOUT cache
    print(f"\nFetching {symbol} for {date} WITHOUT cache...")
    
    df = fetcher.fetch_bars(
        symbol=symbol,
        start_date=date,
        end_date=date,
        timeframe='1min',
        use_cache=False  # Force fresh data
    )
    
    if df is not None and not df.empty:
        print(f"✓ Got {len(df)} bars")
        print(f"  Range: {df.index[0]} to {df.index[-1]}")
        
        # Check if we have market hours data now
        market_start = df[df.index.hour >= 14]  # 14:00 UTC = 10:00 ET
        if not market_start.empty:
            print(f"✓ Market hours data found: {len(market_start)} bars")
        else:
            print("✗ Still no market hours data")
    else:
        print("✗ No data returned")

if __name__ == "__main__":
    print("This will clear the Polygon API server cache")
    
    choice = input("\n1. Clear all cache\n2. Clear specific symbol\n3. Test fetch\nChoice: ").strip()
    
    if choice == "1":
        clear_cache()
    elif choice == "2":
        symbol = input("Symbol to clear: ").strip().upper()
        clear_cache(symbol)
    elif choice == "3":
        symbol = input("Symbol (default NVDA): ").strip().upper() or "NVDA"
        date = input("Date YYYY-MM-DD (default 2025-08-19): ").strip() or "2025-08-19"
        clear_cache(symbol)  # Clear first
        test_fresh_fetch(symbol, date)
    else:
        print("Invalid choice")