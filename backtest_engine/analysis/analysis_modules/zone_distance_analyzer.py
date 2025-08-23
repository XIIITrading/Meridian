"""
Zone distance analysis module
Analyzes performance based on entry distance from zones
"""
import pandas as pd
from typing import Dict, Any

from .base_analyzer import BaseAnalyzer
from .data_models import ZoneDistanceResult

class ZoneDistanceAnalyzer(BaseAnalyzer):
    """Analyzes trading performance by distance from zone"""
    
    def get_analysis_name(self) -> str:
        return "Zone Distance Analysis"
    
    def analyze(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze performance based on entry distance from zone
        
        Args:
            trades_df: DataFrame of trades
            
        Returns:
            Analysis of optimal entry points within zones
        """
        if not self.validate_data(trades_df, ['distance_from_zone_ticks']):
            return {}
        
        # Filter trades with zone data
        zone_trades = trades_df[trades_df['distance_from_zone_ticks'].notna()]
        
        if zone_trades.empty:
            return {}
        
        # Categorize distances
        categories = self._categorize_distances(zone_trades)
        
        # Analyze each category
        results = {}
        for category_name, category_trades in categories.items():
            if len(category_trades) > 0:
                results[category_name] = self._analyze_category(category_trades, category_name)
        
        return results
    
    def _categorize_distances(self, zone_trades: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Categorize trades by distance from zone"""
        bins = [-float('inf'), -10, -5, 0, 5, 10, float('inf')]
        labels = ['Far Below', 'Below', 'Lower Edge', 'Center', 'Upper Edge', 'Above']
        
        zone_trades['distance_category'] = pd.cut(
            zone_trades['distance_from_zone_ticks'],
            bins=bins,
            labels=labels
        )
        
        categories = {}
        for label in labels:
            categories[label] = zone_trades[zone_trades['distance_category'] == label]
        
        return categories
    
    def _analyze_category(self, cat_trades: pd.DataFrame, category: str) -> ZoneDistanceResult:
        """Analyze a specific distance category"""
        trade_count = len(cat_trades)
        winners = cat_trades[cat_trades['r_multiple'] > 0]
        win_rate = (len(winners) / trade_count * 100) if trade_count > 0 else 0
        
        avg_r = cat_trades['r_multiple'].mean()
        avg_mfe_r = cat_trades['mfe_r_multiple'].mean() if 'mfe_r_multiple' in cat_trades else 0
        avg_mae_r = cat_trades['mae_r_multiple'].mean() if 'mae_r_multiple' in cat_trades else 0
        
        return ZoneDistanceResult(
            category=category,
            trade_count=trade_count,
            win_rate=round(win_rate, 2),
            avg_r_multiple=round(avg_r, 2),
            avg_mfe_r=round(avg_mfe_r, 2),
            avg_mae_r=round(avg_mae_r, 2)
        )