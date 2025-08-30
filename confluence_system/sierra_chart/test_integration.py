#!/usr/bin/env python3
"""
Test script for Sierra Chart Integration
Run this to verify everything works together
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work"""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    try:
        from sierra_chart.config import config
        print("✓ config.py imported successfully")
    except Exception as e:
        print(f"✗ Error importing config: {e}")
        return False
    
    try:
        from sierra_chart.supabase_client import SupabaseClient
        print("✓ supabase_client.py imported successfully")
    except Exception as e:
        print(f"✗ Error importing supabase_client: {e}")
        return False
    
    try:
        from sierra_chart.zone_fetcher import ZoneFetcher
        print("✓ zone_fetcher.py imported successfully")
    except Exception as e:
        print(f"✗ Error importing zone_fetcher: {e}")
        return False
    
    try:
        from sierra_chart.sierra_exporter import SierraExporter
        print("✓ sierra_exporter.py imported successfully")
    except Exception as e:
        print(f"✗ Error importing sierra_exporter: {e}")
        return False
    
    try:
        from sierra_chart.main import SierraChartIntegration
        print("✓ main.py imported successfully")
    except Exception as e:
        print(f"✗ Error importing main: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration validation"""
    print("\\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    try:
        from sierra_chart.config import config
        
        # Check environment variables
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            print("✓ Supabase credentials found in environment")
        else:
            print("✗ Missing Supabase credentials in .env file")
            return False
        
        # Test config validation
        config.validate()
        print("✓ Configuration validation passed")
        print(f"  - Sierra Chart Path: {config.SIERRA_CHART_PATH}")
        print(f"  - Output Filename: {config.OUTPUT_FILENAME}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\\n" + "=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        from sierra_chart.config import config
        from sierra_chart.supabase_client import SupabaseClient
        
        # Initialize client
        client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        print("✓ Supabase client initialized")
        
        # Test connection
        if client.test_connection():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
            return False
        
        # Test fetching available dates
        available_dates = client.fetch_available_dates(5)
        print(f"✓ Found {len(available_dates)} dates with zone data")
        
        if available_dates:
            print("  Recent dates:")
            for dt in available_dates[:3]:
                print(f"    - {dt}")
        else:
            print("  No zone data found - run confluence CLI with --save-db first")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_full_integration():
    """Test full integration if data is available"""
    print("\\n" + "=" * 60)
    print("TESTING FULL INTEGRATION")
    print("=" * 60)
    
    try:
        from sierra_chart.main import SierraChartIntegration
        
        # Initialize integration
        integration = SierraChartIntegration()
        print("✓ Sierra Chart integration initialized")
        
        # Get available dates
        available_dates = integration.supabase.fetch_available_dates(5)
        
        if not available_dates:
            print("⚠ No zone data available for testing")
            print("  Run confluence CLI with --save-db to create test data")
            return True  # Not a failure, just no data
        
        # Test with most recent date
        test_date = available_dates[0]
        print(f"✓ Testing with date: {test_date}")
        
        # Fetch zones (limit to avoid too much output)
        zones_by_ticker = integration.fetcher.fetch_and_process_zones(
            test_date, 
            tickers=None,  # All tickers
            min_confluence_score=0.0
        )
        
        if zones_by_ticker:
            total_zones = sum(len(zones) for zones in zones_by_ticker.values())
            print(f"✓ Successfully fetched {total_zones} zones for {len(zones_by_ticker)} tickers")
            
            # Show summary
            for ticker, zones in list(zones_by_ticker.items())[:3]:  # Limit output
                print(f"  - {ticker}: {len(zones)} zones")
        else:
            print("⚠ No zones found for test date")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("SIERRA CHART INTEGRATION - TEST SUITE")
    print("=" * 80)
    print(f"Test time: {datetime.now()}")
    print("=" * 80)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("Database Connection Tests", test_database_connection),
        ("Full Integration Tests", test_full_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\\n❌ {test_name} FAILED with exception: {e}")
    
    print("\\n" + "=" * 80)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\\n🎉 ALL TESTS PASSED! Sierra Chart integration is ready to use.")
        print("\\nNext steps:")
        print("  1. python -m sierra_chart.main --help")
        print("  2. python -m sierra_chart.main  # Interactive mode")
        print("  3. python -m sierra_chart.main --today  # Command line mode")
    else:
        print(f"\\n⚠️ {total - passed} tests failed. Check configuration and database setup.")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)