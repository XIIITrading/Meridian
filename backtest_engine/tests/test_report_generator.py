"""
Test Report Generator with mock data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_realistic_mock_data import RealisticMockDataGenerator
from test_analysis_integration import MockStorageManager
from analysis.statistical_analyzer import StatisticalAnalyzer
from analysis.pattern_recognizer import PatternRecognizer
from analysis.report_generator import ReportGenerator

def test_report_generation():
    """Test report generation with mock data"""
    
    print("\n" + "="*70)
    print("TESTING REPORT GENERATOR")
    print("="*70)
    
    # Step 1: Generate mock data
    print("\n[1] Generating mock data...")
    generator = RealisticMockDataGenerator()
    sessions_df, trades_df = generator.generate_complete_dataset(
        tickers=['AMD', 'NVDA', 'SPY'],
        trades_per_session=20,
        sessions_per_ticker=3
    )
    print(f"✅ Generated {len(trades_df)} trades")
    
    # Step 2: Run analysis
    print("\n[2] Running analysis...")
    mock_storage = MockStorageManager(trades_df)
    
    # Statistical analysis
    stat_analyzer = StatisticalAnalyzer(mock_storage)
    analysis_results = stat_analyzer.analyze_all_trades(save=False)
    print(f"✅ Statistical analysis complete")
    
    # Pattern recognition
    pattern_recognizer = PatternRecognizer(mock_storage)
    pattern_results = pattern_recognizer.discover_patterns(min_confidence=40, save=False)
    print(f"✅ Pattern recognition complete: {pattern_results['total_patterns_discovered']} patterns found")
    
    # Step 3: Generate reports
    print("\n[3] Generating reports...")
    report_gen = ReportGenerator(mock_storage)
    
    # Generate all formats
    files = report_gen.generate_full_report(
        analysis_results,
        pattern_results,
        format_types=['html', 'markdown', 'excel']
    )
    
    print("\n✅ Reports Generated Successfully!")
    print("\n[Generated Files]")
    for format_type, filepath in files.items():
        print(f"  {format_type.upper()}: {filepath}")
        
        # Check file exists and has content
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"    Size: {size:,} bytes")
    
    # Step 4: Test session-specific report
    print("\n[4] Testing session report...")
    first_session = sessions_df.iloc[0]['ticker_id']
    session_report = report_gen.generate_session_report(
        first_session,
        format_type='html'
    )
    print(f"✅ Session report: {session_report}")
    
    # Step 5: Test pattern-specific report
    print("\n[5] Testing pattern report...")
    pattern_report = report_gen.generate_pattern_report(
        pattern_results,
        format_type='markdown'
    )
    print(f"✅ Pattern report: {pattern_report}")
    
    return files

def view_sample_report(filepath):
    """Open the generated report"""
    import webbrowser
    if filepath.endswith('.html'):
        webbrowser.open(f'file://{os.path.abspath(filepath)}')
        print(f"\n📊 Opening report in browser: {filepath}")

if __name__ == "__main__":
    files = test_report_generation()
    
    print("\n" + "="*70)
    print("REPORT GENERATOR TEST COMPLETE")
    print("="*70)
    print("\n✅ All report types generated successfully!")
    print("\nYou can find the reports in: reports/output/")
    print("\nTo view the HTML report in your browser, uncomment the line below:")

if __name__ == "__main__":
    files = test_report_generation()
    
    print("\n" + "="*70)
    print("REPORT GENERATOR TEST COMPLETE")
    print("="*70)
    print("\n✅ All report types generated successfully!")
    print("\nYou can find the reports in: reports/output/")
    
    # Automatically open the HTML report
    import webbrowser
    import os
    
    html_file = files['html']
    full_path = os.path.abspath(html_file)
    print(f"\n📊 Opening HTML report in browser...")
    print(f"   File: {full_path}")
    webbrowser.open(f'file:///{full_path}')