"""
Automatic discovery of failure patterns
Identifies what leads to losses
"""
import pandas as pd
import numpy as np
from typing import List
import uuid

from ..base_pattern import BasePatternEngine
from ..pattern_models import (
    PatternDefinition, PatternCondition,
    PatternSource, PatternType
)

class FailureDiscoveryEngine(BasePatternEngine):
    """Discovers patterns that lead to failures"""
    
    def get_engine_name(self) -> str:
        return "Failure Pattern Discovery"
    
    def identify_patterns(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """
        Discover patterns common in losing trades
        
        Args:
            trades_df: Trade data
            
        Returns:
            List of failure patterns to avoid
        """
        patterns = []
        
        # Get losing trades
        losers = trades_df[trades_df['r_multiple'] <= -1]  # Significant losses
        
        if len(losers) < self.min_sample_size:
            return patterns
        
        # Pattern 1: Low confluence losses
        pattern = self._discover_low_confluence_failures(trades_df, losers)
        if pattern:
            patterns.append(pattern)
        
        # Pattern 2: Quick negative patterns
        pattern = self._discover_quick_negative_failures(trades_df, losers)
        if pattern:
            patterns.append(pattern)
        
        # Pattern 3: Poor zone entry failures
        pattern = self._discover_poor_entry_failures(trades_df, losers)
        if pattern:
            patterns.append(pattern)
        
        # Pattern 4: Time-based failures
        patterns.extend(self._discover_time_failures(trades_df, losers))
        
        return patterns
    
    def _discover_low_confluence_failures(self, trades_df: pd.DataFrame, 
                                         losers: pd.DataFrame) -> PatternDefinition:
        """Check if low confluence leads to more losses"""
        if 'zone_confluence_level' not in trades_df.columns:
            return None
        
        # Calculate loss rate by confluence
        for level in ['L1', 'L2']:
            level_trades = trades_df[trades_df['zone_confluence_level'] == level]
            if len(level_trades) >= self.min_sample_size:
                loss_rate = len(level_trades[level_trades['r_multiple'] <= -1]) / len(level_trades) * 100
                
                if loss_rate >= 40:  # High loss rate
                    return PatternDefinition(
                        pattern_id=str(uuid.uuid4()),
                        name=f"AVOID: {level} Zones (High Loss Rate)",
                        source=PatternSource.DISCOVERED,
                        pattern_type=PatternType.FAILURE,
                        conditions=[
                            PatternCondition(
                                field='zone_confluence_level',
                                operator='==',
                                value=level,
                                description=f'Low confluence {level} zones'
                            )
                        ],
                        discovery_method='failure_rate_analysis'
                    )
        
        return None
    
    def _discover_quick_negative_failures(self, trades_df: pd.DataFrame,
                                         losers: pd.DataFrame) -> PatternDefinition:
        """Discover if trades that go negative quickly tend to fail"""
        if 'first_negative_minute' not in trades_df.columns:
            return None
        
        # Trades that go negative in first 5 minutes
        quick_negative = trades_df[
            (trades_df['first_negative_minute'].notna()) &
            (trades_df['first_negative_minute'] <= 5)
        ]
        
        if len(quick_negative) >= self.min_sample_size:
            loss_rate = len(quick_negative[quick_negative['r_multiple'] <= -1]) / len(quick_negative) * 100
            
            if loss_rate >= 50:
                return PatternDefinition(
                    pattern_id=str(uuid.uuid4()),
                    name="AVOID: Quick Negative (<5 min)",
                    source=PatternSource.DISCOVERED,
                    pattern_type=PatternType.FAILURE,
                    conditions=[
                        PatternCondition(
                            field='first_negative_minute',
                            operator='<=',
                            value=5,
                            description='Goes negative within 5 minutes'
                        )
                    ],
                    discovery_method='negative_timing_analysis'
                )
        
        return None
    
    def _discover_poor_entry_failures(self, trades_df: pd.DataFrame,
                                     losers: pd.DataFrame) -> PatternDefinition:
        """Discover if poor zone entries lead to failures"""
        if 'distance_from_zone_ticks' not in trades_df.columns:
            return None
        
        # Entries far from zone center
        far_entries = trades_df[trades_df['distance_from_zone_ticks'].abs() > 10]
        
        if len(far_entries) >= self.min_sample_size:
            loss_rate = len(far_entries[far_entries['r_multiple'] <= -1]) / len(far_entries) * 100
            
            if loss_rate >= 45:
                return PatternDefinition(
                    pattern_id=str(uuid.uuid4()),
                    name="AVOID: Far Zone Entries (>10 ticks)",
                    source=PatternSource.DISCOVERED,
                    pattern_type=PatternType.FAILURE,
                    conditions=[
                        PatternCondition(
                            field='distance_from_zone_ticks',
                            operator='>',
                            value=10,
                            description='Entry more than 10 ticks from zone'
                        )
                    ],
                    discovery_method='zone_distance_analysis'
                )
        
        return None
    
    def _discover_time_failures(self, trades_df: pd.DataFrame,
                               losers: pd.DataFrame) -> List[PatternDefinition]:
        """Discover time periods with high failure rates"""
        patterns = []
        
        if 'entry_candle_time' not in trades_df.columns:
            return patterns
        
        trades_df['hour'] = pd.to_datetime(trades_df['entry_candle_time']).dt.hour
        
        # Check each hour for high failure rate
        for hour in range(14, 21):  # Market hours in UTC
            hour_trades = trades_df[trades_df['hour'] == hour]
            
            if len(hour_trades) >= self.min_sample_size:
                loss_rate = len(hour_trades[hour_trades['r_multiple'] <= -1]) / len(hour_trades) * 100
                
                if loss_rate >= 50:
                    patterns.append(PatternDefinition(
                        pattern_id=str(uuid.uuid4()),
                        name=f"AVOID: {hour-5}:00 ET Hour",
                        source=PatternSource.DISCOVERED,
                        pattern_type=PatternType.FAILURE,
                        conditions=[
                            PatternCondition(
                                field='hour',
                                operator='==',
                                value=hour,
                                description=f'Trades at {hour}:00 UTC ({hour-5}:00 ET)'
                            )
                        ],
                        discovery_method='hourly_failure_analysis'
                    ))
        
        return patterns