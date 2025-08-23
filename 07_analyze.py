#!/usr/bin/env python
r"""
07_analyze.py - Main analysis runner for backtesting system
Runs statistical analysis, pattern recognition, and generates reports from Supabase data

Location: C:\XIIITradingSystems\Meridian\07_analyze.py

Usage:
    python 07_analyze.py                    # Run full analysis with reports
    python 07_analyze.py --open            # Run and open HTML report
    python 07_analyze.py --summary         # Quick summary only
    python 07_analyze.py --no-reports      # Analysis only, no reports
    python 07_analyze.py --formats html    # Generate specific report format
"""

import sys
import os
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

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
from analysis.statistical_analyzer import StatisticalAnalyzer
from analysis.pattern_recognizer import PatternRecognizer
from analysis.report_generator import ReportGenerator

class BacktestAnalyzer:
    """Main orchestrator for backtest analysis"""
    
    def __init__(self):
        """Initialize connection and analyzers"""
        self.connect_to_database()
        self.setup_analyzers()
    
    def connect_to_database(self):
        """Connect to Supabase database"""
        print("\n[1] Connecting to Supabase...")
        try:
            self.client = BacktestSupabaseClient()
            self.storage = BacktestStorageManager(self.client)
            print("✅ Connected successfully")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)
    
    def setup_analyzers(self):
        """Initialize all analysis components"""
        self.stat_analyzer = StatisticalAnalyzer(self.storage)
        self.pattern_recognizer = PatternRecognizer(self.storage)
        self.report_generator = ReportGenerator(self.storage)
    
    def check_data_availability(self):
        """Check what data is available in database"""
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            print("\n❌ No trades found in database!")
            print("\nTo add trades:")
            print("1. cd backtest_engine")
            print("2. python scripts/cli_trade_entry.py")
            return None
        
        # Get unique sessions from trades
        num_sessions = trades_df['ticker_id'].nunique() if 'ticker_id' in trades_df.columns else 0
        unique_tickers = trades_df['ticker'].unique().tolist() if 'ticker' in trades_df.columns else []
        
        print(f"\n[2] Data Available:")
        print(f"   Trades: {len(trades_df)}")
        print(f"   Sessions: {num_sessions}")
        print(f"   Tickers: {unique_tickers}")
        
        # Handle date display based on available columns
        if 'trade_date' in trades_df.columns:
            print(f"   Date range: {trades_df['trade_date'].min()} to {trades_df['trade_date'].max()}")
        elif 'entry_candle_time' in trades_df.columns:
            # Convert to date for display
            trades_df['entry_date'] = pd.to_datetime(trades_df['entry_candle_time']).dt.date
            print(f"   Date range: {trades_df['entry_date'].min()} to {trades_df['entry_date'].max()}")
        
        # Quick stats
        winners = trades_df[trades_df['r_multiple'] > 0]
        total_pnl = trades_df['trade_result'].sum() if 'trade_result' in trades_df.columns else 0
        
        print(f"\n   Quick Stats:")
        print(f"   • Total P&L: ${total_pnl:.2f}")
        print(f"   • Win Rate: {len(winners)/len(trades_df)*100:.1f}%")
        print(f"   • Avg R: {trades_df['r_multiple'].mean():.2f}")
        
        # Show performance by ticker
        if unique_tickers:
            print(f"\n   By Ticker:")
            for ticker in unique_tickers:
                ticker_trades = trades_df[trades_df['ticker'] == ticker]
                ticker_winners = ticker_trades[ticker_trades['r_multiple'] > 0]
                ticker_wr = len(ticker_winners)/len(ticker_trades)*100 if len(ticker_trades) > 0 else 0
                ticker_avg_r = ticker_trades['r_multiple'].mean()
                print(f"   • {ticker}: {len(ticker_trades)} trades, {ticker_wr:.1f}% WR, {ticker_avg_r:.2f}R")
        
        return trades_df
    
    def run_statistical_analysis(self, save_to_db=True):
        """Run statistical analysis"""
        print("\n[3] Running Statistical Analysis...")
        
        try:
            results = self.stat_analyzer.analyze_all_trades(save=save_to_db)
            
            if results and 'basic_stats' in results:
                stats = results['basic_stats']
                print(f"✅ Analysis complete:")
                print(f"   • Win Rate: {stats.win_rate}%")
                print(f"   • Profit Factor: {stats.profit_factor}")
                print(f"   • Total R: {stats.total_r}")
                print(f"   • Avg R: {stats.avg_r_multiple}")
                
                # Show confluence performance
                if 'confluence_analysis' in results:
                    print(f"\n   Confluence Performance:")
                    for level, data in results['confluence_analysis'].items():
                        print(f"   • {level}: {data.trade_count} trades, "
                              f"{data.win_rate}% WR, {data.avg_r_multiple}R")
                
                # Show edge factors
                if 'edge_factors' in results and results['edge_factors']:
                    print(f"\n   Edge Factors Found:")
                    for edge in results['edge_factors'][:3]:
                        print(f"   • {edge.factor_name}: +{edge.improvement}% improvement")
            
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_pattern_recognition(self, trades_df, save_to_db=True):
        """Run pattern recognition if enough data"""
        if len(trades_df) < 5:
            print(f"\n[4] Pattern Recognition:")
            print(f"   ⚠️ Need at least 5 trades (have {len(trades_df)})")
            return None
        
        print("\n[4] Running Pattern Recognition...")
        
        try:
            results = self.pattern_recognizer.discover_patterns(
                min_confidence=30,
                save=save_to_db
            )
            
            if results:
                print(f"✅ Found {results['total_patterns_discovered']} patterns")
                
                if results.get('patterns'):
                    print(f"\n   Top Patterns:")
                    for i, pattern in enumerate(results['patterns'][:3], 1):
                        print(f"   {i}. {pattern.definition.name}")
                        print(f"      • Confidence: {pattern.confidence_score:.1f}%")
                        print(f"      • Win Rate: {pattern.performance.win_rate:.1f}%")
                        print(f"      • Matches: {pattern.match.total_matches}")
            
            return results
            
        except Exception as e:
            print(f"❌ Pattern recognition failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_reports(self, analysis_results, pattern_results, formats):
        """Generate reports in specified formats"""
        print(f"\n[5] Generating Reports ({', '.join(formats)})...")
        
        try:
            files = self.report_generator.generate_full_report(
                analysis_results,
                pattern_results,
                format_types=formats
            )
            
            print("✅ Reports generated:")
            for format_type, filepath in files.items():
                size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                print(f"   • {format_type.upper()}: {filepath}")
                print(f"     Size: {size:,} bytes")
            
            return files
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def show_summary(self):
        """Show quick summary without full analysis"""
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            print("\n❌ No trades to summarize")
            return
        
        winners = trades_df[trades_df['r_multiple'] > 0]
        total_pnl = trades_df['trade_result'].sum() if 'trade_result' in trades_df.columns else 0
        
        print("\n" + "="*60)
        print("TRADING SUMMARY")
        print("="*60)
        print(f"Total Trades: {len(trades_df)}")
        print(f"Winners: {len(winners)}")
        print(f"Losers: {len(trades_df) - len(winners)}")
        print(f"Win Rate: {len(winners)/len(trades_df)*100:.1f}%")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"Avg R-Multiple: {trades_df['r_multiple'].mean():.2f}")
        
        # Best and worst trades
        if not trades_df.empty:
            best_idx = trades_df['r_multiple'].idxmax()
            worst_idx = trades_df['r_multiple'].idxmin()
            print(f"Best Trade: {trades_df.loc[best_idx, 'ticker']} "
                  f"({trades_df.loc[best_idx, 'r_multiple']:.2f}R)")
            print(f"Worst Trade: {trades_df.loc[worst_idx, 'ticker']} "
                  f"({trades_df.loc[worst_idx, 'r_multiple']:.2f}R)")
        
        # Unique tickers
        if 'ticker' in trades_df.columns:
            print(f"Tickers: {', '.join(trades_df['ticker'].unique())}")
    
    def run_full_analysis(self, save_to_db=True, generate_reports=True, 
                         report_formats=['html', 'markdown', 'excel'], 
                         open_browser=False):
        """Run complete analysis pipeline"""
        
        # Check data
        trades_df = self.check_data_availability()
        if trades_df is None:
            return None
        
        # Statistical analysis
        analysis_results = self.run_statistical_analysis(save_to_db)
        if not analysis_results:
            return None
        
        # Pattern recognition
        pattern_results = self.run_pattern_recognition(trades_df, save_to_db)
        
        # Generate reports
        report_files = None
        if generate_reports:
            report_files = self.generate_reports(
                analysis_results, 
                pattern_results, 
                report_formats
            )
            
            # Open browser if requested
            if open_browser and report_files and 'html' in report_files:
                html_path = Path(report_files['html']).absolute()
                print(f"\n🌐 Opening report in browser...")
                webbrowser.open(f'file:///{html_path}')
        
        return {
            'analysis': analysis_results,
            'patterns': pattern_results,
            'reports': report_files
        }

def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description='Run backtest analysis and generate reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 07_analyze.py                    # Run full analysis
  python 07_analyze.py --open            # Run and open HTML report
  python 07_analyze.py --summary         # Quick summary only
  python 07_analyze.py --no-reports      # Skip report generation
  python 07_analyze.py --formats html    # HTML report only
        """
    )
    
    parser.add_argument('--no-save', action='store_true',
                       help='Skip saving results to database')
    parser.add_argument('--no-reports', action='store_true',
                       help='Skip report generation')
    parser.add_argument('--formats', nargs='+',
                       default=['html', 'markdown', 'excel'],
                       choices=['html', 'markdown', 'excel'],
                       help='Report formats to generate (default: all)')
    parser.add_argument('--open', action='store_true',
                       help='Open HTML report in browser after generation')
    parser.add_argument('--open', action='store_true', default=True,
                   help='Open HTML report in browser after generation (default: True)')
    
    args = parser.parse_args()
    
    # Import pandas here after path is set up
    global pd
    import pandas as pd
    
    # Header
    print("\n" + "="*70)
    print("BACKTEST ANALYSIS SYSTEM - 07_analyze.py")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize analyzer
    analyzer = BacktestAnalyzer()
    
    # Summary mode
    if args.summary:
        analyzer.show_summary()
        return
    
    # Full analysis
    print("\n" + "="*60)
    print("STARTING FULL ANALYSIS")
    print("="*60)
    
    results = analyzer.run_full_analysis(
        save_to_db=not args.no_save,
        generate_reports=not args.no_reports,
        report_formats=args.formats,
        open_browser=args.open
    )
    
    # Final summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    
    if results:
        if results.get('reports'):
            print("\n📊 Reports available in: backtest_engine/reports/output/")
            print("\n💡 To view reports:")
            print("   • HTML: Open in any browser for interactive charts")
            print("   • Markdown: View in VS Code or any text editor")
            print("   • Excel: Open in Excel for data analysis")
        
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n⚠️ Analysis completed with warnings. Check messages above.")

if __name__ == "__main__":
    main()