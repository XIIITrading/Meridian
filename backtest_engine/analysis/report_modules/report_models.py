"""
Data models for report generation
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class ReportMetadata:
    """Metadata for generated reports"""
    title: str
    generated_at: datetime
    report_type: str  # 'full', 'session', 'pattern'
    data_source: str  # 'mock' or 'real'
    total_trades: int
    date_range: str
    output_format: str  # 'html', 'markdown', 'excel'

@dataclass
class ChartConfig:
    """Configuration for a chart"""
    chart_type: str  # 'bar', 'line', 'pie', 'scatter'
    title: str
    x_label: str
    y_label: str
    data: Dict[str, Any]
    layout_options: Optional[Dict] = None