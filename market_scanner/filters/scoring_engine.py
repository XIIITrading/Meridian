"""
Interest scoring engine for ranking stocks.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

@dataclass
class InterestScoreWeights:
    """Weights for interest score calculation."""
    premarket_volume_ratio: float = 0.40
    atr_percentage: float = 0.25
    dollar_volume_score: float = 0.20
    premarket_volume_absolute: float = 0.10
    price_atr_bonus: float = 0.05
    
    def validate(self):
        """Ensure weights sum to 1.0."""
        total = (self.premarket_volume_ratio + self.atr_percentage + 
                self.dollar_volume_score + self.premarket_volume_absolute + 
                self.price_atr_bonus)
        if not np.isclose(total, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total}")

class ScoringEngine:
    """Engine for calculating interest scores."""
    
    def __init__(self, weights: InterestScoreWeights = None):
        """Initialize scoring engine."""
        self.weights = weights or InterestScoreWeights()
        self.weights.validate()
    
    def calculate_scores(self, df: pd.DataFrame, 
                        min_dollar_volume: float = 1_000_000) -> pd.DataFrame:
        """Calculate interest scores for all stocks in DataFrame."""
        # Calculate individual components
        
        # 1. Pre-market Volume Ratio (0-100 scale, capped at 100)
        df['pm_vol_ratio_score'] = (
            (df['premarket_volume'] / df['avg_daily_volume']) * 100
        ).clip(upper=100)
        
        # 2. ATR Percentage (already in percentage form)
        df['atr_percent_score'] = df['atr_percent'].clip(upper=100)
        
        # 3. Dollar Volume Score (normalized to baseline)
        df['dollar_vol_score'] = (
            (df['dollar_volume'] / min_dollar_volume) * 100
        ).clip(upper=100)
        
        # 4. Pre-market Volume Absolute Score (normalized, log scale)
        df['pm_vol_abs_score'] = (
            np.log10(df['premarket_volume'] + 1) / np.log10(1_000_000) * 100
        ).clip(upper=100)
        
        # 5. Price-ATR Sweet Spot Bonus
        df['price_atr_bonus'] = 0.0
        sweet_spot_mask = (df['atr_percent'] >= 2.0) & (df['atr_percent'] <= 5.0)
        df.loc[sweet_spot_mask, 'price_atr_bonus'] = 100.0
        
        # Calculate weighted composite score
        df['interest_score'] = (
            (df['pm_vol_ratio_score'] * self.weights.premarket_volume_ratio) +
            (df['atr_percent_score'] * self.weights.atr_percentage) +
            (df['dollar_vol_score'] * self.weights.dollar_volume_score) +
            (df['pm_vol_abs_score'] * self.weights.premarket_volume_absolute) +
            (df['price_atr_bonus'] * self.weights.price_atr_bonus)
        )
        
        # Round for display
        df['interest_score'] = df['interest_score'].round(2)
        
        logger.debug(f"Interest scores calculated. Range: {df['interest_score'].min():.2f} - {df['interest_score'].max():.2f}")
        
        return df
    
    def rank_by_score(self, df: pd.DataFrame, top_n: int = None) -> pd.DataFrame:
        """Rank stocks by interest score."""
        if df.empty:
            return df
        
        # Sort by interest score descending
        ranked_df = df.sort_values('interest_score', ascending=False)
        
        # Add rank column
        ranked_df['rank'] = range(1, len(ranked_df) + 1)
        
        # Return top N if specified
        if top_n and top_n < len(ranked_df):
            logger.info(f"Returning top {top_n} stocks by interest score")
            return ranked_df.head(top_n)
        
        return ranked_df
    
    def explain_score(self, row: pd.Series) -> Dict[str, Dict[str, float]]:
        """Explain the interest score calculation for a single stock."""
        explanation = {
            'components': {
                'PM Volume Ratio': {
                    'raw_value': f"{row['premarket_volume'] / row['avg_daily_volume']:.2%}",
                    'score': row['pm_vol_ratio_score'],
                    'weight': self.weights.premarket_volume_ratio,
                    'contribution': row['pm_vol_ratio_score'] * self.weights.premarket_volume_ratio
                },
                'ATR Percentage': {
                    'raw_value': f"{row['atr_percent']:.2f}%",
                    'score': row['atr_percent_score'],
                    'weight': self.weights.atr_percentage,
                    'contribution': row['atr_percent_score'] * self.weights.atr_percentage
                },
                'Dollar Volume': {
                    'raw_value': f"${row['dollar_volume']:,.0f}",
                    'score': row['dollar_vol_score'],
                    'weight': self.weights.dollar_volume_score,
                    'contribution': row['dollar_vol_score'] * self.weights.dollar_volume_score
                },
                'PM Volume Absolute': {
                    'raw_value': f"{row['premarket_volume']:,.0f}",
                    'score': row['pm_vol_abs_score'],
                    'weight': self.weights.premarket_volume_absolute,
                    'contribution': row['pm_vol_abs_score'] * self.weights.premarket_volume_absolute
                },
                'Price-ATR Bonus': {
                    'raw_value': f"{'Yes' if row['price_atr_bonus'] > 0 else 'No'}",
                    'score': row['price_atr_bonus'],
                    'weight': self.weights.price_atr_bonus,
                    'contribution': row['price_atr_bonus'] * self.weights.price_atr_bonus
                }
            },
            'total_score': row['interest_score']
        }
        
        return explanation