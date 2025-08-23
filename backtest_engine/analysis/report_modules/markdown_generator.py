"""
Markdown report generator
"""
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from .base_report import BaseReportGenerator

logger = logging.getLogger(__name__)

class MarkdownReportGenerator(BaseReportGenerator):
    """Generates Markdown reports"""
    
    def get_format_name(self) -> str:
        return "Markdown"
    
    def generate(self, data: Dict[str, Any], filename: str) -> str:
        """Generate Markdown report"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for report generation")
        
        filepath = self.output_dir / filename
        
        # Generate Markdown content
        md_content = self._generate_markdown(data)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Generated Markdown report: {filepath}")
        return str(filepath)
    
    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate complete Markdown document"""
        
        title = data.get('title', 'Trading Analysis Report')
        generated_at = data.get('generated_at', datetime.now())
        
        md = f"""# {title}

*Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}*

---

"""
        
        # Add sections
        md += self._generate_summary_section(data)
        md += self._generate_statistics_section(data)
        md += self._generate_confluence_section(data)
        md += self._generate_patterns_section(data)
        md += self._generate_recommendations_section(data)
        
        return md
    
    def _generate_summary_section(self, data: Dict[str, Any]) -> str:
        """Generate summary section"""
        summary = data.get('summary', {})
        if not summary:
            return ""
        
        md = "## Executive Summary\n\n"
        md += f"- **Total Trades**: {summary.get('total_trades', 0)}\n"
        md += f"- **Win Rate**: {summary.get('win_rate', 0):.1f}%\n"
        md += f"- **Avg R-Multiple**: {summary.get('avg_r_multiple', 0):.2f}\n"
        md += f"- **Profit Factor**: {summary.get('profit_factor', 0):.2f}\n\n"
        
        return md
    
    def _generate_statistics_section(self, data: Dict[str, Any]) -> str:
        """Generate statistics section"""
        if 'basic_stats' not in data:
            return ""
        
        stats = data['basic_stats']
        md = "## Trading Statistics\n\n"
        md += "| Metric | Value |\n"
        md += "|--------|-------|\n"
        
        if hasattr(stats, '__dict__'):
            stats_dict = stats.__dict__
        else:
            stats_dict = stats if isinstance(stats, dict) else {}
        
        for key, value in stats_dict.items():
            if key.startswith('_'):
                continue
            display_key = key.replace('_', ' ').title()
            
            if isinstance(value, float):
                display_value = f"{value:.2f}"
            else:
                display_value = str(value)
            
            md += f"| {display_key} | {display_value} |\n"
        
        md += "\n"
        return md
    
    def _generate_confluence_section(self, data: Dict[str, Any]) -> str:
        """Generate confluence section"""
        if 'confluence_analysis' not in data:
            return ""
        
        md = "## Performance by Confluence Level\n\n"
        md += "| Level | Trades | Win Rate | Avg R | Profit Factor |\n"
        md += "|-------|--------|----------|-------|---------------|\n"
        
        confluence = data['confluence_analysis']
        for level, analysis in sorted(confluence.items()):
            md += f"| **{level}** | {analysis.trade_count} | {analysis.win_rate}% | "
            md += f"{analysis.avg_r_multiple:.2f} | {analysis.profit_factor:.2f} |\n"
        
        md += "\n"
        return md
    
    def _generate_patterns_section(self, data: Dict[str, Any]) -> str:
        """Generate patterns section"""
        if 'pattern_results' not in data or not data['pattern_results']:
            return ""
        
        patterns = data['pattern_results'].get('patterns', [])
        if not patterns:
            return ""
        
        md = "## Discovered Patterns\n\n"
        
        for i, pattern in enumerate(patterns[:5], 1):
            md += f"### {i}. {pattern.definition.name}\n\n"
            md += f"- **Confidence**: {pattern.confidence_score:.1f}%\n"
            md += f"- **Win Rate**: {pattern.performance.win_rate:.1f}%\n"
            md += f"- **Avg R**: {pattern.performance.avg_r_multiple:.2f}\n"
            md += f"- **Matches**: {pattern.match.total_matches}\n\n"
        
        return md
    
    def _generate_recommendations_section(self, data: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        if 'recommendations' not in data:
            return ""
        
        md = "## Recommendations\n\n"
        
        for rec in data['recommendations']:
            md += f"- {rec}\n"
        
        md += "\n"
        return md