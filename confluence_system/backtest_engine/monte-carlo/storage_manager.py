"""
Enhanced Supabase storage manager for Monte Carlo results
Integrates with confluence_system database module
"""
import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.service import DatabaseService
from config import BATCH_SIZE

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        """Initialize with confluence_system database service"""
        self.db_service = DatabaseService()
        
        if not self.db_service.enabled:
            logger.warning("Database service not enabled")
            raise RuntimeError("Database service required for storage operations")
        
        # Direct access to Supabase client for Monte Carlo tables
        self.client = self.db_service.client.client
    
    def save_results(self, symbol: str, start_date: str, end_date: str,
                trades_df: pd.DataFrame, metadata: Dict = None) -> Optional[str]:
        """
        Save enhanced Monte Carlo results to Supabase
        
        Args:
            symbol: Trading symbol
            start_date: Simulation start date
            end_date: Simulation end date  
            trades_df: DataFrame of enhanced trade results with confluence data
            metadata: Additional metadata including confluence info
            
        Returns:
            Batch ID if successful, None otherwise
        """
        try:
            # Create batch record
            batch_id = str(uuid.uuid4())
            
            # Enhanced batch record with confluence metadata
            batch_record = {
                'batch_id': batch_id,
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'total_trades': len(trades_df),
                'zones_count': metadata.get('zones_count', 0) if metadata else 0,
                'bars_count': metadata.get('bars_count', 0) if metadata else 0,
                'runtime_seconds': metadata.get('runtime_seconds', 0) if metadata else 0,
                'confluence_enabled': metadata.get('confluence_enabled', True) if metadata else True,
                'single_day': metadata.get('single_day', False) if metadata else False,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Save batch metadata
            result = self.client.table('monte_carlo_batches').insert(batch_record).execute()
            
            if not result.data:
                logger.error("Failed to create batch record")
                return None
            
            logger.info(f"Created batch {batch_id[:8]}... with confluence data")
            
            # Prepare enhanced trade data
            trades_data = self._prepare_trade_data(trades_df, batch_id, symbol)
            
            # Save trades in batches
            total_saved = self._save_trades_in_batches(trades_data)
            
            if total_saved == len(trades_data):
                logger.info(f"Successfully saved {total_saved} enhanced trades to batch {batch_id[:8]}...")
                return batch_id
            else:
                logger.warning(f"Only saved {total_saved}/{len(trades_data)} trades")
                return batch_id  # Return even if partial save
                
        except Exception as e:
            logger.error(f"Error saving Monte Carlo results: {e}")
            return None
    
    def _prepare_trade_data(self, trades_df: pd.DataFrame, batch_id: str, symbol: str) -> List[Dict]:
        """Prepare enhanced trade data for database storage"""
        trades_data = trades_df.to_dict('records')
        
        for trade in trades_data:
            # Add batch and symbol info
            trade['batch_id'] = batch_id
            trade['symbol'] = symbol
            
            # Ensure zone_number is present
            if 'zone_number' not in trade or pd.isna(trade['zone_number']):
                if 'zone_id' in trade and '_zone' in str(trade['zone_id']):
                    try:
                        trade['zone_number'] = int(str(trade['zone_id']).split('_zone')[-1])
                    except:
                        trade['zone_number'] = None
                else:
                    trade['zone_number'] = None
            
            # Convert timestamps to ISO format strings
            for time_field in ['entry_time', 'exit_time']:
                if time_field in trade and pd.notna(trade[time_field]):
                    if hasattr(trade[time_field], 'isoformat'):
                        trade[time_field] = trade[time_field].isoformat()
                    else:
                        # Handle string timestamps
                        trade[time_field] = str(trade[time_field])
                else:
                    trade[time_field] = None
            
            # Handle confluence sources (convert list to array)
            if 'confluence_sources' in trade:
                if isinstance(trade['confluence_sources'], list):
                    trade['confluence_sources'] = trade['confluence_sources']
                else:
                    trade['confluence_sources'] = []
            else:
                trade['confluence_sources'] = []
            
            # Handle confluence flags (convert dict to JSON)
            if 'confluence_flags' in trade:
                if not isinstance(trade['confluence_flags'], dict):
                    trade['confluence_flags'] = {}
            else:
                trade['confluence_flags'] = {}
            
            # Ensure all numeric fields are properly formatted
            numeric_fields = [
                'entry_price', 'stop_price', 'exit_price', 'zone_high', 'zone_low', 'zone_center',
                'highest_price', 'lowest_price', 'max_favorable_excursion', 'max_adverse_excursion',
                'mfe_r_multiple', 'mae_r_multiple', 'actual_r_multiple', 'optimal_r_multiple',
                'weighted_optimal_r', 'confluence_multiplier', 'risk_per_unit', 'zone_size',
                'confluence_score', 'expected_edge', 'risk_adjusted_score'
            ]
            
            for field in numeric_fields:
                if field in trade:
                    value = trade[field]
                    if pd.isna(value) or value is None:
                        trade[field] = None
                    else:
                        try:
                            trade[field] = float(value)
                        except (ValueError, TypeError):
                            trade[field] = None
            
            # Ensure integer fields
            integer_fields = [
                'zone_number', 'time_in_trade_minutes', 'entry_hour', 'entry_minute',
                'day_of_week', 'bars_in_trade', 'confluence_count'
            ]
            
            for field in integer_fields:
                if field in trade:
                    value = trade[field]
                    if pd.isna(value) or value is None:
                        trade[field] = None
                    else:
                        try:
                            trade[field] = int(value)
                        except (ValueError, TypeError):
                            trade[field] = None
            
            # Ensure boolean fields
            boolean_fields = ['has_high_confluence', 'has_multiple_sources']
            
            for field in boolean_fields:
                if field in trade:
                    trade[field] = bool(trade[field]) if trade[field] is not None else False
                else:
                    trade[field] = False
        
        return trades_data
    
    def _save_trades_in_batches(self, trades_data: List[Dict]) -> int:
        """Save trades in batches to handle large datasets"""
        total_saved = 0
        
        for i in range(0, len(trades_data), BATCH_SIZE):
            chunk = trades_data[i:i+BATCH_SIZE]
            
            try:
                result = self.client.table('monte_carlo_trades').insert(chunk).execute()
                
                if result.data:
                    saved_count = len(result.data)
                    total_saved += saved_count
                    logger.info(f"Saved batch {i//BATCH_SIZE + 1}: {saved_count} trades ({total_saved}/{len(trades_data)} total)")
                else:
                    logger.warning(f"No data returned for batch {i//BATCH_SIZE + 1}")
                    
            except Exception as e:
                logger.error(f"Error saving trades batch {i//BATCH_SIZE + 1}: {e}")
                # Continue with next batch rather than failing completely
        
        return total_saved
    
    def get_batch_summary(self, batch_id: str) -> Dict:
        """
        Get enhanced summary statistics for a batch including confluence metrics
        
        Args:
            batch_id: Batch UUID
            
        Returns:
            Enhanced summary dictionary with confluence analysis
        """
        try:
            # Get batch metadata
            batch_result = self.client.table('monte_carlo_batches').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not batch_result.data:
                logger.warning(f"No batch found for ID: {batch_id}")
                return {}
            
            batch_data = batch_result.data[0]
            
            # Get trade data
            trades_result = self.client.table('monte_carlo_trades').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not trades_result.data:
                logger.warning(f"No trades found for batch: {batch_id}")
                return batch_data
            
            df = pd.DataFrame(trades_result.data)
            
            # Calculate enhanced summary statistics
            summary = {
                **batch_data,
                
                # Basic performance metrics
                'total_trades': len(df),
                'win_rate': (df['actual_r_multiple'] > 0).mean() * 100,
                'avg_optimal_r': df['optimal_r_multiple'].mean(),
                'median_optimal_r': df['optimal_r_multiple'].median(),
                'max_optimal_r': df['optimal_r_multiple'].max(),
                'stop_hit_rate': (df['exit_reason'] == 'STOP_HIT').mean() * 100,
                'time_exit_rate': (df['exit_reason'] == 'TIME_EXIT').mean() * 100,
                
                # Enhanced confluence metrics
                'avg_confluence_score': df['confluence_score'].mean() if 'confluence_score' in df.columns else 0,
                'high_confluence_trades': len(df[df.get('has_high_confluence', False)]) if 'has_high_confluence' in df.columns else 0,
                'multi_source_trades': len(df[df.get('has_multiple_sources', False)]) if 'has_multiple_sources' in df.columns else 0,
                
                # Confluence level breakdown
                'confluence_level_breakdown': df['confluence_level'].value_counts().to_dict() if 'confluence_level' in df.columns else {},
                
                # Zone performance with confluence
                'zone_performance': self._calculate_zone_performance(df),
                
                # Best performing confluence combinations
                'top_confluence_sources': self._analyze_top_sources(df)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting batch summary: {e}")
            return {}
    
    def _calculate_zone_performance(self, df: pd.DataFrame) -> Dict:
        """Calculate performance metrics by zone with confluence data"""
        zone_performance = {}
        
        if 'zone_number' in df.columns:
            for zone_num in df['zone_number'].unique():
                if pd.isna(zone_num):
                    continue
                
                zone_trades = df[df['zone_number'] == zone_num]
                
                zone_performance[int(zone_num)] = {
                    'trade_count': len(zone_trades),
                    'win_rate': (zone_trades['actual_r_multiple'] > 0).mean() * 100,
                    'avg_optimal_r': zone_trades['optimal_r_multiple'].mean(),
                    'avg_confluence_score': zone_trades['confluence_score'].mean() if 'confluence_score' in zone_trades.columns else 0,
                    'dominant_confluence_level': zone_trades['confluence_level'].mode().iloc[0] if 'confluence_level' in zone_trades.columns and len(zone_trades) > 0 else 'L1'
                }
        
        return zone_performance
    
    def _analyze_top_sources(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict]:
        """Analyze top performing confluence sources"""
        if 'confluence_sources' not in df.columns:
            return []
        
        # Flatten all sources and count performance
        source_performance = {}
        
        for _, trade in df.iterrows():
            sources = trade.get('confluence_sources', [])
            optimal_r = trade.get('optimal_r_multiple', 0)
            
            for source in sources:
                if source not in source_performance:
                    source_performance[source] = {'trades': 0, 'total_r': 0}
                
                source_performance[source]['trades'] += 1
                source_performance[source]['total_r'] += optimal_r
        
        # Calculate average R for each source
        top_sources = []
        for source, data in source_performance.items():
            if data['trades'] >= 5:  # Only consider sources with at least 5 trades
                avg_r = data['total_r'] / data['trades']
                top_sources.append({
                    'source': source,
                    'trade_count': data['trades'],
                    'avg_optimal_r': round(avg_r, 3)
                })
        
        # Sort by average R and return top N
        top_sources.sort(key=lambda x: x['avg_optimal_r'], reverse=True)
        return top_sources[:top_n]
    
    def export_batch_to_csv(self, batch_id: str, filename: str = None) -> bool:
        """Export batch results to CSV file"""
        try:
            trades_result = self.client.table('monte_carlo_trades').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not trades_result.data:
                logger.warning(f"No trades found for batch: {batch_id}")
                return False
            
            df = pd.DataFrame(trades_result.data)
            
            if not filename:
                filename = f"monte_carlo_{batch_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            df.to_csv(filename, index=False)
            logger.info(f"Exported {len(df)} trades to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False