#!/usr/bin/env python3
"""
Launcher script for Meridian Pre-Market Trading System
"""

import sys
import os
from pathlib import Path
import traceback

def run_meridian():
    """Run the Meridian trading system with proper path configuration"""
    try:
        # Set UTF-8 encoding for Windows
        if sys.platform == 'win32':
            import locale
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            
        print("=" * 60)
        print("LAUNCHING MERIDIAN PRE-MARKET TRADING SYSTEM")
        print("=" * 60)
        
        # Get the directory containing this script
        current_dir = Path(__file__).parent.resolve()
        
        # Add the levels_zones directory to path
        levels_zones_dir = current_dir / 'levels_zones'
        if levels_zones_dir.exists():
            sys.path.insert(0, str(levels_zones_dir))
            sys.path.insert(0, str(levels_zones_dir / 'src'))
            print(f"Working directory: {levels_zones_dir}")
        else:
            print(f"ERROR: Directory not found: {levels_zones_dir}")
            return
        
        # Change to the levels_zones directory
        os.chdir(levels_zones_dir)
        
        # Import and run the main application
        print("Starting application...")
        from main import main
        main()
        
    except ImportError as e:
        print(f"ERROR: Import error - {e}")
        print("\nTroubleshooting:")
        print("1. Check that all required packages are installed")
        print("2. Run: pip install -r requirements.txt")
        print(f"\nTraceback:\n{traceback.format_exc()}")
        
    except Exception as e:
        print(f"ERROR starting application: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has the required API keys")
        print("2. Ensure Supabase and Polygon credentials are valid")
        print("3. Make sure the Polygon REST API server is running")
        print(f"\nTraceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    # Set output encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    run_meridian()