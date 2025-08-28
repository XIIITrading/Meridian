# File: C:\XIIITradingSystems\Meridian\confluence_system\test_market_structure.py
"""
Test market structure levels calculation
"""

import sys
from pathlib import Path
from datetime import datetime

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent))

def test_market_structure():
    """Test market structure calculation"""
    
    # CORRECT IMPORT PATH
    from confluence_scanner.calculations.market_structure.pd_market_structure import MarketStructureCalculator
    from confluence_scanner.data.polygon_client import PolygonClient
    
    # Initialize
    calc = MarketStructureCalculator()
    client = PolygonClient()
    
    # Test with SPY
    symbol = "SPY"
    analysis_time = datetime(2025, 1, 14, 14, 30, 0)  # 2:30 PM UTC
    
    print(f"Testing Market Structure for {symbol}")
    print(f"Analysis Time: {analysis_time}")
    print("=" * 60)
    
    # Fetch data
    print("\nFetching data...")
    daily_data = client.fetch_bars(symbol, "2025-01-01", "2025-01-14", "1day")
    intraday_data = client.fetch_bars(symbol, "2025-01-12", "2025-01-14", "5min")
    
    if daily_data is None or intraday_data is None:
        print("Failed to fetch data")
        return
    
    print(f"Daily bars: {len(daily_data)}")
    print(f"5-min bars: {len(intraday_data)}")
    
    # Calculate levels
    print("\nCalculating levels...")
    levels = calc.calculate_all_levels(daily_data, intraday_data, analysis_time)
    
    # Display results
    print("\n" + "=" * 60)
    print("MARKET STRUCTURE LEVELS:")
    print("-" * 60)
    for name, value in levels.items():
        print(f"{name}: ${value:.2f}")
    
    # Test formatting
    print("\n" + "=" * 60)
    print("CONFLUENCE FORMATTING:")
    print("-" * 60)
    
    atr_5min = 0.5  # Example 5-minute ATR
    formatted = calc.format_for_confluence(levels, atr_5min)
    
    print(f"Created {len(formatted)} confluence zones:")
    for item in formatted:
        print(f"  {item['name']}: ${item['low']:.2f} - ${item['high']:.2f} (center: ${item['level']:.2f})")
    
    return levels

if __name__ == "__main__":
    test_market_structure()
    print("\n✅ Market Structure test complete!")