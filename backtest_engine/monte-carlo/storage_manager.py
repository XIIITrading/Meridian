"""
Supabase storage manager for Monte Carlo results
"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging
from supabase import create_client

from config import SUPABASE_URL, SUPABASE_KEY, BATCH_SIZE

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        """Initialize Supabase connection"""
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def save_results(self, symbol: str, start_date: str, end_date: str,
                trades_df: pd.DataFrame, metadata: Dict = None) -> str:
        """
        Save Monte Carlo results to Supabase
        
        Args:
            symbol: Trading symbol
            start_date: Simulation start date
            end_date: Simulation end date
            trades_df: DataFrame of trade results
            metadata: Additional metadata
            
        Returns:
            Batch ID
        """
        # Create batch record
        batch_id = str(uuid.uuid4())
        
        batch_record = {
            'batch_id': batch_id,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'total_trades': len(trades_df),
            'zones_count': metadata.get('zones_count', 0) if metadata else 0,
            'bars_count': metadata.get('bars_count', 0) if metadata else 0,
            'runtime_seconds': metadata.get('runtime_seconds', 0) if metadata else 0,
            'metadata': metadata
        }
        
        # Save batch metadata
        try:
            self.client.table('monte_carlo_batches').insert(batch_record).execute()
            logger.info(f"Created batch {batch_id}")
        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            return None
        
        trades_data = trades_df.to_dict('records')
        for trade in trades_data:
            trade['batch_id'] = batch_id
            trade['symbol'] = symbol
            
            # Ensure zone fields are included
            if 'zone_number' not in trade:
                # Try to extract from zone_id if available
                if 'zone_id' in trade and '_zone' in trade['zone_id']:
                    try:
                        trade['zone_number'] = int(trade['zone_id'].split('_zone')[-1])
                    except:
                        trade['zone_number'] = None
            
            # Convert timestamps to strings
            trade['entry_time'] = trade['entry_time'].isoformat() if pd.notna(trade['entry_time']) else None
            trade['exit_time'] = trade['exit_time'].isoformat() if pd.notna(trade['exit_time']) else None
        
        # Save trades in batches
        total_saved = 0
        for i in range(0, len(trades_data), BATCH_SIZE):
            chunk = trades_data[i:i+BATCH_SIZE]
            try:
                self.client.table('monte_carlo_trades').insert(chunk).execute()
                total_saved += len(chunk)
                logger.info(f"Saved {total_saved}/{len(trades_data)} trades")
            except Exception as e:
                logger.error(f"Error saving trades batch: {e}")
        
        logger.info(f"Successfully saved {total_saved} trades to batch {batch_id}")
        return batch_id
    
    def get_batch_summary(self, batch_id: str) -> Dict:
        """
        Get summary statistics for a batch
        
        Args:
            batch_id: Batch UUID
            
        Returns:
            Summary dictionary
        """
        try:
            # Get batch metadata
            batch = self.client.table('monte_carlo_batches').select('*').eq(
                'batch_id', batch_id
            ).single().execute()
            
            # Get trade statistics
            trades = self.client.table('monte_carlo_trades').select('*').eq(
                'batch_id', batch_id
            ).execute()
            
            if not trades.data:
                return batch.data
            
            df = pd.DataFrame(trades.data)
            
            # Calculate summary statistics
            summary = {
                **batch.data,
                'win_rate': (df['actual_r_multiple'] > 0).mean() * 100,
                'avg_optimal_r': df['optimal_r_multiple'].mean(),
                'median_optimal_r': df['optimal_r_multiple'].median(),
                'max_optimal_r': df['optimal_r_multiple'].max(),
                'stop_hit_rate': (df['exit_reason'] == 'STOP_HIT').mean() * 100,
                'time_exit_rate': (df['exit_reason'] == 'TIME_EXIT').mean() * 100
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting batch summary: {e}")
            return {}