"""
Pattern Recognition Orchestrator
Coordinates pattern discovery and validation
Supports both automatic discovery and user-defined patterns
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .pattern_modules.base_pattern import BasePatternEngine
from .pattern_modules.pattern_models import (
    PatternDefinition, PatternAnalysis, UserPatternRequest,
    PatternRule, PatternSource
)

# Discovery engines
from .pattern_modules.discovery.confluence_discovery import ConfluenceDiscoveryEngine
from .pattern_modules.discovery.failure_discovery import FailureDiscoveryEngine

# Validation engines
from .pattern_modules.validation.hypothesis_tester import HypothesisTester
from .pattern_modules.validation.hypothesis_tester import PatternValidator

# Support modules
from .pattern_modules.pattern_library import PatternLibrary
from .pattern_modules.pattern_scorer import PatternScorer
from .pattern_modules.pattern_persistence import PatternPersistence

logger = logging.getLogger(__name__)

class PatternRecognizer:
    """
    Main orchestrator for pattern recognition
    Manages both discovery and validation of patterns
    """
    
    def __init__(self, storage_manager):
        """
        Initialize pattern recognizer with all engines
        
        Args:
            storage_manager: BacktestStorageManager instance
        """
        self.storage = storage_manager
        
        # Initialize discovery engines
        self.discovery_engines = [
            ConfluenceDiscoveryEngine(),
            FailureDiscoveryEngine(),
            # Add more discovery engines as created
        ]
        
        # Initialize validation components
        self.hypothesis_tester = HypothesisTester()
        self.validator = PatternValidator(storage_manager)
        
        # Initialize support modules
        self.library = PatternLibrary(storage_manager)
        self.scorer = PatternScorer()
        self.persistence = PatternPersistence(storage_manager)
        
        logger.info(f"Pattern Recognizer initialized with {len(self.discovery_engines)} discovery engines")
    
    def discover_patterns(self, min_confidence: float = 60, 
                         save: bool = True) -> Dict[str, Any]:
        """
        Automatically discover patterns in trading data
        
        Args:
            min_confidence: Minimum confidence threshold
            save: Whether to save discovered patterns
            
        Returns:
            Dictionary with discovered patterns and analysis
        """
        logger.info("Starting automatic pattern discovery")
        
        # Get all trades
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            logger.warning("No trades available for pattern discovery")
            return {}
        
        discovered_patterns = []
        pattern_analyses = []
        
        # Run each discovery engine
        for engine in self.discovery_engines:
            logger.info(f"Running {engine.get_engine_name()}")
            
            # Discover patterns
            patterns = engine.identify_patterns(trades_df)
            
            # Evaluate each pattern
            for pattern in patterns:
                analysis = engine.evaluate_pattern(pattern, trades_df)
                
                if analysis and analysis.confidence_score >= min_confidence:
                    discovered_patterns.append(pattern)
                    pattern_analyses.append(analysis)
                    self.library.add_pattern(pattern, analysis)
        
        # Rank patterns
        ranked_patterns = self.scorer.rank_patterns(pattern_analyses)
        
        # Generate rules from top patterns
        rules = self._generate_rules_from_patterns(ranked_patterns[:5])
        
        results = {
            'discovery_date': datetime.now().isoformat(),
            'total_patterns_discovered': len(discovered_patterns),
            'high_confidence_patterns': [
                p for p in pattern_analyses if p.confidence_score >= 80
            ],
            'patterns': ranked_patterns,
            'rules': rules,
            'summary': self._generate_discovery_summary(pattern_analyses)
        }
        
        # Save if requested
        if save:
            self.persistence.save_patterns(discovered_patterns, pattern_analyses)
        
        return results
    
    def test_user_pattern(self, pattern_request: UserPatternRequest) -> PatternAnalysis:
        """
        Test a user-defined pattern hypothesis
        
        Args:
            pattern_request: User's pattern definition
            
        Returns:
            Analysis of the pattern
        """
        logger.info(f"Testing user pattern: {pattern_request.name}")
        
        trades_df = self.storage.get_all_trades()
        
        if trades_df.empty:
            logger.warning("No trades available for pattern testing")
            return None
        
        # Test the pattern
        analysis = self.hypothesis_tester.test_user_pattern(pattern_request, trades_df)
        
        if analysis:
            # Add to library
            self.library.add_pattern(analysis.definition, analysis)
            
            # Save to database
            self.persistence.save_patterns([analysis.definition], [analysis])
        
        return analysis
    
    def validate_existing_patterns(self) -> Dict[str, Any]:
        """
        Re-validate all existing patterns with latest data
        
        Returns:
            Validation results
        """
        logger.info("Validating existing patterns")
        
        trades_df = self.storage.get_all_trades()
        
        # Get all patterns from library
        all_patterns = list(self.library.patterns.values())
        
        # Validate
        results = self.validator.validate_existing_patterns(all_patterns, trades_df)
        
        return results
    
    def get_active_rules(self) -> List[PatternRule]:
        """
        Get currently active trading rules
        
        Returns:
            List of active rules
        """
        return [rule for rule in self.library.rules if rule.active]
    
    def _generate_rules_from_patterns(self, 
                                     patterns: List[PatternAnalysis]) -> List[PatternRule]:
        """Generate actionable rules from patterns"""
        rules = []
        
        for i, pattern in enumerate(patterns[:5]):  # Top 5 patterns
            if pattern.confidence_score >= 70:
                rule = PatternRule(
                    rule_id=f"auto_rule_{i+1}",
                    pattern_ids=[pattern.definition.pattern_id],
                    name=f"Rule: {pattern.definition.name}",
                    conditions_text=self._format_conditions(pattern.definition.conditions),
                    expected_win_rate=pattern.performance.win_rate,
                    expected_r_multiple=pattern.performance.avg_r_multiple,
                    confidence=pattern.confidence_score,
                    min_sample_size=pattern.match.total_matches
                )
                rules.append(rule)
                self.library.rules.append(rule)
        
        return rules
    
    def _format_conditions(self, conditions) -> str:
        """Format conditions as readable text"""
        texts = []
        for cond in conditions:
            texts.append(cond.description or 
                        f"{cond.field} {cond.operator} {cond.value}")
        return " AND ".join(texts)
    
    def _generate_discovery_summary(self, 
                                   analyses: List[PatternAnalysis]) -> Dict[str, Any]:
        """Generate summary of discovered patterns"""
        if not analyses:
            return {}
        
        return {
            'total_patterns': len(analyses),
            'avg_confidence': round(
                sum(a.confidence_score for a in analyses) / len(analyses), 1
            ),
            'best_pattern': max(analyses, key=lambda x: x.strength_score).definition.name
                           if analyses else None,
            'pattern_types': {
                'confluence': len([a for a in analyses 
                                 if a.definition.pattern_type.value == 'confluence']),
                'failure': len([a for a in analyses 
                              if a.definition.pattern_type.value == 'failure']),
                'combination': len([a for a in analyses 
                                  if a.definition.pattern_type.value == 'combination'])
            }
        }
    
    def print_pattern_summary(self, analysis: PatternAnalysis):
        """Print formatted summary of a pattern analysis"""
        print("\n" + "="*60)
        print(f"PATTERN: {analysis.definition.name}")
        print("="*60)
        
        print(f"\nSource: {analysis.definition.source.value}")
        print(f"Type: {analysis.definition.pattern_type.value}")
        
        print("\nConditions:")
        for cond in analysis.definition.conditions:
            print(f"  - {cond.description or f'{cond.field} {cond.operator} {cond.value}'}")
        
        print(f"\nPerformance:")
        print(f"  Matches: {analysis.match.total_matches} / {analysis.match.total_opportunities}")
        print(f"  Win Rate: {analysis.performance.win_rate}%")
        print(f"  Avg R: {analysis.performance.avg_r_multiple}")
        print(f"  Profit Factor: {analysis.performance.profit_factor}")
        
        print(f"\nScores:")
        print(f"  Confidence: {analysis.confidence_score}%")
        print(f"  Strength: {analysis.strength_score}%")
        
        print(f"\nRecommendations:")
        for rec in analysis.recommendations:
            print(f"  {rec}")

# Example usage
if __name__ == "__main__":
    from data.supabase_client import BacktestSupabaseClient
    from data.backtest_storage_manager import BacktestStorageManager
    
    # Initialize
    client = BacktestSupabaseClient()
    storage = BacktestStorageManager(client)
    recognizer = PatternRecognizer(storage)
    
    print("\n" + "="*60)
    print("PATTERN RECOGNITION ENGINE")
    print("="*60)
    
    # 1. Discover patterns automatically
    print("\n[1] Running Automatic Pattern Discovery...")
    discovered = recognizer.discover_patterns(min_confidence=60)
    
    if discovered:
        print(f"\n✅ Discovered {discovered['total_patterns_discovered']} patterns")
        
        for pattern in discovered['patterns'][:3]:  # Top 3
            recognizer.print_pattern_summary(pattern)
    
    # 2. Test a user-defined pattern
    print("\n[2] Testing User-Defined Pattern...")
    
    user_pattern = UserPatternRequest(
        name="Morning High Confluence",
        hypothesis="L4+ zones in first hour have higher win rate",
        conditions={
            'zone_confluence_level': ['L4', 'L5'],
            'hour': {'operator': 'between', 'value': [14, 15]}  # 9:30-10:30 ET
        },
        success_criteria={'win_rate': 65, 'min_trades': 5}
    )
    
    result = recognizer.test_user_pattern(user_pattern)
    
    if result:
        recognizer.print_pattern_summary(result)
    
    # 3. Get active rules
    print("\n[3] Active Trading Rules:")
    rules = recognizer.get_active_rules()
    
    for rule in rules:
        print(f"\n📋 {rule.name}")
        print(f"   Conditions: {rule.conditions_text}")
        print(f"   Expected: {rule.expected_win_rate}% WR, {rule.expected_r_multiple}R")
        print(f"   Confidence: {rule.confidence}%")