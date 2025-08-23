"""
Connect to your actual Supabase database and analyze real trades
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Debug: Show where we're looking for .env
print("\n[Environment Setup]")
# Go up to Meridian directory for .env
env_path = Path(__file__).parent.parent.parent / '.env'  # Added one more .parent
print(f"Looking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")

if env_path.exists():
    # Load the .env file
    from dotenv import load_dotenv
    result = load_dotenv(env_path)
    print(f"load_dotenv result: {result}")
    
    # Check if variables are loaded
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    print(f"SUPABASE_URL loaded: {bool(url)}")
    print(f"SUPABASE_ANON_KEY loaded: {bool(key)}")
    
    if url:
        print(f"URL preview: {url[:30]}...")
else:
    # Try alternative location (backtest_engine directory)
    alt_env_path = Path(__file__).parent.parent / '.env'
    print(f"\nTrying alternative path: {alt_env_path}")
    if alt_env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(alt_env_path)
        print("✅ Found .env in backtest_engine directory")
    else:
        print("❌ .env file not found in either location!")
        sys.exit(1)

# Check if env vars are actually set
if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
    print("\n❌ Environment variables not set!")
    sys.exit(1)

print("\n✅ Environment variables loaded successfully!")

# NOW import the modules that need environment variables
from data.supabase_client import BacktestSupabaseClient
from data.backtest_storage_manager import BacktestStorageManager
from analysis.statistical_analyzer import StatisticalAnalyzer
from analysis.pattern_recognizer import PatternRecognizer

def analyze_real_database():
    """
    This connects to YOUR Supabase database (not mock data)
    and analyzes any real trades you've entered
    """
    print("\n" + "="*60)
    print("ANALYZING REAL SUPABASE DATA")
    print("="*60)
    
    # Connect to YOUR actual Supabase
    try:
        client = BacktestSupabaseClient()
        print("✅ Connected to Supabase successfully!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None
    
    storage = BacktestStorageManager(client)
    
    # Get YOUR real trades from Supabase
    real_trades = storage.get_all_trades()
    
    if real_trades.empty:
        print("\n❌ No real trades found in your Supabase database")
        
        # Check for sessions
        sessions = storage.get_all_sessions()
        print(f"   Sessions in database: {len(sessions)}")
        
        print("\nTo add real trades:")
        print("1. Go to backtest_engine directory")
        print("2. Run: python scripts/cli_trade_entry.py")
        print("3. Enter your actual trades")
        print("4. Then run this analysis again")
        return None
    
    print(f"\n✅ Found {len(real_trades)} REAL trades in your database!")
    
    # Show what you actually have
    print("\n[Your Real Trading Data]")
    print(f"Tickers traded: {real_trades['ticker'].unique().tolist()}")
    print(f"Date range: {real_trades['entry_candle_time'].min()} to {real_trades['entry_candle_time'].max()}")
    print(f"Sessions: {real_trades['ticker_id'].nunique()}")
    
    # Show performance by ticker
    print("\n[Performance by Ticker]")
    for ticker in real_trades['ticker'].unique():
        ticker_trades = real_trades[real_trades['ticker'] == ticker]
        wins = len(ticker_trades[ticker_trades['r_multiple'] > 0])
        total = len(ticker_trades)
        win_rate = (wins / total * 100) if total > 0 else 0
        avg_r = ticker_trades['r_multiple'].mean()
        print(f"  {ticker}: {total} trades, {win_rate:.1f}% WR, {avg_r:.2f}R avg")
    
    # Analyze YOUR real trades
    print("\n[Running Statistical Analysis...]")
    analyzer = StatisticalAnalyzer(storage)
    results = analyzer.analyze_all_trades(save=True)
    
    print("\n[Your Overall Performance]")
    print(f"Win Rate: {results['basic_stats'].win_rate}%")
    print(f"Avg R-Multiple: {results['basic_stats'].avg_r_multiple}")
    print(f"Total R: {results['basic_stats'].total_r}")
    print(f"Profit Factor: {results['basic_stats'].profit_factor}")
    
    # Show confluence performance
    if 'confluence_analysis' in results:
        print("\n[Performance by Confluence Level]")
        for level, data in results['confluence_analysis'].items():
            print(f"  {level}: {data.trade_count} trades, {data.win_rate}% WR, {data.avg_r_multiple}R")
    
    # Find patterns in YOUR trades
    print("\n[Running Pattern Recognition...]")
    recognizer = PatternRecognizer(storage)
    patterns = recognizer.discover_patterns(save=True)
    
    print(f"\n[Patterns in Your Trading]")
    print(f"Discovered: {patterns['total_patterns_discovered']} patterns")
    
    if patterns.get('patterns'):
        print("\nTop Patterns:")
        for i, pattern in enumerate(patterns['patterns'][:3], 1):
            print(f"  {i}. {pattern.definition.name}")
            print(f"     Confidence: {pattern.confidence_score:.1f}%")
            print(f"     Win Rate: {pattern.performance.win_rate:.1f}%")
    
    # Your actual edge factors
    if results.get('edge_factors'):
        print("\n[Your Trading Edges]")
        for edge in results['edge_factors']:
            print(f"  • {edge.factor_name}")
            print(f"    Improvement: +{edge.improvement}%")
            print(f"    Confidence: {edge.confidence}%")
    
    return results

if __name__ == "__main__":
    results = analyze_real_database()
    
    if results:
        print("\n" + "="*60)
        print("✅ Successfully analyzed your real trading data!")
        print("This is YOUR actual performance, not mock data")
        print("\nAnalysis saved to Supabase analysis_results table")
    else:
        print("\n" + "="*60)
        print("Ready to analyze once you have trades in the database")