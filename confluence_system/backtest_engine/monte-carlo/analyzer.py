"""
Enhanced Monte Carlo Analyzer with confluence integration
All calculations done in Python for maximum flexibility
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.service import DatabaseService

logger = logging.getLogger(__name__)

class MonteCarloAnalyzer:
    def __init__(self):
        """Initialize enhanced analyzer with database service"""
        self.db_service = DatabaseService()
        
        if not self.db_service.enabled:
            logger.warning("Database service not available - some features may not work")
        
        # Direct access to Supabase client
        self.client = self.db_service.client.client if self.db_service.enabled else None
    
    def analyze_batch(self, batch_id: str, export_csv: bool = False) -> Dict:
        """
        Perform comprehensive enhanced analysis on a batch including confluence metrics
        
        Args:
            batch_id: Batch UUID
            export_csv: Whether to export results to CSV
            
        Returns:
            Complete enhanced analysis results dictionary
        """
        logger.info(f"Starting enhanced analysis for batch {batch_id[:8]}...")
        
        # Load trades from database
        trades_df = self._load_trades(batch_id)
        
        if trades_df.empty:
            logger.warning(f"No trades found for batch {batch_id}")
            return {}
        
        # Perform comprehensive analysis
        results = {
            'batch_id': batch_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_trades': len(trades_df),
            
            # Core analysis
            'basic_stats': self._calculate_basic_stats(trades_df),
            'optimal_r_distribution': self._analyze_optimal_r_distribution(trades_df),
            'optimal_r_percentiles': self._calculate_percentiles(trades_df),
            'target_recommendations': self._generate_target_recommendations(trades_df),
            
            # Enhanced confluence analysis
            'confluence_analysis': self._analyze_confluence_performance(trades_df),
            'confluence_level_performance': self._analyze_by_confluence_level(trades_df),
            'confluence_source_analysis': self._analyze_by_confluence_sources(trades_df),
            
            # Traditional analysis enhanced with confluence
            'zone_performance': self._analyze_enhanced_zone_performance(trades_df),
            'time_analysis': self._analyze_time_patterns_with_confluence(trades_df),
            'direction_analysis': self._analyze_by_direction_with_confluence(trades_df),
            'exit_reason_analysis': self._analyze_exit_reasons_with_confluence(trades_df),
            
            # Advanced insights
            'confluence_insights': self._generate_confluence_insights(trades_df),
            'recommendations': self._generate_enhanced_recommendations(trades_df),
            'summary': self._create_enhanced_executive_summary(trades_df)
        }
        
        # Export enhanced analysis to CSV if requested
        if export_csv:
            self._export_enhanced_analysis_to_csv(trades_df, results, batch_id)
        
        logger.info(f"Enhanced analysis complete for batch {batch_id[:8]}...")
        return results
    
    def _load_trades(self, batch_id: str) -> pd.DataFrame:
        """Load trades from database and prepare enhanced DataFrame"""
        if not self.client:
            logger.error("Database client not available")
            return pd.DataFrame()
        
        try:
            response = self.client.table('monte_carlo_trades').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            
            # Convert timestamps to datetime
            for time_field in ['entry_time', 'exit_time']:
                if time_field in df.columns:
                    df[time_field] = pd.to_datetime(df[time_field])
            
            # Ensure confluence columns exist
            confluence_columns = [
                'confluence_level', 'confluence_score', 'confluence_count', 
                'confluence_sources', 'expected_edge', 'weighted_optimal_r',
                'has_high_confluence', 'has_multiple_sources'
            ]
            
            for col in confluence_columns:
                if col not in df.columns:
                    if col in ['has_high_confluence', 'has_multiple_sources']:
                        df[col] = False
                    elif col == 'confluence_sources':
                        df[col] = [[] for _ in range(len(df))]
                    else:
                        df[col] = 0
            
            logger.info(f"Loaded {len(df)} trades with enhanced confluence data")
            return df
            
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return pd.DataFrame()
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate enhanced basic statistics including confluence metrics"""
        stats = {
            # Traditional metrics
            'total_trades': len(df),
            'total_long': len(df[df['direction'] == 'LONG']),
            'total_short': len(df[df['direction'] == 'SHORT']),
            'win_rate': (df['actual_r_multiple'] > 0).mean() * 100,
            'avg_r_multiple': df['actual_r_multiple'].mean(),
            'avg_optimal_r': df['optimal_r_multiple'].mean(),
            'median_optimal_r': df['optimal_r_multiple'].median(),
            'max_optimal_r': df['optimal_r_multiple'].max(),
            'stop_hit_rate': (df['exit_reason'] == 'STOP_HIT').mean() * 100,
            'time_exit_rate': (df['exit_reason'] == 'TIME_EXIT').mean() * 100,
            
            # Enhanced confluence metrics
            'avg_confluence_score': df['confluence_score'].mean() if 'confluence_score' in df.columns else 0,
            'high_confluence_rate': (df['has_high_confluence']).mean() * 100 if 'has_high_confluence' in df.columns else 0,
            'multi_source_rate': (df['has_multiple_sources']).mean() * 100 if 'has_multiple_sources' in df.columns else 0,
            'weighted_avg_optimal_r': df['weighted_optimal_r'].mean() if 'weighted_optimal_r' in df.columns else 0,
        }
        
        # Zone distribution with confluence
        if 'zone_number' in df.columns:
            unique_zones = df['zone_number'].nunique()
            if unique_zones > 0:
                stats['trades_per_zone'] = len(df) / unique_zones
                stats['zones_used'] = unique_zones
        
        return stats
    
    def _analyze_confluence_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by confluence characteristics"""
        analysis = {}
        
        # Performance by high/low confluence
        if 'has_high_confluence' in df.columns:
            high_conf = df[df['has_high_confluence'] == True]
            low_conf = df[df['has_high_confluence'] == False]
            
            if len(high_conf) > 0 and len(low_conf) > 0:
                analysis['high_vs_low_confluence'] = {
                    'high_confluence_trades': len(high_conf),
                    'high_confluence_win_rate': (high_conf['actual_r_multiple'] > 0).mean() * 100,
                    'high_confluence_avg_r': high_conf['optimal_r_multiple'].mean(),
                    'low_confluence_trades': len(low_conf),
                    'low_confluence_win_rate': (low_conf['actual_r_multiple'] > 0).mean() * 100,
                    'low_confluence_avg_r': low_conf['optimal_r_multiple'].mean(),
                }
        
        # Performance by source count
        if 'confluence_count' in df.columns:
            source_performance = {}
            for count in sorted(df['confluence_count'].unique()):
                if pd.isna(count):
                    continue
                
                trades = df[df['confluence_count'] == count]
                if len(trades) >= 5:  # Minimum sample size
                    source_performance[int(count)] = {
                        'trade_count': len(trades),
                        'win_rate': (trades['actual_r_multiple'] > 0).mean() * 100,
                        'avg_optimal_r': trades['optimal_r_multiple'].mean(),
                        'avg_confluence_score': trades['confluence_score'].mean() if 'confluence_score' in trades.columns else 0
                    }
            
            analysis['by_source_count'] = source_performance
        
        return analysis
    
    def _analyze_by_confluence_level(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by confluence level (L1-L5)"""
        if 'confluence_level' not in df.columns:
            return {}
        
        level_analysis = {}
        
        for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
            level_trades = df[df['confluence_level'] == level]
            
            if len(level_trades) >= 3:  # Minimum sample
                level_analysis[level] = {
                    'trade_count': len(level_trades),
                    'percentage_of_trades': len(level_trades) / len(df) * 100,
                    'win_rate': (level_trades['actual_r_multiple'] > 0).mean() * 100,
                    'avg_optimal_r': level_trades['optimal_r_multiple'].mean(),
                    'avg_confluence_score': level_trades['confluence_score'].mean() if 'confluence_score' in level_trades.columns else 0,
                    'stop_hit_rate': (level_trades['exit_reason'] == 'STOP_HIT').mean() * 100
                }
        
        return level_analysis
    
    def _analyze_by_confluence_sources(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by specific confluence sources"""
        if 'confluence_sources' not in df.columns:
            return {}
        
        source_performance = {}
        
        # Flatten all sources and analyze performance
        all_sources = set()
        for sources_list in df['confluence_sources']:
            if isinstance(sources_list, list):
                all_sources.update(sources_list)
        
        for source in all_sources:
            # Find trades that include this source
            trades_with_source = df[df['confluence_sources'].apply(
                lambda x: source in x if isinstance(x, list) else False
            )]
            
            if len(trades_with_source) >= 5:  # Minimum sample size
                source_performance[source] = {
                    'trade_count': len(trades_with_source),
                    'win_rate': (trades_with_source['actual_r_multiple'] > 0).mean() * 100,
                    'avg_optimal_r': trades_with_source['optimal_r_multiple'].mean(),
                    'avg_score': trades_with_source['confluence_score'].mean() if 'confluence_score' in trades_with_source.columns else 0
                }
        
        # Sort by average optimal R
        sorted_sources = sorted(
            source_performance.items(),
            key=lambda x: x[1]['avg_optimal_r'],
            reverse=True
        )
        
        return dict(sorted_sources[:10])  # Top 10 sources
    
    def _analyze_enhanced_zone_performance(self, df: pd.DataFrame) -> Dict:
        """Enhanced zone analysis including confluence data"""
        if 'zone_number' not in df.columns:
            return {}
        
        zone_performance = {}
        
        for zone_num in sorted(df['zone_number'].unique()):
            if pd.isna(zone_num):
                continue
            
            zone_trades = df[df['zone_number'] == zone_num]
            
            performance = {
                'trade_count': len(zone_trades),
                'win_rate': (zone_trades['actual_r_multiple'] > 0).mean() * 100,
                'avg_optimal_r': zone_trades['optimal_r_multiple'].mean(),
                'stop_hit_rate': (zone_trades['exit_reason'] == 'STOP_HIT').mean() * 100,
            }
            
            # Add confluence metrics if available
            if 'confluence_score' in zone_trades.columns:
                performance['avg_confluence_score'] = zone_trades['confluence_score'].mean()
                performance['dominant_confluence_level'] = zone_trades['confluence_level'].mode().iloc[0] if len(zone_trades) > 0 else 'L1'
                performance['high_confluence_rate'] = (zone_trades['has_high_confluence']).mean() * 100 if 'has_high_confluence' in zone_trades.columns else 0
            
            zone_performance[int(zone_num)] = performance
        
        return zone_performance
    
    def _analyze_time_patterns_with_confluence(self, df: pd.DataFrame) -> Dict:
        """Time analysis enhanced with confluence data"""
        time_analysis = {}
        
        if 'entry_hour' in df.columns:
            hourly_performance = {}
            
            for hour in sorted(df['entry_hour'].unique()):
                if pd.isna(hour):
                    continue
                
                hour_trades = df[df['entry_hour'] == hour]
                
                performance = {
                    'trade_count': len(hour_trades),
                    'win_rate': (hour_trades['actual_r_multiple'] > 0).mean() * 100,
                    'avg_optimal_r': hour_trades['optimal_r_multiple'].mean(),
                }
                
                # Add confluence metrics
                if 'confluence_score' in hour_trades.columns:
                    performance['avg_confluence_score'] = hour_trades['confluence_score'].mean()
                    performance['high_confluence_rate'] = (hour_trades['has_high_confluence']).mean() * 100 if 'has_high_confluence' in hour_trades.columns else 0
                
                hourly_performance[int(hour)] = performance
            
            time_analysis['hourly_performance'] = hourly_performance
        
        return time_analysis
    
    def _analyze_by_direction_with_confluence(self, df: pd.DataFrame) -> Dict:
        """Direction analysis with confluence metrics"""
        direction_analysis = {}
        
        for direction in ['LONG', 'SHORT']:
            dir_trades = df[df['direction'] == direction]
            
            if len(dir_trades) > 0:
                analysis = {
                    'trade_count': len(dir_trades),
                    'win_rate': (dir_trades['actual_r_multiple'] > 0).mean() * 100,
                    'avg_optimal_r': dir_trades['optimal_r_multiple'].mean(),
                    'stop_hit_rate': (dir_trades['exit_reason'] == 'STOP_HIT').mean() * 100,
                }
                
                # Enhanced with confluence
                if 'confluence_score' in dir_trades.columns:
                    analysis['avg_confluence_score'] = dir_trades['confluence_score'].mean()
                    analysis['high_confluence_rate'] = (dir_trades['has_high_confluence']).mean() * 100 if 'has_high_confluence' in dir_trades.columns else 0
                
                direction_analysis[direction] = analysis
        
        return direction_analysis
    
    def _analyze_exit_reasons_with_confluence(self, df: pd.DataFrame) -> Dict:
        """Exit reason analysis with confluence context"""
        exit_analysis = {}
        
        for reason in df['exit_reason'].unique():
            if pd.isna(reason):
                continue
            
            reason_trades = df[df['exit_reason'] == reason]
            
            analysis = {
                'trade_count': len(reason_trades),
                'percentage': len(reason_trades) / len(df) * 100,
                'avg_optimal_r': reason_trades['optimal_r_multiple'].mean(),
            }
            
            # Add confluence context
            if 'confluence_score' in reason_trades.columns:
                analysis['avg_confluence_score'] = reason_trades['confluence_score'].mean()
                analysis['high_confluence_percentage'] = (reason_trades['has_high_confluence']).mean() * 100 if 'has_high_confluence' in reason_trades.columns else 0
            
            exit_analysis[reason] = analysis
        
        return exit_analysis
    
    def _generate_confluence_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate insights specific to confluence analysis"""
        insights = []
        
        if 'has_high_confluence' in df.columns:
            high_conf = df[df['has_high_confluence'] == True]
            if len(high_conf) > 0:
                high_conf_win_rate = (high_conf['actual_r_multiple'] > 0).mean() * 100
                overall_win_rate = (df['actual_r_multiple'] > 0).mean() * 100
                
                if high_conf_win_rate > overall_win_rate + 5:
                    insights.append(f"High confluence zones show {high_conf_win_rate:.1f}% win rate vs {overall_win_rate:.1f}% overall - focus on confluence score ≥8")
        
        if 'confluence_level' in df.columns:
            l4_l5_trades = df[df['confluence_level'].isin(['L4', 'L5'])]
            if len(l4_l5_trades) > 0:
                elite_avg_r = l4_l5_trades['optimal_r_multiple'].mean()
                overall_avg_r = df['optimal_r_multiple'].mean()
                
                if elite_avg_r > overall_avg_r * 1.2:
                    insights.append(f"L4/L5 zones deliver {elite_avg_r:.2f}R average vs {overall_avg_r:.2f}R overall - prioritize highest confluence zones")
        
        return insights
    
    def _generate_enhanced_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate recommendations including confluence insights"""
        recommendations = []
        
        # Traditional recommendations
        win_rate = (df['actual_r_multiple'] > 0).mean() * 100
        stop_rate = (df['exit_reason'] == 'STOP_HIT').mean() * 100
        
        if win_rate < 40:
            recommendations.append(f"Low win rate ({win_rate:.1f}%) - consider tighter entry criteria or better confluence filtering")
        
        if stop_rate > 60:
            recommendations.append(f"High stop rate ({stop_rate:.1f}%) - review stop placement strategy")
        
        # Confluence-specific recommendations
        if 'has_high_confluence' in df.columns:
            high_conf_percentage = (df['has_high_confluence']).mean() * 100
            
            if high_conf_percentage < 20:
                recommendations.append("Low percentage of high-confluence trades - consider raising minimum confluence score threshold")
        
        if 'confluence_level' in df.columns:
            l1_l2_percentage = (df['confluence_level'].isin(['L1', 'L2'])).mean() * 100
            
            if l1_l2_percentage > 50:
                recommendations.append("High percentage of low-confluence trades (L1/L2) - focus on L3+ zones for better performance")
        
        return recommendations
    
    def _create_enhanced_executive_summary(self, df: pd.DataFrame) -> Dict:
        """Create enhanced executive summary with confluence highlights"""
        summary = {
            'total_trades': len(df),
            'win_rate': (df['actual_r_multiple'] > 0).mean() * 100,
            'avg_optimal_r': df['optimal_r_multiple'].mean(),
            'best_zone': None,
            'best_confluence_level': None,
            'confluence_edge': None
        }
        
        # Find best performing zone
        if 'zone_number' in df.columns:
            zone_performance = df.groupby('zone_number')['optimal_r_multiple'].agg(['mean', 'count'])
            zone_performance = zone_performance[zone_performance['count'] >= 5]  # Min sample
            
            if not zone_performance.empty:
                best_zone = zone_performance['mean'].idxmax()
                summary['best_zone'] = int(best_zone)
        
        # Find best confluence level
        if 'confluence_level' in df.columns:
            level_performance = df.groupby('confluence_level')['optimal_r_multiple'].agg(['mean', 'count'])
            level_performance = level_performance[level_performance['count'] >= 5]
            
            if not level_performance.empty:
                best_level = level_performance['mean'].idxmax()
                summary['best_confluence_level'] = best_level
        
        # Calculate confluence edge
        if 'has_high_confluence' in df.columns:
            high_conf = df[df['has_high_confluence'] == True]
            low_conf = df[df['has_high_confluence'] == False]
            
            if len(high_conf) > 0 and len(low_conf) > 0:
                high_avg_r = high_conf['optimal_r_multiple'].mean()
                low_avg_r = low_conf['optimal_r_multiple'].mean()
                summary['confluence_edge'] = high_avg_r - low_avg_r
        
        return summary
    
    def _analyze_optimal_r_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze optimal R distribution"""
        optimal_rs = df['optimal_r_multiple']
        
        return {
            'mean': optimal_rs.mean(),
            'median': optimal_rs.median(),
            'std': optimal_rs.std(),
            'min': optimal_rs.min(),
            'max': optimal_rs.max(),
            'positive_rate': (optimal_rs > 0).mean() * 100,
            'above_2r_rate': (optimal_rs >= 2).mean() * 100,
            'above_5r_rate': (optimal_rs >= 5).mean() * 100,
        }
    
    def _calculate_percentiles(self, df: pd.DataFrame) -> Dict:
        """Calculate percentiles for optimal R"""
        optimal_rs = df['optimal_r_multiple']
        
        percentiles = {}
        for p in [10, 25, 50, 75, 90, 95]:
            percentiles[f'p{p}'] = optimal_rs.quantile(p/100)
        
        return percentiles
    
    def _generate_target_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Generate target recommendations based on R distribution"""
        percentiles = self._calculate_percentiles(df)
        
        recommendations = [
            {
                'strategy': 'Conservative',
                'target_r': percentiles['p25'],
                'success_rate': 75,
                'description': f"Target {percentiles['p25']:.1f}R (75% of trades exceed this)"
            },
            {
                'strategy': 'Moderate', 
                'target_r': percentiles['p50'],
                'success_rate': 50,
                'description': f"Target {percentiles['p50']:.1f}R (50% of trades exceed this)"
            },
            {
                'strategy': 'Aggressive',
                'target_r': percentiles['p75'],
                'success_rate': 25,
                'description': f"Target {percentiles['p75']:.1f}R (25% of trades exceed this)"
            }
        ]
        
        return recommendations
    
    def _export_enhanced_analysis_to_csv(self, trades_df: pd.DataFrame, results: Dict, batch_id: str):
        """Export enhanced analysis results to CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        try:
            # Export trades with confluence data
            trades_filename = f"enhanced_trades_{batch_id[:8]}_{timestamp}.csv"
            trades_df.to_csv(trades_filename, index=False)
            logger.info(f"Exported enhanced trades to {trades_filename}")
            
            # Export summary analysis
            summary_filename = f"analysis_summary_{batch_id[:8]}_{timestamp}.csv"
            summary_data = []
            
            # Flatten results for CSV export
            for key, value in results.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        summary_data.append({
                            'category': key,
                            'metric': sub_key,
                            'value': str(sub_value)
                        })
                else:
                    summary_data.append({
                        'category': 'general',
                        'metric': key,
                        'value': str(value)
                    })
            
            pd.DataFrame(summary_data).to_csv(summary_filename, index=False)
            logger.info(f"Exported analysis summary to {summary_filename}")
            
        except Exception as e:
            logger.error(f"Error exporting analysis to CSV: {e}")