"""
Report Generator Orchestrator
Creates HTML, PDF, and Excel reports from analysis results
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .report_modules.base_report import BaseReportGenerator
from .report_modules.html_generator import HTMLReportGenerator
from .report_modules.markdown_generator import MarkdownReportGenerator
from .report_modules.excel_generator import ExcelReportGenerator
from .report_modules.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Main orchestrator for report generation
    Coordinates different report formats and outputs
    """
    
    def __init__(self, storage_manager, output_dir: str = "reports/output"):
        """
        Initialize report generator
        
        Args:
            storage_manager: BacktestStorageManager instance
            output_dir: Directory for report output
        """
        self.storage = storage_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize generators
        self.html_gen = HTMLReportGenerator(output_dir)
        self.markdown_gen = MarkdownReportGenerator(output_dir)
        self.excel_gen = ExcelReportGenerator(output_dir)
        self.chart_gen = ChartGenerator()
        
        logger.info(f"Report Generator initialized, output to {output_dir}")
    
    def generate_full_report(self, 
                           analysis_results: Dict[str, Any],
                           pattern_results: Optional[Dict[str, Any]] = None,
                           format_types: List[str] = ['html', 'markdown']) -> Dict[str, str]:
        """
        Generate comprehensive report in multiple formats
        
        Args:
            analysis_results: Results from StatisticalAnalyzer
            pattern_results: Results from PatternRecognizer
            format_types: List of formats to generate
            
        Returns:
            Dictionary of format: filepath
        """
        logger.info(f"Generating full report in formats: {format_types}")
        
        generated_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare report data
        report_data = self._prepare_report_data(analysis_results, pattern_results)
        
        # Generate charts
        charts = self._generate_charts(report_data)
        report_data['charts'] = charts
        
        # Generate each format
        if 'html' in format_types:
            html_file = self.html_gen.generate(
                report_data, 
                f"analysis_report_{timestamp}.html"
            )
            generated_files['html'] = html_file
            logger.info(f"Generated HTML report: {html_file}")
        
        if 'markdown' in format_types:
            md_file = self.markdown_gen.generate(
                report_data,
                f"analysis_report_{timestamp}.md"
            )
            generated_files['markdown'] = md_file
            logger.info(f"Generated Markdown report: {md_file}")
        
        if 'excel' in format_types:
            excel_file = self.excel_gen.generate(
                report_data,
                f"analysis_report_{timestamp}.xlsx"
            )
            generated_files['excel'] = excel_file
            logger.info(f"Generated Excel report: {excel_file}")
        
        return generated_files
    
    def generate_session_report(self, 
                              session_id: str,
                              format_type: str = 'html') -> str:
        """
        Generate report for a specific trading session
        
        Args:
            session_id: Session identifier
            format_type: Output format
            
        Returns:
            Path to generated report
        """
        from .statistical_analyzer import StatisticalAnalyzer
        
        analyzer = StatisticalAnalyzer(self.storage)
        session_results = analyzer.analyze_session(session_id, save=False)
        
        if not session_results:
            logger.warning(f"No results for session {session_id}")
            return None
        
        report_data = self._prepare_report_data(session_results, None)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'html':
            return self.html_gen.generate(
                report_data,
                f"session_report_{session_id}_{timestamp}.html"
            )
        elif format_type == 'markdown':
            return self.markdown_gen.generate(
                report_data,
                f"session_report_{session_id}_{timestamp}.md"
            )
        else:
            logger.error(f"Unsupported format: {format_type}")
            return None
    
    def generate_pattern_report(self,
                              pattern_results: Dict[str, Any],
                              format_type: str = 'html') -> str:
        """
        Generate report focused on patterns
        
        Args:
            pattern_results: Results from PatternRecognizer
            format_type: Output format
            
        Returns:
            Path to generated report
        """
        report_data = {
            'title': 'Pattern Recognition Report',
            'generated_at': datetime.now(),
            'pattern_results': pattern_results,
            'summary': self._create_pattern_summary(pattern_results)
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'html':
            return self.html_gen.generate(
                report_data,
                f"pattern_report_{timestamp}.html"
            )
        else:
            return self.markdown_gen.generate(
                report_data,
                f"pattern_report_{timestamp}.md"
            )
    
    def _prepare_report_data(self, 
                            analysis_results: Dict[str, Any],
                            pattern_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare consolidated report data"""
        
        report_data = {
            'title': 'Trading Analysis Report',
            'generated_at': datetime.now(),
            'analysis_results': analysis_results,
            'pattern_results': pattern_results,
            'summary': self._create_summary(analysis_results, pattern_results)
        }
        
        # Add basic stats if available
        if 'basic_stats' in analysis_results:
            report_data['basic_stats'] = analysis_results['basic_stats']
        
        # Add confluence analysis if available
        if 'confluence_analysis' in analysis_results:
            report_data['confluence_analysis'] = analysis_results['confluence_analysis']
        
        # Add recommendations
        if 'recommendations' in analysis_results:
            report_data['recommendations'] = analysis_results['recommendations']
        
        return report_data
    
    def _generate_charts(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all charts for the report"""
        charts = {}
        
        try:
            # Win rate by confluence chart
            if 'confluence_analysis' in report_data:
                charts['confluence_win_rate'] = self.chart_gen.create_confluence_chart(
                    report_data['confluence_analysis']
                )
            
            # R-multiple distribution
            if 'analysis_results' in report_data:
                trades_df = self.storage.get_all_trades()
                if not trades_df.empty:
                    charts['r_distribution'] = self.chart_gen.create_r_distribution_chart(trades_df)
                    charts['cumulative_pnl'] = self.chart_gen.create_pnl_chart(trades_df)
            
            # Pattern performance chart
            if report_data.get('pattern_results'):
                charts['pattern_performance'] = self.chart_gen.create_pattern_chart(
                    report_data['pattern_results']
                )
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts
    
    def _create_summary(self, 
                       analysis_results: Dict[str, Any],
                       pattern_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create executive summary"""
        
        summary = {
            'total_trades': 0,
            'win_rate': 0,
            'avg_r_multiple': 0,
            'profit_factor': 0,
            'best_pattern': None,
            'key_insights': []
        }
        
        if 'basic_stats' in analysis_results:
            stats = analysis_results['basic_stats']
            # Handle both dataclass and dict formats
            if hasattr(stats, '__dict__'):
                summary.update({
                    'total_trades': stats.total_trades,
                    'win_rate': stats.win_rate,
                    'avg_r_multiple': stats.avg_r_multiple,
                    'profit_factor': stats.profit_factor
                })
            elif isinstance(stats, dict):
                summary.update({
                    'total_trades': stats.get('total_trades', 0),
                    'win_rate': stats.get('win_rate', 0),
                    'avg_r_multiple': stats.get('avg_r_multiple', 0),
                    'profit_factor': stats.get('profit_factor', 0)
                })
        
        if pattern_results and 'patterns' in pattern_results:
            if pattern_results['patterns']:
                best = pattern_results['patterns'][0]
                summary['best_pattern'] = best.definition.name
        
        # Generate key insights
        if summary['win_rate'] > 60:
            summary['key_insights'].append("Strong win rate above 60%")
        
        if summary['avg_r_multiple'] > 1:
            summary['key_insights'].append("Positive expectancy with R > 1")
        
        return summary
    
    def _create_pattern_summary(self, pattern_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create pattern-specific summary"""
        
        if not pattern_results:
            return {}
        
        return {
            'total_patterns': pattern_results.get('total_patterns_discovered', 0),
            'high_confidence': len([
                p for p in pattern_results.get('patterns', [])
                if p.confidence_score >= 80
            ]) if 'patterns' in pattern_results else 0,
            'rules_generated': len(pattern_results.get('rules', []))
        }