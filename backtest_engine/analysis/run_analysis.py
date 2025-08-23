"""
Main analysis runner for backtesting system
Runs statistical analysis, pattern recognition, and generates reports
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .statistical_analyzer import StatisticalAnalyzer
from .pattern_recognizer import PatternRecognizer
from .report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnalysisRunner:
    """
    Main orchestrator for running all analyses and generating reports
    """
    
    def __init__(self, storage_manager):
        """
        Initialize the analysis runner
        
        Args:
            storage_manager: BacktestStorageManager instance
        """
        self.storage = storage_manager
        self.stat_analyzer = StatisticalAnalyzer(storage_manager)
        self.pattern_recognizer = PatternRecognizer(storage_manager)
        self.report_generator = ReportGenerator(storage_manager)
        
        logger.info("Analysis Runner initialized")
    
    def run_full_analysis(self, 
                         save_to_db: bool = True,
                         generate_reports: bool = True,
                         report_formats: List[str] = ['html', 'markdown', 'excel'],
                         min_pattern_confidence: float = 50.0) -> Dict[str, Any]:
        """
        Run complete analysis pipeline
        
        Args:
            save_to_db: Whether to save results to database
            generate_reports: Whether to generate report files
            report_formats: List of report formats to generate
            min_pattern_confidence: Minimum confidence for pattern discovery
            
        Returns:
            Dictionary containing all results and file paths
        """
        results = {
            'timestamp': datetime.now(),
            'success': False,
            'analysis_results': None,
            'pattern_results': None,
            'report_files': None,
            'summary': {}
        }
        
        # Check for available data
        logger.info("Checking available data...")
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            logger.warning("No trades found in database!")
            results['error'] = "No trades available for analysis"
            return results
        
        logger.info(f"Found {len(trades_df)} trades for analysis")
        
        # Data summary
        results['summary']['total_trades'] = len(trades_df)
        results['summary']['tickers'] = trades_df['ticker'].unique().tolist()
        results['summary']['date_range'] = f"{trades_df['trade_date'].min()} to {trades_df['trade_date'].max()}"
        
        # Step 1: Statistical Analysis
        logger.info("Running statistical analysis...")
        try:
            analysis_results = self.stat_analyzer.analyze_all_trades(save=save_to_db)
            results['analysis_results'] = analysis_results
            
            # Extract key metrics
            if analysis_results and 'basic_stats' in analysis_results:
                stats = analysis_results['basic_stats']
                results['summary']['win_rate'] = stats.win_rate
                results['summary']['avg_r_multiple'] = stats.avg_r_multiple
                results['summary']['profit_factor'] = stats.profit_factor
                results['summary']['total_pnl'] = stats.total_r * 100  # Assuming $100 per R
                
                logger.info(f"Statistical analysis complete - Win Rate: {stats.win_rate}%")
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
            results['error'] = str(e)
            return results
        
        # Step 2: Pattern Recognition (if enough data)
        pattern_results = None
        if len(trades_df) >= 5:
            logger.info("Running pattern recognition...")
            try:
                pattern_results = self.pattern_recognizer.discover_patterns(
                    min_confidence=min_pattern_confidence,
                    save=save_to_db
                )
                results['pattern_results'] = pattern_results
                
                if pattern_results:
                    results['summary']['patterns_found'] = pattern_results.get('total_patterns_discovered', 0)
                    logger.info(f"Pattern recognition complete - Found {results['summary']['patterns_found']} patterns")
            except Exception as e:
                logger.error(f"Pattern recognition failed: {e}")
                # Continue even if patterns fail
        else:
            logger.info(f"Skipping pattern recognition (need 5+ trades, have {len(trades_df)})")
            results['summary']['patterns_found'] = 0
        
        # Step 3: Generate Reports
        if generate_reports:
            logger.info(f"Generating reports in formats: {report_formats}")
            try:
                report_files = self.report_generator.generate_full_report(
                    analysis_results,
                    pattern_results,
                    format_types=report_formats
                )
                results['report_files'] = report_files
                results['summary']['reports_generated'] = len(report_files)
                
                logger.info(f"Reports generated successfully: {list(report_files.keys())}")
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                results['report_error'] = str(e)
        
        results['success'] = True
        return results
    
    def run_session_analysis(self, 
                            session_id: str,
                            save_to_db: bool = True,
                            generate_report: bool = True) -> Dict[str, Any]:
        """
        Run analysis for a specific session
        
        Args:
            session_id: Session identifier (e.g., 'AMD.121824')
            save_to_db: Whether to save results to database
            generate_report: Whether to generate report
            
        Returns:
            Dictionary containing session results
        """
        logger.info(f"Running analysis for session: {session_id}")
        
        results = {
            'session_id': session_id,
            'timestamp': datetime.now(),
            'success': False
        }
        
        try:
            # Run session analysis
            session_analysis = self.stat_analyzer.analyze_session(session_id, save=save_to_db)
            results['analysis'] = session_analysis
            
            # Generate session report
            if generate_report and session_analysis:
                report_path = self.report_generator.generate_session_report(
                    session_id,
                    format_type='html'
                )
                results['report_file'] = report_path
            
            results['success'] = True
            logger.info(f"Session analysis complete for {session_id}")
            
        except Exception as e:
            logger.error(f"Session analysis failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a quick summary of current trading performance
        
        Returns:
            Dictionary with key performance metrics
        """
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            return {'error': 'No trades available'}
        
        winners = trades_df[trades_df['r_multiple'] > 0]
        
        summary = {
            'total_trades': len(trades_df),
            'winners': len(winners),
            'losers': len(trades_df) - len(winners),
            'win_rate': round(len(winners) / len(trades_df) * 100, 2),
            'total_pnl': round(trades_df['trade_result'].sum(), 2),
            'avg_r_multiple': round(trades_df['r_multiple'].mean(), 2),
            'best_trade': {
                'ticker': trades_df.loc[trades_df['r_multiple'].idxmax(), 'ticker'] if not trades_df.empty else None,
                'r_multiple': round(trades_df['r_multiple'].max(), 2)
            },
            'worst_trade': {
                'ticker': trades_df.loc[trades_df['r_multiple'].idxmin(), 'ticker'] if not trades_df.empty else None,
                'r_multiple': round(trades_df['r_multiple'].min(), 2)
            },
            'tickers_traded': trades_df['ticker'].unique().tolist(),
            'last_trade_date': trades_df['trade_date'].max()
        }
        
        return summary

def run_analysis(storage_manager, **kwargs):
    """
    Convenience function to run analysis
    
    Args:
        storage_manager: BacktestStorageManager instance
        **kwargs: Arguments to pass to run_full_analysis
        
    Returns:
        Analysis results dictionary
    """
    runner = AnalysisRunner(storage_manager)
    return runner.run_full_analysis(**kwargs)

# For direct execution
if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent))
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    
    # Import storage components
    from data.supabase_client import BacktestSupabaseClient
    from data.backtest_storage_manager import BacktestStorageManager
    
    # Connect to database
    print("\nConnecting to Supabase...")
    client = BacktestSupabaseClient()
    storage = BacktestStorageManager(client)
    
    # Run analysis
    print("Running full analysis...")
    runner = AnalysisRunner(storage)
    results = runner.run_full_analysis()
    
    # Display results
    if results['success']:
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nSummary:")
        for key, value in results['summary'].items():
            print(f"  {key}: {value}")
        
        if results.get('report_files'):
            print(f"\nReports generated:")
            for format_type, filepath in results['report_files'].items():
                print(f"  {format_type}: {filepath}")
    else:
        print(f"\n❌ Analysis failed: {results.get('error', 'Unknown error')}")