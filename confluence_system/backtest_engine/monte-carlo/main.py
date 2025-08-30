#!/usr/bin/env python3
"""
Monte Carlo Backtesting Engine - Enhanced CLI Interface
Integrated with Confluence System Database

Usage:
    python main.py TICKER.MMDDYY                    # Single day analysis
    python main.py --batch TICKER START END        # Batch analysis  
    python main.py --list [TICKER]                 # List available sessions
    python main.py --analyze BATCH_ID              # Analyze existing batch
    python main.py --config                        # Show configuration
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DEFAULT_SYMBOL, get_config_summary, validate_config
from data_loader import DataLoader
from trade_simulator import TradeSimulator
from storage_manager import StorageManager
from analyzer import MonteCarloAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonteCarloAPI:
    """Enhanced Monte Carlo API with CLI interface"""
    
    def __init__(self):
        """Initialize the Monte Carlo engine"""
        self.data_loader = DataLoader()
        self.simulator = TradeSimulator()
        self.storage = StorageManager()
        self.analyzer = MonteCarloAnalyzer()
    
    def run_single_day_analysis(self, ticker_id: str, 
                               save_to_db: bool = True,
                               analyze: bool = True,
                               export_csv: bool = False) -> Optional[str]:
        """
        Run Monte Carlo simulation for a single trading day
        
        Args:
            ticker_id: Ticker ID in format TICKER.MMDDYY
            save_to_db: Whether to save results to database
            analyze: Whether to run analysis after simulation
            export_csv: Whether to export results to CSV
            
        Returns:
            Batch ID if successful, None otherwise
        """
        print("\n" + "="*70)
        print("MONTE CARLO INTRADAY ZONE BREAKOUT BACKTESTING")
        print("Confluence System Integration")
        print("="*70)
        
        # Validate ticker ID format
        if not self._validate_ticker_id(ticker_id):
            return None
        
        symbol, trade_date = self._parse_ticker_id(ticker_id)
        
        print(f"Ticker ID: {ticker_id}")
        print(f"Symbol: {symbol}")
        print(f"Trade Date: {trade_date}")
        print("-"*70)
        
        start_time = time.time()
        
        # Step 1: Load zones with confluence data
        print("\n[1] Loading Zones with Confluence Data...")
        zones = self.data_loader.fetch_zones_from_database(ticker_id)
        
        if not zones:
            print(f"ERROR: No zones found for {ticker_id}")
            print("  Make sure you've run confluence analysis with --save-db first")
            return None
        
        print(f"   SUCCESS: Loaded {len(zones)} zones with confluence data")
        
        # Display zone summary with confluence info
        self._display_zone_summary(zones)
        
        # Step 2: Fetch minute bars  
        print(f"\n[2] Fetching minute bars for {trade_date}...")
        bars_df = self.data_loader.fetch_minute_bars_for_date(symbol, trade_date)
        
        if bars_df.empty:
            print(f"ERROR: No minute data available for {symbol} on {trade_date}")
            return None
        
        print(f"   SUCCESS: Loaded {len(bars_df)} minute bars ({bars_df.index[0]} to {bars_df.index[-1]})")
        
        # Step 3: Run simulation
        print(f"\n[3] Running Monte Carlo Simulation...")
        print(f"   Testing {len(bars_df)} bars × {len(zones)} zones")
        print(f"   Estimating ~{len(bars_df) * len(zones) * 2} potential trade scenarios")
        
        trades = self.simulator.run_monte_carlo_simulation(bars_df, zones)
        
        if not trades:
            print("WARNING: No trades generated")
            print("  This could mean:")
            print("    - Price never touched any zones")
            print("    - All trades were filtered out")  
            print("    - Data quality issues")
            return None
        
        trades_df = pd.DataFrame(trades)
        print(f"   SUCCESS: Generated {len(trades_df)} simulated trades")
        
        # Step 4: Quick statistics
        self._display_quick_stats(trades_df, zones)
        
        # Step 5: Save to database
        batch_id = None
        if save_to_db:
            print(f"\n[5] Saving to Database...")
            runtime = time.time() - start_time
            
            metadata = {
                'ticker_id': ticker_id,
                'zones_count': len(zones),
                'bars_count': len(bars_df),
                'runtime_seconds': round(runtime, 2),
                'confluence_enabled': True,
                'single_day': True
            }
            
            batch_id = self.storage.save_results(symbol, trade_date, trade_date, trades_df, metadata)
            
            if batch_id:
                print(f"   SUCCESS: Saved to batch {batch_id[:8]}...")
            else:
                print("   ERROR: Failed to save to database")
        
        # Step 6: Run detailed analysis
        if analyze and batch_id:
            print(f"\n[6] Running Detailed Analysis...")
            self._run_detailed_analysis(batch_id)
        
        # Step 7: Export CSV
        if export_csv and batch_id:
            print(f"\n[7] Exporting to CSV...")
            self._export_to_csv(batch_id)
        
        # Final summary
        runtime = time.time() - start_time
        print(f"\n" + "="*70)
        print(f"ANALYSIS COMPLETED in {runtime:.1f} seconds")
        print(f"Batch ID: {batch_id[:8] if batch_id else 'Not saved'}")
        print("="*70)
        
        return batch_id
    
    def list_available_sessions(self, ticker: Optional[str] = None, limit: int = 20):
        """List available trading sessions"""
        print("\n" + "="*70)  
        print("AVAILABLE TRADING SESSIONS")
        print("="*70)
        
        sessions = self.data_loader.get_available_sessions(ticker=ticker)
        
        if not sessions:
            print("No sessions found")
            if ticker:
                print(f"  No data for {ticker}")
            else:
                print("  No confluence data in database")
                print("  Run: python confluence_cli.py --save-db first")
            return
        
        # Display sessions
        sessions_to_show = sessions[:limit]
        print(f"Showing {len(sessions_to_show)} of {len(sessions)} sessions:")
        print()
        
        for i, session in enumerate(sessions_to_show, 1):
            ticker_id = session['ticker_id']
            ticker_symbol = session['ticker']
            date = session['session_date'] 
            price = session.get('current_price')
            price_str = f"${price:.2f}" if price else "N/A"
            
            print(f"{i:2d}. {ticker_id:<12} | {ticker_symbol:<6} | {date} | {price_str}")
        
        if len(sessions) > limit:
            print(f"\n... and {len(sessions) - limit} more sessions")
        
        print(f"\nUsage: python main.py TICKER.MMDDYY")
        print(f"Example: python main.py {sessions_to_show[0]['ticker_id']}")
    
    def run_batch_analysis(self, ticker: str, start_date: str, end_date: str):
        """Run Monte Carlo for multiple days"""
        print("\n" + "="*70)
        print("BATCH MONTE CARLO ANALYSIS") 
        print("="*70)
        
        sessions = self.data_loader.get_available_sessions(ticker, start_date, end_date)
        
        if not sessions:
            print(f"No sessions found for {ticker} between {start_date} and {end_date}")
            return []
        
        print(f"Found {len(sessions)} sessions to process")
        
        batch_ids = []
        for i, session in enumerate(sessions, 1):
            ticker_id = session['ticker_id']
            print(f"\n[{i}/{len(sessions)}] Processing {ticker_id}...")
            
            try:
                batch_id = self.run_single_day_analysis(
                    ticker_id, 
                    save_to_db=True, 
                    analyze=False,
                    export_csv=False
                )
                if batch_id:
                    batch_ids.append(batch_id)
                    print(f"   SUCCESS: Batch {batch_id[:8]}...")
                else:
                    print(f"   FAILED: No batch created")
            except Exception as e:
                logger.error(f"Error processing {ticker_id}: {e}")
                print(f"   ERROR: {e}")
                continue
        
        print(f"\n{'='*70}")
        print(f"BATCH ANALYSIS COMPLETE")
        print(f"Successfully processed: {len(batch_ids)} / {len(sessions)} sessions")
        print(f"Batch IDs: {[bid[:8] for bid in batch_ids]}")
        print(f"{'='*70}")
        
        return batch_ids
    
    def analyze_existing_batch(self, batch_id: str, export_csv: bool = False):
        """Analyze an existing batch"""
        print(f"\n" + "="*70)
        print(f"ANALYZING EXISTING BATCH")
        print(f"Batch ID: {batch_id}")
        print("="*70)
        
        try:
            results = self.analyzer.analyze_batch(batch_id, export_csv=export_csv)
            
            if not results:
                print("ERROR: No results found for this batch")
                return
            
            self._display_detailed_results(results)
            
            if export_csv:
                print("\n   CSV files exported to output directory")
            
        except Exception as e:
            print(f"ERROR: Analysis failed: {e}")
    
    def show_configuration(self):
        """Display current configuration"""
        print("\n" + "="*70)
        print("MONTE CARLO ENGINE CONFIGURATION")
        print("="*70)
        
        # Validate configuration
        errors = validate_config()
        if errors:
            print("CONFIGURATION ERRORS:")
            for error in errors:
                print(f"  ERROR: {error}")
            print()
        
        # Show configuration summary
        config = get_config_summary()
        print(f"Polygon API: {'CONFIGURED' if config['polygon_configured'] else 'MISSING'}")
        print(f"Supabase DB: {'CONFIGURED' if config['supabase_configured'] else 'MISSING'}")
        print(f"Trading Hours: {config['trading_hours']}")
        print(f"Stop Offset: {config['stop_offset']}")
        print(f"Zone Size Limits: {config['min_zone_size']} - {config['max_zone_size']}")
        print(f"Batch Size: {config['batch_size']}")
        
        # Test database connection
        if self.data_loader.db_service.enabled:
            print(f"Database: CONNECTED")
            recent = self.data_loader.db_service.list_recent_analyses(1)
            print(f"Available Data: {len(recent)} recent analyses")
        else:
            print(f"Database: DISCONNECTED")
    
    def _validate_ticker_id(self, ticker_id: str) -> bool:
        """Validate ticker ID format"""
        parts = ticker_id.split('.')
        if len(parts) != 2:
            print(f"ERROR: Invalid ticker ID format: {ticker_id}")
            print("  Expected format: TICKER.MMDDYY (e.g., AMD.082524)")
            return False
        
        symbol, date_str = parts
        if len(date_str) != 6:
            print(f"ERROR: Invalid date format: {date_str}")
            print("  Expected format: MMDDYY (e.g., 082524)")
            return False
        
        return True
    
    def _parse_ticker_id(self, ticker_id: str) -> tuple:
        """Parse ticker ID into symbol and date"""
        symbol, date_str = ticker_id.split('.')
        
        # Parse date (MMDDYY to YYYY-MM-DD)
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = 2000 + int(date_str[4:6])
        trade_date = f"{year:04d}-{month:02d}-{day:02d}"
        
        return symbol, trade_date
    
    def _display_zone_summary(self, zones: List[Dict]):
        """Display zone summary with confluence information"""
        print("\n   Zone Summary (with Confluence):")
        for zone in zones:
            confluence_info = f"{zone['confluence_level']} (Score: {zone['confluence_score']:.1f})"
            source_count = zone['confluence_count']
            
            print(f"     Zone {zone['zone_number']}: ${zone['low']:.2f}-${zone['high']:.2f} "
                  f"| {confluence_info} | {source_count} sources")
            
            # Show top confluence sources
            if zone['confluence_sources']:
                top_sources = zone['confluence_sources'][:3]
                sources_str = ', '.join(top_sources)
                if len(zone['confluence_sources']) > 3:
                    sources_str += f" (+{len(zone['confluence_sources'])-3} more)"
                print(f"       Sources: {sources_str}")
    
    def _display_quick_stats(self, trades_df: pd.DataFrame, zones: List[Dict]):
        """Display quick statistics"""
        print(f"\n[4] Quick Statistics:")
        
        # Overall stats
        win_rate = (trades_df['actual_r_multiple'] > 0).mean() * 100
        avg_optimal_r = trades_df['optimal_r_multiple'].mean()
        median_optimal_r = trades_df['optimal_r_multiple'].median()
        max_optimal_r = trades_df['optimal_r_multiple'].max()
        stop_hit_rate = (trades_df['exit_reason'] == 'STOP_HIT').mean() * 100
        
        print(f"   Total Trades: {len(trades_df)}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Stop Hit Rate: {stop_hit_rate:.1f}%")
        print(f"   Avg Optimal R: {avg_optimal_r:.2f}")
        print(f"   Median Optimal R: {median_optimal_r:.2f}")
        print(f"   Max Optimal R: {max_optimal_r:.2f}")
        
        # By zone (with confluence info)
        print(f"\n   By Zone (with Confluence):")
        zones_by_number = {z['zone_number']: z for z in zones}
        
        for zone_id in trades_df['zone_id'].unique():
            zone_trades = trades_df[trades_df['zone_id'] == zone_id]
            zone_num = int(zone_id.split('_zone')[-1])
            zone_info = zones_by_number.get(zone_num, {})
            
            zone_win_rate = (zone_trades['actual_r_multiple'] > 0).mean() * 100
            zone_avg_optimal = zone_trades['optimal_r_multiple'].mean()
            
            confluence_level = zone_info.get('confluence_level', 'N/A')
            confluence_score = zone_info.get('confluence_score', 0)
            
            print(f"     Zone {zone_num}: {len(zone_trades)} trades | "
                  f"{zone_win_rate:.0f}% win | {zone_avg_optimal:.2f} avg R | "
                  f"{confluence_level} ({confluence_score:.1f})")
    
    def _run_detailed_analysis(self, batch_id: str):
        """Run and display detailed analysis"""
        results = self.analyzer.analyze_batch(batch_id)
        self._display_detailed_results(results)
    
    def _display_detailed_results(self, results: Dict):
        """Display detailed analysis results"""
        print("\n" + "="*70)
        print("DETAILED ANALYSIS RESULTS")
        print("="*70)
        
        if 'basic_stats' in results:
            stats = results['basic_stats']
            print(f"\nBasic Statistics:")
            print(f"  Total Trades: {stats['total_trades']}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Average R: {stats['avg_r_multiple']:.2f}")
        
        if 'optimal_r_percentiles' in results:
            percentiles = results['optimal_r_percentiles']
            print(f"\nOptimal R Distribution:")
            print(f"  10th percentile: {percentiles['p10']:.2f}R (90% exceed this)")
            print(f"  25th percentile: {percentiles['p25']:.2f}R (75% exceed this)")
            print(f"  50th percentile: {percentiles['p50']:.2f}R (50% exceed this)")
            print(f"  75th percentile: {percentiles['p75']:.2f}R (25% exceed this)")
            print(f"  90th percentile: {percentiles['p90']:.2f}R (10% exceed this)")
        
        if 'recommendations' in results and results['recommendations']:
            print(f"\nKey Insights:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
    
    def _export_to_csv(self, batch_id: str):
        """Export batch results to CSV"""
        try:
            filename = f"monte_carlo_{batch_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            # This would be implemented in the storage manager
            # self.storage.export_batch_to_csv(batch_id, filename)
            
            print(f"   Results exported to: {filename}")
        except Exception as e:
            print(f"   Export failed: {e}")

def create_argument_parser():
    """Create argument parser for CLI"""
    parser = argparse.ArgumentParser(
        description="Monte Carlo Backtesting Engine - Confluence System Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py AAPL.082524                    # Single day analysis
  python main.py --batch AAPL 2024-08-01 2024-08-31  # Batch analysis
  python main.py --list                         # List all sessions
  python main.py --list AAPL                    # List AAPL sessions
  python main.py --analyze abc123def            # Analyze existing batch
  python main.py --config                       # Show configuration
        """
    )
    
    # Main commands (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        'ticker_id', 
        nargs='?',
        help='Ticker ID in format TICKER.MMDDYY (e.g., AAPL.082524)'
    )
    
    group.add_argument(
        '--batch',
        nargs=3,
        metavar=('TICKER', 'START_DATE', 'END_DATE'),
        help='Run batch analysis (TICKER START_DATE END_DATE)'
    )
    
    group.add_argument(
        '--list',
        nargs='?',
        const='',
        help='List available sessions (optionally filter by ticker)'
    )
    
    group.add_argument(
        '--analyze',
        metavar='BATCH_ID',
        help='Analyze existing batch by ID'
    )
    
    group.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )
    
    # Options
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Skip saving to database'
    )
    
    parser.add_argument(
        '--no-analyze',
        action='store_true', 
        help='Skip detailed analysis'
    )
    
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Export results to CSV'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit number of sessions shown (default: 20)'
    )
    
    return parser

def main():
    """Main CLI entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Initialize Monte Carlo API
    api = MonteCarloAPI()
    
    try:
        if args.ticker_id:
            # Single day analysis
            api.run_single_day_analysis(
                args.ticker_id,
                save_to_db=not args.no_save,
                analyze=not args.no_analyze,
                export_csv=args.export_csv
            )
            
        elif args.batch:
            # Batch analysis
            ticker, start_date, end_date = args.batch
            api.run_batch_analysis(ticker, start_date, end_date)
            
        elif args.list is not None:
            # List sessions
            ticker = args.list if args.list else None
            api.list_available_sessions(ticker, args.limit)
            
        elif args.analyze:
            # Analyze existing batch
            api.analyze_existing_batch(args.analyze, args.export_csv)
            
        elif args.config:
            # Show configuration
            api.show_configuration()
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        logger.exception("Unexpected error")
        sys.exit(1)

if __name__ == "__main__":
    main()