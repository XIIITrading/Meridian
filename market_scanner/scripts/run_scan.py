#!/usr/bin/env python
"""
Main script to run market scanner.
"""
import sys
import os

# Add the parent of market_scanner to Python path
scanner_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
meridian_root = os.path.dirname(scanner_root)
sys.path.insert(0, meridian_root)

import argparse
from datetime import datetime
import logging

# Now import from market_scanner package
from market_scanner.config import config
from market_scanner.data import TickerList
from market_scanner.filters import FilterCriteria
from market_scanner.scanners import PremarketScanner
from market_scanner.outputs import CSVExporter, SupabaseExporter, MarkdownExporter, ReportFormatter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run market scanner')
    parser.add_argument('--list', type=str, default='sp500', 
                       choices=['sp500', 'nasdaq100', 'russell2000', 'dow30'],
                       help='Ticker list to scan')
    parser.add_argument('--profile', type=str, default='relaxed',
                       choices=['strict', 'relaxed', 'momentum', 'penny_stocks'],
                       help='Filter profile to use')
    parser.add_argument('--output', type=str, nargs='+', 
                       default=['console', 'csv'],
                       choices=['console', 'csv', 'markdown', 'supabase'],
                       help='Output formats')
    parser.add_argument('--top', type=int, default=20,
                       help='Number of top stocks to display')
    
    args = parser.parse_args()
    
    print("Market Scanner")
    print("=" * 70)
    print(f"Scan Time: {datetime.now()}")
    print(f"Ticker List: {args.list.upper()}")
    print(f"Filter Profile: {args.profile}")
    print()
    
    # Initialize scanner
    try:
        ticker_list = TickerList(args.list)
        criteria = FilterCriteria.from_profile(args.profile)
        
        scanner = PremarketScanner(
            ticker_list=ticker_list,
            filter_criteria=criteria
        )
        
        # Progress callback
        def progress(completed, total, ticker):
            if completed % 10 == 0 or completed == total:
                print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%) - Current: {ticker}")
        
        # Run scan
        print("Starting scan...")
        scan_results = scanner.run_scan(progress_callback=progress)
        
        if scan_results.empty:
            print("\nNo stocks passed filters.")
            return
        
        # Get summary
        summary = scanner.get_summary_stats(scan_results)
        
        # Output results
        for output_format in args.output:
            if output_format == 'console':
                print(ReportFormatter.format_console_output(scan_results, args.top))
                
                # Show score explanation for top stock
                if len(scan_results) > 0:
                    top_stock = scan_results.iloc[0]
                    explanation = scanner.filter.explain_score(top_stock)
                    print(f"\nScore explanation for {top_stock['ticker']}:")
                    print(ReportFormatter.format_score_explanation(explanation))
            
            elif output_format == 'csv':
                path = CSVExporter.export(scan_results)
                print(f"\n✅ CSV exported to: {path}")
            
            elif output_format == 'markdown':
                path = MarkdownExporter.export(
                    scan_results, 
                    summary, 
                    criteria.to_dict()
                )
                print(f"\n✅ Markdown report exported to: {path}")
            
            elif output_format == 'supabase':
                success = SupabaseExporter.export(scan_results, datetime.now())
                if success:
                    print("\n✅ Results pushed to Supabase")
                else:
                    print("\n❌ Failed to push to Supabase")
        
        # Print summary
        print(f"\nScan Summary:")
        print(f"  Pass rate: {summary['pass_rate']}")
        print(f"  Avg interest score: {summary.get('avg_interest_score', 0):.2f}")
        print(f"  Top 5: {', '.join(summary.get('top_5_tickers', []))}")
        
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())