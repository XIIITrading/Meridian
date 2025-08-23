"""
HTML report generator with embedded charts
"""
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from .base_report import BaseReportGenerator

logger = logging.getLogger(__name__)

class HTMLReportGenerator(BaseReportGenerator):
    """Generates HTML reports with embedded charts"""
    
    def get_format_name(self) -> str:
        return "HTML"
    
    def generate(self, data: Dict[str, Any], filename: str) -> str:
        """Generate HTML report"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for report generation")
        
        filepath = self.output_dir / filename
        
        # Generate HTML content
        html_content = self._generate_html(data)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {filepath}")
        return str(filepath)
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate complete HTML document"""
        
        # Extract data
        title = data.get('title', 'Trading Analysis Report')
        generated_at = data.get('generated_at', datetime.now())
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="subtitle">Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        {self._generate_summary_section(data)}
        {self._generate_statistics_section(data)}
        {self._generate_confluence_section(data)}
        {self._generate_patterns_section(data)}
        {self._generate_charts_section(data)}
        {self._generate_recommendations_section(data)}
    </div>
</body>
</html>
"""
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        header {
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 30px;
        }
        .subtitle {
            color: #7f8c8d;
            margin: 5px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .positive {
            color: #27ae60;
        }
        .negative {
            color: #e74c3c;
        }
        .recommendation {
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        """
    
    def _generate_summary_section(self, data: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        summary = data.get('summary', {})
        
        if not summary:
            return ""
        
        html = "<section class='summary'><h2>Executive Summary</h2>"
        html += "<div class='stats-grid'>"
        
        # Key metrics
        metrics = [
            ('Total Trades', summary.get('total_trades', 0)),
            ('Win Rate', f"{summary.get('win_rate', 0):.1f}%"),
            ('Avg R-Multiple', f"{summary.get('avg_r_multiple', 0):.2f}"),
            ('Profit Factor', f"{summary.get('profit_factor', 0):.2f}")
        ]
        
        for label, value in metrics:
            html += f"""
            <div class='stat-card'>
                <div class='stat-value'>{value}</div>
                <div class='stat-label'>{label}</div>
            </div>
            """
        
        html += "</div></section>"
        return html
    
    def _generate_statistics_section(self, data: Dict[str, Any]) -> str:
        """Generate detailed statistics section"""
        if 'basic_stats' not in data:
            return ""
        
        stats = data['basic_stats']
        
        html = "<section class='statistics'><h2>Trading Statistics</h2>"
        html += "<table>"
        html += "<tr><th>Metric</th><th>Value</th></tr>"
        
        # Create rows
        if hasattr(stats, '__dict__'):
            stats_dict = stats.__dict__
        else:
            stats_dict = stats if isinstance(stats, dict) else {}
        
        for key, value in stats_dict.items():
            if key.startswith('_'):
                continue
            display_key = key.replace('_', ' ').title()
            
            # Format value
            if isinstance(value, float):
                display_value = f"{value:.2f}"
                if value > 0 and 'r_multiple' in key:
                    display_value = f"<span class='positive'>{display_value}</span>"
                elif value < 0:
                    display_value = f"<span class='negative'>{display_value}</span>"
            else:
                display_value = str(value)
            
            html += f"<tr><td>{display_key}</td><td>{display_value}</td></tr>"
        
        html += "</table></section>"
        return html
    
    def _generate_confluence_section(self, data: Dict[str, Any]) -> str:
        """Generate confluence analysis section"""
        if 'confluence_analysis' not in data:
            return ""
        
        html = "<section class='confluence'><h2>Performance by Confluence Level</h2>"
        html += "<table>"
        html += "<tr><th>Level</th><th>Trades</th><th>Win Rate</th><th>Avg R</th><th>Profit Factor</th></tr>"
        
        confluence = data['confluence_analysis']
        for level, analysis in sorted(confluence.items()):
            win_rate_class = 'positive' if analysis.win_rate > 50 else 'negative'
            r_class = 'positive' if analysis.avg_r_multiple > 0 else 'negative'
            
            html += f"""
            <tr>
                <td><strong>{level}</strong></td>
                <td>{analysis.trade_count}</td>
                <td class='{win_rate_class}'>{analysis.win_rate}%</td>
                <td class='{r_class}'>{analysis.avg_r_multiple:.2f}</td>
                <td>{analysis.profit_factor:.2f}</td>
            </tr>
            """
        
        html += "</table></section>"
        return html
    
    def _generate_patterns_section(self, data: Dict[str, Any]) -> str:
        """Generate patterns section"""
        if 'pattern_results' not in data or not data['pattern_results']:
            return ""
        
        patterns = data['pattern_results'].get('patterns', [])
        if not patterns:
            return ""
        
        html = "<section class='patterns'><h2>Discovered Patterns</h2>"
        
        for i, pattern in enumerate(patterns[:5], 1):
            html += f"""
            <div class='pattern-card'>
                <h3>{i}. {pattern.definition.name}</h3>
                <p>Confidence: <strong>{pattern.confidence_score:.1f}%</strong></p>
                <p>Win Rate: {pattern.performance.win_rate:.1f}% | 
                   Avg R: {pattern.performance.avg_r_multiple:.2f} | 
                   Matches: {pattern.match.total_matches}</p>
            </div>
            """
        
        html += "</section>"
        return html
    
    def _generate_charts_section(self, data: Dict[str, Any]) -> str:
        """Generate charts section"""
        if 'charts' not in data:
            return ""
        
        html = "<section class='charts'><h2>Visual Analysis</h2>"
        
        for chart_id, chart_html in data['charts'].items():
            html += f"<div class='chart-container'>{chart_html}</div>"
        
        html += "</section>"
        return html
    
    def _generate_recommendations_section(self, data: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        if 'recommendations' not in data:
            return ""
        
        html = "<section class='recommendations'><h2>Recommendations</h2>"
        
        for rec in data['recommendations']:
            html += f"<div class='recommendation'>{rec}</div>"
        
        html += "</section>"
        return html