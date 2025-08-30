#!/usr/bin/env python3
"""
PyCharm Database Examples
Copy and paste these examples into PyCharm Console or create scripts

Usage in PyCharm:
1. Open Python Console (View -> Tool Windows -> Python Console)
2. Copy and paste the examples below
3. Run them interactively

OR

1. Create a new Python file in PyCharm
2. Copy these examples
3. Run the file
"""

import sys
import pandas as pd
from pathlib import Path

# Add confluence_system to path (adjust if needed)
sys.path.insert(0, str(Path(__file__).parent.parent))

def pycharm_example_1_basic_queries():
    """Example 1: Basic database queries"""
    print("EXAMPLE 1: Basic Database Queries")
    print("-" * 40)
    
    from database.service import DatabaseService
    
    # Initialize database
    db = DatabaseService()
    print(f"Database connected: {db.enabled}")
    
    if not db.enabled:
        print("Fix connection before continuing")
        return
    
    # Get recent analyses
    recent = db.list_recent_analyses(5)
    print(f"\nFound {len(recent)} recent analyses:")
    
    for analysis in recent:
        ticker_id = analysis['ticker_id']
        ticker = analysis['ticker']
        price = analysis.get('current_price', 'N/A')
        date = analysis['session_date']
        print(f"  {ticker_id}: {ticker} on {date} @ ${price}")
    
    return db, recent

def pycharm_example_2_detailed_analysis():
    """Example 2: Detailed ticker analysis"""
    print("\nEXAMPLE 2: Detailed Ticker Analysis")
    print("-" * 40)
    
    from database.service import DatabaseService
    
    db = DatabaseService()
    
    # Get a ticker (use real ticker_id from your data)
    ticker_id = "NVDA.082625"  # Example - replace with actual ticker_id
    
    summary = db.get_analysis_summary(ticker_id)
    
    if summary:
        print(f"Analysis for {summary['ticker']} ({summary['ticker_id']})")
        print(f"  Session Date: {summary['session_date']}")
        print(f"  Current Price: ${summary.get('current_price', 0):.2f}")
        print(f"  Daily ATR: {summary.get('atr_daily', 0):.2f}")
        print(f"  15min ATR: {summary.get('atr_15min', 0):.2f}")
        print(f"  Total Zones: {summary['zone_count']}")
        
        print(f"\n  M15 Zones:")
        for zone in summary['zones']:
            score = zone.get('score', 0)
            level = zone.get('confluence_level', 'N/A')
            sources = len(zone['sources'])
            
            print(f"    Zone {zone['zone_number']}: ${zone['low']:.2f}-${zone['high']:.2f}")
            print(f"      Score: {score:.1f} | Level: {level} | Sources: {sources}")
            
            if zone['sources']:
                source_list = ', '.join(zone['sources'][:3])
                if len(zone['sources']) > 3:
                    source_list += f" (+{len(zone['sources']) - 3} more)"
                print(f"      Sources: {source_list}")
    else:
        print(f"No data found for {ticker_id}")
        print("Available ticker IDs:")
        recent = db.list_recent_analyses(5)
        for analysis in recent:
            print(f"  {analysis['ticker_id']}")

def pycharm_example_3_pandas_analysis():
    """Example 3: Export to pandas for analysis"""
    print("\nEXAMPLE 3: Pandas Analysis")
    print("-" * 40)
    
    from database.service import DatabaseService
    
    db = DatabaseService()
    
    # Get data
    data = db.list_recent_analyses(50)  # Get more data for analysis
    
    if not data:
        print("No data available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    print(f"Created DataFrame: {df.shape[0]} rows x {df.shape[1]} columns")
    
    # Basic analysis
    print(f"\nBasic Statistics:")
    print(f"  Unique tickers: {df['ticker'].nunique()}")
    print(f"  Date range: {df['session_date'].min()} to {df['session_date'].max()}")
    
    if 'current_price' in df.columns:
        prices = df['current_price'].dropna()
        if not prices.empty:
            print(f"  Price range: ${prices.min():.2f} - ${prices.max():.2f}")
            print(f"  Average price: ${prices.mean():.2f}")
    
    # Group by ticker
    print(f"\nAnalyses per ticker:")
    ticker_counts = df['ticker'].value_counts().head(5)
    for ticker, count in ticker_counts.items():
        print(f"  {ticker}: {count} analyses")
    
    return df

def pycharm_example_4_direct_supabase_queries():
    """Example 4: Direct Supabase queries"""
    print("\nEXAMPLE 4: Direct Supabase Queries")
    print("-" * 40)
    
    from database.service import DatabaseService
    
    db = DatabaseService()
    client = db.client  # Get direct Supabase client
    
    # Query 1: Get specific columns
    print("Query 1: Recent tickers with prices")
    result = client.client.table('levels_zones')\
        .select('ticker_id, ticker, current_price, session_date')\
        .order('session_date', desc=True)\
        .limit(5)\
        .execute()
    
    if result.data:
        for row in result.data:
            print(f"  {row['ticker_id']}: {row['ticker']} @ ${row.get('current_price', 'N/A')}")
    
    # Query 2: Filter by ticker
    print(f"\nQuery 2: All TSLA analyses")
    tesla_result = client.client.table('levels_zones')\
        .select('ticker_id, session_date, current_price')\
        .eq('ticker', 'TSLA')\
        .order('session_date', desc=True)\
        .execute()
    
    if tesla_result.data:
        for row in tesla_result.data:
            print(f"  {row['ticker_id']}: {row['session_date']} @ ${row.get('current_price', 'N/A')}")
    
    # Query 3: High confluence zones
    print(f"\nQuery 3: High confluence zones (score >= 8)")
    high_conf = client.client.table('levels_zones')\
        .select('ticker_id, m15_zone1_confluence_score, m15_zone2_confluence_score, m15_zone3_confluence_score')\
        .or_('m15_zone1_confluence_score.gte.8,m15_zone2_confluence_score.gte.8,m15_zone3_confluence_score.gte.8')\
        .limit(5)\
        .execute()
    
    if high_conf.data:
        for row in high_conf.data:
            scores = [row.get(f'm15_zone{i}_confluence_score') for i in range(1, 4)]
            high_scores = [f"{i+1}:{s:.1f}" for i, s in enumerate(scores) if s and s >= 8]
            if high_scores:
                print(f"  {row['ticker_id']}: Zones {', '.join(high_scores)}")

def run_all_pycharm_examples():
    """Run all examples"""
    print("PYCHARM DATABASE EXAMPLES")
    print("=" * 50)
    
    # Example 1
    db, recent = pycharm_example_1_basic_queries()
    
    if not db or not db.enabled:
        print("Cannot continue - fix database connection")
        return
    
    # Example 2
    pycharm_example_2_detailed_analysis()
    
    # Example 3
    df = pycharm_example_3_pandas_analysis()
    
    # Example 4
    pycharm_example_4_direct_supabase_queries()
    
    print(f"\n" + "=" * 50)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 50)
    print("\nQuick reference for PyCharm Console:")
    print("  from database.service import DatabaseService")
    print("  db = DatabaseService()")
    print("  recent = db.list_recent_analyses(5)")
    print("  summary = db.get_analysis_summary('TICKER.MMDDYY')")

# Individual functions you can call from PyCharm Console
def quick_query(ticker=None, limit=5):
    """Quick query function for PyCharm Console"""
    from database.service import DatabaseService
    db = DatabaseService()
    
    if ticker:
        analyses = [a for a in db.list_recent_analyses(50) if a['ticker'].upper() == ticker.upper()]
        print(f"Found {len(analyses)} analyses for {ticker.upper()}")
    else:
        analyses = db.list_recent_analyses(limit)
        print(f"Found {len(analyses)} recent analyses")
    
    for analysis in analyses:
        print(f"  {analysis['ticker_id']}: {analysis['ticker']} @ ${analysis.get('current_price', 'N/A')}")
    
    return analyses

def get_ticker_details(ticker_id):
    """Get details for a specific ticker"""
    from database.service import DatabaseService
    db = DatabaseService()
    
    summary = db.get_analysis_summary(ticker_id)
    if summary:
        print(f"{summary['ticker']} ({ticker_id})")
        print(f"  Date: {summary['session_date']}")
        print(f"  Price: ${summary.get('current_price', 0):.2f}")
        print(f"  Zones: {summary['zone_count']}")
        return summary
    else:
        print(f"No data for {ticker_id}")
        return None

if __name__ == "__main__":
    # Run examples when file is executed
    run_all_pycharm_examples()
    
    print(f"\n" + "-" * 50)
    print("INDIVIDUAL FUNCTIONS AVAILABLE:")
    print("  quick_query('TSLA', 10)")
    print("  get_ticker_details('TSLA.082625')")
    print("  run_all_pycharm_examples()")