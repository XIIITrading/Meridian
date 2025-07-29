#!/usr/bin/env python
"""
Runner script for market scanner.
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run
from market_scanner.scripts.run_scan import main

if __name__ == "__main__":
    sys.exit(main())