# test_pattern_with_realistic_data.py
"""
Test Pattern Recognition with schema-compliant mock data
"""
from generate_realistic_mock_data import RealisticMockDataGenerator
from test_analysis_integration import MockStorageManager
from analysis.pattern_recognizer import PatternRecognizer
from analysis.pattern_modules.pattern_models import UserPatternRequest

def test_patterns_with_real_schema():
    # Generate schema-compliant data
    generator = RealisticMockDataGenerator()
    sessions_df, trades_df = generator.generate_complete_dataset(
        tickers=['AMD', 'NVDA', 'SPY'],
        trades_per_session=20,  # More data for patterns
        sessions_per_ticker=5
    )
    
    print(f"Generated {len(trades_df)} trades for pattern discovery")
    
    # Create mock storage
    mock_storage = MockStorageManager(trades_df)
    recognizer = PatternRecognizer(mock_storage)
    
    # Discover patterns
    patterns = recognizer.discover_patterns(min_confidence=50)
    
    if patterns:
        print(f"✅ Discovered {patterns['total_patterns_discovered']} patterns")
        
        # Test a user pattern based on what we see in the data
        user_pattern = UserPatternRequest(
            name="High Confluence Winner",
            hypothesis="L4-L5 zones have 70%+ win rate",
            conditions={
                'zone_confluence_level': ['L4', 'L5'],
                'zone_confluence_score': '>=60'
            },
            success_criteria={'win_rate': 70}
        )
        
        result = recognizer.test_user_pattern(user_pattern)
        if result:
            print(f"User pattern validated: {result.performance.win_rate}% WR")
    
    return patterns

if __name__ == "__main__":
    test_patterns_with_real_schema()