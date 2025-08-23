"""
Pattern persistence to database
"""
import json
import logging
from typing import List
from datetime import datetime

from .pattern_models import PatternDefinition, PatternAnalysis

logger = logging.getLogger(__name__)

class PatternPersistence:
    """Handles pattern database operations"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
    
    def save_patterns(self, patterns: List[PatternDefinition],
                     analyses: List[PatternAnalysis]) -> bool:
        """
        Save patterns to database
        
        Args:
            patterns: Pattern definitions
            analyses: Pattern analyses
            
        Returns:
            Success status
        """
        try:
            for pattern, analysis in zip(patterns, analyses):
                data = {
                    'pattern_type': pattern.pattern_type.value,
                    'pattern_name': pattern.name,
                    'conditions': json.dumps([
                        {
                            'field': c.field,
                            'operator': c.operator,
                            'value': c.value
                        } for c in pattern.conditions
                    ]),
                    'statistics': json.dumps({
                        'win_rate': analysis.performance.win_rate,
                        'avg_r': analysis.performance.avg_r_multiple,
                        'matches': analysis.match.total_matches
                    }),
                    'strength_score': analysis.strength_score,
                    'sample_size': analysis.match.total_matches
                }
                
                self.storage.client.table('pattern_results').insert(data).execute()
            
            logger.info(f"Saved {len(patterns)} patterns to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
            return False