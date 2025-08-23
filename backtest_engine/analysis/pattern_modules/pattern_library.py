"""
Pattern library management
Store, retrieve, and manage both discovered and user patterns
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .pattern_models import (
    PatternDefinition, PatternAnalysis, PatternRule,
    PatternSource, PatternType
)

logger = logging.getLogger(__name__)

class PatternLibrary:
    """Manages the library of trading patterns"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
        self.patterns: Dict[str, PatternDefinition] = {}
        self.analyses: Dict[str, PatternAnalysis] = {}
        self.rules: List[PatternRule] = []
    
    def add_pattern(self, pattern: PatternDefinition, 
                   analysis: Optional[PatternAnalysis] = None) -> bool:
        """
        Add a pattern to the library
        
        Args:
            pattern: Pattern definition
            analysis: Optional analysis results
            
        Returns:
            Success status
        """
        try:
            self.patterns[pattern.pattern_id] = pattern
            
            if analysis:
                self.analyses[pattern.pattern_id] = analysis
            
            logger.info(f"Added pattern {pattern.name} to library")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add pattern: {e}")
            return False
    
    def get_pattern(self, pattern_id: str) -> Optional[PatternDefinition]:
        """Get a specific pattern by ID"""
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[PatternDefinition]:
        """Get all patterns of a specific type"""
        return [p for p in self.patterns.values() if p.pattern_type == pattern_type]
    
    def get_patterns_by_source(self, source: PatternSource) -> List[PatternDefinition]:
        """Get patterns by source (discovered vs user-defined)"""
        return [p for p in self.patterns.values() if p.source == source]
    
    def get_high_confidence_patterns(self, min_confidence: float = 70) -> List[PatternAnalysis]:
        """Get patterns with high confidence scores"""
        return [
            analysis for analysis in self.analyses.values()
            if analysis.confidence_score >= min_confidence
        ]
    
    def create_rule_from_patterns(self, pattern_ids: List[str],
                                 name: str) -> Optional[PatternRule]:
        """
        Create a trading rule from one or more patterns
        
        Args:
            pattern_ids: List of pattern IDs to combine
            name: Name for the rule
            
        Returns:
            PatternRule or None
        """
        patterns = [self.patterns.get(pid) for pid in pattern_ids]
        patterns = [p for p in patterns if p is not None]
        
        if not patterns:
            return None
        
        # Combine analyses
        combined_performance = self._combine_pattern_performance(pattern_ids)
        
        if not combined_performance:
            return None
        
        # Create rule
        rule = PatternRule(
            rule_id=f"rule_{len(self.rules) + 1}",
            pattern_ids=pattern_ids,
            name=name,
            conditions_text=self._generate_rule_text(patterns),
            expected_win_rate=combined_performance['win_rate'],
            expected_r_multiple=combined_performance['avg_r'],
            confidence=combined_performance['confidence'],
            min_sample_size=combined_performance['sample_size']
        )
        
        self.rules.append(rule)
        return rule
    
    def _combine_pattern_performance(self, pattern_ids: List[str]) -> Dict[str, float]:
        """Combine performance metrics from multiple patterns"""
        analyses = [self.analyses.get(pid) for pid in pattern_ids]
        analyses = [a for a in analyses if a is not None]
        
        if not analyses:
            return None
        
        # Weight by sample size
        total_matches = sum(a.match.total_matches for a in analyses)
        
        if total_matches == 0:
            return None
        
        weighted_win_rate = sum(
            a.performance.win_rate * a.match.total_matches 
            for a in analyses
        ) / total_matches
        
        weighted_r = sum(
            a.performance.avg_r_multiple * a.match.total_matches 
            for a in analyses
        ) / total_matches
        
        avg_confidence = sum(a.confidence_score for a in analyses) / len(analyses)
        
        return {
            'win_rate': round(weighted_win_rate, 2),
            'avg_r': round(weighted_r, 3),
            'confidence': round(avg_confidence, 1),
            'sample_size': total_matches
        }
    
    def _generate_rule_text(self, patterns: List[PatternDefinition]) -> str:
        """Generate human-readable rule text"""
        conditions = []
        
        for pattern in patterns:
            for condition in pattern.conditions:
                conditions.append(condition.description or 
                                f"{condition.field} {condition.operator} {condition.value}")
        
        return " AND ".join(conditions)
    
    def export_patterns(self, filepath: str):
        """Export patterns to JSON file"""
        export_data = {
            'patterns': [self._pattern_to_dict(p) for p in self.patterns.values()],
            'rules': [self._rule_to_dict(r) for r in self.rules],
            'export_date': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _pattern_to_dict(self, pattern: PatternDefinition) -> dict:
        """Convert pattern to dictionary for export"""
        return {
            'id': pattern.pattern_id,
            'name': pattern.name,
            'source': pattern.source.value,
            'type': pattern.pattern_type.value,
            'conditions': [
                {
                    'field': c.field,
                    'operator': c.operator,
                    'value': c.value,
                    'description': c.description
                }
                for c in pattern.conditions
            ],
            'hypothesis': pattern.hypothesis,
            'discovery_method': pattern.discovery_method,
            'created_date': pattern.created_date.isoformat()
        }
    
    def _rule_to_dict(self, rule: PatternRule) -> dict:
        """Convert rule to dictionary for export"""
        return {
            'id': rule.rule_id,
            'name': rule.name,
            'pattern_ids': rule.pattern_ids,
            'conditions': rule.conditions_text,
            'expected_win_rate': rule.expected_win_rate,
            'expected_r': rule.expected_r_multiple,
            'confidence': rule.confidence,
            'active': rule.active
        }