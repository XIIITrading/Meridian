#!/usr/bin/env python
"""
Quick scanner runner with default settings.
Runs SP500 scan with relaxed profile, outputs to both console and Supabase.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the market scanner with default settings."""
    
    # Get the directory where this script is located (root directory)
    root_dir = Path(__file__).parent
    
    # Change to the root directory
    os.chdir(root_dir)
    
    # Define the command to run
    cmd = [
        sys.executable,  # Use the same Python interpreter
        "market_scanner/scripts/run_scan.py",
        "--list", "sp500",
        "--profile", "relaxed", 
        "--output", "console", "supabase",  # Show in terminal AND push to Supabase
        "--top", "10"
    ]
    
    print("🚀 Starting Market Scanner...")
    print("=" * 60)
    print("Settings:")
    print("  • List: S&P 500")  
    print("  • Profile: Relaxed")
    print("  • Output: Console + Supabase")
    print("  • Top Results: 10")
    print("=" * 60)
    print()
    
    try:
        # Run the scanner
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("✅ Scanner completed successfully!")
        print("📊 Check your Supabase dashboard for the data")
        print("=" * 60)
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Scanner failed with error code: {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n\n⚠️  Scanner interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    # Keep window open on Windows if run by double-clicking
    if os.name == 'nt' and not sys.stdin.isatty():
        input("\nPress Enter to exit...")
    
    sys.exit(exit_code)