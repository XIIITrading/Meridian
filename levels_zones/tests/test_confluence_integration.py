"""
Test script for confluence engine integration
Tests imports, data structures, and basic functionality
"""

import sys
import os
from pathlib import Path

# Add levels_zones directory to path (parent of tests)
levels_zones_root = Path(__file__).parent.parent
sys.path.insert(0, str(levels_zones_root))

print(f"Levels_zones root: {levels_zones_root}")
print(f"Python path: {sys.path[:3]}")

def test_imports():
    """Test all required imports work"""
    print("\n=== TESTING IMPORTS ===")
    
    try:
        from calculations.confluence.confluence_engine import ConfluenceEngine
        print("✅ ConfluenceEngine imported successfully")
    except ImportError as e:
        print(f"❌ ConfluenceEngine import failed: {e}")
        return False
    
    try:
        from calculations.volume.hvn_engine import TimeframeResult
        print("✅ TimeframeResult imported successfully")
    except ImportError as e:
        print(f"❌ TimeframeResult import failed: {e}")
        return False
        
    try:
        from calculations.pivots.camarilla_engine import CamarillaResult
        print("✅ CamarillaResult imported successfully")
    except ImportError as e:
        print(f"❌ CamarillaResult import failed: {e}")
        return False
    
    return True

def show_directory_structure():
    """Show the actual directory structure"""
    print("\n=== DIRECTORY STRUCTURE ===")
    
    levels_zones = Path(__file__).parent.parent
    print(f"levels_zones: {levels_zones}")
    
    calc_dir = levels_zones / "calculations"
    print(f"calculations exists: {calc_dir.exists()}")
    
    if calc_dir.exists():
        print("\nCalculations structure:")
        for item in calc_dir.rglob("*"):
            relative_path = item.relative_to(calc_dir)
            if item.is_dir():
                print(f"  📁 {relative_path}/")
            else:
                print(f"  📄 {relative_path}")

def show_data_structures():
    """Create and display sample data structures"""
    print("\n=== DATA STRUCTURES ===")
    
    try:
        from calculations.volume.hvn_engine import TimeframeResult
        print("\n--- TimeframeResult Structure ---")
        print("TimeframeResult attributes:")
        attrs = [attr for attr in dir(TimeframeResult) if not attr.startswith('_')]
        for attr in attrs:
            print(f"  • {attr}")
        
    except ImportError as e:
        print(f"Cannot import TimeframeResult: {e}")
    
    try:
        from calculations.pivots.camarilla_engine import CamarillaResult
        print("\n--- CamarillaResult Structure ---")
        print("CamarillaResult attributes:")
        attrs = [attr for attr in dir(CamarillaResult) if not attr.startswith('_')]
        for attr in attrs:
            print(f"  • {attr}")
        
    except ImportError as e:
        print(f"Cannot import CamarillaResult: {e}")

def test_confluence_with_mock_data():
    """Test confluence engine with mock data"""
    print("\n=== TESTING CONFLUENCE ENGINE ===")
    
    try:
        from calculations.confluence.confluence_engine import ConfluenceEngine
    except ImportError as e:
        print(f"❌ Cannot import ConfluenceEngine: {e}")
        return None
    
    # Mock M15 zones (realistic format from UI)
    mock_zones = [
        {'zone_number': 1, 'high': '250.50', 'low': '248.75'},
        {'zone_number': 2, 'high': '245.25', 'low': '243.80'},
        {'zone_number': 3, 'high': '255.10', 'low': '253.40'},
        {'zone_number': 4, 'high': '240.60', 'low': '238.90'},
    ]
    
    # Mock daily levels (6 levels: 3 above, 3 below current price)
    mock_daily_levels = [252.30, 250.75, 249.20, 246.80, 244.50, 242.10]
    
    # Mock metrics (ATR and reference prices)
    mock_metrics = {
        'current_price': 247.50,
        'atr_high': 250.25,
        'atr_low': 244.75,
        'open_price': 246.80,
        'pre_market_price': 247.10
    }
    
    print("Mock Data:")
    print(f"M15 Zones: {len(mock_zones)} zones")
    print(f"Daily Levels: {mock_daily_levels}")
    print(f"Current Price: ${mock_metrics['current_price']}")
    
    # Test confluence engine
    engine = ConfluenceEngine()
    
    try:
        result = engine.calculate_confluence(
            m15_zones=mock_zones,
            hvn_results=None,  # Start without HVN/Camarilla
            camarilla_results=None,
            daily_levels=mock_daily_levels,
            metrics=mock_metrics
        )
        
        print(f"\n✅ Confluence calculation successful!")
        print(f"Zones processed: {len(result.zone_scores)}")
        print(f"Total inputs: {result.total_inputs_checked}")
        print(f"Zones with confluence: {result.zones_with_confluence}")
        
        # Show formatted output
        print("\n--- Formatted Output ---")
        formatted = engine.format_confluence_result(result, mock_metrics['current_price'])
        print(formatted)
        
        return result
        
    except Exception as e:
        print(f"❌ Confluence calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("CONFLUENCE INTEGRATION TEST")
    print("=" * 50)
    
    # Step 1: Show directory structure
    show_directory_structure()
    
    # Step 2: Test imports
    if not test_imports():
        print("\n❌ Import tests failed - check if files exist")
    else:
        # Step 3: Show data structures  
        show_data_structures()
        
        # Step 4: Test basic confluence
        test_confluence_with_mock_data()
    
    print("\n" + "=" * 50)
    print("Test complete! Check results above.")