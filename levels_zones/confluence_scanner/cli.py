# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\cli.py

"""
Zone Scanner CLI - Command Line Interface
Main entry point for the zone-first M15 confluence scanner
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path
import argparse
import json
from decimal import Decimal

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from config import ScannerConfig, setup_logging
from scanner.zone_scanner import ZoneScanner


class ZoneScannerCLI:
    """Command line interface for zone scanner"""
    
    def __init__(self):
        """Initialize CLI"""
        self.scanner = None
        self.logger = None
        
    def setup(self, debug: bool = False):
        """Setup scanner and logging"""
        self.logger = setup_logging(debug)
        self.scanner = ZoneScanner()
        
        # Initialize scanner
        success, msg = self.scanner.initialize()
        if not success:
            self.logger.error(f"Failed to initialize scanner: {msg}")
            return False
        
        return True
    
    def print_header(self):
        """Print application header"""
        print("\n" + "="*80)
        print("ZONE-FIRST M15 CONFLUENCE SCANNER")
        print("Discovering High-Probability Trading Zones")
        print("="*80)
    
    def get_ticker_input(self) -> str:
        """Get ticker symbol from user"""
        while True:
            ticker = input("\nEnter ticker symbol: ").strip().upper()
            if ticker and ticker.isalpha() and len(ticker) <= 5:
                return ticker
            print("❌ Invalid ticker. Please enter a valid stock symbol (e.g., SPY, AAPL)")
    
    def get_datetime_input(self) -> datetime:
        """Get analysis datetime from user"""
        print("\nAnalysis Date and Time:")
        print("1. Current date/time (live analysis)")
        print("2. Custom date/time (historical analysis)")
        
        while True:
            choice = input("\nSelect option (1 or 2): ").strip()
            
            if choice == '1':
                return datetime.now()
            
            elif choice == '2':
                while True:
                    try:
                        date_str = input("Enter date (YYYY-MM-DD): ").strip()
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        time_str = input("Enter time in UTC (HH:MM:SS) or press Enter for 14:30:00: ").strip()
                        if not time_str:
                            time_str = "14:30:00"
                        
                        time = datetime.strptime(time_str, '%H:%M:%S').time()
                        
                        return datetime.combine(date.date(), time)
                        
                    except ValueError:
                        print("❌ Invalid date/time format. Please try again.")
            
            else:
                print("❌ Please enter 1 or 2")
    
    def get_levels_input(self, level_type: str, count: int) -> List[float]:
        """
        Get price levels from user
        
        Args:
            level_type: 'Weekly' or 'Daily'
            count: Number of levels to get
            
        Returns:
            List of price levels
        """
        print(f"\n{level_type} Levels Input:")
        print(f"Enter {count} {level_type.lower()} levels (or 'skip' to use defaults)")
        
        levels = []
        
        # Check for skip
        first_input = input(f"{level_type[0]}L1: ").strip()
        if first_input.lower() == 'skip':
            print(f"⚠️  Skipping {level_type.lower()} levels - using zeros")
            return [0.0] * count
        
        # Process first input
        try:
            levels.append(float(first_input))
        except ValueError:
            print(f"❌ Invalid number. Using 0 for {level_type[0]}L1")
            levels.append(0.0)
        
        # Get remaining levels
        for i in range(2, count + 1):
            while True:
                try:
                    value = input(f"{level_type[0]}L{i}: ").strip()
                    if not value:
                        levels.append(0.0)
                        break
                    levels.append(float(value))
                    break
                except ValueError:
                    print("❌ Invalid number. Please enter a valid price or press Enter for 0")
        
        return levels
    
    def get_quick_input(self) -> bool:
        """Check if user wants quick mode"""
        print("\nInput Mode:")
        print("1. Quick mode (fetch from market, no manual levels)")
        print("2. Full mode (enter weekly and daily levels)")
        
        choice = input("\nSelect mode (1 or 2): ").strip()
        return choice == '1'
    
    def display_metrics(self, metrics: dict):
        """Display calculated metrics"""
        print("\n" + "="*60)
        print("MARKET METRICS")
        print("="*60)
        
        print(f"Current Price:     ${metrics.get('current_price', 0):.2f}")
        print(f"Pre-Market Price:  ${metrics.get('pre_market_price', 0):.2f}")
        print(f"Open Price:        ${metrics.get('open_price', 0):.2f}")
        
        print(f"\nATR Metrics:")
        print(f"  5-min ATR:       ${metrics.get('atr_5min', 0):.2f}")
        print(f"  15-min ATR:      ${metrics.get('atr_15min', 0):.2f}")
        print(f"  2-hour ATR:      ${metrics.get('atr_2hour', 0):.2f}")
        print(f"  Daily ATR:       ${metrics.get('daily_atr', 0):.2f}")
        
        print(f"\nATR Bands:")
        print(f"  ATR High (1x):   ${metrics.get('atr_high', 0):.2f}")
        print(f"  ATR Low (1x):    ${metrics.get('atr_low', 0):.2f}")
        
        print(f"\n🎯 Scanning Bounds (2x ATR):")
        print(f"  Scan Low:        ${metrics.get('scan_low', 0):.2f}")
        print(f"  Scan High:       ${metrics.get('scan_high', 0):.2f}")
        print(f"  Range Width:     ${(metrics.get('scan_high', 0) - metrics.get('scan_low', 0)):.2f}")
    
    def confirm_scan(self, ticker: str, analysis_datetime: datetime, 
                    weekly_levels: List[float], daily_levels: List[float]) -> bool:
        """Confirm scan parameters"""
        print("\n" + "="*60)
        print("SCAN CONFIGURATION SUMMARY")
        print("="*60)
        
        print(f"\nTicker: {ticker}")
        print(f"Analysis DateTime: {analysis_datetime}")
        
        if any(level > 0 for level in weekly_levels):
            print(f"\nWeekly Levels:")
            for i, level in enumerate(weekly_levels, 1):
                if level > 0:
                    print(f"  WL{i}: ${level:.2f}")
        
        if any(level > 0 for level in daily_levels):
            print(f"\nDaily Levels:")
            for i, level in enumerate(daily_levels, 1):
                if level > 0:
                    print(f"  DL{i}: ${level:.2f}")
        
        response = input("\nProceed with scan? (y/n): ").strip().lower()
        return response == 'y'
    
    def save_results(self, result):
        """Ask user if they want to save results"""
        print("\n" + "-"*60)
        response = input("Save results to file? (y/n): ").strip().lower()
        
        if response == 'y':
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"{result.ticker}_{timestamp}.json"
            
            filename = input(f"Enter filename (default: {default_name}): ").strip()
            if not filename:
                filename = default_name
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create results directory if needed
            results_dir = Path('scan_results')
            results_dir.mkdir(exist_ok=True)
            
            filepath = results_dir / filename
            
            try:
                self.scanner.export_result(result, str(filepath))
                print(f"✅ Results saved to: {filepath}")
            except Exception as e:
                print(f"❌ Failed to save results: {e}")
    
    def run_interactive(self):
        """Run interactive CLI session"""
        self.print_header()
        
        # Get inputs
        ticker = self.get_ticker_input()
        
        # Check for quick mode
        quick_mode = self.get_quick_input()
        
        if quick_mode:
            print("\n✨ Quick Mode - Fetching market data...")
            analysis_datetime = datetime.now()
            weekly_levels = [0.0] * 4  # Will rely on other confluence
            daily_levels = [0.0] * 6
        else:
            analysis_datetime = self.get_datetime_input()
            weekly_levels = self.get_levels_input("Weekly", 4)
            daily_levels = self.get_levels_input("Daily", 6)
        
        # Confirm parameters
        if not self.confirm_scan(ticker, analysis_datetime, weekly_levels, daily_levels):
            print("Scan cancelled.")
            return
        
        # Run scan
        print("\n" + "="*60)
        print("STARTING ZONE DISCOVERY SCAN...")
        print("="*60)
        
        try:
            result = self.scanner.scan(
                ticker=ticker,
                analysis_datetime=analysis_datetime,
                weekly_levels=weekly_levels,
                daily_levels=daily_levels,
                lookback_days=30
            )
            
            # Display metrics if in quick mode
            if quick_mode:
                self.display_metrics(result.metrics)
            
            # Display results
            formatted_result = self.scanner.format_result(result)
            print(formatted_result)
            
            # Save results option
            self.save_results(result)
            
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            print(f"\n❌ Scan failed: {e}")
            return
        
        print("\n✅ Scan complete!")
    
    def run_batch(self, config_file: str):
        """
        Run batch scan from configuration file
        
        Args:
            config_file: Path to JSON configuration file
        """
        print(f"\n📋 Loading batch configuration from: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                batch_config = json.load(f)
            
            scans = batch_config.get('scans', [])
            print(f"Found {len(scans)} scan configurations")
            
            results = []
            
            for i, scan_config in enumerate(scans, 1):
                print(f"\n[{i}/{len(scans)}] Scanning {scan_config['ticker']}...")
                
                try:
                    # Parse datetime
                    analysis_datetime = datetime.fromisoformat(scan_config['analysis_datetime'])
                    
                    result = self.scanner.scan(
                        ticker=scan_config['ticker'],
                        analysis_datetime=analysis_datetime,
                        weekly_levels=scan_config.get('weekly_levels', [0]*4),
                        daily_levels=scan_config.get('daily_levels', [0]*6),
                        lookback_days=scan_config.get('lookback_days', 30)
                    )
                    
                    results.append(result)
                    print(f"✅ {scan_config['ticker']} complete: "
                         f"{len(result.zones_with_candles)} zones found")
                    
                except Exception as e:
                    print(f"❌ {scan_config['ticker']} failed: {e}")
                    continue
            
            # Save all results
            if results:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                batch_dir = Path('scan_results') / f'batch_{timestamp}'
                batch_dir.mkdir(parents=True, exist_ok=True)
                
                for result in results:
                    filepath = batch_dir / f'{result.ticker}.json'
                    self.scanner.export_result(result, str(filepath))
                
                print(f"\n✅ Batch complete! Results saved to: {batch_dir}")
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Zone-First M15 Confluence Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run interactive mode
  %(prog)s -t SPY            # Quick scan for SPY
  %(prog)s -t AAPL -d        # Debug mode scan for AAPL
  %(prog)s -b batch.json     # Run batch scan from config file
  %(prog)s --test            # Test connection only
        """
    )
    
    parser.add_argument('-t', '--ticker', type=str, help='Ticker symbol for quick scan')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-b', '--batch', type=str, help='Batch configuration file')
    parser.add_argument('--test', action='store_true', help='Test connection and exit')
    parser.add_argument('--lookback', type=int, default=30, help='Lookback days (default: 30)')
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = ZoneScannerCLI()
    
    # Setup scanner
    if not cli.setup(debug=args.debug):
        print("❌ Failed to initialize scanner")
        sys.exit(1)
    
    # Test mode
    if args.test:
        print("\n🔧 Testing connection...")
        success, msg = cli.scanner.polygon_client.test_connection()
        if success:
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
        sys.exit(0)
    
    # Batch mode
    if args.batch:
        cli.run_batch(args.batch)
        sys.exit(0)
    
    # Quick scan mode
    if args.ticker:
        print(f"\n⚡ Quick scan mode for {args.ticker}")
        try:
            result = cli.scanner.scan(
                ticker=args.ticker,
                analysis_datetime=datetime.now(),
                weekly_levels=[0.0] * 4,
                daily_levels=[0.0] * 6,
                lookback_days=args.lookback
            )
            
            # Display results
            formatted_result = cli.scanner.format_result(result)
            print(formatted_result)
            
            # Auto-save in quick mode
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"scan_results/{args.ticker}_{timestamp}.json"
            cli.scanner.export_result(result, filepath)
            print(f"\n✅ Results saved to: {filepath}")
            
        except Exception as e:
            print(f"❌ Quick scan failed: {e}")
            sys.exit(1)
    
    else:
        # Interactive mode
        try:
            cli.run_interactive()
        except KeyboardInterrupt:
            print("\n\n👋 Scan cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()