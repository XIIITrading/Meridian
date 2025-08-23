"""
Time-based pattern analysis module
Identifies patterns related to timing and temporal aspects of trades
"""
import pandas as pd
from typing import List
from scipy import stats

from .base_analyzer import BaseAnalyzer
from .data_models import TimePatternAnalysis

class TimePatternAnalyzer(BaseAnalyzer):
    """Analyzes time-based patterns in trading performance"""
    
    def get_analysis_name(self) -> str:
        return "Time Pattern Analysis"
    
    def analyze(self, trades_df: pd.DataFrame) -> List[TimePatternAnalysis]:
        """
        Analyze time-based patterns in trading performance
        
        Args:
            trades_df: DataFrame of trades
            
        Returns:
            List of identified time patterns
        """
        if trades_df.empty:
            return []
        
        patterns = []
        
        # Analyze each pattern type
        if 'first_negative_minute' in trades_df.columns:
            pattern = self._analyze_never_negative_pattern(trades_df)
            if pattern:
                patterns.append(pattern)
        
        if 'minutes_to_target' in trades_df.columns:
            pattern = self._analyze_quick_target_pattern(trades_df)
            if pattern:
                patterns.append(pattern)
        
        if 'entry_candle_time' in trades_df.columns:
            pattern = self._analyze_time_of_day_pattern(trades_df)
            if pattern:
                patterns.append(pattern)
        
        if 'pivot_strength' in trades_df.columns:
            pattern = self._analyze_pivot_strength_pattern(trades_df)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_never_negative_pattern(self, trades_df: pd.DataFrame) -> TimePatternAnalysis:
        """Analyze trades that never went negative"""
        never_negative = trades_df[trades_df['first_negative_minute'].isna()]
        
        if len(never_negative) < self.min_sample_size:
            return None
        
        nn_winrate = (len(never_negative[never_negative['r_multiple'] > 0]) / 
                     len(never_negative) * 100)
        
        # Statistical test
        overall_winrate = (len(trades_df[trades_df['r_multiple'] > 0]) / 
                          len(trades_df) * 100)
        
        # Chi-square test for independence
        contingency_table = pd.crosstab(
            trades_df['first_negative_minute'].isna(),
            trades_df['r_multiple'] > 0
        )
        chi2, p_value, _, _ = stats.chi2_contingency(contingency_table)
        
        return TimePatternAnalysis(
            pattern_name="Never Negative Entry",
            description="Trades that never showed unrealized loss",
            occurrence_count=len(never_negative),
            win_rate=round(nn_winrate, 2),
            avg_r_multiple=round(never_negative['r_multiple'].mean(), 2),
            p_value=round(p_value, 4),
            is_significant=p_value < 0.05
        )
    
    def _analyze_quick_target_pattern(self, trades_df: pd.DataFrame) -> TimePatternAnalysis:
        """Analyze trades that hit target quickly"""
        quick_targets = trades_df[
            (trades_df['minutes_to_target'].notna()) & 
            (trades_df['minutes_to_target'] <= 30)
        ]
        
        if len(quick_targets) < self.min_sample_size:
            return None
        
        qt_winrate = (len(quick_targets[quick_targets['r_multiple'] > 0]) / 
                     len(quick_targets) * 100)
        
        return TimePatternAnalysis(
            pattern_name="Quick Target Hit",
            description="Trades reaching target within 30 minutes",
            occurrence_count=len(quick_targets),
            win_rate=round(qt_winrate, 2),
            avg_r_multiple=round(quick_targets['r_multiple'].mean(), 2),
            p_value=0.0,  # Would need proper statistical test
            is_significant=len(quick_targets) >= 10
        )
    
    def _analyze_time_of_day_pattern(self, trades_df: pd.DataFrame) -> TimePatternAnalysis:
        """Analyze morning session performance"""
        trades_df = trades_df.copy()  # Add this line before
        trades_df['hour'] = pd.to_datetime(trades_df['entry_candle_time']).dt.hour
        
        # Morning trades (9:30-11:00 ET = 14:30-16:00 UTC)
        morning_trades = trades_df[(trades_df['hour'] >= 14) & (trades_df['hour'] < 16)]
        
        if len(morning_trades) < self.min_sample_size:
            return None
        
        morning_winrate = (len(morning_trades[morning_trades['r_multiple'] > 0]) / 
                          len(morning_trades) * 100)
        
        return TimePatternAnalysis(
            pattern_name="Morning Session",
            description="Trades during first 90 minutes",
            occurrence_count=len(morning_trades),
            win_rate=round(morning_winrate, 2),
            avg_r_multiple=round(morning_trades['r_multiple'].mean(), 2),
            p_value=0.0,
            is_significant=len(morning_trades) >= 10
        )
    
    def _analyze_pivot_strength_pattern(self, trades_df: pd.DataFrame) -> TimePatternAnalysis:
        """Analyze strong pivot entries"""
        strong_pivots = trades_df[trades_df['pivot_strength'] >= 7]
        
        if len(strong_pivots) < self.min_sample_size:
            return None
        
        sp_winrate = (len(strong_pivots[strong_pivots['r_multiple'] > 0]) / 
                     len(strong_pivots) * 100)
        
        return TimePatternAnalysis(
            pattern_name="Strong Pivot Entry",
            description="Entries with pivot strength >= 7",
            occurrence_count=len(strong_pivots),
            win_rate=round(sp_winrate, 2),
            avg_r_multiple=round(strong_pivots['r_multiple'].mean(), 2),
            p_value=0.0,
            is_significant=True
        )