"""
Overview Widget for Meridian Trading System
Modularized implementation maintaining backward compatibility
UPDATED: Added PivotConfluenceWidget, removed M15ZoneTable
"""

# Import the main widget to maintain backward compatibility
from .app_overview import OverviewWidget

# Import components
from .components import TrendSelector, SectionHeader
from .session_info import SessionInfoFrame
from .analysis_frames import WeeklyAnalysisFrame, DailyAnalysisFrame
from .metrics_frame import MetricsFrame
from .pivot_confluence_widget import PivotConfluenceWidget  # NEW
from .calculations import CalculationsDisplay

__all__ = [
    'OverviewWidget',
    'TrendSelector',
    'SectionHeader',
    'SessionInfoFrame',
    'WeeklyAnalysisFrame',
    'DailyAnalysisFrame',
    'MetricsFrame',
    'PivotConfluenceWidget',
    'CalculationsDisplay'
]