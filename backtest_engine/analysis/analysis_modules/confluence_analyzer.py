"""
Confluence level analysis module
Analyzes performance by zone confluence levels (L1-L5)
"""
import pandas as pd
from typing import Dict
from scipy import stats
import numpy as np

from .base_analyzer import BaseAnalyzer
from .data_models import ConfluenceAnalysis

class ConfluenceAnalyzer(BaseAnalyzer):
    """Analyzes trading performance by confluence level"""
    
    def get_analysis_name(self) -> str:
        return "Confluence Level Analysis"
    
    def analyze(self, trades_df: pd.DataFrame) -> Dict[str, ConfluenceAnalysis]:
        """
        Analyze performance grouped by confluence level
        
        Args:
            trades_df: DataFrame of trades
            
        Returns:
            Dictionary mapping confluence levels to their analysis
        """
        if not self.validate_data(trades_df, ['zone_confluence_level', 'r_multiple']):
            return {}
        
        results = {}
        
        # Analyze each confluence level
        for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
            level_trades = trades_df[trades_df['zone_confluence_level'] == level]
            
            if len(level_trades) < 1:
                continue
            
            analysis = self._analyze_level(level_trades, level)
            results[level] = analysis
        
        return results
    
    def _analyze_level(self, level_trades: pd.DataFrame, level: str) -> ConfluenceAnalysis:
        """Analyze a specific confluence level"""
        trade_count = len(level_trades)
        winners = level_trades[level_trades['r_multiple'] > 0]
        losers = level_trades[level_trades['r_multiple'] <= 0]
        
        win_rate = (len(winners) / trade_count * 100) if trade_count > 0 else 0
        avg_r = level_trades['r_multiple'].mean()
        
        avg_winner = winners['r_multiple'].mean() if len(winners) > 0 else 0
        avg_loser = abs(losers['r_multiple'].mean()) if len(losers) > 0 else 0
        
        # Calculate profit factor
        profit_factor = self._calculate_profit_factor(winners, losers)
        
        # Statistical significance testing
        p_value, ci_low, ci_high = self._calculate_statistical_significance(
            len(winners), trade_count
        )
        
        return ConfluenceAnalysis(
            level=level,
            trade_count=trade_count,
            win_rate=round(win_rate, 2),
            avg_r_multiple=round(avg_r, 2),
            avg_winner=round(avg_winner, 2),
            avg_loser=round(avg_loser, 2),
            profit_factor=round(profit_factor, 2),
            statistical_significance=round(p_value, 4),
            confidence_interval=(round(ci_low, 1), round(ci_high, 1))
        )
    
    def _calculate_profit_factor(self, winners: pd.DataFrame, losers: pd.DataFrame) -> float:
        """Calculate profit factor for a set of trades"""
        if 'trade_result' not in winners.columns:
            return 0.0
            
        total_wins = winners['trade_result'].sum() if len(winners) > 0 else 0
        total_losses = abs(losers['trade_result'].sum()) if len(losers) > 0 else 1
        
        return total_wins / total_losses if total_losses > 0 else float('inf')
    
    def _calculate_statistical_significance(self, wins: int, total: int):
        """Calculate statistical significance and confidence interval"""
        if total < self.min_sample_size:
            return 1.0, 0, 100
        
        # Use the newer binomtest for scipy compatibility
        try:
            # Try newer scipy version first (>= 1.7.0)
            from scipy.stats import binomtest
            result = binomtest(wins, total, 0.5, alternative='two-sided')
            p_value = result.pvalue
        except ImportError:
            # Fall back to older method for scipy < 1.7.0
            try:
                p_value = stats.binom_test(wins, total, 0.5, alternative='two-sided')
            except AttributeError:
                # If neither works, use a manual calculation
                # Using normal approximation to binomial
                expected = total * 0.5
                std_dev = np.sqrt(total * 0.5 * 0.5)
                if std_dev > 0:
                    z_score = (wins - expected) / std_dev
                    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                else:
                    p_value = 1.0
        
        # Wilson score confidence interval
        p_hat = wins / total
        z = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)
        
        denominator = 1 + z**2 / total
        center = (p_hat + z**2 / (2 * total)) / denominator
        
        margin = z * np.sqrt(
            (p_hat * (1 - p_hat) + z**2 / (4 * total)) / total
        ) / denominator
        
        ci_low = max(0, center - margin) * 100
        ci_high = min(1, center + margin) * 100
        
        return p_value, ci_low, ci_high