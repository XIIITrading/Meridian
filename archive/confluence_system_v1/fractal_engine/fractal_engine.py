"""
Fractal Engine - Main CLI Interface
Market structure analysis using fractal pivot detection
"""

import argparse
import pandas as pd
from datetime import datetime
from tabulate import tabulate
import sys
import os
from typing import List, Dict

# Add parent directory to path to ensure proper imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from confluence_system.fractal_engine.detector import FractalDetector
from data_fetcher import DataFetcher

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fractal Engine - Market Structure Analysis"
    )
    
    parser.add_argument(
        'ticker',
        type=str,
        help='Stock ticker symbol (e.g., SPY, AAPL)'
    )
    
    parser.add_argument(
        'date',
        type=str,
        help='Date in YYYY-MM-DD format'
    )
    
    parser.add_argument(
        'time',
        type=str,
        help='Time in HH:MM format (24-hour, UTC)'
    )
    
    parser.add_argument(
        '--fractal-length',
        type=int,
        default=config.FRACTAL_LENGTH,
        help=f'Number of bars for fractal pattern (default: {config.FRACTAL_LENGTH})'
    )
    
    parser.add_argument(
        '--atr-distance',
        type=float,
        default=config.MIN_FRACTAL_DISTANCE_ATR,
        help=f'Minimum ATR distance between fractals (default: {config.MIN_FRACTAL_DISTANCE_ATR})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='terminal',
        choices=['terminal', 'csv', 'json'],
        help='Output format (default: terminal)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test connection to Polygon server'
    )
    
    return parser.parse_args()

def apply_overlap_filter(swings: List[Dict], df: pd.DataFrame) -> List[Dict]:
    """
    Filter swings to remove those with overlapping price ranges
    Ensures clean separation between swing points
    """
    if not swings:
        return swings
    
    # Sort by datetime (oldest to newest for forward processing)
    swings = sorted(swings, key=lambda x: x['datetime'])
    
    filtered = []
    
    for i, current_swing in enumerate(swings):
        # Get the bar data for current swing
        if current_swing.get('index') is not None and current_swing['index'] < len(df):
            current_bar = {
                'high': df.loc[current_swing['index'], 'high'],
                'low': df.loc[current_swing['index'], 'low']
            }
        else:
            # Fallback if no index
            current_bar = {
                'high': current_swing['price'],
                'low': current_swing['price']
            }
        
        # Check for overlap with previously accepted swings
        has_overlap = False
        valid_alternation = True
        
        if filtered:
            last_valid = filtered[-1]
            
            # Check type alternation
            if current_swing['type'] == last_valid['type']:
                valid_alternation = False
            
            # Get the bar data for the last valid swing
            if last_valid.get('index') is not None and last_valid['index'] < len(df):
                last_bar = {
                    'high': df.loc[last_valid['index'], 'high'],
                    'low': df.loc[last_valid['index'], 'low']
                }
            else:
                last_bar = {
                    'high': last_valid['price'],
                    'low': last_valid['price']
                }
            
            # Check for price overlap
            # Overlap occurs if current bar's range intersects with last bar's range
            if (current_bar['low'] <= last_bar['high'] and 
                current_bar['high'] >= last_bar['low']):
                has_overlap = True
        
        # Add swing if it passes filters
        if valid_alternation and not has_overlap:
            current_swing['status'] = 'Valid'
            filtered.append(current_swing)
        else:
            if not valid_alternation:
                current_swing['status'] = 'Same Type'
            elif has_overlap:
                current_swing['status'] = 'Overlap'
    
    return filtered

def display_results(fractals: dict, ticker: str, start_time: datetime, df: pd.DataFrame = None):
    """Display fractal detection results with optional overlap filtering"""
    
    print(f"\n{'='*70}")
    print(f"FRACTAL ANALYSIS RESULTS - {ticker}")
    print(f"Analysis Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*70}\n")
    
    # Display Swing Highs
    if fractals['highs']:
        print(f"SWING HIGHS ({len(fractals['highs'])} detected):")
        print("-" * 50)
        
        high_data = []
        for fractal in fractals['highs']:
            high_data.append([
                fractal['datetime'].strftime('%Y-%m-%d %H:%M'),
                f"${fractal['price']:.5f}",
                f"{fractal['atr']:.5f}" if fractal['atr'] else "N/A"
            ])
        
        print(tabulate(
            high_data,
            headers=['DateTime (UTC)', 'Price', 'ATR'],
            tablefmt='grid'
        ))
    else:
        print("No swing highs detected with current parameters.\n")
    
    print()
    
    # Display Swing Lows
    if fractals['lows']:
        print(f"SWING LOWS ({len(fractals['lows'])} detected):")
        print("-" * 50)
        
        low_data = []
        for fractal in fractals['lows']:
            low_data.append([
                fractal['datetime'].strftime('%Y-%m-%d %H:%M'),
                f"${fractal['price']:.5f}",
                f"{fractal['atr']:.5f}" if fractal['atr'] else "N/A"
            ])
        
        print(tabulate(
            low_data,
            headers=['DateTime (UTC)', 'Price', 'ATR'],
            tablefmt='grid'
        ))
    else:
        print("No swing lows detected with current parameters.\n")
    
    # Combine all swings with type indicator and index info
    all_swings = []
    
    for high in fractals['highs']:
        all_swings.append({
            'datetime': high['datetime'],
            'type': 'HIGH',
            'price': high['price'],
            'atr': high['atr'],
            'index': high.get('index')
        })
    
    for low in fractals['lows']:
        all_swings.append({
            'datetime': low['datetime'],
            'type': 'LOW',
            'price': low['price'],
            'atr': low['atr'],
            'index': low.get('index')
        })
    
    # Sort by datetime and take last 10 swings (or more if configured)
    all_swings.sort(key=lambda x: x['datetime'])
    num_swings = max(10, config.MAX_DISPLAY_SWINGS) if hasattr(config, 'MAX_DISPLAY_SWINGS') else 10
    last_swings = all_swings[-num_swings:] if len(all_swings) >= num_swings else all_swings
    
    # Apply overlap filter if configured and df is available
    if config.CHECK_PRICE_OVERLAP and df is not None:
        last_swings_filtered = apply_overlap_filter(last_swings, df)
    else:
        last_swings_filtered = last_swings
    
    # Reverse to show most recent first
    last_swings_filtered.reverse()
    
    # Display filtered swings with high/low values
    print(f"\n{'='*70}")
    if config.CHECK_PRICE_OVERLAP:
        print(f"LAST {len(last_swings_filtered)} SWINGS - FILTERED (No Price Overlap)")
    else:
        print(f"LAST {len(last_swings_filtered)} SWINGS - MARKET STRUCTURE")
    print("-" * 70)
    
    # Prepare data for table with high/low columns
    structure_data = []
    for i, swing in enumerate(last_swings_filtered):
        # Get bar high and low
        if df is not None and swing.get('index') is not None and swing['index'] < len(df):
            bar_high = df.loc[swing['index'], 'high']
            bar_low = df.loc[swing['index'], 'low']
        else:
            # Fallback if no bar data
            bar_high = swing['price']
            bar_low = swing['price']
        
        # Add visual indicator for highs vs lows
        type_indicator = "↑ HIGH" if swing['type'] == 'HIGH' else "↓ LOW"
        
        # Calculate price change from previous swing if not the last one
        price_change = ""
        if i < len(last_swings_filtered) - 1:
            prev_price = last_swings_filtered[i + 1]['price']
            change = swing['price'] - prev_price
            change_pct = (change / prev_price) * 100
            price_change = f"{'+' if change > 0 else ''}{change:.2f} ({change_pct:+.2f}%)"
        
        structure_data.append([
            swing['datetime'].strftime('%Y-%m-%d %H:%M'),
            type_indicator,
            f"${bar_high:.2f}",
            f"${bar_low:.2f}",
            f"${swing['price']:.2f}",
            price_change,
            f"{swing['atr']:.3f}" if swing['atr'] else "N/A"
        ])
    
    print(tabulate(
        structure_data,
        headers=['DateTime (UTC)', 'Type', 'High', 'Low', 'Swing', 'Change', 'ATR'],
        tablefmt='grid'
    ))
    
    # Add market structure analysis
    if len(last_swings_filtered) >= 4:
        print("\nQuick Structure Analysis:")
        
        # Get the last few highs and lows for trend analysis
        recent_highs = [s for s in last_swings_filtered[:6] if s['type'] == 'HIGH']
        recent_lows = [s for s in last_swings_filtered[:6] if s['type'] == 'LOW']
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Check for higher highs/higher lows (uptrend) or lower highs/lower lows (downtrend)
            hh = recent_highs[0]['price'] > recent_highs[1]['price']
            hl = recent_lows[0]['price'] > recent_lows[1]['price']
            lh = recent_highs[0]['price'] < recent_highs[1]['price']
            ll = recent_lows[0]['price'] < recent_lows[1]['price']
            
            if hh and hl:
                print("  → Structure: UPTREND (Higher Highs & Higher Lows)")
            elif lh and ll:
                print("  → Structure: DOWNTREND (Lower Highs & Lower Lows)")
            elif hh and ll:
                print("  → Structure: EXPANDING (Higher Highs & Lower Lows)")
            elif lh and hl:
                print("  → Structure: CONTRACTING (Lower Highs & Higher Lows)")
            else:
                print("  → Structure: MIXED/TRANSITIONING")
                
            # Show current position relative to recent swings
            current_high = recent_highs[0]['price'] if recent_highs else 0
            current_low = recent_lows[0]['price'] if recent_lows else 0
            print(f"  → Recent High: ${current_high:.2f}")
            print(f"  → Recent Low: ${current_low:.2f}")
            print(f"  → Range: ${(current_high - current_low):.2f}")
    
    print(f"\n{'='*70}")
    print(f"Parameters: Fractal Length={config.FRACTAL_LENGTH}, "
          f"Min ATR Distance={config.MIN_FRACTAL_DISTANCE_ATR}")
    if config.CHECK_PRICE_OVERLAP:
        print(f"Overlap Filter: ENABLED")
    print(f"{'='*70}\n")

def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Test connection if requested
    if args.test:
        print("\nTesting connection to Polygon server...")
        fetcher = DataFetcher()
        if fetcher.test_connection():
            print(f"✓ Successfully connected to Polygon server at {config.POLYGON_SERVER_URL}")
        else:
            print(f"✗ Failed to connect to Polygon server at {config.POLYGON_SERVER_URL}")
        sys.exit(0)
    
    # Parse datetime as UTC
    try:
        start_datetime = datetime.strptime(
            f"{args.date} {args.time}", 
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        print(f"Error: Invalid date/time format. Use YYYY-MM-DD HH:MM")
        sys.exit(1)
    
    print(f"\nInitializing Fractal Engine...")
    print(f"Connecting to Polygon server at {config.POLYGON_SERVER_URL}...")
    print(f"Fetching {config.LOOKBACK_DAYS} days of 15-minute data for {args.ticker}...")
    print(f"Analysis point: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Fetch data
    try:
        fetcher = DataFetcher()
        
        # Test connection first
        if not fetcher.test_connection():
            print(f"Error: Cannot connect to Polygon server at {config.POLYGON_SERVER_URL}")
            print("Please ensure the server is running on port 8200")
            sys.exit(1)
        
        df = fetcher.fetch_bars(
            ticker=args.ticker,
            end_date=start_datetime,
            lookback_days=config.LOOKBACK_DAYS,
            timeframe="minute",
            multiplier=config.AGGREGATION_MULTIPLIER
        )
        print(f"✓ Successfully fetched {len(df)} bars")
        
    except Exception as e:
        print(f"✗ Error fetching data: {str(e)}")
        sys.exit(1)
    
    # Detect fractals
    detector = FractalDetector(
        fractal_length=args.fractal_length,
        min_atr_distance=args.atr_distance
    )
    
    print(f"Analyzing market structure...")
    fractals = detector.detect_fractals(df, start_datetime)
    
    # Display results - pass df for overlap checking
    display_results(fractals, args.ticker, start_datetime, df)
    
    # Export if requested
    if args.output == 'csv':
        export_to_csv(fractals, args.ticker)
    elif args.output == 'json':
        export_to_json(fractals, args.ticker)

def export_to_csv(fractals: dict, ticker: str):
    """Export results to CSV"""
    import csv
    from datetime import datetime
    
    filename = f"fractals_{ticker}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_UTC.csv"
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Type', 'DateTime_UTC', 'Price', 'ATR'])
        
        for high in fractals['highs']:
            writer.writerow(['HIGH', high['datetime'], high['price'], high['atr']])
        
        for low in fractals['lows']:
            writer.writerow(['LOW', low['datetime'], low['price'], low['atr']])
    
    print(f"\nResults exported to {filename}")

def export_to_json(fractals: dict, ticker: str):
    """Export results to JSON"""
    import json
    from datetime import datetime
    
    filename = f"fractals_{ticker}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_UTC.json"
    
    # Convert datetime objects to strings
    export_data = {
        'ticker': ticker,
        'analysis_date_utc': datetime.utcnow().isoformat() + 'Z',
        'parameters': {
            'fractal_length': config.FRACTAL_LENGTH,
            'min_atr_distance': config.MIN_FRACTAL_DISTANCE_ATR
        },
        'highs': [
            {
                'datetime_utc': h['datetime'].isoformat() + 'Z',
                'price': h['price'],
                'atr': h['atr']
            } for h in fractals['highs']
        ],
        'lows': [
            {
                'datetime_utc': l['datetime'].isoformat() + 'Z',
                'price': l['price'],
                'atr': l['atr']
            } for l in fractals['lows']
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\nResults exported to {filename}")

if __name__ == "__main__":
    main()