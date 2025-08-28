"""
Confluence System CLI
Modeled exactly after working test_zone_identification.py
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Confluence System - Complete Zone Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        'ticker',
        type=str,
        help='Stock ticker symbol (e.g., SPY, AAPL, TSLA)'
    )
    
    parser.add_argument(
        'date',
        type=str,
        help='Analysis date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        'time',
        type=str,
        help='Analysis time in HH:MM format (24-hour UTC)'
    )
    
    # Weekly and Daily levels (required)
    parser.add_argument(
        '-w', '--weekly-levels',
        nargs=4,
        type=float,
        required=True,
        metavar=('WL1', 'WL2', 'WL3', 'WL4'),
        help='Four weekly levels (WL1 WL2 WL3 WL4)'
    )
    
    parser.add_argument(
        '-d', '--daily-levels',
        nargs=4,
        type=float,
        required=True,
        metavar=('DL1', 'DL2', 'DL3', 'DL4'),
        help='Four daily levels (DL1 DL2 DL3 DL4)'
    )
    
    # Optional parameters
    parser.add_argument(
        '--fractal-length',
        type=int,
        default=11,
        help='Number of bars for fractal pattern (default: 11)'
    )
    
    parser.add_argument(
        '--atr-distance',
        type=float,
        default=1.0,
        help='Minimum ATR distance between fractals (default: 1.0)'
    )
    
    parser.add_argument(
        '--lookback',
        type=int,
        default=30,
        help='Days to look back for analysis (default: 30)'
    )
    
    parser.add_argument(
        '--merge-mode',
        choices=['overlap', 'identical', 'none'],
        default='overlap',
        help='Zone merging mode (default: overlap)'
    )
    
    parser.add_argument(
        '-o', '--output',
        choices=['terminal', 'json', 'both'],
        default='terminal',
        help='Output format (default: terminal)'
    )
    
    parser.add_argument(
        '--save-file',
        type=str,
        help='Save JSON output to specific filename'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    
    return parser.parse_args()


def run_analysis(args) -> Dict:
    """Run the complete analysis pipeline - modeled after test_zone_identification.py"""
    
    # EXACTLY like test file - naive datetime for processing, UTC for display
    analysis_time_utc = datetime(
        int(args.date.split('-')[0]),
        int(args.date.split('-')[1]),
        int(args.date.split('-')[2]),
        int(args.time.split(':')[0]),
        int(args.time.split(':')[1]),
        0,
        tzinfo=timezone.utc
    )
    analysis_time_naive = datetime(
        int(args.date.split('-')[0]),
        int(args.date.split('-')[1]),
        int(args.date.split('-')[2]),
        int(args.time.split(':')[0]),
        int(args.time.split(':')[1]),
        0
    )  # No timezone for fractal engine
    
    if args.verbose:
        print("=" * 80)
        print(f"CONFLUENCE ANALYSIS - {args.ticker}")
        print(f"Analysis Time: {analysis_time_utc.strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 80)
    
    # Get price EXACTLY like test file
    from confluence_scanner.data.polygon_client import PolygonClient
    client = PolygonClient()
    
    # Fetch bars for the day - EXACTLY like test file
    bars = client.fetch_bars(
        args.ticker, 
        args.date,  # Just the date string
        args.date,  # Same date
        "15min"
    )
    
    current_price = None
    if bars is not None and not bars.empty:
        # Find the bar at analysis time - EXACTLY like test file
        target_time = analysis_time_naive
        
        try:
            if target_time in bars.index:
                current_price = bars.loc[target_time, 'close']
            else:
                # Find nearest time
                time_diff = abs(bars.index - target_time)
                closest_idx = time_diff.argmin()
                closest_bar = bars.iloc[closest_idx]
                current_price = closest_bar['close']
                if args.verbose:
                    print(f"Using bar at {bars.index[closest_idx]}: ${current_price:.2f}")
        except Exception as e:
            if args.verbose:
                print(f"Error finding bar: {e}")
    
    if current_price is None:
        if args.verbose:
            print("Warning: Could not fetch exact price, using approximate")
        # Default prices for known tickers
        defaults = {'AAPL': 225.0, 'SPY': 450.0, 'TSLA': 350.0, 'QQQ': 380.0}
        current_price = defaults.get(args.ticker, 100.0)
    else:
        if args.verbose:
            print(f"\nPrice at {analysis_time_utc.strftime('%H:%M UTC')}: ${current_price:.2f}")
    
    # Import orchestrators
    from fractal_engine.orchestrator import FractalOrchestrator
    from confluence_scanner.orchestrator import ConfluenceOrchestrator
    from zone_identification.orchestrator import ZoneIdentificationOrchestrator
    
    # 1. FRACTALS - use naive datetime EXACTLY like test file
    if args.verbose:
        print("\n" + "="*40)
        print("DETECTING FRACTALS")
        print("="*40)
    
    fractal_orch = FractalOrchestrator()
    fractal_results = fractal_orch.run_detection(
        symbol=args.ticker,
        analysis_time=analysis_time_naive,  # Use naive datetime here
        lookback_days=args.lookback
    )
    
    if args.verbose:
        print(f"Found {len(fractal_results['fractals']['highs'])} highs, "
              f"{len(fractal_results['fractals']['lows'])} lows")
    
    # 2. CONFLUENCE - use naive datetime EXACTLY like test file
    if args.verbose:
        print("\n" + "="*40)
        print("FINDING CONFLUENCE")
        print("="*40)
    
    confluence_orch = ConfluenceOrchestrator()
    confluence_orch.initialize()
    
    # Set merge mode
    merge_overlapping = args.merge_mode == 'overlap'
    merge_identical = args.merge_mode == 'identical'
    
    confluence_result = confluence_orch.run_analysis(
        symbol=args.ticker,
        analysis_datetime=analysis_time_naive,  # Use naive datetime here
        fractal_data=fractal_results,
        weekly_levels=args.weekly_levels,
        daily_levels=args.daily_levels,
        lookback_days=args.lookback,
        merge_overlapping=merge_overlapping,
        merge_identical=merge_identical
    )
    
    if args.verbose:
        print(f"Found {len(confluence_result.zones)} zones")
        
        # Count by level
        level_counts = {}
        for zone in confluence_result.zones:
            level = zone.confluence_level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        for level in ['L5', 'L4', 'L3', 'L2', 'L1', 'L0']:
            if level in level_counts:
                print(f"  {level}: {level_counts[level]} zones")
    
    # 3. ZONE IDENTIFICATION - EXACTLY like test file
    if args.verbose:
        print("\n" + "="*40)
        print("IDENTIFYING TRADING LEVELS")
        print("="*40)
    
    zone_id_orch = ZoneIdentificationOrchestrator()
    zone_id_orch.initialize(current_price)
    
    atr_daily = confluence_result.metrics['atr_daily']
    atr_filter = atr_daily * 2
    
    trading_levels = zone_id_orch.identify_trading_levels(
        fractal_data=fractal_results,
        confluence_zones=confluence_result.zones,
        atr_filter=atr_filter
    )
    
    if args.verbose:
        print(f"Identified {len(trading_levels)} trading levels")
    
    # Prepare output data - EXACTLY like test file
    output_data = {
        'symbol': args.ticker,
        'analysis_time': analysis_time_utc.isoformat(),
        'current_price': current_price,
        'parameters': {
            'weekly_levels': args.weekly_levels,
            'daily_levels': args.daily_levels,
            'fractal_length': args.fractal_length,
            'atr_distance': args.atr_distance,
            'lookback_days': args.lookback,
            'merge_mode': args.merge_mode
        },
        'metrics': {
            'atr_daily': confluence_result.metrics.get('atr_daily', 0),
            'atr_15min': confluence_result.metrics.get('atr_m15', 0),
        },
        'statistics': {
            'total_fractals': len(fractal_results['fractals']['highs']) + len(fractal_results['fractals']['lows']),
            'confluence_zones': len(confluence_result.zones),
            'trading_levels': len(trading_levels)
        },
        'levels': []
    }
    
    # Add trading levels to output
    for level in sorted(trading_levels, key=lambda x: x.priority_score, reverse=True)[:20]:
        output_data['levels'].append({
            'low': level.low_price,
            'high': level.high_price,
            'confluence': level.confluence_level,
            'score': level.confluence_score,
            'distance_pct': level.distance_percentage,
            'type': level.fractal_type,
            'priority': level.priority_score
        })
    
    return output_data


def display_terminal_output(results: Dict):
    """Display formatted output to terminal"""
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print(f"Symbol: {results['symbol']}")
    print(f"Analysis Time: {results['analysis_time']}")
    print(f"Current Price: ${results['current_price']:.2f}")
    print(f"ATR Daily: ${results['metrics']['atr_daily']:.2f}")
    print(f"ATR 15min: ${results['metrics']['atr_15min']:.2f}")
    
    print(f"\nStatistics:")
    print(f"  Fractals: {results['statistics']['total_fractals']}")
    print(f"  Zones: {results['statistics']['confluence_zones']}")
    print(f"  Levels: {results['statistics']['trading_levels']}")
    
    if results['levels']:
        print("\n" + "=" * 80)
        print("TOP TRADING LEVELS")
        print("=" * 80)
        
        table_data = []
        for i, level in enumerate(results['levels'][:10], 1):
            direction = "RES" if level['low'] > results['current_price'] else "SUP"
            table_data.append([
                i,
                level['confluence'],
                direction,
                f"${level['low']:.2f}-${level['high']:.2f}",
                f"{level['score']:.1f}",
                f"{abs(level['distance_pct']):.1f}%"
            ])
        
        print(tabulate(
            table_data,
            headers=['Rank', 'Level', 'Type', 'Price Range', 'Score', 'Distance'],
            tablefmt='grid'
        ))
    
    print("\n" + "=" * 80)


def main():
    """Main execution"""
    args = parse_arguments()
    
    try:
        # Run analysis
        results = run_analysis(args)
        
        # Output results
        if args.output in ['terminal', 'both']:
            display_terminal_output(results)
        
        if args.output in ['json', 'both']:
            # Save JSON file
            if args.save_file:
                with open(args.save_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"✓ Results saved to {args.save_file}")
            else:
                # Print to stdout
                print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()