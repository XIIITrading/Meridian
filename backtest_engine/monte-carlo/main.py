"""
Main entry point for Monte Carlo backtesting - Single Day Version
"""
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional  # ADD THIS LINE
import pandas as pd

from config import DEFAULT_SYMBOL
from data_loader import DataLoader
from zone_processor import ZoneProcessor
from trade_simulator import TradeSimulator
from storage_manager import StorageManager
from analysis import MonteCarloAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_monte_carlo_single_day(ticker_id: str,
                              save_to_db: bool = True,
                              analyze: bool = True):
    """
    Run Monte Carlo simulation for a single trading day
    
    Args:
        ticker_id: Ticker ID in format TICKER.MMDDYY (e.g., 'AMD.121824')
        save_to_db: Whether to save results to database
        analyze: Whether to run analysis after simulation
        
    Returns:
        Batch ID if saved, None otherwise
    """
    print("\n" + "="*60)
    print("MONTE CARLO INTRADAY ZONE BREAKOUT BACKTESTING")
    print("="*60)
    
    # Parse ticker_id
    parts = ticker_id.split('.')
    if len(parts) != 2:
        logger.error(f"Invalid ticker_id format: {ticker_id}")
        return None
    
    symbol = parts[0]
    date_str = parts[1]
    
    # Parse date (MMDDYY to YYYY-MM-DD)
    try:
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = 2000 + int(date_str[4:6])
        trade_date = f"{year:04d}-{month:02d}-{day:02d}"
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid date format in ticker_id: {date_str}")
        return None
    
    print(f"Ticker ID: {ticker_id}")
    print(f"Symbol: {symbol}")
    print(f"Date: {trade_date}")
    print("-"*60)
    
    start_time = time.time()
    
    # Step 1: Load zones from levels_zones
    print("\n[1] Loading Zones from levels_zones...")
    loader = DataLoader()
    
    zones = loader.fetch_zones_from_levels_zones(ticker_id)
    if not zones:
        logger.error(f"No zones found for {ticker_id}")
        return None
    print(f"   ✓ Loaded {len(zones)} zones")
    
    # Display zone summary
    for zone in zones:
        print(f"   Zone {zone['zone_number']}: "
              f"${zone['low']:.2f}-${zone['high']:.2f} "
              f"({zone['confluence_level']})")
    
    # Step 2: Fetch minute bars for the day
    print(f"\n[2] Fetching minute bars for {trade_date}...")
    bars_df = loader.fetch_minute_bars_for_date(symbol, trade_date)
    
    if bars_df.empty:
        logger.error(f"No minute data available for {symbol} on {trade_date}")
        return None
    print(f"   ✓ Loaded {len(bars_df)} minute bars")
    
    # Step 3: Process zones (validation only, no merging needed for same day)
    print("\n[3] Validating Zones...")
    processor = ZoneProcessor()
    zones_valid = processor.filter_valid_zones(zones)
    print(f"   ✓ {len(zones_valid)} valid zones")
    
    # Step 4: Run simulation
    print("\n[4] Running Monte Carlo Simulation...")
    print(f"   Testing {len(bars_df)} bars × {len(zones_valid)} zones")
    
    simulator = TradeSimulator()
    trades = simulator.run_monte_carlo_simulation(bars_df, zones_valid)
    
    if not trades:
        logger.warning("No trades generated")
        return None
    
    # Convert to DataFrame
    trades_df = pd.DataFrame(trades)
    
    print(f"\n   ✓ Generated {len(trades_df)} trades")
    
    # Step 5: Quick statistics
    print("\n[5] Quick Statistics:")
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
    
    # Show breakdown by zone
    print("\n   By Zone:")
    for zone_id in trades_df['zone_id'].unique():
        zone_trades = trades_df[trades_df['zone_id'] == zone_id]
        zone_num = zone_id.split('_zone')[-1]
        zone_win_rate = (zone_trades['actual_r_multiple'] > 0).mean() * 100
        zone_avg_optimal = zone_trades['optimal_r_multiple'].mean()
        print(f"   Zone {zone_num}: {len(zone_trades)} trades, "
              f"{zone_win_rate:.0f}% win rate, {zone_avg_optimal:.2f} avg optimal R")
    
    # Step 6: Save to database
    batch_id = None
    if save_to_db:
        print("\n[6] Saving to Database...")
        storage = StorageManager()
        
        runtime = time.time() - start_time
        metadata = {
            'ticker_id': ticker_id,
            'zones_count': len(zones_valid),
            'bars_count': len(bars_df),
            'runtime_seconds': round(runtime, 2),
            'single_day': True
        }
        
        batch_id = storage.save_results(symbol, trade_date, trade_date, trades_df, metadata)
        
        if batch_id:
            print(f"   ✓ Saved to batch: {batch_id}")
        else:
            print("   ✗ Failed to save to database")
    
    # Step 7: Run analysis
    if analyze and batch_id:
        print("\n[7] Running Analysis...")
        analyzer = MonteCarloAnalyzer()
        results = analyzer.analyze_batch(batch_id)
        
        print("\n" + "="*60)
        print("OPTIMAL R-MULTIPLE ANALYSIS")
        print("="*60)
        
        if 'optimal_r_distribution' in results:
            percentiles = results['optimal_r_percentiles']
            print(f"\nOptimal R Distribution:")
            print(f"  10th percentile: {percentiles['p10']:.2f}R (90% of trades exceed this)")
            print(f"  25th percentile: {percentiles['p25']:.2f}R (75% of trades exceed this)")
            print(f"  50th percentile: {percentiles['p50']:.2f}R (50% of trades exceed this)")
            print(f"  75th percentile: {percentiles['p75']:.2f}R (25% of trades exceed this)")
            print(f"  90th percentile: {percentiles['p90']:.2f}R (10% of trades exceed this)")
            
            if 'target_recommendations' in results:
                print("\n  Recommended Target Strategy:")
                for rec in results['target_recommendations']:
                    if rec['strategy'] == 'Conservative':
                        print(f"    {rec['description']}")
                        break
        
        if 'recommendations' in results:
            print("\nKey Insights:")
            for rec in results['recommendations']:
                print(f"  {rec}")
    
    # Final summary
    runtime = time.time() - start_time
    print("\n" + "="*60)
    print(f"Completed in {runtime:.1f} seconds")
    print("="*60)
    
    return batch_id

def run_batch_analysis(ticker: str = "AMD", 
                      start_date: str = "2024-01-01",
                      end_date: str = "2024-01-31"):
    """
    Run Monte Carlo for multiple days
    
    Args:
        ticker: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    print("\n" + "="*60)
    print("BATCH MONTE CARLO ANALYSIS")
    print("="*60)
    
    loader = DataLoader()
    
    # Get available sessions
    sessions = loader.get_available_sessions(ticker, start_date, end_date)
    
    if not sessions:
        print(f"No sessions found for {ticker} between {start_date} and {end_date}")
        return
    
    print(f"Found {len(sessions)} sessions to process")
    
    batch_ids = []
    for session in sessions:
        ticker_id = session['ticker_id']
        print(f"\nProcessing {ticker_id}...")
        
        try:
            batch_id = run_monte_carlo_single_day(ticker_id, save_to_db=True, analyze=False)
            if batch_id:
                batch_ids.append(batch_id)
        except Exception as e:
            logger.error(f"Error processing {ticker_id}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Processed {len(batch_ids)} sessions successfully")
    
    # Aggregate analysis
    if batch_ids:
        print("\nWould you like to run aggregate analysis? (y/n): ", end="")
        if input().lower() == 'y':
            run_aggregate_analysis(batch_ids)

def run_aggregate_analysis(batch_ids: List[str]):  # Now List is properly imported
    """Run analysis across multiple batches"""
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch all trades from batches
    all_trades = []
    for batch_id in batch_ids:
        response = client.table('monte_carlo_trades').select('*').eq(
            'batch_id', batch_id
        ).execute()
        if response.data:
            all_trades.extend(response.data)
    
    if not all_trades:
        print("No trades found")
        return
    
    df = pd.DataFrame(all_trades)
    
    print("\n" + "="*60)
    print("AGGREGATE ANALYSIS")
    print("="*60)
    
    print(f"\nTotal Trades: {len(df)}")
    print(f"Win Rate: {(df['actual_r_multiple'] > 0).mean() * 100:.1f}%")
    print(f"Avg Optimal R: {df['optimal_r_multiple'].mean():.2f}")
    print(f"Median Optimal R: {df['optimal_r_multiple'].median():.2f}")
    
    # Optimal R percentiles
    print("\nOptimal R Percentiles:")
    for p in [10, 25, 50, 75, 90, 95]:
        value = df['optimal_r_multiple'].quantile(p/100)
        print(f"  {p}th: {value:.2f}R")

def export_to_csv(batch_id: str):
    """Export batch results to CSV"""
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    response = client.table('monte_carlo_trades').select('*').eq(
        'batch_id', batch_id
    ).execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        filename = f"output/monte_carlo_{batch_id[:8]}.csv"
        df.to_csv(filename, index=False)
        print(f"✓ Exported to {filename}")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single day: python main.py TICKER.MMDDYY")
        print("  Example: python main.py PLTR.080525")
        print("  Batch: python main.py --batch TICKER START_DATE END_DATE")
        sys.exit(1)
    
    if sys.argv[1] == '--batch':
        # Batch mode
        ticker = sys.argv[2] if len(sys.argv) > 2 else "AMD"
        start_date = sys.argv[3] if len(sys.argv) > 3 else "2024-01-01"
        end_date = sys.argv[4] if len(sys.argv) > 4 else "2024-01-31"
        run_batch_analysis(ticker, start_date, end_date)
    else:
        # Single day mode
        ticker_id = sys.argv[1]
        batch_id = run_monte_carlo_single_day(ticker_id)
        
        if batch_id:
            print(f"\nBatch ID: {batch_id}")
            print("\nExport to CSV? (y/n): ", end="")
            if input().lower() == 'y':
                export_to_csv(batch_id)

if __name__ == "__main__":
    main()