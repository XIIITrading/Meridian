# market_review/market_filter_run.py
"""
Simple runner for the market filter
Supports both S&P 500 and All US Equities modes
"""

import sys
import os

# Add parent directory to path when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_review.pre_market.sp500_filter.market_filter import example_usage

def run_scanner(mode='sp500'):
    """Run scanner in specified mode."""
    if mode == 'all_equities':
        print("\n" + "="*70)
        print("WARNING: Scanning ALL US Equities")
        print("This will scan 5,000-10,000+ stocks and may take 30-60 minutes!")
        print("="*70)
        
        response = input("\nContinue? (y/n): ").strip().lower()
        if response != 'y':
            print("Scan cancelled.")
            return
    
    example_usage(mode=mode)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run market scanner')
    parser.add_argument('--mode', choices=['sp500', 'all_equities'], 
                       default='sp500', help='Scanner mode')
    args = parser.parse_args()
    
    run_scanner(mode=args.mode)