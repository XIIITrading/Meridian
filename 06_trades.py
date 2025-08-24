#!/usr/bin/env python
r"""
06_trades.py - Trade entry and management system for backtesting
Enter manual trades with zone analysis and performance metrics

Location: C:\XIIITradingSystems\Meridian\06_trades.py

Usage:
    python 06_trades.py                    # Enter new trade
    python 06_trades.py --list            # List all trades
    python 06_trades.py --ticker NVDA     # List trades for specific ticker
    python 06_trades.py --session AMD.121824  # List trades for specific session
    python 06_trades.py --summary         # Show overall trade summary
    python 06_trades.py --delete          # Delete a trade (interactive)
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# Add backtest_engine to path
sys.path.append(str(Path(__file__).parent / 'backtest_engine'))

# Load environment variables from Meridian/.env
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    print(f"❌ .env file not found at {env_path}")
    print("Please create a .env file with your Supabase credentials:")
    print("  SUPABASE_URL=your_url_here")
    print("  SUPABASE_ANON_KEY=your_key_here")
    sys.exit(1)

load_dotenv(env_path)
print(f"✅ Environment loaded from {env_path}")

# Import modules from backtest_engine
from data.supabase_client import BacktestSupabaseClient
from data.backtest_storage_manager import BacktestStorageManager
from scripts.cli_trade_entry import CLITradeEntry

class TradeManager:
    """Main trade management interface"""
    
    def __init__(self):
        """Initialize connection"""
        self.connect_to_database()
    
    def connect_to_database(self):
        """Connect to Supabase database"""
        print("\n[Database Connection]")
        try:
            self.client = BacktestSupabaseClient()
            self.storage = BacktestStorageManager(self.client)
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
    
    def enter_new_trade(self):
        """Launch the trade entry CLI"""
        print("\n" + "="*70)
        print("LAUNCHING TRADE ENTRY SYSTEM")
        print("="*70)
        
        # Ask about debug mode
        debug_input = input("Enable debug mode? (y/n): ").strip().lower()
        debug_mode = (debug_input == 'y')
        
        # Create CLI with debug mode setting
        cli = CLITradeEntry(debug_mode=debug_mode)
        cli.run()
    
    def list_trades(self, ticker=None, session_id=None):
        """List trades with optional filters"""
        print("\n" + "="*70)
        print("TRADE LIST")
        print("="*70)
        
        # Get trades based on filters
        if session_id:
            trades_df = self.storage.get_session_trades(session_id)
            print(f"Session: {session_id}")
        elif ticker:
            trades_df = self.storage.get_all_trades(ticker=ticker)
            print(f"Ticker: {ticker}")
        else:
            trades_df = self.storage.get_all_trades()
            print("All Trades")
        
        if trades_df.empty:
            print("\n❌ No trades found")
            return
        
        # Format for display
        display_df = self._format_trades_for_display(trades_df)
        
        print(f"\nFound {len(trades_df)} trades:")
        print("\n" + tabulate(display_df, headers='keys', tablefmt='grid', floatfmt='.2f'))
        
        # Show summary statistics
        self._show_trade_statistics(trades_df)
    
    def _format_trades_for_display(self, trades_df):
        """Format trades DataFrame for display"""
        # Select and rename columns for display
        display_columns = {
            'ticker': 'Ticker',
            'trade_date': 'Date',
            'trade_direction': 'Dir',
            'entry_price': 'Entry',
            'exit_price': 'Exit',
            'trade_result': 'P&L',
            'r_multiple': 'R',
            'zone_confluence_level': 'Zone',
            'notes': 'Notes'
        }
        
        # Create display dataframe
        display_df = pd.DataFrame()
        for col, display_name in display_columns.items():
            if col in trades_df.columns:
                display_df[display_name] = trades_df[col]
        
        # Format specific columns
        if 'Date' in display_df.columns:
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
        
        if 'Dir' in display_df.columns:
            display_df['Dir'] = display_df['Dir'].str.upper()[:1]  # L or S
        
        if 'Notes' in display_df.columns:
            # Truncate long notes
            display_df['Notes'] = display_df['Notes'].fillna('').str[:30]
        
        return display_df
    
    def _show_trade_statistics(self, trades_df):
        """Show statistics for trades"""
        print("\n" + "-"*50)
        print("STATISTICS")
        print("-"*50)
        
        # Basic stats
        total_trades = len(trades_df)
        
        # Handle different column names
        if 'trade_result' in trades_df.columns:
            total_pnl = trades_df['trade_result'].sum()
            winners = trades_df[trades_df['trade_result'] > 0]
        else:
            total_pnl = 0
            winners = pd.DataFrame()
        
        if 'r_multiple' in trades_df.columns:
            avg_r = trades_df['r_multiple'].mean()
            total_r = trades_df['r_multiple'].sum()
        else:
            avg_r = 0
            total_r = 0
        
        win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0
        
        print(f"Total Trades: {total_trades}")
        print(f"Winners: {len(winners)}")
        print(f"Losers: {total_trades - len(winners)}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"Total R: {total_r:.2f}")
        print(f"Avg R: {avg_r:.2f}")
        
        # By ticker breakdown
        if 'ticker' in trades_df.columns:
            print("\n[By Ticker]")
            for ticker in trades_df['ticker'].unique():
                ticker_trades = trades_df[trades_df['ticker'] == ticker]
                ticker_pnl = ticker_trades['trade_result'].sum() if 'trade_result' in ticker_trades.columns else 0
                ticker_r = ticker_trades['r_multiple'].mean() if 'r_multiple' in ticker_trades.columns else 0
                print(f"  {ticker}: {len(ticker_trades)} trades, ${ticker_pnl:.2f} P&L, {ticker_r:.2f} avg R")
        
        # By confluence level
        if 'zone_confluence_level' in trades_df.columns:
            print("\n[By Confluence Level]")
            for level in sorted(trades_df['zone_confluence_level'].dropna().unique()):
                level_trades = trades_df[trades_df['zone_confluence_level'] == level]
                level_count = len(level_trades)
                if 'trade_result' in level_trades.columns:
                    level_winners = level_trades[level_trades['trade_result'] > 0]
                    level_wr = (len(level_winners) / level_count * 100) if level_count > 0 else 0
                else:
                    level_wr = 0
                
                if 'r_multiple' in level_trades.columns:
                    level_r = level_trades['r_multiple'].mean()
                else:
                    level_r = 0
                    
                print(f"  {level}: {level_count} trades, {level_wr:.1f}% WR, {level_r:.2f} avg R")
    
    def show_summary(self):
        """Show overall trading summary"""
        print("\n" + "="*70)
        print("TRADING SUMMARY")
        print("="*70)
        
        # Get all trades
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            print("\n❌ No trades in database")
            print("\nTo add trades:")
            print("  python 06_trades.py")
            return
        
        # Overall statistics
        self._show_trade_statistics(trades_df)
        
        # Recent trades
        print("\n" + "-"*50)
        print("RECENT TRADES (Last 5)")
        print("-"*50)
        
        recent = trades_df.nlargest(5, 'entry_candle_time') if 'entry_candle_time' in trades_df.columns else trades_df.head(5)
        display_df = self._format_trades_for_display(recent)
        print("\n" + tabulate(display_df, headers='keys', tablefmt='grid', floatfmt='.2f'))
        
        # Best and worst trades
        if 'r_multiple' in trades_df.columns and not trades_df['r_multiple'].isna().all():
            print("\n" + "-"*50)
            print("NOTABLE TRADES")
            print("-"*50)
            
            best_idx = trades_df['r_multiple'].idxmax()
            worst_idx = trades_df['r_multiple'].idxmin()
            
            best_trade = trades_df.loc[best_idx]
            worst_trade = trades_df.loc[worst_idx]
            
            print(f"\nBest Trade:")
            print(f"  Ticker: {best_trade['ticker']}")
            print(f"  Date: {best_trade['trade_date']}")
            print(f"  R-Multiple: {best_trade['r_multiple']:.2f}")
            print(f"  P&L: ${best_trade.get('trade_result', 0):.2f}")
            
            print(f"\nWorst Trade:")
            print(f"  Ticker: {worst_trade['ticker']}")
            print(f"  Date: {worst_trade['trade_date']}")
            print(f"  R-Multiple: {worst_trade['r_multiple']:.2f}")
            print(f"  P&L: ${worst_trade.get('trade_result', 0):.2f}")
    
    def delete_trade_interactive(self):
        """Interactive trade deletion"""
        print("\n" + "="*70)
        print("DELETE TRADE")
        print("="*70)
        
        # Get all trades
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            print("\n❌ No trades to delete")
            return
        
        # Show trades with index
        print("\nSelect trade to delete:")
        for i, (idx, trade) in enumerate(trades_df.iterrows(), 1):
            print(f"\n[{i}] {trade['ticker']} - {trade['trade_date']}")
            print(f"    Entry: ${trade['entry_price']:.2f} → Exit: ${trade['exit_price']:.2f}")
            if 'r_multiple' in trade and pd.notna(trade['r_multiple']):
                print(f"    Result: {trade['r_multiple']:.2f}R")
            if 'notes' in trade and pd.notna(trade['notes']):
                print(f"    Notes: {trade['notes'][:50]}")
        
        # Get selection
        while True:
            selection = input(f"\nEnter number (1-{len(trades_df)}) or 'cancel': ").strip()
            
            if selection.lower() == 'cancel':
                print("Deletion cancelled")
                return
            
            try:
                index = int(selection) - 1
                if 0 <= index < len(trades_df):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(trades_df)}")
            except ValueError:
                print("Invalid input. Enter a number or 'cancel'")
        
        # Get the trade to delete
        trade_to_delete = trades_df.iloc[index]
        trade_id = trade_to_delete['trade_id']
        
        # Confirm deletion
        print(f"\n⚠️  About to delete:")
        print(f"   {trade_to_delete['ticker']} trade from {trade_to_delete['trade_date']}")
        
        confirm = input("\nAre you sure? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            try:
                success = self.storage.delete_trade(trade_id)
                if success:
                    print("✅ Trade deleted successfully")
                    
                    # Update session metrics
                    if 'ticker_id' in trade_to_delete:
                        session = self.storage.get_or_create_session(trade_to_delete['ticker_id'])
                        if session and 'session_id' in session:
                            self.storage.update_session_metrics(session['session_id'])
                else:
                    print("❌ Failed to delete trade")
            except Exception as e:
                print(f"❌ Error deleting trade: {e}")
        else:
            print("Deletion cancelled")

def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description='Trade entry and management system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 06_trades.py                    # Enter new trade
  python 06_trades.py --list            # List all trades
  python 06_trades.py --ticker NVDA     # List NVDA trades
  python 06_trades.py --session AMD.121824  # List session trades
  python 06_trades.py --summary         # Show summary
  python 06_trades.py --delete          # Delete a trade
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all trades')
    parser.add_argument('--ticker', type=str,
                       help='Filter by ticker symbol')
    parser.add_argument('--session', type=str,
                       help='Filter by session ID (e.g., AMD.121824)')
    parser.add_argument('--summary', action='store_true',
                       help='Show trading summary')
    parser.add_argument('--delete', action='store_true',
                       help='Delete a trade (interactive)')
    
    args = parser.parse_args()
    
    # Header
    print("\n" + "="*70)
    print("BACKTEST TRADE MANAGEMENT - 06_trades.py")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize manager
    manager = TradeManager()
    
    # Handle different modes
    if args.summary:
        manager.show_summary()
    elif args.list or args.ticker or args.session:
        manager.list_trades(ticker=args.ticker, session_id=args.session)
    elif args.delete:
        manager.delete_trade_interactive()
    else:
        # Default: Enter new trade
        manager.enter_new_trade()
        
        # After trade entry, ask if they want to see summary
        print("\n" + "="*70)
        show_summary = input("Show trading summary? (y/n): ").strip().lower()
        if show_summary == 'y':
            manager.show_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()