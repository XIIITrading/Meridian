#!/usr/bin/env python3
"""
Database Query Examples
Simple examples of how to read/write Supabase data from PyCharm

Run individual functions or the entire script for examples
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.service import DatabaseService
from database.supabase_client import SupabaseClient
from database.config import SUPABASE_URL, SUPABASE_KEY

def example_1_basic_connection():
    """Example 1: Test basic database connection"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Database Connection")
    print("=" * 60)
    
    # Initialize service
    db = DatabaseService()
    
    # Check connection
    if db.enabled:
        print("✅ Connected to Supabase!")
        
        # Show connection details
        status = db.get_connection_status()
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Connection failed")
    
    return db

def example_2_list_recent_data(db: DatabaseService):
    """Example 2: List recent analyses"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: List Recent Analyses")
    print("=" * 60)
    
    try:
        # Get recent analyses
        analyses = db.list_recent_analyses(limit=5)
        
        print(f"Found {len(analyses)} recent analyses:")
        for analysis in analyses:
            print(f"  📊 {analysis['ticker_id']}: {analysis['ticker']} on {analysis['session_date']} - ${analysis.get('current_price', 'N/A')}")
        
        return analyses
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def example_3_get_specific_ticker(db: DatabaseService, ticker_id: str = None):
    """Example 3: Get detailed data for a specific ticker"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Get Ticker Details")
    print("=" * 60)
    
    # Use provided ticker_id or find one from recent data
    if not ticker_id:
        recent = db.list_recent_analyses(limit=1)
        if recent:
            ticker_id = recent[0]['ticker_id']
            print(f"Using most recent ticker: {ticker_id}")
        else:
            print("No data found in database")
            return None
    
    try:
        # Get detailed analysis
        summary = db.get_analysis_summary(ticker_id)
        
        if summary:
            print(f"📈 Analysis for {summary['ticker']} ({summary['ticker_id']}):")
            print(f"   Date: {summary['session_date']}")
            print(f"   Price: ${summary.get('current_price', 0):.2f}")
            print(f"   ATR Daily: {summary.get('atr_daily', 0):.2f}")
            print(f"   Zones: {summary['zone_count']}")
            
            # Show zones
            print(f"\n   🎯 M15 Zones:")
            for zone in summary['zones'][:3]:  # Show first 3 zones
                print(f"      Zone {zone['zone_number']}: ${zone['low']:.2f}-${zone['high']:.2f}")
                print(f"         Score: {zone.get('score', 0):.1f}, Sources: {len(zone['sources'])}")
        
        return summary
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def example_4_direct_sql_queries(db: DatabaseService):
    """Example 4: Direct SQL queries using Supabase client"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Direct SQL Queries")
    print("=" * 60)
    
    try:
        client = db.client
        
        # Query 1: Get all tickers with their latest session
        print("🔍 Query 1: Latest session per ticker")
        result = client.client.table('levels_zones')\
            .select('ticker, session_date, current_price')\
            .order('session_date', desc=True)\
            .limit(10)\
            .execute()
        
        if result.data:
            for row in result.data[:5]:
                print(f"   {row['ticker']}: {row['session_date']} - ${row.get('current_price', 'N/A')}")
        
        # Query 2: Get zones with high confluence scores
        print(f"\n🔍 Query 2: High confluence zones (score >= 8)")
        zones_query = """
        SELECT ticker_id, 
               m15_zone1_confluence_score as zone1_score,
               m15_zone2_confluence_score as zone2_score,
               m15_zone3_confluence_score as zone3_score
        FROM levels_zones 
        WHERE m15_zone1_confluence_score >= 8 
           OR m15_zone2_confluence_score >= 8 
           OR m15_zone3_confluence_score >= 8
        ORDER BY session_date DESC
        LIMIT 5;
        """
        
        # Note: Custom SQL might require RPC function or might not be available on all plans
        print("   (Custom SQL queries may require Supabase Pro plan)")
        
        # Alternative: Use basic filtering
        high_conf_result = client.client.table('levels_zones')\
            .select('ticker_id, m15_zone1_confluence_score, m15_zone2_confluence_score, m15_zone3_confluence_score')\
            .or_('m15_zone1_confluence_score.gte.8,m15_zone2_confluence_score.gte.8,m15_zone3_confluence_score.gte.8')\
            .limit(5)\
            .execute()
        
        if high_conf_result.data:
            for row in high_conf_result.data:
                scores = [row.get(f'm15_zone{i}_confluence_score') for i in range(1, 4)]
                high_scores = [s for s in scores if s and s >= 8]
                if high_scores:
                    print(f"   {row['ticker_id']}: High scores = {high_scores}")
        
        return True
        
    except Exception as e:
        print(f"Error with direct queries: {e}")
        return False

def example_5_confluence_analysis(db: DatabaseService):
    """Example 5: Analyze confluence patterns"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Confluence Pattern Analysis")
    print("=" * 60)
    
    try:
        client = db.client
        
        # Get confluence details
        print("🔍 Looking for confluence details...")
        details_result = client.client.table('zone_confluence_details')\
            .select('*, confluence_analyses_enhanced(ticker, session_date)')\
            .limit(10)\
            .execute()
        
        if details_result.data:
            print(f"Found {len(details_result.data)} confluence detail records")
            
            # Analyze patterns
            hvn_count = sum(1 for d in details_result.data if d.get('has_hvn_30d'))
            cam_count = sum(1 for d in details_result.data if d.get('has_cam_weekly'))
            pdh_count = sum(1 for d in details_result.data if d.get('has_pdh'))
            
            print(f"   📊 Pattern Summary:")
            print(f"      HVN 30D zones: {hvn_count}")
            print(f"      Camarilla Weekly zones: {cam_count}")
            print(f"      PDH zones: {pdh_count}")
            
            # Show detailed examples
            print(f"\n   🎯 Example confluences:")
            for detail in details_result.data[:3]:
                ticker_info = detail.get('confluence_analyses_enhanced', {})
                if ticker_info:
                    flags = [k for k, v in detail.items() if k.startswith('has_') and v]
                    if flags:
                        print(f"      Zone {detail['zone_number']} ({ticker_info.get('ticker', 'Unknown')}): {', '.join(flags[:3])}")
        else:
            print("   No confluence details found - may need to run CLI with --save-db first")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing confluence: {e}")
        return False

def example_6_export_to_pandas(db: DatabaseService):
    """Example 6: Export data to pandas for analysis"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Export to Pandas DataFrame")
    print("=" * 60)
    
    try:
        # Get recent analyses
        analyses = db.list_recent_analyses(limit=20)
        
        if not analyses:
            print("No data to export")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(analyses)
        print(f"📊 Created DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"   Columns: {list(df.columns)}")
        
        # Basic analysis
        if 'ticker' in df.columns:
            print(f"\n   📈 Summary:")
            print(f"      Unique tickers: {df['ticker'].nunique()}")
            print(f"      Ticker distribution:")
            ticker_counts = df['ticker'].value_counts().head(5)
            for ticker, count in ticker_counts.items():
                print(f"         {ticker}: {count} analyses")
        
        if 'current_price' in df.columns:
            prices = df['current_price'].dropna()
            if not prices.empty:
                print(f"      Price range: ${prices.min():.2f} - ${prices.max():.2f}")
                print(f"      Average price: ${prices.mean():.2f}")
        
        # Save option
        save_csv = input("\n💾 Save to CSV file? (y/n): ").strip().lower()
        if save_csv == 'y':
            filename = f"supabase_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"   ✅ Saved to {filename}")
        
        return df
        
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        return None

def run_all_examples():
    """Run all examples in sequence"""
    print("🚀 RUNNING ALL DATABASE EXAMPLES")
    print("=" * 80)
    
    # Example 1: Connection
    db = example_1_basic_connection()
    if not db or not db.enabled:
        print("❌ Cannot continue - database connection failed")
        return
    
    # Example 2: List data
    recent_data = example_2_list_recent_data(db)
    
    # Example 3: Specific ticker
    ticker_id = recent_data[0]['ticker_id'] if recent_data else None
    example_3_get_specific_ticker(db, ticker_id)
    
    # Example 4: Direct queries
    example_4_direct_sql_queries(db)
    
    # Example 5: Confluence analysis
    example_5_confluence_analysis(db)
    
    # Example 6: Pandas export
    example_6_export_to_pandas(db)
    
    print(f"\n" + "=" * 80)
    print("🎉 ALL EXAMPLES COMPLETED!")
    print("=" * 80)
    print("\n💡 Next steps:")
    print("   1. Run confluence CLI with --save-db to add more data")
    print("   2. Use these examples as templates for your analysis")
    print("   3. Import individual functions for custom analysis")

if __name__ == "__main__":
    # Check if user wants to run all examples or specific ones
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        db = example_1_basic_connection()
        if db and db.enabled:
            if example_num == "2":
                example_2_list_recent_data(db)
            elif example_num == "3":
                example_3_get_specific_ticker(db)
            elif example_num == "4":
                example_4_direct_sql_queries(db)
            elif example_num == "5":
                example_5_confluence_analysis(db)
            elif example_num == "6":
                example_6_export_to_pandas(db)
            else:
                print(f"Unknown example: {example_num}")
                print("Available: 2, 3, 4, 5, 6")
    else:
        run_all_examples()