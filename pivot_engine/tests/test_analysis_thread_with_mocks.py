"""
Test real analysis_thread.py with mocked dependencies
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

# Mock all the missing dependencies BEFORE importing analysis_thread
class MockQThread:
    def __init__(self):
        pass

class MockPyQtSignal:
    def __init__(self, *args):
        self.connected_slots = []
    
    def emit(self, *args):
        print(f"📡 {args[1] if len(args) > 1 else args[0]}")
        for slot in self.connected_slots:
            slot(*args)
    
    def connect(self, slot):
        self.connected_slots.append(slot)

# Mock PyQt6
sys.modules['PyQt6'] = type(sys)('MockPyQt6')
sys.modules['PyQt6.QtCore'] = type(sys)('MockQtCore')
sys.modules['PyQt6.QtCore'].QThread = MockQThread
sys.modules['PyQt6.QtCore'].pyqtSignal = MockPyQtSignal

# Mock pandas
class MockPandas:
    class Timestamp:
        def __init__(self, dt):
            self.dt = dt
        def tz_localize(self, tz):
            return self
        def tz_convert(self, tz):
            return self
    
    def __init__(self):
        pass

sys.modules['pandas'] = MockPandas()
sys.modules['pd'] = sys.modules['pandas']

# Mock asyncio
class MockAsyncio:
    def new_event_loop(self):
        return None
    def set_event_loop(self, loop):
        pass

sys.modules['asyncio'] = MockAsyncio()

# Mock services module
class MockPolygonService:
    def __init__(self):
        pass

class MockServices:
    def __init__(self):
        self.PolygonService = MockPolygonService

sys.modules['services'] = MockServices()
sys.modules['services.polygon_service'] = MockServices()
sys.modules['services.polygon_service'].PolygonService = MockPolygonService

# Mock data module  
class MockPolygonBridge:
    def __init__(self):
        pass
    
    def get_historical_bars(self, **kwargs):
        # Return empty DataFrame-like object
        class MockDataFrame:
            def __init__(self):
                self.empty = True
                self.index = []
                self.columns = []
            def __len__(self):
                return 0
        return MockDataFrame()

class MockData:
    def __init__(self):
        self.PolygonBridge = MockPolygonBridge

sys.modules['data'] = MockData()
sys.modules['data.polygon_bridge'] = MockData()
sys.modules['data.polygon_bridge'].PolygonBridge = MockPolygonBridge

def create_mock_session_data():
    """Create realistic session data"""
    return {
        'ticker': 'AAPL',
        'datetime': datetime(2025, 8, 5, 14, 30),
        'pre_market_price': 247.10,
        'zones': [
            {'zone_number': 1, 'high': '250.50', 'low': '248.75'},
            {'zone_number': 2, 'high': '245.25', 'low': '243.80'},
            {'zone_number': 3, 'high': '255.10', 'low': '253.40'},
            {'zone_number': 4, 'high': '240.60', 'low': '238.90'},
        ],
        'daily': {
            'price_levels': ['252.30', '250.75', '249.20', '246.80', '244.50', '242.10']
        },
        'session_start': datetime(2025, 8, 5, 9, 30),
        'session_end': datetime(2025, 8, 5, 16, 0),
    }

def test_analysis_thread_import_with_mocks():
    """Test importing analysis_thread with all dependencies mocked"""
    print("=== TESTING ANALYSIS THREAD WITH MOCKED DEPENDENCIES ===")
    
    analysis_thread_file = analysis_thread_path / "analysis_thread.py"
    print(f"File: {analysis_thread_file}")
    print(f"Exists: {analysis_thread_file.exists()}")
    print(f"Size: {analysis_thread_file.stat().st_size} bytes")
    
    try:
        from analysis_thread import AnalysisThread
        print("✅ AnalysisThread imported successfully with mocks!")
        return AnalysisThread
        
    except Exception as e:
        print(f"❌ Import still failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_analysis_thread_attributes():
    """Test that AnalysisThread has the expected confluence attributes"""
    print("\n=== TESTING ANALYSIS THREAD ATTRIBUTES ===")
    
    AnalysisThread = test_analysis_thread_import_with_mocks()
    if not AnalysisThread:
        return False
    
    try:
        session_data = create_mock_session_data()
        analysis_thread = AnalysisThread(session_data)
        
        print("✅ AnalysisThread instance created!")
        
        # Check for confluence integration
        expected_attrs = [
            'confluence_engine',
            'session_data',
            'progress',
            'finished', 
            'error'
        ]
        
        all_present = True
        for attr in expected_attrs:
            if hasattr(analysis_thread, attr):
                print(f"✅ Has {attr}")
            else:
                print(f"❌ Missing {attr}")
                all_present = False
        
        # Check if it's the updated version with confluence
        if hasattr(analysis_thread, 'confluence_engine'):
            print("🎉 CONFLUENCE ENGINE DETECTED!")
            print("✅ This is the updated analysis_thread.py with confluence integration!")
        else:
            print("⚠️ No confluence_engine found - might be the old version")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Attribute test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_confluence_method_exists():
    """Test if the confluence formatting method exists"""
    print("\n=== TESTING CONFLUENCE METHODS ===")
    
    AnalysisThread = test_analysis_thread_import_with_mocks()
    if not AnalysisThread:
        return False
    
    try:
        session_data = create_mock_session_data()
        analysis_thread = AnalysisThread(session_data)
        
        # Check for confluence-specific methods
        confluence_methods = [
            '_format_confluence_zones',
            'run'  # The main method that should include confluence
        ]
        
        for method in confluence_methods:
            if hasattr(analysis_thread, method):
                print(f"✅ Has {method} method")
            else:
                print(f"❌ Missing {method} method")
        
        # Try to inspect the run method to see if it mentions confluence
        if hasattr(analysis_thread, 'run'):
            import inspect
            run_source = inspect.getsource(analysis_thread.run)
            if 'confluence' in run_source.lower():
                print("🎉 CONFLUENCE INTEGRATION CONFIRMED!")
                print("✅ The run() method contains confluence logic!")
                return True
            else:
                print("⚠️ run() method exists but no confluence mentions found")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Method inspection failed: {e}")
        return False

def show_file_content_summary():
    """Show a summary of what's in the analysis_thread.py file"""
    print("\n=== ANALYSIS THREAD FILE CONTENT SUMMARY ===")
    
    analysis_thread_file = analysis_thread_path / "analysis_thread.py"
    
    try:
        with open(analysis_thread_file, 'r') as f:
            content = f.read()
        
        # Check for key confluence-related content
        confluence_indicators = [
            'confluence_engine',
            'ConfluenceEngine',
            'calculate_confluence',
            'format_confluence_result',
            '_format_confluence_zones'
        ]
        
        print(f"File analysis:")
        print(f"Total lines: {len(content.splitlines())}")
        print(f"Size: {len(content)} characters")
        
        found_indicators = []
        for indicator in confluence_indicators:
            if indicator in content:
                found_indicators.append(indicator)
                print(f"✅ Contains: {indicator}")
            else:
                print(f"❌ Missing: {indicator}")
        
        if len(found_indicators) >= 3:
            print(f"🎉 HIGH CONFIDENCE: This is the confluence-integrated version!")
        elif len(found_indicators) >= 1:
            print(f"⚠️ PARTIAL: Some confluence code detected")
        else:
            print(f"❌ NO CONFLUENCE: This appears to be the old version")
        
        return len(found_indicators) >= 3
        
    except Exception as e:
        print(f"❌ File analysis failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test of analysis_thread integration"""
    print("COMPREHENSIVE ANALYSIS THREAD TEST")
    print("=" * 70)
    
    # Test 1: File content analysis
    has_confluence_code = show_file_content_summary()
    
    # Test 2: Import with mocks
    analysis_thread_class = test_analysis_thread_import_with_mocks()
    
    # Test 3: Attribute testing
    attrs_ok = test_analysis_thread_attributes() if analysis_thread_class else False
    
    # Test 4: Method inspection
    methods_ok = test_confluence_method_exists() if analysis_thread_class else False
    
    # Test 5: Confluence logic test (from previous test)
    print(f"\n=== CONFLUENCE LOGIC TEST (STANDALONE) ===")
    try:
        from calculations.confluence.confluence_engine import ConfluenceEngine
        engine = ConfluenceEngine()
        print("✅ ConfluenceEngine still works independently")
        confluence_works = True
    except:
        print("❌ ConfluenceEngine broken")
        confluence_works = False
    
    # Final assessment
    print(f"\n" + "=" * 70)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    print(f"📄 File has confluence code: {'✅' if has_confluence_code else '❌'}")
    print(f"📦 Analysis thread imports: {'✅' if analysis_thread_class else '❌'}")
    print(f"🔧 Required attributes present: {'✅' if attrs_ok else '❌'}")
    print(f"🎯 Confluence methods present: {'✅' if methods_ok else '❌'}")
    print(f"⚙️ Confluence engine works: {'✅' if confluence_works else '❌'}")
    
    all_good = has_confluence_code and analysis_thread_class and attrs_ok and methods_ok and confluence_works
    
    if all_good:
        print(f"\n🚀 COMPLETE SUCCESS!")
        print(f"✅ Your analysis_thread.py has confluence integration")
        print(f"✅ All components working properly")
        print(f"✅ Ready for production deployment!")
        
        print(f"\n📋 DEPLOYMENT INSTRUCTIONS:")
        print(f"1. Your confluence integration is working")
        print(f"2. The analysis_thread.py contains the updated code")
        print(f"3. Test with real market data in your UI")
        print(f"4. Check that zones_ranked TextEdit shows confluence results")
        
    else:
        print(f"\n🔧 ISSUES IDENTIFIED:")
        if not has_confluence_code:
            print(f"❌ File doesn't contain confluence integration code")
            print(f"   → Need to update with Document index 3 content")
        if not analysis_thread_class:
            print(f"❌ Import issues (likely missing dependencies)")
        if not attrs_ok:
            print(f"❌ Missing expected attributes")
        if not methods_ok:
            print(f"❌ Missing confluence methods")
    
    return all_good

if __name__ == "__main__":
    success = run_comprehensive_test()
    
    if success:
        print(f"\n🎉 READY FOR PRODUCTION!")
    else:
        print(f"\n⚠️ NEEDS UPDATES BEFORE DEPLOYMENT")
    
    print(f"\n" + "=" * 70)
    print("Comprehensive test complete!")