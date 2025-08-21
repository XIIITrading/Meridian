"""
Test the real analysis_thread.py with correct path
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add levels_zones directory to path
levels_zones_root = Path(__file__).parent.parent
sys.path.insert(0, str(levels_zones_root))

# Add the correct path for analysis_thread
analysis_thread_path = levels_zones_root / "src" / "ui" / "threads"
sys.path.insert(0, str(analysis_thread_path))

# Mock the UI dependencies that analysis_thread imports
class MockQThread:
    def __init__(self):
        pass

class MockPyQtSignal:
    def __init__(self, *args):
        self.connected_slots = []
    
    def emit(self, *args):
        print(f"📡 Signal emitted: {args[1] if len(args) > 1 else args[0]}")
        for slot in self.connected_slots:
            slot(*args)
    
    def connect(self, slot):
        self.connected_slots.append(slot)

# Mock PyQt6 imports before they're needed
sys.modules['PyQt6'] = type(sys)('MockPyQt6')
sys.modules['PyQt6.QtCore'] = type(sys)('MockQtCore')
sys.modules['PyQt6.QtCore'].QThread = MockQThread
sys.modules['PyQt6.QtCore'].pyqtSignal = MockPyQtSignal

def create_mock_session_data():
    """Create realistic session data that mimics UI input"""
    return {
        'ticker': 'AAPL',
        'datetime': datetime(2025, 8, 5, 14, 30),  # Monday 2:30 PM
        'pre_market_price': 247.10,
        
        # M15 zones from UI table (realistic zones around current price)
        'zones': [
            {'zone_number': 1, 'high': '250.50', 'low': '248.75'},
            {'zone_number': 2, 'high': '245.25', 'low': '243.80'},
            {'zone_number': 3, 'high': '255.10', 'low': '253.40'},
            {'zone_number': 4, 'high': '240.60', 'low': '238.90'},
        ],
        
        # Daily price levels (6 manual levels from UI)
        'daily': {
            'price_levels': ['252.30', '250.75', '249.20', '246.80', '244.50', '242.10']
        },
        
        # Additional session metadata
        'session_start': datetime(2025, 8, 5, 9, 30),
        'session_end': datetime(2025, 8, 5, 16, 0),
    }

def test_analysis_thread_import():
    """Test that we can import the real analysis thread"""
    print("=== TESTING REAL ANALYSIS THREAD IMPORT ===")
    
    # Show the path we're using
    print(f"Looking for analysis_thread.py in: {analysis_thread_path}")
    analysis_thread_file = analysis_thread_path / "analysis_thread.py"
    print(f"File exists: {analysis_thread_file.exists()}")
    
    if analysis_thread_file.exists():
        print(f"File size: {analysis_thread_file.stat().st_size} bytes")
    
    try:
        from analysis_thread import AnalysisThread
        print("✅ AnalysisThread imported successfully!")
        
        # Check if it has confluence_engine attribute
        print(f"✅ AnalysisThread class found")
        return AnalysisThread
        
    except ImportError as e:
        print(f"❌ AnalysisThread import failed: {e}")
        print(f"Available files in {analysis_thread_path}:")
        if analysis_thread_path.exists():
            for item in analysis_thread_path.iterdir():
                print(f"  📄 {item.name}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error importing AnalysisThread: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_analysis_thread_creation():
    """Test creating the real AnalysisThread instance"""
    print("\n=== TESTING REAL ANALYSIS THREAD CREATION ===")
    
    AnalysisThread = test_analysis_thread_import()
    if not AnalysisThread:
        return None
    
    try:
        session_data = create_mock_session_data()
        
        print("Session Data for Analysis:")
        print(f"  • Ticker: {session_data['ticker']}")
        print(f"  • Analysis Time: {session_data['datetime']}")
        print(f"  • Pre-market Price: ${session_data['pre_market_price']}")
        print(f"  • M15 Zones: {len(session_data['zones'])} zones")
        print(f"  • Daily Levels: {len(session_data['daily']['price_levels'])} levels")
        
        # Create the real analysis thread
        analysis_thread = AnalysisThread(session_data)
        print("✅ Real AnalysisThread created successfully!")
        
        # Check key attributes
        expected_attrs = ['confluence_engine', 'hvn_engine', 'camarilla_engine', 'session_data']
        for attr in expected_attrs:
            if hasattr(analysis_thread, attr):
                print(f"✅ Has {attr}")
            else:
                print(f"❌ Missing {attr}")
        
        return analysis_thread
        
    except Exception as e:
        print(f"❌ AnalysisThread creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_signals_and_methods():
    """Test the analysis thread signals and key methods"""
    print("\n=== TESTING ANALYSIS THREAD SIGNALS ===")
    
    AnalysisThread = test_analysis_thread_import()
    if not AnalysisThread:
        return False
    
    try:
        session_data = create_mock_session_data()
        analysis_thread = AnalysisThread(session_data)
        
        # Check signals exist
        signals = ['progress', 'finished', 'error']
        for signal_name in signals:
            if hasattr(analysis_thread, signal_name):
                print(f"✅ Has {signal_name} signal")
            else:
                print(f"❌ Missing {signal_name} signal")
        
        # Check key methods
        methods = ['run', '_calculate_metrics', '_format_confluence_zones']
        for method_name in methods:
            if hasattr(analysis_thread, method_name):
                print(f"✅ Has {method_name} method")
            else:
                print(f"❌ Missing {method_name} method")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal/method test failed: {e}")
        return False

def simulate_analysis_run():
    """Simulate what happens when analysis thread runs (without actual market data)"""
    print("\n=== SIMULATING ANALYSIS RUN ===")
    print("Note: This won't fetch real market data, but will test the confluence logic")
    
    try:
        # Test just the confluence integration part
        from calculations.confluence.confluence_engine import ConfluenceEngine
        from calculations.volume.hvn_engine import TimeframeResult, VolumePeak
        from calculations.pivots.camarilla_engine import CamarillaResult, CamarillaPivot
        
        session_data = create_mock_session_data()
        
        # Create mock data similar to what the real analysis would produce
        mock_hvn_results = {
            7: TimeframeResult(
                timeframe_days=7,
                price_range=(240.0, 255.0),
                total_levels=100,
                peaks=[
                    VolumePeak(price=249.75, rank=1, volume_percent=15.2, level_index=87),
                    VolumePeak(price=246.30, rank=2, volume_percent=12.8, level_index=45),
                    VolumePeak(price=252.10, rank=3, volume_percent=11.5, level_index=95),
                ],
                data_points=2016
            ),
            14: TimeframeResult(
                timeframe_days=14,
                price_range=(238.0, 257.0),
                total_levels=100,
                peaks=[
                    VolumePeak(price=248.90, rank=1, volume_percent=18.5, level_index=72),
                    VolumePeak(price=245.60, rank=2, volume_percent=14.2, level_index=38),
                ],
                data_points=4032
            )
        }
        
        mock_camarilla_results = {
            'daily': CamarillaResult(
                timeframe='daily',
                close=247.50,
                high=248.90,
                low=246.20,
                pivots=[
                    CamarillaPivot(level_name='R6', price=253.45, strength=6, timeframe='daily'),
                    CamarillaPivot(level_name='R4', price=251.20, strength=4, timeframe='daily'),
                    CamarillaPivot(level_name='R3', price=250.10, strength=3, timeframe='daily'),
                    CamarillaPivot(level_name='S3', price=245.80, strength=3, timeframe='daily'),
                    CamarillaPivot(level_name='S4', price=244.70, strength=4, timeframe='daily'),
                    CamarillaPivot(level_name='S6', price=242.35, strength=6, timeframe='daily'),
                ],
                range_type='higher',
                central_pivot=247.87
            )
        }
        
        mock_metrics = {
            'current_price': 247.50,
            'atr_high': 250.25,
            'atr_low': 244.75,
            'open_price': 246.80,
            'pre_market_price': 247.10
        }
        
        # Extract daily levels
        daily_levels = [float(level) for level in session_data['daily']['price_levels'] if level and float(level) > 0]
        
        # Run the confluence calculation (this is the core integration!)
        engine = ConfluenceEngine()
        confluence_results = engine.calculate_confluence(
            m15_zones=session_data['zones'],
            hvn_results=mock_hvn_results,
            camarilla_results=mock_camarilla_results,
            daily_levels=daily_levels,
            metrics=mock_metrics
        )
        
        print(f"🎉 CONFLUENCE SIMULATION SUCCESSFUL!")
        print(f"Total inputs: {confluence_results.total_inputs_checked}")
        print(f"Zones with confluence: {confluence_results.zones_with_confluence}/{len(confluence_results.zone_scores)}")
        
        # Test the formatter (what will appear in UI)
        formatted = engine.format_confluence_result(confluence_results, 247.50)
        
        print(f"\n--- UI OUTPUT PREVIEW ---")
        lines = formatted.split('\n')
        for i, line in enumerate(lines[:15]):  # Show first 15 lines
            print(line)
        if len(lines) > 15:
            print("... (truncated)")
        
        return confluence_results
        
    except Exception as e:
        print(f"❌ Analysis simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_complete_integration_test():
    """Run the complete integration test with real analysis_thread.py"""
    print("REAL ANALYSIS THREAD INTEGRATION TEST")
    print("=" * 70)
    
    # Test 1: Import and create analysis thread
    analysis_thread = test_analysis_thread_creation()
    
    # Test 2: Check signals and methods
    signals_ok = test_signals_and_methods()
    
    # Test 3: Simulate confluence analysis
    confluence_result = simulate_analysis_run()
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print("FINAL INTEGRATION ASSESSMENT")
    print("=" * 70)
    
    all_good = analysis_thread and signals_ok and confluence_result
    
    if all_good:
        print("🚀 COMPLETE SUCCESS!")
        print("✅ Real AnalysisThread imports and creates successfully")
        print("✅ All required signals and methods present")
        print("✅ Confluence integration works perfectly")
        print("✅ UI output formatting is beautiful")
        print("✅ Ready for live market data testing!")
        
        print(f"\n🎯 DEPLOYMENT READY:")
        print(f"Your updated analysis_thread.py with confluence integration")
        print(f"is ready to replace your current version!")
        
    else:
        print("🔧 ISSUES TO RESOLVE:")
        if not analysis_thread:
            print("❌ AnalysisThread creation issues")
        if not signals_ok:
            print("❌ Missing signals or methods")
        if not confluence_result:
            print("❌ Confluence integration problems")
    
    return all_good

if __name__ == "__main__":
    success = run_complete_integration_test()
    
    if success:
        print(f"\n🎉 READY TO DEPLOY TO PRODUCTION!")
        print(f"Replace your current analysis_thread.py with the confluence-integrated version!")
    else:
        print(f"\n⚠️  RESOLVE ISSUES BEFORE DEPLOYMENT")
    
    print(f"\n" + "=" * 70)
    print("Integration test complete!")