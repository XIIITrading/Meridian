"""
Basic statistics calculation module
Handles fundamental statistical calculations
"""
import pandas as pd
from typing import Dict, Any

from .base_analyzer import BaseAnalyzer
from .data_models import BasicStatistics

class StatisticsCalculator(BaseAnalyzer):
    """Calculates basic trading statistics"""
    
    def get_analysis_name(self) -> str:
        return "Basic Statistics"
    
    def analyze(self, trades_df: pd.DataFrame) -> BasicStatistics:
        """
        Calculate basic trading statistics
        
        Args:
            trades_df: DataFrame of trades
            
        Returns:
            BasicStatistics object with calculated metrics
        """
        if not self.validate_data(trades_df, ['r_multiple']):
            return self._empty_statistics()
        
        total_trades = len(trades_df)
        winners = trades_df[trades_df['r_multiple'] > 0]
        losers = trades_df[trades_df['r_multiple'] <= 0]
        
        win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0
        avg_r = trades_df['r_multiple'].mean()
        total_r = trades_df['r_multiple'].sum()
        
        avg_winner_r = winners['r_multiple'].mean() if len(winners) > 0 else 0
        avg_loser_r = losers['r_multiple'].mean() if len(losers) > 0 else 0
        
        best_trade = trades_df['r_multiple'].max()
        worst_trade = trades_df['r_multiple'].min()
        
        profit_factor = self._calculate_profit_factor(winners, losers)
        expectancy = trades_df['trade_result'].mean() if 'trade_result' in trades_df else 0
        
        return BasicStatistics(
            total_trades=total_trades,
            winners=len(winners),
            losers=len(losers),
            win_rate=round(win_rate, 2),
            avg_r_multiple=round(avg_r, 2),
            total_r=round(total_r, 2),
            avg_winner_r=round(avg_winner_r, 2),
            avg_loser_r=round(avg_loser_r, 2),
            best_trade_r=round(best_trade, 2),
            worst_trade_r=round(worst_trade, 2),
            profit_factor=round(profit_factor, 2),
            expectancy=round(expectancy, 2)
        )
    
    def _calculate_profit_factor(self, winners: pd.DataFrame, losers: pd.DataFrame) -> float:
        """Calculate profit factor"""
        if 'trade_result' not in winners.columns:
            return 0.0 if winners.empty else float('inf')
        
        total_wins = winners['trade_result'].sum() if len(winners) > 0 else 0
        total_losses = abs(losers['trade_result'].sum()) if len(losers) > 0 else 0
        
        return total_wins / total_losses if total_losses > 0 else float('inf')
    
    def _empty_statistics(self) -> BasicStatistics:
        """Return empty statistics object"""
        return BasicStatistics(
            total_trades=0,
            winners=0,
            losers=0,
            win_rate=0.0,
            avg_r_multiple=0.0,
            total_r=0.0,
            avg_winner_r=0.0,
            avg_loser_r=0.0,
            best_trade_r=0.0,
            worst_trade_r=0.0,
            profit_factor=0.0,
            expectancy=0.0
        )