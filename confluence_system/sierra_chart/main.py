"""Main script for pulling zones from Supabase to Sierra Chart"""

import logging
import sys
from datetime import datetime, date, timedelta
from typing import Optional, List
import argparse

from .config import config
from .supabase_client import SupabaseClient
from .zone_fetcher import ZoneFetcher
from .sierra_exporter import SierraExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SierraChartIntegration:
    """Main integration class"""
    
    def __init__(self):
        """Initialize the integration"""
        logger.info("Initializing Sierra Chart Integration...")
        
        # Validate config
        try:
            config.validate()
            logger.info("Configuration validated successfully")
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
        
        # Initialize components
        try:
            self.supabase = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
            
            # Test connection
            if not self.supabase.test_connection():
                raise ConnectionError("Failed to connect to Supabase database")
            
            self.fetcher = ZoneFetcher(self.supabase)
            self.exporter = SierraExporter(config.SIERRA_CHART_PATH)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def run_interactive(self):
        """Run in interactive mode - prompt user for date and tickers"""
        print("\n" + "="*60)
        print("SIERRA CHART ZONE INTEGRATION")
        print("Pull confluence zones from Supabase → Sierra Chart")
        print("="*60)
        
        # Get available dates
        print("\nFetching available dates from database...")
        try:
            available_dates = self.supabase.fetch_available_dates(30)
        except Exception as e:
            print(f"ERROR: Failed to fetch available dates: {e}")
            return
        
        if not available_dates:
            print("ERROR: No zone data available in database")
            print("\nTry running the confluence CLI first:")
            print("  python confluence_cli.py TICKER DATE TIME -w WL1 WL2 WL3 WL4 -d DL1 DL2 DL3 DL4 --save-db")
            return
        
        print(f"\nFound {len(available_dates)} dates with zone data:")
        for i, dt in enumerate(available_dates[:15], 1):
            day_name = dt.strftime('%A')
            print(f"  {i:2}. {dt.strftime('%Y-%m-%d')} ({day_name})")
        
        # Get date selection
        selected_date = None
        while not selected_date:
            try:
                choice = input("\nEnter date (YYYY-MM-DD) or number from list: ").strip()
                
                if not choice:
                    print("Please enter a date or number")
                    continue
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_dates):
                        selected_date = available_dates[idx]
                    else:
                        print(f"Invalid number. Please enter 1-{len(available_dates)}")
                else:
                    try:
                        selected_date = datetime.strptime(choice, '%Y-%m-%d').date()
                        # Verify this date has data
                        if selected_date not in available_dates:
                            print(f"Warning: {selected_date} may not have zone data")
                    except ValueError:
                        print("Invalid date format. Use YYYY-MM-DD or select a number")
                        
            except (ValueError, IndexError, KeyboardInterrupt):
                print("\nOperation cancelled")
                return
        
        print(f"\nSelected date: {selected_date.strftime('%Y-%m-%d (%A)')}")
        
        # Get ticker selection
        print("\nTicker Selection:")
        print("  - Press Enter for ALL tickers")
        print("  - Enter comma-separated list (e.g., TSLA,AAPL,NVDA)")
        
        ticker_input = input("Enter tickers: ").strip()
        
        if ticker_input:
            tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
            print(f"\nSelected tickers: {', '.join(tickers)}")
        else:
            tickers = None
            print("\nSelected: ALL tickers")
        
        # Get minimum confluence score filter
        try:
            min_score_input = input("\nMinimum confluence score (0-10, default=0): ").strip()
            min_score = float(min_score_input) if min_score_input else 0.0
            print(f"Minimum confluence score: {min_score}")
        except ValueError:
            min_score = 0.0
            print("Using default minimum score: 0.0")
        
        # Fetch and export
        print(f"\n{'='*60}")
        self._fetch_and_export(selected_date, tickers, min_score)
    
    def run_with_args(self, trade_date: date, tickers: Optional[List[str]] = None, 
                     min_confluence_score: float = 0.0):
        """Run with specific arguments"""
        print(f"\nRunning Sierra Chart integration:")
        print(f"  Date: {trade_date}")
        print(f"  Tickers: {', '.join(tickers) if tickers else 'ALL'}")
        print(f"  Min Confluence Score: {min_confluence_score}")
        
        self._fetch_and_export(trade_date, tickers, min_confluence_score)
    
    def _fetch_and_export(self, trade_date: date, tickers: Optional[List[str]] = None,
                         min_confluence_score: float = 0.0):
        """Fetch zones and export to Sierra Chart format"""
        
        print(f"\n{'='*60}")
        print(f"FETCHING ZONES FOR {trade_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}")
        
        try:
            # Fetch zones
            print("\n[1] Fetching zones from Supabase database...")
            zones_by_ticker = self.fetcher.fetch_and_process_zones(
                trade_date, 
                tickers, 
                min_confluence_score
            )
            
            if not zones_by_ticker:
                print("\nERROR: No zones found for specified criteria")
                print("\nPossible solutions:")
                print("  1. Check that confluence analysis was run for this date")
                print("  2. Verify --save-db was used when running confluence CLI")
                print("  3. Try a different date or lower minimum confluence score")
                return
            
            # Display summary
            print(f"\n[2] Processing complete - Found zones for {len(zones_by_ticker)} tickers:")
            
            total_zones = 0
            for ticker, zones in zones_by_ticker.items():
                level_counts = {}
                score_sum = 0
                max_score = 0
                
                for zone in zones:
                    level = zone.confluence_level
                    level_counts[level] = level_counts.get(level, 0) + 1
                    score_sum += zone.confluence_score
                    max_score = max(max_score, zone.confluence_score)
                
                avg_score = score_sum / len(zones) if zones else 0
                level_str = ', '.join(f"{level}:{count}" for level, count in sorted(level_counts.items()))
                
                print(f"    {ticker:6}: {len(zones):2} zones | Levels: {level_str:15} | Avg: {avg_score:.1f} | Max: {max_score:.1f}")
                total_zones += len(zones)
            
            print(f"\n    TOTAL: {total_zones} zones across {len(zones_by_ticker)} tickers")
            
            # Get zone statistics
            stats = self.fetcher.get_zone_statistics(zones_by_ticker)
            print(f"\n[3] Zone Statistics:")
            print(f"    Confluence Range: {stats['confluence_stats']['min']:.1f} - {stats['confluence_stats']['max']:.1f}")
            print(f"    Average Score: {stats['confluence_stats']['avg']:.1f}")
            print(f"    Level Distribution: {stats['level_distribution']}")
            
            # Export to Sierra Chart format
            print(f"\n[4] Exporting to Sierra Chart format...")
            output_file = self.exporter.export_zones(zones_by_ticker, trade_date)
            
            # Create ACSIL header file
            header_file = self.exporter.create_acsil_header_file()
            
            print(f"\n{'='*60}")
            print("SUCCESS: ZONES EXPORTED TO SIERRA CHART")
            print(f"{'='*60}")
            print(f"\nOutput Location: {config.SIERRA_CHART_PATH}")
            print(f"\nFiles Created:")
            print(f"  - confluence_zones.json     - Master file with all data")
            print(f"  - zones_summary.json        - Statistics summary")
            print(f"  - confluence_zones.h        - ACSIL C++ header")
            
            for ticker in zones_by_ticker:
                print(f"  - {ticker}_zones.json         - Individual ticker data")
            
            print(f"\nNext Steps:")
            print(f"  1. Compile your ACSIL study in Sierra Chart")
            print(f"  2. Add the study to your charts")
            print(f"  3. The study will automatically read the zone files")
            print(f"  4. Zones will appear as colored rectangles on your charts")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error during fetch and export: {e}")
            print(f"\nERROR: {e}")
            print("\nCheck the logs for more details")
            raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Pull zones from Supabase for Sierra Chart',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py                                    # Interactive mode
  python main.py --today                           # Today's zones (all tickers)
  python main.py --yesterday                       # Yesterday's zones
  python main.py --date 2025-08-28                 # Specific date
  python main.py --date 2025-08-28 --tickers TSLA,AAPL  # Specific date and tickers
  python main.py --yesterday --min-score 5.0       # Yesterday's zones with min score
        '''
    )
    
    parser.add_argument('--date', type=str, 
                       help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--tickers', type=str, 
                       help='Comma-separated ticker list (e.g., TSLA,AAPL,NVDA)')
    parser.add_argument('--yesterday', action='store_true', 
                       help='Use yesterday\'s date')
    parser.add_argument('--today', action='store_true', 
                       help='Use today\'s date')
    parser.add_argument('--min-score', type=float, default=0.0,
                       help='Minimum confluence score to include (default: 0.0)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize integration
        integration = SierraChartIntegration()
        
        # Parse tickers
        tickers = None
        if args.tickers:
            tickers = [t.strip().upper() for t in args.tickers.split(',') if t.strip()]
        
        # Determine mode
        if args.date:
            trade_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            integration.run_with_args(trade_date, tickers, args.min_score)
        elif args.yesterday:
            trade_date = date.today() - timedelta(days=1)
            integration.run_with_args(trade_date, tickers, args.min_score)
        elif args.today:
            trade_date = date.today()
            integration.run_with_args(trade_date, tickers, args.min_score)
        else:
            # Interactive mode
            integration.run_interactive()
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFATAL ERROR: {e}")
        print("Check your configuration and database connection")
        sys.exit(1)

if __name__ == "__main__":
    main()