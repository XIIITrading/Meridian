"""
Statistical Analyzer Orchestrator
Main entry point for all statistical analysis operations
Coordinates all analysis modules and aggregates results
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .analysis_modules.base_analyzer import BaseAnalyzer
from .analysis_modules.statistics_calculator import StatisticsCalculator
from .analysis_modules.confluence_analyzer import ConfluenceAnalyzer
from .analysis_modules.time_pattern_analyzer import TimePatternAnalyzer
from .analysis_modules.zone_distance_analyzer import ZoneDistanceAnalyzer
from .analysis_modules.edge_factor_analyzer import EdgeFactorAnalyzer
from .analysis_modules.analysis_persistence import AnalysisPersistence
from .analysis_modules.analysis_utils import generate_recommendations, format_analysis_summary

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """
    Main orchestrator for statistical analysis
    Coordinates all analysis modules and provides unified interface
    """
    
    def __init__(self, storage_manager):
        """
        Initialize the orchestrator with all analysis modules
        
        Args:
            storage_manager: BacktestStorageManager instance
        """
        self.storage = storage_manager
        
        # Initialize all analysis modules
        self.statistics = StatisticsCalculator(storage_manager)
        self.confluence = ConfluenceAnalyzer(storage_manager)
        self.time_patterns = TimePatternAnalyzer(storage_manager)
        self.zone_distance = ZoneDistanceAnalyzer(storage_manager)
        self.edge_factors = EdgeFactorAnalyzer(storage_manager)
        
        # Initialize persistence
        self.persistence = AnalysisPersistence(storage_manager)
        
        # List of all analyzers for easy iteration
        self.analyzers = [
            self.statistics,
            self.confluence,
            self.time_patterns,
            self.zone_distance,
            self.edge_factors
        ]
        
        logger.info(f"Statistical Analyzer initialized with {len(self.analyzers)} modules")
    
    def analyze_session(self, ticker_id: str, save: bool = True) -> Dict[str, Any]:
        """
        Run complete analysis on a single trading session
        
        Args:
            ticker_id: Session identifier (e.g., 'AMD.121824')
            save: Whether to save results to database
            
        Returns:
            Dictionary containing all analysis results
        """
        logger.info(f"Starting session analysis for {ticker_id}")
        
        # Get trades for this session
        trades_df = self.storage.get_session_trades(ticker_id)
        
        if trades_df.empty:
            logger.warning(f"No trades found for session {ticker_id}")
            return {}
        
        # Run analysis through all modules
        results = self._run_all_analyses(trades_df)
        
        # Add metadata
        results['ticker_id'] = ticker_id
        results['analysis_date'] = datetime.now().isoformat()
        results['analysis_type'] = 'session'
        
        # Generate recommendations
        results['recommendations'] = generate_recommendations(
            results.get('basic_stats'),
            results.get('confluence_analysis'),
            results.get('time_patterns'),
            results.get('edge_factors')
        )
        
        # Save if requested
        if save:
            self.persistence.save_results('session', results, ticker_id)
            logger.info(f"Session analysis saved for {ticker_id}")
        
        return results
    
    def analyze_all_trades(self, save: bool = True) -> Dict[str, Any]:
        """
        Run complete analysis on all trades in database
        
        Args:
            save: Whether to save results to database
            
        Returns:
            Dictionary containing all analysis results
        """
        logger.info("Starting analysis of all trades")
        
        # Get all trades
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            logger.warning("No trades found in database")
            return {}
        
        # Run analysis through all modules
        results = self._run_all_analyses(trades_df)
        
        # Add metadata
        results['analysis_date'] = datetime.now().isoformat()
        results['analysis_type'] = 'full'
        results['total_sessions'] = len(trades_df['ticker_id'].unique()) if 'ticker_id' in trades_df else 0
        
        # Generate recommendations
        results['recommendations'] = generate_recommendations(
            results.get('basic_stats'),
            results.get('confluence_analysis'),
            results.get('time_patterns'),
            results.get('edge_factors')
        )
        
        # Save if requested
        if save:
            self.persistence.save_results('full', results)
            logger.info("Full analysis saved to database")
        
        return results
    
    def _run_all_analyses(self, trades_df) -> Dict[str, Any]:
        """
        Run trades through all analysis modules
        
        Args:
            trades_df: DataFrame of trades to analyze
            
        Returns:
            Aggregated results from all modules
        """
        results = {}
        
        # Run each analyzer
        logger.debug("Running basic statistics...")
        results['basic_stats'] = self.statistics.analyze(trades_df)
        
        logger.debug("Running confluence analysis...")
        results['confluence_analysis'] = self.confluence.analyze(trades_df)
        
        logger.debug("Running time pattern analysis...")
        results['time_patterns'] = self.time_patterns.analyze(trades_df)
        
        logger.debug("Running zone distance analysis...")
        results['zone_analysis'] = self.zone_distance.analyze(trades_df)
        
        logger.debug("Running edge factor analysis...")
        results['edge_factors'] = self.edge_factors.analyze(trades_df)
        
        return results
    
    def find_edge_factors(self, min_trades: int = 5, save: bool = False) -> List:
        """
        Quick method to find edge factors only
        
        Args:
            min_trades: Minimum trades for significance
            save: Whether to save results
            
        Returns:
            List of edge factors
        """
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            return []
        
        edges = self.edge_factors.analyze(trades_df)
        
        if save and edges:
            results = {'edge_factors': edges}
            self.persistence.save_results('edge_factors', results)
        
        return edges
    
    def get_confluence_analysis(self) -> Dict:
        """Quick method to get confluence analysis only"""
        trades_df = self.storage.get_all_trades()
        return self.confluence.analyze(trades_df) if not trades_df.empty else {}
    
    def get_time_patterns(self) -> List:
        """Quick method to get time patterns only"""
        trades_df = self.storage.get_all_trades()
        return self.time_patterns.analyze(trades_df) if not trades_df.empty else []
    
    def load_latest_analysis(self, analysis_type: str = None, 
                           ticker_id: str = None) -> Optional[dict]:
        """
        Load the most recent analysis from database
        
        Args:
            analysis_type: Filter by type ('session', 'full', 'edge_factors')
            ticker_id: Filter by ticker/session
            
        Returns:
            Saved analysis results or None
        """
        return self.persistence.load_latest(analysis_type, ticker_id)
    
    def print_summary(self, results: Dict[str, Any]):
        """
        Print a formatted summary of analysis results
        
        Args:
            results: Analysis results dictionary
        """
        summary = format_analysis_summary(results)
        print(summary)

# Example usage
if __name__ == "__main__":
    from data.supabase_client import BacktestSupabaseClient
    from data.backtest_storage_manager import BacktestStorageManager
    
    # Initialize
    client = BacktestSupabaseClient()
    storage = BacktestStorageManager(client)
    analyzer = StatisticalAnalyzer(storage)
    
    # Run full analysis
    print("\n" + "="*60)
    print("RUNNING COMPLETE ANALYSIS")
    print("="*60)
    
    results = analyzer.analyze_all_trades(save=True)
    
    if results:
        # Print summary
        analyzer.print_summary(results)
        
        # Show edge factors
        if 'edge_factors' in results:
            print("\n" + "="*60)
            print("IDENTIFIED EDGE FACTORS")
            print("="*60)
            for edge in results['edge_factors']:
                print(f"\n{edge.factor_name}")
                print(f"  Win Rate: {edge.baseline_winrate}% → {edge.edge_winrate}%")
                print(f"  Improvement: +{edge.improvement}%")
                print(f"  Confidence: {edge.confidence}%")
                print(f"  💡 {edge.actionable_insight}")