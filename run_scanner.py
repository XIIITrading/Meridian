#!/usr/bin/env python
"""
Market Scanner Runner - Quick access to market scans including gap scans.
Place this in your root directory.
"""
import sys
import os
import argparse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Check if user wants the gap scanner shortcut
    if len(sys.argv) > 1 and sys.argv[1] in ['gap', 'gaps', 'gapper']:
        print("Launching Gap Scanner...")
        # Remove the 'gap' argument and add gap-specific defaults
        sys.argv.pop(1)
        
        # If no other arguments, default to gap_up scan of all equities
        if len(sys.argv) == 1:
            sys.argv.extend(['--profile', 'gap_up', '--list', 'all'])
        
        # Import and run the scanner
        from market_scanner.scripts.run_scan import main as run_scan
        return run_scan()
    
    # Otherwise, run normal scanner
    from market_scanner.scripts.run_scan import main as run_scan
    return run_scan()

if __name__ == "__main__":
    sys.exit(main())