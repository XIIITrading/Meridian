"""
Overview Widget for Meridian Trading System
Modularized implementation maintaining backward compatibility
"""

# Import the main widget to maintain backward compatibility
from .app_overview import OverviewWidget

# Optionally expose other components if needed elsewhere
from .components import TrendSelector, SectionHeader
from .session_info import SessionInfoFrame
from .analysis_frames import WeeklyAnalysisFrame, DailyAnalysisFrame
from .metrics_frame import MetricsFrame
from .zone_table import M15ZoneTable
from .calculations import CalculationsDisplay

__all__ = [
    'OverviewWidget',
    'TrendSelector',
    'SectionHeader',
    'SessionInfoFrame',
    'WeeklyAnalysisFrame',
    'DailyAnalysisFrame',
    'MetricsFrame',
    'M15ZoneTable',
    'CalculationsDisplay'
]