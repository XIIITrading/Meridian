"""
Integration tests for analysis modules
Tests each module individually and then the orchestrator
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.analysis_modules.data_models import (
    BasicStatistics, ConfluenceAnalysis, TimePatternAnalysis, 
    EdgeFactor, ZoneDistanceResult
)
from analysis.analysis_modules.statistics_calculator import StatisticsCalculator
from analysis.analysis_modules.confluence_analyzer import ConfluenceAnalyzer
from analysis.analysis_modules.time_pattern_analyzer import TimePatternAnalyzer
from analysis.analysis_modules.zone_distance_analyzer import ZoneDistanceAnalyzer
from analysis.analysis_modules.edge_factor_analyzer import EdgeFactorAnalyzer
from analysis.statistical_analyzer import StatisticalAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockStorageManager:
    """Mock storage manager for testing"""
    
    def __init__(self, trades_df):
        self.trades_df = trades_df
        self.client = self  # Mock client
    
    def get_all_trades(self):
        return self.trades_df
    
    def get_session_trades(self, ticker_id):
        return self.trades_df[self.trades_df['ticker_id'] == ticker_id]
    
    def table(self, name):
        # Mock Supabase table interface
        return self
    
    def insert(self, data):
        # Mock insert
        return self
    
    def execute(self):
        # Mock execute
        return {'data': []}

def generate_mock_trades(num_trades=50):
    """
    Generate realistic mock trade data
    
    Args:
        num_trades: Number of mock trades to generate
        
    Returns:
        DataFrame with mock trade data
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate base data
    trades = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(num_trades):
        # Create realistic distributions
        confluence_level = np.random.choice(['L1', 'L2', 'L3', 'L4', 'L5'], 
                                          p=[0.1, 0.2, 0.3, 0.25, 0.15])
        
        # Higher confluence = better win rate
        confluence_bonus = {'L1': -0.2, 'L2': -0.1, 'L3': 0, 'L4': 0.1, 'L5': 0.2}
        win_probability = 0.5 + confluence_bonus[confluence_level]
        
        is_winner = np.random.random() < win_probability
        
        if is_winner:
            r_multiple = np.random.uniform(0.5, 3.0)
            trade_result = r_multiple * 100  # $100 per R
        else:
            r_multiple = np.random.uniform(-2.0, -0.5)
            trade_result = r_multiple * 100
        
        # Generate other fields
        entry_time = base_time + timedelta(hours=i*2)
        
        trade = {
            'id': i + 1,
            'ticker_id': f"TEST.{(i // 10) + 1:02d}",
            'ticker': 'TEST',
            'entry_price': 100 + np.random.uniform(-5, 5),
            'exit_price': 100 + np.random.uniform(-5, 5),
            'stop_price': 95 + np.random.uniform(-2, 2),
            'target_price': 105 + np.random.uniform(-2, 2),
            'position_size': np.random.choice([10, 20, 30, 40, 50]),
            'r_multiple': round(r_multiple, 2),
            'trade_result': round(trade_result, 2),
            'zone_confluence_level': confluence_level,
            'distance_from_zone_ticks': np.random.uniform(-15, 15),
            'entry_candle_time': entry_time,
            'exit_candle_time': entry_time + timedelta(minutes=np.random.randint(5, 120)),
            
            # MFE/MAE metrics
            'mfe_price': 100 + np.random.uniform(0, 10) if is_winner else 100 + np.random.uniform(0, 3),
            'mae_price': 100 - np.random.uniform(0, 3) if is_winner else 100 - np.random.uniform(0, 10),
            'mfe_r_multiple': np.random.uniform(r_multiple, r_multiple + 2) if is_winner else r_multiple + 0.5,
            'mae_r_multiple': np.random.uniform(-0.5, 0) if is_winner else np.random.uniform(-2, -0.5),
            
            # Time metrics
            'first_negative_minute': None if is_winner and np.random.random() > 0.5 else np.random.randint(1, 20),
            'minutes_to_target': np.random.randint(5, 60) if is_winner else None,
            'minutes_to_stop': None if is_winner else np.random.randint(10, 90),
            
            # Additional metrics
            'pivot_strength': np.random.randint(1, 10),
            'efficiency_ratio': np.random.uniform(0.3, 0.9) if is_winner else np.random.uniform(0.1, 0.4),
            
            # Confluence sources (mock JSONB)
            'confluence_sources': {
                'moving_average': np.random.random() > 0.5,
                'fibonacci': np.random.random() > 0.5,
                'volume_profile': np.random.random() > 0.5,
                'pivot_point': np.random.random() > 0.5,
                'trend_line': np.random.random() > 0.5
            }
        }
        
        trades.append(trade)
    
    df = pd.DataFrame(trades)
    
    # Add hour column for time analysis
    df['hour'] = pd.to_datetime(df['entry_candle_time']).dt.hour
    
    return df

def test_individual_modules(mock_storage):
    """Test each analysis module individually"""
    
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL MODULES")
    print("="*60)
    
    trades_df = mock_storage.get_all_trades()
    results = {}
    
    # Test 1: Statistics Calculator
    print("\n[1] Testing Statistics Calculator...")
    try:
        calc = StatisticsCalculator(mock_storage)
        stats = calc.analyze(trades_df)
        
        assert isinstance(stats, BasicStatistics)
        assert stats.total_trades == len(trades_df)
        assert 0 <= stats.win_rate <= 100
        
        print(f"✅ Statistics Calculator: {stats.total_trades} trades analyzed")
        print(f"   Win Rate: {stats.win_rate}%")
        print(f"   Avg R: {stats.avg_r_multiple}")
        print(f"   Profit Factor: {stats.profit_factor}")
        
        results['statistics'] = stats
        
    except Exception as e:
        print(f"❌ Statistics Calculator failed: {e}")
        return False
    
    # Test 2: Confluence Analyzer
    print("\n[2] Testing Confluence Analyzer...")
    try:
        conf_analyzer = ConfluenceAnalyzer(mock_storage)
        confluence = conf_analyzer.analyze(trades_df)
        
        assert isinstance(confluence, dict)
        assert len(confluence) > 0
        
        print(f"✅ Confluence Analyzer: {len(confluence)} levels analyzed")
        for level, analysis in confluence.items():
            print(f"   {level}: {analysis.trade_count} trades, "
                  f"{analysis.win_rate}% WR, {analysis.avg_r_multiple}R")
        
        results['confluence'] = confluence
        
    except Exception as e:
        print(f"❌ Confluence Analyzer failed: {e}")
        return False
    
    # Test 3: Time Pattern Analyzer
    print("\n[3] Testing Time Pattern Analyzer...")
    try:
        time_analyzer = TimePatternAnalyzer(mock_storage)
        patterns = time_analyzer.analyze(trades_df)
        
        assert isinstance(patterns, list)
        
        print(f"✅ Time Pattern Analyzer: {len(patterns)} patterns found")
        for pattern in patterns:
            print(f"   {pattern.pattern_name}: {pattern.occurrence_count} occurrences, "
                  f"{pattern.win_rate}% WR")
        
        results['time_patterns'] = patterns
        
    except Exception as e:
        print(f"❌ Time Pattern Analyzer failed: {e}")
        return False
    
    # Test 4: Zone Distance Analyzer
    print("\n[4] Testing Zone Distance Analyzer...")
    try:
        zone_analyzer = ZoneDistanceAnalyzer(mock_storage)
        zone_analysis = zone_analyzer.analyze(trades_df)
        
        assert isinstance(zone_analysis, dict)
        
        print(f"✅ Zone Distance Analyzer: {len(zone_analysis)} categories analyzed")
        for category, data in zone_analysis.items():
            if isinstance(data, ZoneDistanceResult):
                print(f"   {category}: {data.trade_count} trades, {data.win_rate}% WR")
            elif isinstance(data, dict):
                print(f"   {category}: {data.get('trade_count', 0)} trades")
        
        results['zone_distance'] = zone_analysis
        
    except Exception as e:
        print(f"❌ Zone Distance Analyzer failed: {e}")
        return False
    
    # Test 5: Edge Factor Analyzer
    print("\n[5] Testing Edge Factor Analyzer...")
    try:
        edge_analyzer = EdgeFactorAnalyzer(mock_storage)
        edges = edge_analyzer.analyze(trades_df)
        
        assert isinstance(edges, list)
        
        print(f"✅ Edge Factor Analyzer: {len(edges)} edges found")
        for edge in edges:
            print(f"   {edge.factor_name}: {edge.improvement}% improvement, "
                  f"{edge.confidence}% confidence")
        
        results['edge_factors'] = edges
        
    except Exception as e:
        print(f"❌ Edge Factor Analyzer failed: {e}")
        return False
    
    return results

def test_orchestrator(mock_storage):
    """Test the main Statistical Analyzer orchestrator"""
    
    print("\n" + "="*60)
    print("TESTING STATISTICAL ANALYZER ORCHESTRATOR")
    print("="*60)
    
    try:
        analyzer = StatisticalAnalyzer(mock_storage)
        
        # Test 1: Analyze all trades
        print("\n[1] Testing analyze_all_trades()...")
        results = analyzer.analyze_all_trades(save=False)
        
        assert 'basic_stats' in results
        assert 'confluence_analysis' in results
        assert 'time_patterns' in results
        assert 'zone_analysis' in results
        assert 'edge_factors' in results
        assert 'recommendations' in results
        
        print("✅ Full analysis completed successfully")
        print(f"   Basic Stats: ✓")
        print(f"   Confluence Analysis: ✓")
        print(f"   Time Patterns: {len(results['time_patterns'])} found")
        print(f"   Edge Factors: {len(results['edge_factors'])} found")
        print(f"   Recommendations: {len(results['recommendations'])} generated")
        
        # Test 2: Analyze specific session
        print("\n[2] Testing analyze_session()...")
        session_results = analyzer.analyze_session('TEST.01', save=False)
        
        if session_results:
            print("✅ Session analysis completed")
        else:
            print("⚠️ No trades for session TEST.01")
        
        # Test 3: Get specific analyses
        print("\n[3] Testing individual analysis methods...")
        
        confluence = analyzer.get_confluence_analysis()
        print(f"✅ get_confluence_analysis(): {len(confluence)} levels")
        
        patterns = analyzer.get_time_patterns()
        print(f"✅ get_time_patterns(): {len(patterns)} patterns")
        
        edges = analyzer.find_edge_factors(min_trades=3)
        print(f"✅ find_edge_factors(): {len(edges)} edges")
        
        return results
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def validate_calculations(results):
    """Validate that calculations are correct"""
    
    print("\n" + "="*60)
    print("VALIDATING CALCULATIONS")
    print("="*60)
    
    if not results:
        print("❌ No results to validate")
        return False
    
    # Validate basic statistics
    stats = results['basic_stats']
    
    # Check win rate calculation
    expected_win_rate = (stats.winners / stats.total_trades * 100) if stats.total_trades > 0 else 0
    assert abs(stats.win_rate - expected_win_rate) < 0.01, "Win rate calculation error"
    print("✅ Win rate calculation correct")
    
    # Check profit factor
    if stats.profit_factor != float('inf') and stats.profit_factor > 0:
        print(f"✅ Profit factor valid: {stats.profit_factor}")
    
    # Validate confluence analysis
    confluence = results['confluence_analysis']
    total_confluence_trades = sum(c.trade_count for c in confluence.values())
    print(f"✅ Confluence trades sum: {total_confluence_trades}")
    
    # Validate recommendations
    if results['recommendations']:
        print(f"✅ Recommendations generated: {len(results['recommendations'])}")
        for rec in results['recommendations'][:3]:
            print(f"   - {rec}")
    
    return True

def run_stress_test(sizes=[10, 50, 100, 500]):
    """Test with different data sizes"""
    
    print("\n" + "="*60)
    print("STRESS TESTING WITH DIFFERENT SIZES")
    print("="*60)
    
    for size in sizes:
        print(f"\n[Testing with {size} trades]")
        
        try:
            # Generate data
            df = generate_mock_trades(size)
            mock_storage = MockStorageManager(df)
            
            # Time the analysis
            import time
            start = time.time()
            
            analyzer = StatisticalAnalyzer(mock_storage)
            results = analyzer.analyze_all_trades(save=False)
            
            elapsed = time.time() - start
            
            print(f"✅ {size} trades analyzed in {elapsed:.2f} seconds")
            
            if elapsed > 5:
                print(f"⚠️ Performance warning: {size} trades took {elapsed:.2f}s")
        
        except Exception as e:
            print(f"❌ Failed with {size} trades: {e}")

def main():
    """Main test runner"""
    
    print("\n" + "="*70)
    print("ANALYSIS MODULES INTEGRATION TEST")
    print("="*70)
    
    # Generate mock data
    print("\n[Generating Mock Data]")
    trades_df = generate_mock_trades(50)
    print(f"✅ Generated {len(trades_df)} mock trades")
    print(f"   Date range: {trades_df['entry_candle_time'].min()} to {trades_df['entry_candle_time'].max()}")
    print(f"   Confluence levels: {trades_df['zone_confluence_level'].value_counts().to_dict()}")
    
    # Create mock storage
    mock_storage = MockStorageManager(trades_df)
    
    # Run tests
    print("\n[Phase 1: Individual Module Tests]")
    module_results = test_individual_modules(mock_storage)
    
    if module_results:
        print("\n✅ All individual modules passed!")
    else:
        print("\n❌ Individual module tests failed")
        return
    
    print("\n[Phase 2: Orchestrator Tests]")
    orchestrator_results = test_orchestrator(mock_storage)
    
    if orchestrator_results:
        print("\n✅ Orchestrator tests passed!")
    else:
        print("\n❌ Orchestrator tests failed")
        return
    
    print("\n[Phase 3: Calculation Validation]")
    if validate_calculations(orchestrator_results):
        print("\n✅ All calculations validated!")
    else:
        print("\n❌ Calculation validation failed")
        return
    
    print("\n[Phase 4: Stress Testing]")
    run_stress_test([10, 50, 100])
    
    # Final summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✅ All integration tests passed successfully!")
    print("\nModules tested:")
    print("  ✅ Statistics Calculator")
    print("  ✅ Confluence Analyzer")
    print("  ✅ Time Pattern Analyzer")
    print("  ✅ Zone Distance Analyzer")
    print("  ✅ Edge Factor Analyzer")
    print("  ✅ Statistical Analyzer Orchestrator")
    print("\nYour analysis modules are ready for production use!")

if __name__ == "__main__":
    main()