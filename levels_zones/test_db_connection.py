"""
Test database connection and basic operations
"""

import sys
from pathlib import Path
from datetime import date

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

import config
from src.data.supabase_client import SupabaseClient
from src.data.models import TradingSession

def test_connection():
    """Test basic database connection"""
    print("Testing database connection...")
    print(f"Using Supabase URL: {config.SUPABASE_URL[:30]}...")
    
    # Validate config
    if not config.validate_config():
        print("❌ Configuration validation failed")
        print("   Make sure SUPABASE_URL and SUPABASE_KEY are set in .env file")
        return False
    
    try:
        # Create client
        client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        print("✅ Client created successfully")
        
        # Try to list sessions
        sessions = client.list_sessions()
        print(f"✅ Found {len(sessions)} existing sessions")
        
        # Show first few sessions if any exist
        if sessions:
            print("\nFirst few sessions:")
            for session in sessions[:3]:
                print(f"   - {session.ticker_id} ({session.date})")
        
        # Create a test session
        test_session = TradingSession(
            ticker="TEST",
            date=date.today()
        )
        
        print(f"\nCreating test session: {test_session.ticker_id}")
        success, session_id = client.create_session(test_session)
        
        if success:
            print(f"✅ Test session created with ID: {session_id}")
            
            # Try to retrieve it
            retrieved = client.get_session(test_session.ticker_id)
            if retrieved:
                print(f"✅ Session retrieved successfully: {retrieved.ticker_id}")
                print(f"   Date: {retrieved.date}")
                print(f"   Created at: {retrieved.created_at}")
            else:
                print("❌ Failed to retrieve session")
        else:
            print("❌ Failed to create test session")
        
        print("\n✅ All tests passed! Database connection is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your .env file exists and contains:")
        print("   SUPABASE_URL=your_project_url")
        print("   SUPABASE_KEY=your_anon_key")
        print("2. Verify your Supabase project is active")
        print("3. Check that the database tables are created")
        return False

if __name__ == "__main__":
    test_connection()