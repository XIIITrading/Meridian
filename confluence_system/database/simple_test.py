#!/usr/bin/env python3
"""
Simple database connection test - Windows compatible (no Unicode)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        from database.service import DatabaseService
        
        print("1. Initializing database service...")
        db = DatabaseService()
        
        if db.enabled:
            print("   SUCCESS: Database connected!")
            
            # Test basic query
            print("2. Testing basic queries...")
            recent = db.list_recent_analyses(3)
            print(f"   Found {len(recent)} recent analyses")
            
            if recent:
                print("   Recent analyses:")
                for analysis in recent:
                    ticker_id = analysis['ticker_id']
                    ticker = analysis['ticker']
                    price = analysis.get('current_price', 'N/A')
                    print(f"     - {ticker_id}: {ticker} @ ${price}")
                
                # Test detailed query
                print("3. Testing detailed query...")
                summary = db.get_analysis_summary(recent[0]['ticker_id'])
                if summary:
                    print(f"   SUCCESS: Got details for {summary['ticker']}")
                    print(f"   Zones: {summary['zone_count']}")
                else:
                    print("   WARNING: No detailed data found")
            
            print("\n" + "=" * 60)
            print("DATABASE TEST COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print("\nYou can now:")
            print("1. Use the database from PyCharm console")
            print("2. Run confluence CLI with --save-db")
            print("3. Query data for Monte Carlo analysis")
            
            return True
        else:
            print("   ERROR: Database connection failed")
            print("   Check your .env file and Supabase credentials")
            return False
            
    except ImportError as e:
        print(f"   ERROR: Missing dependencies: {e}")
        print("   Run: pip install supabase python-dotenv")
        return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if not success:
        sys.exit(1)
    
    print("\nREADY FOR USE!")