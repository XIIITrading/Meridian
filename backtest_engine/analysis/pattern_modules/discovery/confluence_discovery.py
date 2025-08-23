"""
Automatic discovery of confluence-based patterns
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from itertools import combinations
import uuid

from ..base_pattern import BasePatternEngine
from ..pattern_models import (
    PatternDefinition, PatternCondition,
    PatternSource, PatternType
)

class ConfluenceDiscoveryEngine(BasePatternEngine):
    """Discovers patterns in confluence combinations"""
    
    def get_engine_name(self) -> str:
        return "Confluence Pattern Discovery"
    
    def identify_patterns(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """
        Discover profitable confluence combinations
        
        Args:
            trades_df: Trade data with confluence information
            
        Returns:
            List of discovered patterns
        """
        patterns = []
        
        # Check if confluence data exists
        if 'zone_confluence_level' not in trades_df.columns:
            return patterns
        
        # Pattern 1: High confluence levels
        pattern = self._discover_high_confluence_pattern(trades_df)
        if pattern:
            patterns.append(pattern)
        
        # Pattern 2: Specific confluence combinations
        combo_patterns = self._discover_confluence_combinations(trades_df)
        patterns.extend(combo_patterns)
        
        # Pattern 3: Confluence + time patterns
        time_patterns = self._discover_confluence_time_patterns(trades_df)
        patterns.extend(time_patterns)
        
        return patterns
    
    def _discover_high_confluence_pattern(self, trades_df: pd.DataFrame) -> PatternDefinition:
        """Discover if high confluence zones perform better"""
        high_conf = trades_df[trades_df['zone_confluence_level'].isin(['L4', 'L5'])]
        
        if len(high_conf) < self.min_sample_size:
            return None
        
        # Calculate performance
        win_rate = len(high_conf[high_conf['r_multiple'] > 0]) / len(high_conf) * 100
        
        # Only create pattern if it's profitable
        if win_rate < 55:  # Minimum threshold
            return None
        
        return PatternDefinition(
            pattern_id=str(uuid.uuid4()),
            name="High Confluence Zones (L4-L5)",
            source=PatternSource.DISCOVERED,
            pattern_type=PatternType.CONFLUENCE,
            conditions=[
                PatternCondition(
                    field='zone_confluence_level',
                    operator='in',
                    value=['L4', 'L5'],
                    description='Zone has L4 or L5 confluence'
                )
            ],
            discovery_method='confluence_level_analysis'
        )
    
    def _discover_confluence_combinations(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """Discover specific confluence source combinations"""
        patterns = []
        
        # This would parse the confluence_sources JSONB field
        # Looking for specific combinations that work
        
        if 'confluence_sources' not in trades_df.columns:
            return patterns
        
        # Example: Find which 2-3 confluence sources work best together
        # Implementation depends on your confluence_sources structure
        
        return patterns
    
    def _discover_confluence_time_patterns(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """Discover confluence + timing patterns"""
        patterns = []
        
        if 'entry_candle_time' not in trades_df.columns:
            return patterns
        
        # Convert to hour
        trades_df['hour'] = pd.to_datetime(trades_df['entry_candle_time']).dt.hour
        
        # Test each confluence level at different times
        for level in ['L3', 'L4', 'L5']:
            for hour_range in [(14, 16), (16, 18), (18, 20)]:  # UTC hours
                subset = trades_df[
                    (trades_df['zone_confluence_level'] == level) &
                    (trades_df['hour'] >= hour_range[0]) &
                    (trades_df['hour'] < hour_range[1])
                ]
                
                if len(subset) >= self.min_sample_size:
                    win_rate = len(subset[subset['r_multiple'] > 0]) / len(subset) * 100
                    
                    if win_rate >= 60:  # Threshold for pattern
                        patterns.append(PatternDefinition(
                            pattern_id=str(uuid.uuid4()),
                            name=f"{level} Zones @ {hour_range[0]-5}:00-{hour_range[1]-5}:00 ET",
                            source=PatternSource.DISCOVERED,
                            pattern_type=PatternType.COMBINATION,
                            conditions=[
                                PatternCondition(
                                    field='zone_confluence_level',
                                    operator='==',
                                    value=level,
                                    description=f'Zone confluence is {level}'
                                ),
                                PatternCondition(
                                    field='hour',
                                    operator='between',
                                    value=hour_range,
                                    description=f'Entry between {hour_range[0]}:00-{hour_range[1]}:00 UTC'
                                )
                            ],
                            discovery_method='confluence_time_combination'
                        ))
        
        return patterns