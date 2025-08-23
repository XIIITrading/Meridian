"""
Test user-defined pattern hypotheses
"""
import pandas as pd
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from ..base_pattern import BasePatternEngine
from ..pattern_models import (
    PatternDefinition, PatternCondition, PatternAnalysis,
    PatternSource, PatternType, UserPatternRequest
)

class HypothesisTester(BasePatternEngine):
    """Tests user-defined trading patterns"""
    
    def get_engine_name(self) -> str:
        return "User Hypothesis Testing"
    
    def identify_patterns(self, trades_df: pd.DataFrame) -> List[PatternDefinition]:
        """Not used for user patterns - they're explicitly defined"""
        return []
    
    def test_user_pattern(self, request: UserPatternRequest,
                         trades_df: pd.DataFrame) -> PatternAnalysis:
        """
        Test a user-defined pattern hypothesis
        
        Args:
            request: User pattern request
            trades_df: Trade data
            
        Returns:
            Complete analysis of the pattern
        """
        # Convert user request to pattern definition
        pattern = self._convert_request_to_pattern(request)
        
        # Evaluate the pattern
        analysis = self.evaluate_pattern(pattern, trades_df)
        
        # Check against success criteria if provided
        if analysis and request.success_criteria:
            analysis = self._check_success_criteria(analysis, request.success_criteria)
        
        return analysis
    
    def _convert_request_to_pattern(self, request: UserPatternRequest) -> PatternDefinition:
        """Convert user request to formal pattern definition"""
        conditions = []
        
        for field, criteria in request.conditions.items():
            condition = self._parse_user_condition(field, criteria)
            if condition:
                conditions.append(condition)
        
        return PatternDefinition(
            pattern_id=str(uuid.uuid4()),
            name=request.name,
            source=PatternSource.USER_DEFINED,
            pattern_type=PatternType.CUSTOM,
            conditions=conditions,
            hypothesis=request.hypothesis,
            created_by=request.user_id
        )
    
    def _parse_user_condition(self, field: str, criteria: Any) -> Optional[PatternCondition]:
        """Parse user-friendly condition format"""
        
        # Handle different input formats
        if isinstance(criteria, dict):
            # Format: {'operator': '>', 'value': 5}
            return PatternCondition(
                field=field,
                operator=criteria.get('operator', '=='),
                value=criteria.get('value'),
                description=criteria.get('description', '')
            )
        elif isinstance(criteria, list):
            # Format: ['L4', 'L5'] implies 'in' operator
            return PatternCondition(
                field=field,
                operator='in',
                value=criteria,
                description=f"{field} in {criteria}"
            )
        elif isinstance(criteria, str):
            # Parse string formats like '>5', '==L4', 'between:1,10'
            if criteria.startswith('>='):
                return PatternCondition(field=field, operator='>=', 
                                      value=float(criteria[2:]))
            elif criteria.startswith('>'):
                return PatternCondition(field=field, operator='>', 
                                      value=float(criteria[1:]))
            elif criteria.startswith('<='):
                return PatternCondition(field=field, operator='<=', 
                                      value=float(criteria[2:]))
            elif criteria.startswith('<'):
                return PatternCondition(field=field, operator='<', 
                                      value=float(criteria[1:]))
            elif criteria.startswith('between:'):
                values = criteria[8:].split(',')
                return PatternCondition(field=field, operator='between',
                                      value=[float(values[0]), float(values[1])])
            else:
                # Default to equality
                return PatternCondition(field=field, operator='==', value=criteria)
        else:
            # Simple value, assume equality
            return PatternCondition(field=field, operator='==', value=criteria)
    
    def _check_success_criteria(self, analysis: PatternAnalysis,
                               criteria: Dict[str, float]) -> PatternAnalysis:
        """Check if pattern meets user's success criteria"""
        
        success_notes = []
        
        for metric, threshold in criteria.items():
            actual_value = None
            
            if metric == 'win_rate':
                actual_value = analysis.performance.win_rate
            elif metric == 'avg_r':
                actual_value = analysis.performance.avg_r_multiple
            elif metric == 'profit_factor':
                actual_value = analysis.performance.profit_factor
            elif metric == 'min_trades':
                actual_value = analysis.match.total_matches
            
            if actual_value is not None:
                if actual_value >= threshold:
                    success_notes.append(f"✅ {metric}: {actual_value} >= {threshold}")
                else:
                    success_notes.append(f"❌ {metric}: {actual_value} < {threshold}")
        
        # Add success notes to recommendations
        analysis.recommendations.extend(success_notes)
        
        return analysis

class PatternValidator:
    """Validates and refines patterns over time"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
    
    def validate_existing_patterns(self, patterns: List[PatternDefinition],
                                  new_trades_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Re-validate existing patterns with new data
        
        Args:
            patterns: Existing patterns to validate
            new_trades_df: New trade data
            
        Returns:
            Validation results
        """
        results = {
            'validated': [],
            'invalidated': [],
            'needs_more_data': []
        }
        
        tester = HypothesisTester()
        
        for pattern in patterns:
            analysis = tester.evaluate_pattern(pattern, new_trades_df)
            
            if not analysis:
                results['needs_more_data'].append(pattern.name)
            elif analysis.confidence_score >= 70:
                results['validated'].append({
                    'name': pattern.name,
                    'confidence': analysis.confidence_score,
                    'performance': analysis.performance
                })
            else:
                results['invalidated'].append({
                    'name': pattern.name,
                    'reason': 'Low confidence',
                    'confidence': analysis.confidence_score
                })
        
        return results