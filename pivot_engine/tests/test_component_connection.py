"""
Debug Script 1: Component Connection Test
Tests all imports and basic component initialization for Pivot Engine
"""

import sys
import os
import traceback
from pathlib import Path

# Add both root and src to path based on your structure
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_core_imports():
    """Test all pivot engine core imports"""
    print("🔍 Testing Core Pivot Engine Imports...")
    
    try:
        # Core calculations (from root level)
        from calculations.pivots.camarilla_engine import CamarillaEngine
        print("✅ CamarillaEngine imported")
        
        from calculations.confluence.pivot_confluence_engine import PivotConfluenceEngine
        print("✅ PivotConfluenceEngine imported")
        
        from calculations.volume.hvn_engine import HVNEngine
        print("✅ HVNEngine imported")
        
        # Zone calculators
        from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
        print("✅ WeeklyZoneCalculator imported")
        
        from calculations.zones.daily_zone_calc import DailyZoneCalculator
        print("✅ DailyZoneCalculator imported")
        
        from calculations.zones.atr_zone_calc import ATRZoneCalculator
        print("✅ ATRZoneCalculator imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        traceback.print_exc()
        return False

def test_ui_imports():
    """Test UI component imports"""
    print("\n🔍 Testing UI Component Imports...")
    
    try:
        # UI Components (from src)
        from ui.widgets.overview_widget.pivot_confluence_widget import PivotConfluenceWidget
        print("✅ PivotConfluenceWidget imported")
        
        from ui.widgets.overview_widget.app_overview import OverviewWidget
        print("✅ OverviewWidget imported")
        
        # Analysis thread
        from ui.threads.analysis_thread import AnalysisThread
        print("✅ AnalysisThread imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ UI import failed: {e}")
        traceback.print_exc()
        return False

def test_data_model_imports():
    """Test data model imports"""
    print("\n🔍 Testing Data Model Imports...")
    
    try:
        # Data models (from src)
        from data.models import TradingSession, PivotConfluenceData, WeeklyData, DailyData
        print("✅ Core data models imported")
        
        from data.models import TrendDirection
        print("✅ Enum models imported")
        
        # Services
        from services.database_service import DatabaseService
        print("✅ DatabaseService imported")
        
        from data.supabase_client import SupabaseClient
        print("✅ SupabaseClient imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Data model import failed: {e}")
        traceback.print_exc()
        return False

def test_component_initialization():
    """Test component initialization"""
    print("\n🔍 Testing Component Initialization...")
    
    try:
        # Initialize core engines
        from calculations.pivots.camarilla_engine import CamarillaEngine
        from calculations.confluence.pivot_confluence_engine import PivotConfluenceEngine
        from calculations.volume.hvn_engine import HVNEngine
        
        camarilla_engine = CamarillaEngine()
        print("✅ CamarillaEngine initialized")
        
        pivot_confluence_engine = PivotConfluenceEngine()
        print("✅ PivotConfluenceEngine initialized")
        
        hvn_engine = HVNEngine()
        print("✅ HVNEngine initialized")
        
        # Test zone calculators
        from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
        from calculations.zones.daily_zone_calc import DailyZoneCalculator
        from calculations.zones.atr_zone_calc import ATRZoneCalculator
        
        weekly_calc = WeeklyZoneCalculator()
        daily_calc = DailyZoneCalculator()
        atr_calc = ATRZoneCalculator()
        
        print("✅ All zone calculators initialized")
        
        # Test database service (won't connect without credentials)
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        print("✅ DatabaseService initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        traceback.print_exc()
        return False

def check_m15_removal():
    """Verify that M15 components have been completely removed"""
    print("\n🔍 Checking M15 Component Removal...")
    
    try:
        # These imports should fail if M15 components are properly removed
        m15_components_found = []
        
        # Check for M15 zone calculator in candlestick folder
        try:
            from calculations.candlestick.m15_zone_calc import M15ZoneCalculator
            m15_components_found.append("M15ZoneCalculator (still exists)")
        except ImportError:
            print("✅ M15ZoneCalculator properly removed or doesn't exist")
        
        # Check if any M15 references remain in key files
        key_files = [
            "src/ui/widgets/overview_widget/app_overview.py",
            "src/services/database_service.py",
            "src/data/supabase_client.py",
            "src/ui/threads/analysis_thread.py"
        ]
        
        m15_references = []
        
        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if ('m15' in line.lower() or 'M15' in line) and not line.strip().startswith('#'):
                                m15_references.append(f"{file_path}:{i} - {line.strip()}")
                except Exception as e:
                    print(f"⚠️  Could not read {file_path}: {e}")
        
        if m15_components_found:
            print(f"❌ M15 components still found: {m15_components_found}")
            return False
        elif m15_references:
            print(f"⚠️  M15 references still found:")
            for ref in m15_references[:5]:  # Show first 5
                print(f"   {ref}")
            if len(m15_references) > 5:
                print(f"   ... and {len(m15_references) - 5} more")
            print("   (Manual review needed - could be comments or legitimate references)")
            return True
        else:
            print("✅ M15 components completely removed")
            return True
            
    except Exception as e:
        print(f"❌ M15 removal check failed: {e}")
        return False

def test_path_setup():
    """Test that paths are set up correctly"""
    print("\n🔍 Testing Path Setup...")
    
    try:
        print(f"Project root: {project_root}")
        print(f"Src path: {project_root / 'src'}")
        print(f"Python path entries:")
        for i, path in enumerate(sys.path[:5]):  # Show first 5
            print(f"   {i}: {path}")
        
        # Check key directories exist
        dirs_to_check = [
            "calculations",
            "src/data", 
            "src/ui",
            "src/services"
        ]
        
        for dir_path in dirs_to_check:
            full_path = project_root / dir_path
            if full_path.exists():
                print(f"✅ Directory exists: {dir_path}")
            else:
                print(f"❌ Directory missing: {dir_path}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Path setup failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("PIVOT ENGINE DEBUG: Component Connection Test")
    print("=" * 70)
    
    path_ok = test_path_setup()
    core_ok = test_core_imports()
    ui_ok = test_ui_imports()
    data_ok = test_data_model_imports()
    init_ok = test_component_initialization()
    m15_ok = check_m15_removal()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"Path Setup: {'✅ PASS' if path_ok else '❌ FAIL'}")
    print(f"Core Imports: {'✅ PASS' if core_ok else '❌ FAIL'}")
    print(f"UI Imports: {'✅ PASS' if ui_ok else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if data_ok else '❌ FAIL'}")
    print(f"Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
    print(f"M15 Removal: {'✅ PASS' if m15_ok else '❌ FAIL'}")
    
    if all([path_ok, core_ok, ui_ok, data_ok, init_ok, m15_ok]):
        print("\n🎉 ALL COMPONENT TESTS PASSED - System Ready!")
    else:
        print("\n🚨 SOME TESTS FAILED - Review Issues Above")
    
    print("=" * 70)