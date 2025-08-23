"""
Pattern scoring and ranking
"""
from typing import List
from .pattern_models import PatternAnalysis

class PatternScorer:
    """Scores and ranks patterns"""
    
    def rank_patterns(self, patterns: List[PatternAnalysis]) -> List[PatternAnalysis]:
        """
        Rank patterns by composite score
        
        Args:
            patterns: List of pattern analyses
            
        Returns:
            Sorted list (best first)
        """
        # Sort by strength score
        return sorted(patterns, key=lambda x: x.strength_score, reverse=True)
    
    def calculate_composite_score(self, analysis: PatternAnalysis) -> float:
        """Calculate composite pattern score"""
        # Already calculated in base class
        return analysis.strength_score