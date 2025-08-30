#!/usr/bin/env python3
"""
Interactive Database Client for Supabase - Windows Compatible
Run this script to interact with your confluence and Monte Carlo data

Usage:
    python database/interactive_client_windows.py
    
Features:
- List recent analyses
- Query specific ticker data
- Explore confluence patterns
- Export data for analysis
- Test database connectivity
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.service import DatabaseService
from database.config import get_connection_info

class InteractiveClient:
    """Interactive client for database operations"""
    
    def __init__(self):
        """Initialize the client"""
        self.db = DatabaseService()
        self.setup_complete = False
        
    def setup(self):
        """Setup and test the database connection"""
        print("=" * 70)
        print("SUPABASE INTERACTIVE CLIENT")
        print("=" * 70)
        
        # Test connection
        if not self.db.enabled:
            print("ERROR: Database connection failed!")
            print("\nTroubleshooting:")
            print("1. Check your .env file has SUPABASE_URL and SUPABASE_KEY")
            print("2. Verify your Supabase credentials are correct")
            print("3. Ensure network connectivity to Supabase")
            return False
        
        print("SUCCESS: Database connected successfully!")
        
        # Show connection info
        config_info = get_connection_info()
        print(f"Connected to: {config_info['url_preview']}")
        
        # Test basic query
        try:
            recent_count = len(self.db.list_recent_analyses(1))
            print(f"Found data in database (sample query successful)")
        except Exception as e:
            print(f"WARNING: Database connected but query failed: {e}")
        
        self.setup_complete = True
        return True
    
    def list_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent confluence analyses"""
        print(f"\nRECENT ANALYSES (Last {limit})")
        print("-" * 50)
        
        try:
            analyses = self.db.list_recent_analyses(limit)
            
            if not analyses:
                print("No analyses found in database.")
                return []
            
            # Display in table format
            for i, analysis in enumerate(analyses, 1):
                date_str = analysis.get('session_date', 'Unknown')
                price = analysis.get('current_price')
                price_str = f"${price:.2f}" if price else "N/A"
                
                print(f"{i:2d}. {analysis['ticker_id']:<12} | {analysis['ticker']:<6} | {date_str} | {price_str}")
            
            return analyses
            
        except Exception as e:
            print(f"ERROR: Error fetching analyses: {e}")
            return []
    
    def get_ticker_details(self, ticker_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis for a specific ticker"""
        print(f"\nANALYSIS DETAILS: {ticker_id}")
        print("-" * 50)
        
        try:
            summary = self.db.get_analysis_summary(ticker_id)
            
            if not summary:
                print(f"No analysis found for {ticker_id}")
                available = self.db.list_recent_analyses(5)
                if available:
                    print("\nAvailable ticker IDs:")
                    for a in available:
                        print(f"  • {a['ticker_id']}")
                return None
            
            # Display summary
            print(f"Ticker: {summary['ticker']}")
            print(f"Date: {summary['session_date']}")
            print(f"Current Price: ${summary.get('current_price', 0):.2f}")
            print(f"Daily ATR: {summary.get('atr_daily', 0):.2f}")
            print(f"15min ATR: {summary.get('atr_15min', 0):.2f}")
            print(f"Total Zones: {summary['zone_count']}")
            
            # Display zones
            print(f"\nM15 ZONES:")
            for zone in summary['zones']:
                sources_str = ", ".join(zone['sources'][:3])
                if len(zone['sources']) > 3:
                    sources_str += f" (+{len(zone['sources']) - 3} more)"
                
                flags_str = ", ".join(zone['flags'].keys()) if zone['flags'] else "None"
                
                print(f"  Zone {zone['zone_number']}: ${zone['low']:.2f}-${zone['high']:.2f} "
                      f"(Score: {zone.get('score', 0):.1f}, Level: {zone.get('confluence_level', 'N/A')})")
                print(f"    Sources: {sources_str}")
                if flags_str != "None":
                    print(f"    Flags: {flags_str}")
            
            return summary
            
        except Exception as e:
            print(f"ERROR: Error fetching ticker details: {e}")
            return None
    
    def find_confluence_patterns(self, pattern_type: str = "high_confluence") -> List[Dict[str, Any]]:
        """Find specific confluence patterns"""
        print(f"\nCONFLUENCE PATTERNS: {pattern_type.upper()}")
        print("-" * 50)
        
        try:
            # Use basic filtering since custom SQL might not be available
            if pattern_type == "high_confluence":
                # Find zones with high confluence scores
                client = self.db.client
                result = client.client.table('levels_zones')\
                    .select('ticker_id, ticker, session_date, m15_zone1_confluence_score, m15_zone2_confluence_score, m15_zone3_confluence_score')\
                    .or_('m15_zone1_confluence_score.gte.8,m15_zone2_confluence_score.gte.8,m15_zone3_confluence_score.gte.8')\
                    .order('session_date', desc=True)\
                    .limit(10)\
                    .execute()
                
                if result.data:
                    count = 0
                    for row in result.data:
                        scores = [
                            ('1', row.get('m15_zone1_confluence_score')),
                            ('2', row.get('m15_zone2_confluence_score')),
                            ('3', row.get('m15_zone3_confluence_score'))
                        ]
                        high_scores = [(zone, score) for zone, score in scores if score and score >= 8]
                        
                        if high_scores:
                            count += 1
                            score_text = ", ".join([f"Zone {zone}: {score:.1f}" for zone, score in high_scores])
                            print(f"{count:2d}. {row['ticker_id']:<12} | {score_text}")
                    
                    print(f"\nFound {count} tickers with high confluence zones")
                    return result.data
                else:
                    print("No high confluence patterns found")
                    return []
            
            elif pattern_type == "recent_activity":
                # Show most recent analyses
                recent = self.db.list_recent_analyses(15)
                for i, analysis in enumerate(recent, 1):
                    print(f"{i:2d}. {analysis['ticker_id']:<12} | {analysis['session_date']}")
                return recent
            
            else:
                print(f"Available pattern types: high_confluence, recent_activity")
                return []
                
        except Exception as e:
            print(f"ERROR: Error finding patterns: {e}")
            return []
    
    def export_data_for_analysis(self, ticker: Optional[str] = None, days: int = 30) -> Optional[pd.DataFrame]:
        """Export data to pandas DataFrame for analysis"""
        print(f"\nEXPORTING DATA FOR ANALYSIS")
        print("-" * 50)
        
        try:
            # Get recent analyses
            analyses = self.db.list_recent_analyses(100)  # Get more data
            
            if not analyses:
                print("No data to export")
                return None
            
            # Filter by ticker if specified
            if ticker:
                analyses = [a for a in analyses if a['ticker'].upper() == ticker.upper()]
                print(f"Filtered to {len(analyses)} analyses for {ticker.upper()}")
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            analyses = [
                a for a in analyses 
                if datetime.fromisoformat(a.get('analysis_datetime', '1970-01-01')) >= cutoff_date
            ]
            
            print(f"Found {len(analyses)} analyses in the last {days} days")
            
            # Convert to DataFrame
            df = pd.DataFrame(analyses)
            
            if not df.empty:
                print(f"DataFrame created: {df.shape[0]} rows, {df.shape[1]} columns")
                print(f"Columns: {list(df.columns)}")
                
                # Show summary statistics
                if 'current_price' in df.columns:
                    print(f"\nPrice Range: ${df['current_price'].min():.2f} - ${df['current_price'].max():.2f}")
                
                print(f"Unique Tickers: {df['ticker'].nunique() if 'ticker' in df.columns else 'N/A'}")
                
                return df
            else:
                print("No data to export")
                return None
                
        except Exception as e:
            print(f"ERROR: Error exporting data: {e}")
            return None
    
    def interactive_menu(self):
        """Run interactive menu"""
        if not self.setup_complete:
            return
        
        while True:
            print(f"\n" + "=" * 50)
            print("INTERACTIVE MENU")
            print("=" * 50)
            print("1. List recent analyses")
            print("2. Get ticker details")
            print("3. Find confluence patterns")
            print("4. Export data to DataFrame")
            print("5. Connection status")
            print("6. Exit")
            
            try:
                choice = input("\nEnter choice (1-6): ").strip()
                
                if choice == "1":
                    limit = input("Number of analyses to show (default 10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    self.list_recent_analyses(limit)
                
                elif choice == "2":
                    ticker_id = input("Enter ticker ID (e.g., AAPL.082924): ").strip()
                    if ticker_id:
                        self.get_ticker_details(ticker_id)
                
                elif choice == "3":
                    print("\nPattern types:")
                    print("  a) high_confluence - Zones with scores >= 8")
                    print("  b) recent_activity - Recent analyses")
                    
                    pattern_choice = input("Choose pattern (a/b): ").strip().lower()
                    pattern_map = {"a": "high_confluence", "b": "recent_activity"}
                    
                    if pattern_choice in pattern_map:
                        self.find_confluence_patterns(pattern_map[pattern_choice])
                
                elif choice == "4":
                    ticker = input("Ticker filter (optional, press Enter for all): ").strip()
                    days = input("Days back (default 30): ").strip()
                    days = int(days) if days.isdigit() else 30
                    
                    df = self.export_data_for_analysis(ticker if ticker else None, days)
                    if df is not None:
                        save = input("\nSave to CSV? (y/n): ").strip().lower()
                        if save == 'y':
                            filename = f"confluence_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            df.to_csv(filename, index=False)
                            print(f"SUCCESS: Saved to {filename}")
                
                elif choice == "5":
                    status = self.db.get_connection_status()
                    print(f"\nConnection Status:")
                    for key, value in status.items():
                        print(f"  {key}: {value}")
                
                elif choice == "6":
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"ERROR: {e}")

def main():
    """Main function"""
    client = InteractiveClient()
    
    if client.setup():
        print(f"\nReady! You can now:")
        print("- Query your confluence data")
        print("- Explore Monte Carlo preparation data")
        print("- Export data for analysis")
        
        try:
            # Show quick overview
            client.list_recent_analyses(5)
            
            # Start interactive menu
            start_menu = input("\nStart interactive menu? (y/n): ").strip().lower()
            if start_menu == 'y':
                client.interactive_menu()
            else:
                print("SUCCESS: Client ready. Import this module to use programmatically:")
                print("  from database.interactive_client_windows import InteractiveClient")
                print("  client = InteractiveClient()")
                print("  client.setup()")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")

if __name__ == "__main__":
    main()