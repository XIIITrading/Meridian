"""
Excel report generator
"""
import pandas as pd
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import logging

from .base_report import BaseReportGenerator

logger = logging.getLogger(__name__)

class ExcelReportGenerator(BaseReportGenerator):
    """Generates Excel reports with multiple sheets"""
    
    def get_format_name(self) -> str:
        return "Excel"
    
    def generate(self, data: Dict[str, Any], filename: str) -> str:
        """Generate Excel report"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for report generation")
        
        filepath = self.output_dir / filename
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            self._write_summary_sheet(writer, data)
            
            # Statistics sheet
            self._write_statistics_sheet(writer, data)
            
            # Confluence analysis sheet
            self._write_confluence_sheet(writer, data)
            
            # Patterns sheet
            self._write_patterns_sheet(writer, data)
            
            # Recommendations sheet
            self._write_recommendations_sheet(writer, data)
        
        logger.info(f"Generated Excel report: {filepath}")
        return str(filepath)
    
    def _write_summary_sheet(self, writer, data: Dict[str, Any]):
        """Write summary sheet"""
        summary = data.get('summary', {})
        
        summary_data = {
            'Metric': ['Total Trades', 'Win Rate', 'Avg R-Multiple', 
                      'Profit Factor', 'Best Pattern'],
            'Value': [
                summary.get('total_trades', 0),
                f"{summary.get('win_rate', 0):.1f}%",
                f"{summary.get('avg_r_multiple', 0):.2f}",
                f"{summary.get('profit_factor', 0):.2f}",
                summary.get('best_pattern', 'N/A')
            ]
        }
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _write_statistics_sheet(self, writer, data: Dict[str, Any]):
        """Write detailed statistics sheet"""
        if 'basic_stats' not in data:
            return
        
        stats = data['basic_stats']
        
        # Convert to dictionary
        if hasattr(stats, '__dict__'):
            stats_dict = stats.__dict__
        else:
            stats_dict = stats if isinstance(stats, dict) else {}
        
        # Create DataFrame
        stats_data = {
            'Metric': [],
            'Value': []
        }
        
        for key, value in stats_dict.items():
            if not key.startswith('_'):
                stats_data['Metric'].append(key.replace('_', ' ').title())
                stats_data['Value'].append(value)
        
        df = pd.DataFrame(stats_data)
        df.to_excel(writer, sheet_name='Statistics', index=False)
    
    def _write_confluence_sheet(self, writer, data: Dict[str, Any]):
        """Write confluence analysis sheet"""
        if 'confluence_analysis' not in data:
            return
        
        confluence = data['confluence_analysis']
        
        conf_data = {
            'Level': [],
            'Trades': [],
            'Win Rate': [],
            'Avg R': [],
            'Profit Factor': []
        }
        
        for level, analysis in sorted(confluence.items()):
            conf_data['Level'].append(level)
            conf_data['Trades'].append(analysis.trade_count)
            conf_data['Win Rate'].append(f"{analysis.win_rate}%")
            conf_data['Avg R'].append(analysis.avg_r_multiple)
            conf_data['Profit Factor'].append(analysis.profit_factor)
        
        df = pd.DataFrame(conf_data)
        df.to_excel(writer, sheet_name='Confluence', index=False)
    
    def _write_patterns_sheet(self, writer, data: Dict[str, Any]):
        """Write patterns sheet"""
        if 'pattern_results' not in data or not data['pattern_results']:
            return
        
        patterns = data['pattern_results'].get('patterns', [])
        if not patterns:
            return
        
        pattern_data = {
            'Pattern Name': [],
            'Type': [],
            'Confidence': [],
            'Win Rate': [],
            'Avg R': [],
            'Matches': []
        }
        
        for pattern in patterns[:20]:  # Top 20 patterns
            pattern_data['Pattern Name'].append(pattern.definition.name)
            pattern_data['Type'].append(pattern.definition.pattern_type.value)
            pattern_data['Confidence'].append(f"{pattern.confidence_score:.1f}%")
            pattern_data['Win Rate'].append(f"{pattern.performance.win_rate:.1f}%")
            pattern_data['Avg R'].append(pattern.performance.avg_r_multiple)
            pattern_data['Matches'].append(pattern.match.total_matches)
        
        df = pd.DataFrame(pattern_data)
        df.to_excel(writer, sheet_name='Patterns', index=False)
    
    def _write_recommendations_sheet(self, writer, data: Dict[str, Any]):
        """Write recommendations sheet"""
        if 'recommendations' not in data:
            return
        
        rec_data = {
            'Recommendation': data['recommendations']
        }
        
        df = pd.DataFrame(rec_data)
        df.to_excel(writer, sheet_name='Recommendations', index=False)