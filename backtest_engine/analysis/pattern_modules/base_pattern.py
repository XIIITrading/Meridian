"""
Base classes for pattern discovery and validation
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
import logging

from .pattern_models import (
    PatternDefinition, PatternMatch, PatternPerformance,
    PatternAnalysis, PatternCondition, PatternSource, PatternType
)

logger = logging.getLogger(__name__)

class BasePatternEngine(ABC):
    """Abstract base for all pattern engines"""
    
    def __init__(self, min_sample_size: int = 5, confidence_level: float = 0.95):
        self.min_sample_size = min_sample_size
        self.confidence_level = confidence_level
    
    @abstractmethod
    def identify_patterns(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """Identify patterns in the data"""
        pass
    
    @abstractmethod
    def get_engine_name(self) -> str:
        """Get name of this engine"""
        pass
    
    def evaluate_pattern(self, pattern: PatternDefinition, 
                        trades_df: pd.DataFrame) -> Optional[PatternAnalysis]:
        """
        Evaluate a pattern's performance
        
        Args:
            pattern: Pattern definition to evaluate
            trades_df: Trade data
            
        Returns:
            Complete pattern analysis or None
        """
        # Match pattern
        matches = self._match_pattern(pattern, trades_df)
        
        if not matches or len(matches.matching_trades) < self.min_sample_size:
            logger.info(f"Insufficient matches for pattern {pattern.name}: "
                       f"{len(matches.matching_trades) if matches else 0}")
            return None
        
        # Calculate performance
        performance = self._calculate_performance(matches, trades_df)
        
        # Statistical testing
        significance = self._test_significance(matches, trades_df)
        
        # Score the pattern
        confidence = self._calculate_confidence(matches, performance, significance)
        strength = self._calculate_strength(matches, performance, confidence)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(pattern, performance, confidence)
        
        return PatternAnalysis(
            definition=pattern,
            match=matches,
            performance=performance,
            statistical_significance=significance,
            confidence_score=confidence,
            strength_score=strength,
            sample_size_sufficient=len(matches.matching_trades) >= self.min_sample_size,
            recommendations=recommendations
        )
    
    def _match_pattern(self, pattern: PatternDefinition, 
                      trades_df: pd.DataFrame) -> PatternMatch:
        """Match pattern conditions against trades"""
        mask = pd.Series([True] * len(trades_df))
        
        for condition in pattern.conditions:
            mask &= self._apply_condition(trades_df, condition)
        
        matching_trades = trades_df[mask]
        
        return PatternMatch(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.name,
            matching_trades=matching_trades.index.tolist(),
            total_matches=len(matching_trades),
            total_opportunities=len(trades_df),
            match_rate=round(len(matching_trades) / len(trades_df) * 100, 2)
        )
    
    def _apply_condition(self, df: pd.DataFrame, condition: PatternCondition) -> pd.Series:
        """Apply a single condition to dataframe"""
        if condition.field not in df.columns:
            logger.warning(f"Field {condition.field} not in dataframe")
            return pd.Series([False] * len(df))
        
        series = df[condition.field]
        
        if condition.operator == '==':
            return series == condition.value
        elif condition.operator == '>':
            return series > condition.value
        elif condition.operator == '>=':
            return series >= condition.value
        elif condition.operator == '<':
            return series < condition.value
        elif condition.operator == '<=':
            return series <= condition.value
        elif condition.operator == 'in':
            return series.isin(condition.value)
        elif condition.operator == 'between':
            return (series >= condition.value[0]) & (series <= condition.value[1])
        elif condition.operator == 'not_null':
            return series.notna()
        elif condition.operator == 'is_null':
            return series.isna()
        else:
            logger.warning(f"Unknown operator: {condition.operator}")
            return pd.Series([False] * len(df))
    
    def _calculate_performance(self, matches: PatternMatch, 
                              trades_df: pd.DataFrame) -> PatternPerformance:
        """Calculate performance metrics for matched trades"""
        matched_df = trades_df.loc[matches.matching_trades]
        
        if matched_df.empty:
            return self._empty_performance(matches.pattern_id)
        
        winners = matched_df[matched_df['r_multiple'] > 0]
        win_rate = len(winners) / len(matched_df) * 100
        
        avg_r = matched_df['r_multiple'].mean()
        total_r = matched_df['r_multiple'].sum()
        
        # Profit factor
        total_wins = winners['r_multiple'].sum() if len(winners) > 0 else 0
        total_losses = abs(matched_df[matched_df['r_multiple'] <= 0]['r_multiple'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Risk metrics
        stddev_r = matched_df['r_multiple'].std()
        sharpe = avg_r / stddev_r if stddev_r > 0 else 0
        
        return PatternPerformance(
            pattern_id=matches.pattern_id,
            win_rate=round(win_rate, 2),
            avg_r_multiple=round(avg_r, 3),
            total_r=round(total_r, 2),
            profit_factor=round(profit_factor, 2),
            best_trade=round(matched_df['r_multiple'].max(), 2),
            worst_trade=round(matched_df['r_multiple'].min(), 2),
            stddev_r=round(stddev_r, 3),
            sharpe_ratio=round(sharpe, 2)
        )
    
    def _test_significance(self, matches: PatternMatch, 
                      trades_df: pd.DataFrame) -> float:
        """Test statistical significance of pattern"""
        matched_df = trades_df.loc[matches.matching_trades]
        
        if len(matched_df) < self.min_sample_size:
            return 1.0  # Not significant
        
        # Test if win rate is different from overall
        pattern_winners = len(matched_df[matched_df['r_multiple'] > 0])
        overall_win_rate = len(trades_df[trades_df['r_multiple'] > 0]) / len(trades_df)
        
        # Use the newer binomtest for scipy compatibility
        try:
            # Try newer scipy version first (>= 1.7.0)
            from scipy.stats import binomtest
            result = binomtest(pattern_winners, len(matched_df), 
                            overall_win_rate, alternative='two-sided')
            p_value = result.pvalue
        except ImportError:
            # Fall back to older method or manual calculation
            try:
                p_value = stats.binom_test(pattern_winners, len(matched_df), 
                                        overall_win_rate, alternative='two-sided')
            except AttributeError:
                # Manual calculation using normal approximation
                expected = len(matched_df) * overall_win_rate
                variance = len(matched_df) * overall_win_rate * (1 - overall_win_rate)
                if variance > 0:
                    z_score = (pattern_winners - expected) / np.sqrt(variance)
                    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                else:
                    p_value = 1.0
        
        return p_value

    
    def _calculate_confidence(self, matches: PatternMatch,
                            performance: PatternPerformance,
                            significance: float) -> float:
        """Calculate confidence score (0-100)"""
        # Factor 1: Sample size (max at 30+ trades)
        sample_factor = min(1.0, matches.total_matches / 30)
        
        # Factor 2: Statistical significance
        sig_factor = 1.0 - significance if significance < 0.05 else 0
        
        # Factor 3: Performance consistency (low stddev is good)
        consistency_factor = 1.0 / (1 + performance.stddev_r) if performance.stddev_r > 0 else 1
        
        # Factor 4: Win rate improvement
        win_factor = min(1.0, performance.win_rate / 50)  # 50% baseline
        
        # Weighted average
        confidence = (
            sample_factor * 0.3 +
            sig_factor * 0.3 +
            consistency_factor * 0.2 +
            win_factor * 0.2
        ) * 100
        
        return round(min(100, confidence), 1)
    
    def _calculate_strength(self, matches: PatternMatch,
                          performance: PatternPerformance,
                          confidence: float) -> float:
        """Calculate overall pattern strength score"""
        # Combine multiple factors
        strength = (
            confidence * 0.4 +  # Confidence is key
            min(100, performance.win_rate) * 0.3 +  # Win rate
            min(100, performance.avg_r_multiple * 20) * 0.2 +  # Avg R (scaled)
            min(100, matches.total_matches * 2) * 0.1  # Sample size (scaled)
        )
        
        return round(min(100, strength), 1)
    
    def _generate_recommendations(self, pattern: PatternDefinition,
                                performance: PatternPerformance,
                                confidence: float) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        if confidence >= 80:
            recs.append(f"✅ High confidence pattern: Use in live trading")
        elif confidence >= 60:
            recs.append(f"⚠️ Medium confidence: Monitor for more data")
        else:
            recs.append(f"❌ Low confidence: Needs validation")
        
        if performance.win_rate >= 70:
            recs.append(f"🎯 Excellent win rate of {performance.win_rate}%")
        
        if performance.avg_r_multiple >= 2:
            recs.append(f"💰 Strong R-multiple of {performance.avg_r_multiple}")
        
        return recs
    
    def _empty_performance(self, pattern_id: str) -> PatternPerformance:
        """Return empty performance metrics"""
        return PatternPerformance(
            pattern_id=pattern_id,
            win_rate=0,
            avg_r_multiple=0,
            total_r=0,
            profit_factor=0,
            best_trade=0,
            worst_trade=0,
            stddev_r=0,
            sharpe_ratio=0
        )