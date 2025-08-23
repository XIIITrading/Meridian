"""
View and explore the mock data structure
"""
import pandas as pd
from test_analysis_integration import generate_mock_trades

def explore_mock_data():
    """Explore the mock data structure"""
    
    # Generate sample data
    df = generate_mock_trades(20)
    
    print("\n" + "="*60)
    print("MOCK DATA STRUCTURE")
    print("="*60)
    
    print("\n[Data Shape]")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    
    print("\n[Column List]")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")
    
    print("\n[Sample Data - First 5 Trades]")
    print(df[['ticker_id', 'zone_confluence_level', 'r_multiple', 
              'trade_result', 'pivot_strength']].head())
    
    print("\n[Statistical Summary]")
    print(df[['r_multiple', 'trade_result', 'distance_from_zone_ticks', 
              'pivot_strength']].describe())
    
    print("\n[Confluence Distribution]")
    print(df['zone_confluence_level'].value_counts())
    
    print("\n[Win/Loss Distribution]")
    winners = df[df['r_multiple'] > 0]
    losers = df[df['r_multiple'] <= 0]
    print(f"Winners: {len(winners)} ({len(winners)/len(df)*100:.1f}%)")
    print(f"Losers: {len(losers)} ({len(losers)/len(df)*100:.1f}%)")
    
    print("\n[Performance by Confluence]")
    for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
        level_df = df[df['zone_confluence_level'] == level]
        if not level_df.empty:
            win_rate = len(level_df[level_df['r_multiple'] > 0]) / len(level_df) * 100
            avg_r = level_df['r_multiple'].mean()
            print(f"  {level}: {len(level_df)} trades, {win_rate:.1f}% WR, {avg_r:.2f}R")

if __name__ == "__main__":
    explore_mock_data()