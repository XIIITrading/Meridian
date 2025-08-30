#!/usr/bin/env python3
"""
Test script for Monte Carlo Engine Integration
Run this to verify everything works together
"""

import sys
from pathlib import Path

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import validate_config, get_config_summary
from data_loader import DataLoader
from main import MonteCarloAPI

def test_configuration():
    """Test configuration and dependencies"""
    print("=" * 60)
    print("MONTE CARLO ENGINE - CONFIGURATION TEST")
    print("=" * 60)
    
    # Validate config
    errors = validate_config()
    if errors:
        print("CONFIGURATION ERRORS:")
        for error in errors:
            print(f"  ERROR: {error}")
        return False
    
    # Show config summary
    config = get_config_summary()
    print("Configuration Status:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    return True

def test_database_connectivity():
    """Test database connectivity"""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTIVITY TEST")
    print("=" * 60)
    
    try:
        loader = DataLoader()
        
        if not loader.db_service.enabled:
            print("ERROR: Database service not enabled")
            return False
        
        print("SUCCESS: Database service connected")
        
        # Test getting available sessions
        sessions = loader.get_available_sessions()
        print(f"Available sessions: {len(sessions)}")
        
        if sessions:
            print("Sample sessions:")
            for session in sessions[:3]:
                print(f"  {session['ticker_id']}: {session['ticker']} on {session['session_date']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def test_full_integration():
    """Test full Monte Carlo integration"""
    print("\n" + "=" * 60)
    print("FULL INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Initialize API
        api = MonteCarloAPI()
        
        # Get available sessions
        loader = DataLoader()
        sessions = loader.get_available_sessions()
        
        if not sessions:
            print("ERROR: No sessions available for testing")
            print("Run confluence CLI with --save-db first to create test data")
            return False
        
        # Use most recent session
        test_ticker_id = sessions[0]['ticker_id']
        print(f"Testing with: {test_ticker_id}")
        
        # Validate ticker ID
        if not api._validate_ticker_id(test_ticker_id):
            print(f"ERROR: Invalid ticker ID: {test_ticker_id}")
            return False
        
        print("SUCCESS: Ticker ID validation passed")
        
        # Test zone loading
        zones = loader.fetch_zones_from_database(test_ticker_id)
        
        if not zones:
            print(f"ERROR: No zones found for {test_ticker_id}")
            return False
        
        print(f"SUCCESS: Loaded {len(zones)} zones with confluence data")
        
        # Display zone summary
        print("\nZone Summary:")
        for zone in zones[:3]:  # Show first 3
            print(f"  Zone {zone['zone_number']}: ${zone['low']:.2f}-${zone['high']:.2f} "
                  f"({zone['confluence_level']}, Score: {zone['confluence_score']:.1f})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_full_test():
    """Run all tests"""
    print("MONTE CARLO ENGINE - COMPREHENSIVE TEST")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Configuration
    if test_configuration():
        print("✓ Configuration test PASSED")
        tests_passed += 1
    else:
        print("✗ Configuration test FAILED")
    
    # Test 2: Database connectivity
    if test_database_connectivity():
        print("✓ Database connectivity test PASSED")
        tests_passed += 1
    else:
        print("✗ Database connectivity test FAILED")
    
    # Test 3: Full integration
    if test_full_integration():
        print("✓ Full integration test PASSED")
        tests_passed += 1
    else:
        print("✗ Full integration test FAILED")
    
    # Final results
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 80)
    
    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED - Monte Carlo engine is ready!")
        print("\nNext steps:")
        print("  1. Run: python main.py --list")
        print("  2. Run: python main.py TICKER.MMDDYY")
        print("  3. Check results in Supabase database")
        return True
    else:
        print("\n❌ Some tests failed - check configuration and database setup")
        return False

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)