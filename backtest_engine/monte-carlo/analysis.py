"""
Complete analysis functions for Monte Carlo results
All calculations done in Python, database is storage only
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from supabase import create_client
from datetime import datetime

from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class MonteCarloAnalyzer:
    def __init__(self):
        """Initialize analyzer with Supabase connection"""
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def analyze_batch(self, batch_id: str, export_csv: bool = False) -> Dict:
        """
        Perform comprehensive analysis on a batch
        All calculations done in Python
        
        Args:
            batch_id: Batch UUID
            export_csv: Whether to export results to CSV
            
        Returns:
            Complete analysis results dictionary
        """
        # Load trades from database (raw data only)
        trades_df = self._load_trades(batch_id)
        
        if trades_df.empty:
            logger.warning(f"No trades found for batch {batch_id}")
            return {}
        
        # Perform all analyses in Python
        results = {
            'batch_id': batch_id,
            'total_trades': len(trades_df),
            'basic_stats': self._calculate_basic_stats(trades_df),
            'optimal_r_distribution': self._analyze_optimal_r_distribution(trades_df),
            'optimal_r_percentiles': self._calculate_percentiles(trades_df),
            'target_recommendations': self._generate_target_recommendations(trades_df),
            'zone_performance': self._analyze_zone_performance(trades_df),
            'confluence_analysis': self._analyze_by_confluence(trades_df),
            'time_analysis': self._analyze_time_patterns(trades_df),
            'direction_analysis': self._analyze_by_direction(trades_df),
            'exit_reason_analysis': self._analyze_exit_reasons(trades_df),
            'recommendations': self._generate_recommendations(trades_df),
            'summary': self._create_executive_summary(trades_df)
        }
        
        # Export to CSV if requested
        if export_csv:
            self._export_analysis_to_csv(trades_df, results, batch_id)
        
        return results
    
    def _load_trades(self, batch_id: str) -> pd.DataFrame:
        """Load trades from database and prepare DataFrame"""
        try:
            response = self.client.table('monte_carlo_trades').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            
            # Convert timestamps to datetime
            if 'entry_time' in df.columns:
                df['entry_time'] = pd.to_datetime(df['entry_time'])
            if 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return pd.DataFrame()
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate all basic statistics in Python"""
        
        # Calculate trades_per_zone safely
        trades_per_zone = 0
        if 'zone_number' in df.columns:
            unique_zones = df['zone_number'].nunique()
            if unique_zones > 0:
                trades_per_zone = len(df) / unique_zones
        
        stats = {
            'total_trades': len(df),
            'total_long': len(df[df['direction'] == 'LONG']),
            'total_short': len(df[df['direction'] == 'SHORT']),
            
            # Win rates
            'win_rate': (df['actual_r_multiple'] > 0).mean() * 100,
            'long_win_rate': (df[df['direction'] == 'LONG']['actual_r_multiple'] > 0).mean() * 100 if len(df[df['direction'] == 'LONG']) > 0 else 0,
            'short_win_rate': (df[df['direction'] == 'SHORT']['actual_r_multiple'] > 0).mean() * 100 if len(df[df['direction'] == 'SHORT']) > 0 else 0,
            
            # R-multiple statistics
            'avg_actual_r': df['actual_r_multiple'].mean(),
            'avg_optimal_r': df['optimal_r_multiple'].mean(),
            'median_optimal_r': df['optimal_r_multiple'].median(),
            'std_optimal_r': df['optimal_r_multiple'].std(),
            'max_optimal_r': df['optimal_r_multiple'].max(),
            'min_optimal_r': df['optimal_r_multiple'].min(),
            
            # Exit reasons
            'stop_hit_rate': (df['exit_reason'] == 'STOP_HIT').mean() * 100,
            'time_exit_rate': (df['exit_reason'] == 'TIME_EXIT').mean() * 100,
            
            # Time metrics
            'avg_time_in_trade': df['time_in_trade_minutes'].mean(),
            'median_time_in_trade': df['time_in_trade_minutes'].median(),
            
            # Zone metrics
            'avg_zone_size': df['zone_size'].mean() if 'zone_size' in df.columns else 0,
            'trades_per_zone': len(df) / df['zone_number'].nunique() if 'zone_number' in df.columns and df['zone_number'].nunique() > 0 else 0
        }
        
        # Round all values
        for key, value in stats.items():
            if isinstance(value, float):
                stats[key] = round(value, 2)
        
        return stats
    
    def _calculate_percentiles(self, df: pd.DataFrame) -> Dict:
        """Calculate all percentiles for optimal R"""
        percentiles_to_calc = [1, 5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95, 99]
        percentiles = {}
        
        for p in percentiles_to_calc:
            percentiles[f'p{p}'] = round(df['optimal_r_multiple'].quantile(p/100), 2)
        
        return percentiles
    
    def _analyze_optimal_r_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze the distribution of optimal R values"""
        # Create bins
        bins = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 10, 100]
        labels = ['0-0.5R', '0.5-1R', '1-1.5R', '1.5-2R', '2-2.5R', 
                 '2.5-3R', '3-3.5R', '3.5-4R', '4-5R', '5-10R', '10R+']
        
        df['optimal_r_bin'] = pd.cut(df['optimal_r_multiple'], bins=bins, labels=labels)
        
        # Calculate distribution
        distribution = []
        for bin_label in labels:
            bin_trades = df[df['optimal_r_bin'] == bin_label]
            if len(bin_trades) > 0:
                distribution.append({
                    'range': bin_label,
                    'count': len(bin_trades),
                    'percentage': round(len(bin_trades) / len(df) * 100, 2),
                    'avg_actual_r': round(bin_trades['actual_r_multiple'].mean(), 2),
                    'win_rate': round((bin_trades['actual_r_multiple'] > 0).mean() * 100, 2),
                    'stop_rate': round((bin_trades['exit_reason'] == 'STOP_HIT').mean() * 100, 2)
                })
        
        return {
            'distribution': distribution,
            'cumulative': self._calculate_cumulative_distribution(df)
        }
    
    def _calculate_cumulative_distribution(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate cumulative distribution for optimal R"""
        thresholds = [0.5, 1, 1.5, 2, 2.5, 3, 4, 5]
        cumulative = []
        
        for threshold in thresholds:
            pct_above = (df['optimal_r_multiple'] >= threshold).mean() * 100
            cumulative.append({
                'threshold': f'{threshold}R',
                'percent_achieving': round(pct_above, 2)
            })
        
        return cumulative
    
    def _generate_target_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Generate specific target recommendations based on data"""
        percentiles = self._calculate_percentiles(df)
        
        recommendations = [
            {
                'strategy': 'Conservative',
                'target_r': percentiles['p50'],
                'achievable_rate': 50,
                'description': f"Target {percentiles['p50']}R - achievable in 50% of trades",
                'suitable_for': 'Consistent income, lower drawdown tolerance'
            },
            {
                'strategy': 'Moderate',
                'target_r': percentiles['p75'],
                'achievable_rate': 25,
                'description': f"Target {percentiles['p75']}R - achievable in 25% of trades",
                'suitable_for': 'Balanced risk/reward, standard account'
            },
            {
                'strategy': 'Aggressive',
                'target_r': percentiles['p90'],
                'achievable_rate': 10,
                'description': f"Target {percentiles['p90']}R - achievable in 10% of trades",
                'suitable_for': 'High risk tolerance, small position sizing'
            },
            {
                'strategy': 'Scaled Exit',
                'target_r': f"{percentiles['p50']}/{percentiles['p75']}/{percentiles['p90']}",
                'achievable_rate': 'Variable',
                'description': f"Scale out at {percentiles['p50']}R, {percentiles['p75']}R, {percentiles['p90']}R",
                'suitable_for': 'Professional traders, larger positions'
            }
        ]
        
        return recommendations
    
    def _analyze_zone_performance(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze performance by individual zone"""
        if 'zone_number' not in df.columns:
            return []
        
        zone_stats = []
        for zone_num in sorted(df['zone_number'].unique()):
            zone_df = df[df['zone_number'] == zone_num]
            
            zone_stats.append({
                'zone_number': zone_num,
                'trade_count': len(zone_df),
                'avg_optimal_r': round(zone_df['optimal_r_multiple'].mean(), 2),
                'median_optimal_r': round(zone_df['optimal_r_multiple'].median(), 2),
                'p75_optimal_r': round(zone_df['optimal_r_multiple'].quantile(0.75), 2),
                'max_optimal_r': round(zone_df['optimal_r_multiple'].max(), 2),
                'win_rate': round((zone_df['actual_r_multiple'] > 0).mean() * 100, 2),
                'avg_zone_size': round(zone_df['zone_size'].mean(), 4) if 'zone_size' in zone_df.columns else 0,
                'stop_hit_rate': round((zone_df['exit_reason'] == 'STOP_HIT').mean() * 100, 2)
            })
        
        # Sort by average optimal R
        zone_stats.sort(key=lambda x: x['avg_optimal_r'], reverse=True)
        
        return zone_stats
    
    def _analyze_by_confluence(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by confluence level"""
        if 'zone_confluence_level' not in df.columns:
            return {}
        
        confluence_stats = {}
        for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
            level_df = df[df['zone_confluence_level'] == level]
            
            if len(level_df) > 0:
                confluence_stats[level] = {
                    'trade_count': len(level_df),
                    'percentage_of_trades': round(len(level_df) / len(df) * 100, 2),
                    'avg_optimal_r': round(level_df['optimal_r_multiple'].mean(), 2),
                    'median_optimal_r': round(level_df['optimal_r_multiple'].median(), 2),
                    'p75_optimal_r': round(level_df['optimal_r_multiple'].quantile(0.75), 2),
                    'win_rate': round((level_df['actual_r_multiple'] > 0).mean() * 100, 2),
                    'stop_hit_rate': round((level_df['exit_reason'] == 'STOP_HIT').mean() * 100, 2),
                    'avg_time_in_trade': round(level_df['time_in_trade_minutes'].mean(), 1)
                }
        
        return confluence_stats
    
    def _analyze_time_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns by time of day"""
        time_analysis = {
            'by_hour': {},
            'by_session': {}
        }
        
        # By hour
        for hour in sorted(df['entry_hour'].unique()):
            hour_df = df[df['entry_hour'] == hour]
            time_analysis['by_hour'][f'{hour:02d}:00'] = {
                'trade_count': len(hour_df),
                'avg_optimal_r': round(hour_df['optimal_r_multiple'].mean(), 2),
                'win_rate': round((hour_df['actual_r_multiple'] > 0).mean() * 100, 2),
                'stop_hit_rate': round((hour_df['exit_reason'] == 'STOP_HIT').mean() * 100, 2)
            }
        
        # By session (morning, midday, afternoon)
        morning = df[df['entry_hour'].between(13, 15)]  # 9:30-11:30 ET
        midday = df[df['entry_hour'].between(15, 17)]   # 11:30-1:30 ET
        afternoon = df[df['entry_hour'].between(17, 19)] # 1:30-3:30 ET
        
        for session_name, session_df in [('Morning', morning), ('Midday', midday), ('Afternoon', afternoon)]:
            if len(session_df) > 0:
                time_analysis['by_session'][session_name] = {
                    'trade_count': len(session_df),
                    'percentage': round(len(session_df) / len(df) * 100, 2),
                    'avg_optimal_r': round(session_df['optimal_r_multiple'].mean(), 2),
                    'median_optimal_r': round(session_df['optimal_r_multiple'].median(), 2),
                    'win_rate': round((session_df['actual_r_multiple'] > 0).mean() * 100, 2)
                }
        
        return time_analysis
    
    def _analyze_by_direction(self, df: pd.DataFrame) -> Dict:
        """Analyze long vs short performance"""
        direction_stats = {}
        
        for direction in ['LONG', 'SHORT']:
            dir_df = df[df['direction'] == direction]
            
            if len(dir_df) > 0:
                direction_stats[direction] = {
                    'trade_count': len(dir_df),
                    'percentage': round(len(dir_df) / len(df) * 100, 2),
                    'avg_optimal_r': round(dir_df['optimal_r_multiple'].mean(), 2),
                    'median_optimal_r': round(dir_df['optimal_r_multiple'].median(), 2),
                    'p75_optimal_r': round(dir_df['optimal_r_multiple'].quantile(0.75), 2),
                    'win_rate': round((dir_df['actual_r_multiple'] > 0).mean() * 100, 2),
                    'stop_hit_rate': round((dir_df['exit_reason'] == 'STOP_HIT').mean() * 100, 2),
                    'avg_time_in_trade': round(dir_df['time_in_trade_minutes'].mean(), 1)
                }
        
        return direction_stats
    
    def _analyze_exit_reasons(self, df: pd.DataFrame) -> Dict:
        """Analyze trades by exit reason"""
        exit_stats = {}
        
        for reason in df['exit_reason'].unique():
            reason_df = df[df['exit_reason'] == reason]
            
            exit_stats[reason] = {
                'trade_count': len(reason_df),
                'percentage': round(len(reason_df) / len(df) * 100, 2),
                'avg_optimal_r': round(reason_df['optimal_r_multiple'].mean(), 2),
                'median_optimal_r': round(reason_df['optimal_r_multiple'].median(), 2),
                'avg_actual_r': round(reason_df['actual_r_multiple'].mean(), 2)
            }
        
        return exit_stats
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on all analyses"""
        recommendations = []
        
        # Optimal R analysis
        percentiles = self._calculate_percentiles(df)
        
        # Primary target recommendation
        if percentiles['p50'] >= 2:
            recommendations.append(
                f"✅ Strong profit potential: Median optimal R of {percentiles['p50']} suggests 2R+ targets are reasonable"
            )
        elif percentiles['p50'] >= 1.5:
            recommendations.append(
                f"📊 Moderate profit potential: Target {percentiles['p50']}R for 50% win rate"
            )
        else:
            recommendations.append(
                f"⚠️ Limited profit potential: Consider tighter stops or better entry timing (median optimal R only {percentiles['p50']})"
            )
        
        # Stop analysis
        stop_rate = (df['exit_reason'] == 'STOP_HIT').mean() * 100
        if stop_rate > 60:
            recommendations.append(
                f"⚠️ High stop rate ({stop_rate:.1f}%): Consider wider stops or waiting for better zone tests"
            )
        elif stop_rate < 40:
            recommendations.append(
                f"✅ Good stop placement: Only {stop_rate:.1f}% hit stops"
            )
        
        # Confluence analysis
        if 'zone_confluence_level' in df.columns:
            # Find best performing confluence level
            best_level = None
            best_median = 0
            
            for level in ['L5', 'L4', 'L3', 'L2', 'L1']:
                level_df = df[df['zone_confluence_level'] == level]
                if len(level_df) >= 5:  # Minimum sample
                    median_r = level_df['optimal_r_multiple'].median()
                    if median_r > best_median:
                        best_median = median_r
                        best_level = level
            
            if best_level:
                recommendations.append(
                    f"🎯 Focus on {best_level} zones: Best median optimal R of {best_median:.2f}"
                )
        
        # Time analysis
        if 'entry_hour' in df.columns:
            morning = df[df['entry_hour'].between(13, 15)]
            afternoon = df[df['entry_hour'].between(17, 19)]
            
            if len(morning) > 10 and len(afternoon) > 10:
                morning_median = morning['optimal_r_multiple'].median()
                afternoon_median = afternoon['optimal_r_multiple'].median()
                
                if morning_median > afternoon_median * 1.2:
                    recommendations.append(
                        f"⏰ Morning session offers better opportunities: {morning_median:.2f}R vs {afternoon_median:.2f}R median"
                    )
        
        # Scaling recommendation
        if percentiles['p75'] >= percentiles['p50'] * 1.5:
            recommendations.append(
                f"📈 Consider scaling: 50% out at {percentiles['p50']}R, remainder at {percentiles['p75']}R"
            )
        
        return recommendations
    
    def _create_executive_summary(self, df: pd.DataFrame) -> Dict:
        """Create executive summary of findings"""
        percentiles = self._calculate_percentiles(df)
        
        return {
            'total_opportunities': len(df),
            'median_profit_potential': f"{percentiles['p50']}R",
            'conservative_target': f"{percentiles['p50']}R",
            'moderate_target': f"{percentiles['p75']}R", 
            'aggressive_target': f"{percentiles['p90']}R",
            'win_rate_at_median': round((df['optimal_r_multiple'] >= percentiles['p50']).mean() * 100, 1),
            'stop_hit_rate': round((df['exit_reason'] == 'STOP_HIT').mean() * 100, 1),
            'best_zone': self._find_best_zone(df),
            'best_confluence': self._find_best_confluence(df),
            'key_finding': self._generate_key_finding(df, percentiles)
        }
    
    def _find_best_zone(self, df: pd.DataFrame) -> str:
        """Find the best performing zone"""
        if 'zone_number' not in df.columns:
            return "N/A"
        
        best_zone = df.groupby('zone_number')['optimal_r_multiple'].median().idxmax()
        best_median = df.groupby('zone_number')['optimal_r_multiple'].median().max()
        
        return f"Zone {best_zone} ({best_median:.2f}R median)"
    
    def _find_best_confluence(self, df: pd.DataFrame) -> str:
        """Find the best performing confluence level"""
        if 'zone_confluence_level' not in df.columns:
            return "N/A"
        
        confluence_medians = df.groupby('zone_confluence_level')['optimal_r_multiple'].median()
        if not confluence_medians.empty:
            best = confluence_medians.idxmax()
            best_value = confluence_medians.max()
            return f"{best} ({best_value:.2f}R median)"
        
        return "N/A"
    
    def _generate_key_finding(self, df: pd.DataFrame, percentiles: Dict) -> str:
        """Generate the most important finding"""
        if percentiles['p75'] >= 3:
            return "Excellent profit potential - 25% of trades can achieve 3R+"
        elif percentiles['p50'] >= 2:
            return "Strong profit potential - 50% of trades can achieve 2R+"
        elif percentiles['p50'] >= 1.5:
            return "Moderate profit potential - Consider 1.5R primary target"
        else:
            return "Limited profit potential - Focus on high probability setups"
    
    def _export_analysis_to_csv(self, df: pd.DataFrame, results: Dict, batch_id: str):
        """Export detailed analysis to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export raw trades
        df.to_csv(f"output/trades_{batch_id[:8]}_{timestamp}.csv", index=False)
        
        # Export summary
        summary_df = pd.DataFrame([results['basic_stats']])
        summary_df.to_csv(f"output/summary_{batch_id[:8]}_{timestamp}.csv", index=False)
        
        # Export percentiles
        percentiles_df = pd.DataFrame([results['optimal_r_percentiles']])
        percentiles_df.to_csv(f"output/percentiles_{batch_id[:8]}_{timestamp}.csv", index=False)
        
        logger.info(f"Analysis exported to CSV files with timestamp {timestamp}")
    
    def print_analysis_report(self, results: Dict):
        """Print formatted analysis report to console"""
        print("\n" + "="*80)
        print("MONTE CARLO ANALYSIS REPORT")
        print("="*80)
        
        # Executive Summary
        summary = results.get('summary', {})
        print("\n📊 EXECUTIVE SUMMARY")
        print("-"*40)
        print(f"Total Opportunities: {summary.get('total_opportunities', 0)}")
        print(f"Median Profit Potential: {summary.get('median_profit_potential', 'N/A')}")
        print(f"Stop Hit Rate: {summary.get('stop_hit_rate', 0)}%")
        print(f"Best Zone: {summary.get('best_zone', 'N/A')}")
        print(f"Best Confluence: {summary.get('best_confluence', 'N/A')}")
        print(f"Key Finding: {summary.get('key_finding', 'N/A')}")
        
        # Target Recommendations
        print("\n🎯 RECOMMENDED TARGETS")
        print("-"*40)
        for rec in results.get('target_recommendations', []):
            print(f"{rec['strategy']}: {rec['target_r']}R ({rec['achievable_rate']}% achievable)")
            print(f"  {rec['description']}")
        
        # Optimal R Distribution
        print("\n📈 OPTIMAL R DISTRIBUTION")
        print("-"*40)
        percentiles = results.get('optimal_r_percentiles', {})
        key_percentiles = ['p10', 'p25', 'p50', 'p75', 'p90', 'p95']
        for p in key_percentiles:
            if p in percentiles:
                achieving = 100 - int(p[1:])
                print(f"{p}: {percentiles[p]}R ({achieving}% of trades exceed this)")
        
        # Zone Performance
        print("\n🎲 ZONE PERFORMANCE")
        print("-"*40)
        for zone in results.get('zone_performance', [])[:3]:  # Top 3 zones
            print(f"Zone {zone['zone_number']}: {zone['avg_optimal_r']}R avg, "
                  f"{zone['median_optimal_r']}R median ({zone['trade_count']} trades)")
        
        # Recommendations
        print("\n💡 KEY RECOMMENDATIONS")
        print("-"*40)
        for rec in results.get('recommendations', []):
            print(f"  {rec}")
        
        print("\n" + "="*80)