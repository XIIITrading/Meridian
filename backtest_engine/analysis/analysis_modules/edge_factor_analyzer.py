"""
Edge factor identification module
Identifies statistically significant trading edges
"""
import pandas as pd
import numpy as np
from typing import List

from .base_analyzer import BaseAnalyzer
from .data_models import EdgeFactor

class EdgeFactorAnalyzer(BaseAnalyzer):
    """Identifies statistically significant edge factors in trading"""
    
    def get_analysis_name(self) -> str:
        return "Edge Factor Analysis"
    
    def analyze(self, trades_df: pd.DataFrame) -> List[EdgeFactor]:
        """
        Identify statistically significant edge factors
        
        Args:
            trades_df: DataFrame of trades
            
        Returns:
            List of identified edge factors
        """
        if not self.validate_data(trades_df, ['r_multiple']):
            return []
        
        edges = []
        baseline_winrate = self._calculate_baseline_winrate(trades_df)
        
        # Test various edge factors
        edge = self._test_high_confluence_edge(trades_df, baseline_winrate)
        if edge:
            edges.append(edge)
        
        edge = self._test_never_negative_edge(trades_df, baseline_winrate)
        if edge:
            edges.append(edge)
        
        edge = self._test_optimal_zone_entry_edge(trades_df, baseline_winrate)
        if edge:
            edges.append(edge)
        
        return edges
    
    def _calculate_baseline_winrate(self, trades_df: pd.DataFrame) -> float:
        """Calculate overall baseline win rate"""
        winners = len(trades_df[trades_df['r_multiple'] > 0])
        total = len(trades_df)
        return (winners / total * 100) if total > 0 else 0
    
    def _test_high_confluence_edge(self, trades_df: pd.DataFrame, baseline: float) -> EdgeFactor:
        """Test if high confluence zones provide an edge"""
        if 'zone_confluence_level' not in trades_df.columns:
            return None
        
        high_conf = trades_df[trades_df['zone_confluence_level'].isin(['L4', 'L5'])]
        
        if len(high_conf) < self.min_sample_size:
            return None
        
        hc_winrate = (len(high_conf[high_conf['r_multiple'] > 0]) / len(high_conf) * 100)
        
        if hc_winrate <= baseline * 1.2:  # Need 20% improvement
            return None
        
        return EdgeFactor(
            factor_name="High Confluence Zones",
            condition="Trade only L4-L5 confluence zones",
            baseline_winrate=round(baseline, 2),
            edge_winrate=round(hc_winrate, 2),
            improvement=round((hc_winrate / baseline - 1) * 100, 2),
            sample_size=len(high_conf),
            confidence=round(self._calculate_confidence_score(
                len(high_conf), hc_winrate, baseline
            ), 2),
            actionable_insight="Focus on zones with L4+ confluence for higher probability trades"
        )
    
    def _test_never_negative_edge(self, trades_df: pd.DataFrame, baseline: float) -> EdgeFactor:
        """Test if never-negative trades provide an edge"""
        if 'first_negative_minute' not in trades_df.columns:
            return None
        
        never_neg = trades_df[trades_df['first_negative_minute'].isna()]
        
        if len(never_neg) < self.min_sample_size:
            return None
        
        nn_winrate = (len(never_neg[never_neg['r_multiple'] > 0]) / len(never_neg) * 100)
        
        if nn_winrate <= baseline * 1.15:  # Need 15% improvement
            return None
        
        return EdgeFactor(
            factor_name="Immediate Positive Trades",
            condition="Trades that never go negative",
            baseline_winrate=round(baseline, 2),
            edge_winrate=round(nn_winrate, 2),
            improvement=round((nn_winrate / baseline - 1) * 100, 2),
            sample_size=len(never_neg),
            confidence=round(self._calculate_confidence_score(
                len(never_neg), nn_winrate, baseline
            ), 2),
            actionable_insight="Entries that immediately move in your favor have higher success rate"
        )
    
    def _test_optimal_zone_entry_edge(self, trades_df: pd.DataFrame, baseline: float) -> EdgeFactor:
        """Test if precise zone entries provide an edge"""
        if 'distance_from_zone_ticks' not in trades_df.columns:
            return None
        
        optimal_entry = trades_df[
            (trades_df['distance_from_zone_ticks'].abs() <= 5) &
            (trades_df['zone_confluence_level'].notna())
        ]
        
        if len(optimal_entry) < self.min_sample_size:
            return None
        
        oe_winrate = (len(optimal_entry[optimal_entry['r_multiple'] > 0]) / 
                     len(optimal_entry) * 100)
        
        if oe_winrate <= baseline * 1.15:
            return None
        
        return EdgeFactor(
            factor_name="Precise Zone Entry",
            condition="Entry within 5 ticks of zone center",
            baseline_winrate=round(baseline, 2),
            edge_winrate=round(oe_winrate, 2),
            improvement=round((oe_winrate / baseline - 1) * 100, 2),
            sample_size=len(optimal_entry),
            confidence=round(self._calculate_confidence_score(
                len(optimal_entry), oe_winrate, baseline
            ), 2),
            actionable_insight="Wait for price to reach optimal zone location before entry"
        )
    
    def _calculate_confidence_score(self, sample_size: int, observed_rate: float, 
                                   baseline_rate: float) -> float:
        """Calculate confidence score for an edge factor"""
        if sample_size < self.min_sample_size:
            return 0.0
        
        # Weight by sample size (logarithmic scale)
        sample_weight = min(1.0, np.log10(sample_size) / 2)
        
        # Weight by improvement magnitude
        improvement = abs(observed_rate - baseline_rate) / baseline_rate if baseline_rate > 0 else 0
        improvement_weight = min(1.0, improvement * 2)
        
        # Combine weights
        confidence = sample_weight * improvement_weight * 100
        
        return min(100, confidence)