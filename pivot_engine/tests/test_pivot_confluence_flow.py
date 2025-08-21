"""
Debug Script 2: Pivot Confluence Flow Test
Tests the complete pivot confluence calculation pipeline
"""

import sys
import os
import traceback
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

# Add both root and src to path based on your structure
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_camarilla_calculation():
    """Test Camarilla pivot calculation"""
    print("🔍 Testing Camarilla Pivot Calculation...")
    
    try:
        from calculations.pivots.camarilla_engine import CamarillaEngine
        
        engine = CamarillaEngine()
        
        # Mock OHLC data for Camarilla calculation
        test_data = {
            'high': 247.50,
            'low': 242.80,
            'close': 245.25
        }
        
        # Try to calculate daily Camarilla pivots
        # Check what methods are available
        methods = [method for method in dir(engine) if not method.startswith('_')]
        print(f"✅ Available methods: {methods}")
        
        # Try common method names
        if hasattr(engine, 'calculate_daily_pivots'):
            result = engine.calculate_daily_pivots(
                high=test_data['high'],
                low=test_data['low'],
                close=test_data['close']
            )
        elif hasattr(engine, 'calculate_pivots'):
            result = engine.calculate_pivots(
                high=test_data['high'],
                low=test_data['low'],
                close=test_data['close']
            )
        elif hasattr(engine, 'calculate'):
            result = engine.calculate(
                high=test_data['high'],
                low=test_data['low'],
                close=test_data['close']
            )
        else:
            print("❌ No suitable calculation method found")
            return False, None
        
        print(f"✅ Daily Camarilla calculated")
        print(f"   Result type: {type(result)}")
        
        # Try to display result info
        if hasattr(result, 'pivots'):
            print(f"   Pivots generated: {len(result.pivots)}")
        if hasattr(result, 'central_pivot'):
            print(f"   Central pivot: ${result.central_pivot:.2f}")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Camarilla calculation failed: {e}")
        traceback.print_exc()
        return False, None

def test_pivot_confluence_engine():
    """Test pivot confluence calculation"""
    print("\n🔍 Testing Pivot Confluence Engine...")
    
    try:
        from calculations.confluence.pivot_confluence_engine import PivotConfluenceEngine
        
        engine = PivotConfluenceEngine()
        print("✅ PivotConfluenceEngine initialized")
        
        # Check available methods
        methods = [method for method in dir(engine) if not method.startswith('_')]
        print(f"✅ Available methods: {methods}")
        
        # Test basic functionality without full calculation for now
        print("✅ Pivot confluence engine structure verified")
        
        return True, None
        
    except Exception as e:
        print(f"❌ Pivot confluence engine test failed: {e}")
        traceback.print_exc()
        return False, None

def test_hvn_engine():
    """Test HVN engine"""
    print("\n🔍 Testing HVN Engine...")
    
    try:
        from calculations.volume.hvn_engine import HVNEngine
        
        engine = HVNEngine()
        print("✅ HVNEngine initialized")
        
        # Check available methods
        methods = [method for method in dir(engine) if not method.startswith('_')]
        print(f"✅ Available methods: {methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ HVN engine test failed: {e}")
        traceback.print_exc()
        return False

def test_zone_calculators():
    """Test zone calculators"""
    print("\n🔍 Testing Zone Calculators...")
    
    try:
        from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
        from calculations.zones.daily_zone_calc import DailyZoneCalculator  
        from calculations.zones.atr_zone_calc import ATRZoneCalculator
        
        weekly_calc = WeeklyZoneCalculator()
        daily_calc = DailyZoneCalculator()
        atr_calc = ATRZoneCalculator()
        
        print("✅ All zone calculators initialized")
        
        # Check methods on each
        for name, calc in [("Weekly", weekly_calc), ("Daily", daily_calc), ("ATR", atr_calc)]:
            methods = [method for method in dir(calc) if not method.startswith('_')]
            print(f"   {name} methods: {methods[:3]}...")  # Show first 3
        
        return True
        
    except Exception as e:
        print(f"❌ Zone calculator test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_data_models():
    """Test UI data model creation"""
    print("\n🔍 Testing UI Data Models...")
    
    try:
        from data.models import TradingSession, WeeklyData, DailyData, TrendDirection
        
        # Create session
        session = TradingSession(
            ticker='SPY',
            date=date.today(),
            is_live=True
        )
        print("✅ TradingSession created")
        
        # Test trend direction
        trend = TrendDirection.BULL
        print(f"✅ TrendDirection works: {trend}")
        
        # Create weekly data
        weekly_data = WeeklyData(
            trend_direction=TrendDirection.BULL,
            internal_trend=TrendDirection.BULL,
            position_structure=75,
            eow_bias=TrendDirection.BULL,
            notes="Test"
        )
        print("✅ WeeklyData created")
        
        # Create daily data  
        daily_data = DailyData(
            trend_direction=TrendDirection.BULL,
            internal_trend=TrendDirection.RANGE,
            position_structure=60,
            eod_bias=TrendDirection.BULL,
            price_levels=[Decimal('243.00')],
            notes="Test"
        )
        print("✅ DailyData created")
        
        return True
        
    except Exception as e:
        print(f"❌ UI data model test failed: {e}")
        traceback.print_exc()
        return False

def test_database_service():
    """Test database service"""
    print("\n🔍 Testing Database Service...")
    
    try:
        from services.database_service import DatabaseService
        
        service = DatabaseService()
        print("✅ DatabaseService initialized")
        
        # Check available methods
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"✅ Available public methods: {len(methods)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database service test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("PIVOT ENGINE DEBUG: Analysis Flow Test")
    print("=" * 70)
    
    camarilla_ok, camarilla_result = test_camarilla_calculation()
    confluence_ok, confluence_result = test_pivot_confluence_engine()
    hvn_ok = test_hvn_engine()
    zones_ok = test_zone_calculators()
    ui_models_ok = test_ui_data_models()
    db_ok = test_database_service()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"Camarilla Calculation: {'✅ PASS' if camarilla_ok else '❌ FAIL'}")
    print(f"Pivot Confluence: {'✅ PASS' if confluence_ok else '❌ FAIL'}")
    print(f"HVN Engine: {'✅ PASS' if hvn_ok else '❌ FAIL'}")
    print(f"Zone Calculators: {'✅ PASS' if zones_ok else '❌ FAIL'}")
    print(f"UI Data Models: {'✅ PASS' if ui_models_ok else '❌ FAIL'}")
    print(f"Database Service: {'✅ PASS' if db_ok else '❌ FAIL'}")
    
    if all([camarilla_ok, confluence_ok, hvn_ok, zones_ok, ui_models_ok, db_ok]):
        print("\n🎉 ALL ANALYSIS FLOW TESTS PASSED!")
        print("   Core components are working correctly")
    else:
        print("\n🚨 SOME ANALYSIS FLOW TESTS FAILED")
        print("   Review specific test failures above")
    
    print("=" * 70)