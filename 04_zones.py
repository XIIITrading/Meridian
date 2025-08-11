#!/usr/bin/env python3
"""
Quick launcher for Meridian Pre-Market Trading System
Save as: run_zones.py (in the Meridian root directory)
"""

import sys
import os
from pathlib import Path

def run_meridian():
    """Launch the Meridian Trading System"""
    
    # Find the levels_zones directory
    script_dir = Path(__file__).parent
    levels_zones_dir = script_dir / "levels_zones"
    
    # Check if levels_zones directory exists
    if not levels_zones_dir.exists():
        print(f"❌ Error: levels_zones directory not found at {levels_zones_dir}")
        print("Make sure you're running this from the Meridian root directory")
        sys.exit(1)
    
    # Change to levels_zones directory
    os.chdir(levels_zones_dir)
    
    # Add levels_zones to Python path
    sys.path.insert(0, str(levels_zones_dir))
    
    print("=" * 60)
    print("🚀 Launching Meridian Pre-Market Trading System")
    print("=" * 60)
    print(f"📁 Working directory: {levels_zones_dir}")
    
    try:
        # Import and run the main application
        from main import main
        print("✓ Starting application...")
        main()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that levels_zones/main.py exists")
        print("2. Verify all dependencies are installed")
        print("3. Make sure you have a virtual environment activated")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has the required API keys")
        print("2. Ensure Supabase and Polygon credentials are valid") 
        print("3. Make sure the Polygon REST API server is running")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_meridian()