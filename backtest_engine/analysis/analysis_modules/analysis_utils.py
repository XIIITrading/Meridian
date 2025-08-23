"""
Utility functions for analysis modules
Shared helper functions and recommendation generation
"""
from typing import List, Dict, Any
from dataclasses import asdict

def generate_recommendations(basic_stats: Any, 
                            confluence_analysis: Dict,
                            time_patterns: List,
                            edge_factors: List = None) -> List[str]:
    """
    Generate actionable recommendations based on analysis
    
    Args:
        basic_stats: Basic statistics object
        confluence_analysis: Confluence analysis results
        time_patterns: Time pattern results
        edge_factors: Optional edge factors
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check if basic_stats is a dataclass and convert if needed
    if hasattr(basic_stats, '__dataclass_fields__'):
        stats_dict = asdict(basic_stats)
    else:
        stats_dict = basic_stats if isinstance(basic_stats, dict) else {}
    
    # Win rate recommendations
    win_rate = stats_dict.get('win_rate', 0)
    if win_rate < 40:
        recommendations.append(
            "⚠️ Win rate below 40% - Review entry criteria and consider higher confluence zones"
        )
    elif win_rate > 60:
        recommendations.append(
            "✅ Strong win rate above 60% - Consider increasing position size or frequency"
        )
    
    # R-multiple recommendations
    if stats_dict.get('avg_r_multiple', 0) < 0:
        recommendations.append(
            "⚠️ Negative expectancy - Focus on improving entry timing and stop placement"
        )
    
    # Confluence recommendations
    if confluence_analysis:
        # Find best confluence level
        best_level = None
        best_r = -999
        
        for level, analysis in confluence_analysis.items():
            if hasattr(analysis, 'avg_r_multiple') and analysis.trade_count >= 5:
                if analysis.avg_r_multiple > best_r:
                    best_r = analysis.avg_r_multiple
                    best_level = analysis
        
        if best_level:
            recommendations.append(
                f"💡 Best performance in {best_level.level} zones "
                f"({best_level.win_rate}% win rate, {best_level.avg_r_multiple}R avg)"
            )
    
    # Time pattern recommendations
    for pattern in time_patterns:
        if hasattr(pattern, 'is_significant') and pattern.is_significant:
            if pattern.win_rate > win_rate * 1.2:
                recommendations.append(
                    f"📊 {pattern.pattern_name}: {pattern.win_rate}% win rate "
                    f"({pattern.occurrence_count} occurrences)"
                )
    
    # Edge factor recommendations
    if edge_factors:
        for edge in edge_factors[:3]:  # Top 3 edges
            if hasattr(edge, 'confidence') and edge.confidence > 70:
                recommendations.append(
                    f"🎯 {edge.factor_name}: {edge.improvement}% improvement "
                    f"(confidence: {edge.confidence}%)"
                )
    
    return recommendations

def format_analysis_summary(results: dict) -> str:
    """
    Format analysis results into a readable summary
    
    Args:
        results: Complete analysis results
        
    Returns:
        Formatted string summary
    """
    lines = []
    lines.append("="*60)
    lines.append("ANALYSIS SUMMARY")
    lines.append("="*60)
    
    # Basic stats
    if 'basic_stats' in results:
        stats = results['basic_stats']
        if hasattr(stats, '__dict__'):
            lines.append(f"\nTotal Trades: {stats.total_trades}")
            lines.append(f"Win Rate: {stats.win_rate}%")
            lines.append(f"Avg R-Multiple: {stats.avg_r_multiple}")
            lines.append(f"Total R: {stats.total_r}")
            lines.append(f"Profit Factor: {stats.profit_factor}")
    
    # Recommendations
    if 'recommendations' in results:
        lines.append("\nKey Recommendations:")
        for rec in results['recommendations']:
            lines.append(f"  {rec}")
    
    return "\n".join(lines)