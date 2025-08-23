"""
Persistence module for saving and loading analysis results
Handles all database operations for analysis
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

class AnalysisPersistence:
    """Handles saving and loading of analysis results"""
    
    def __init__(self, storage_manager):
        """
        Initialize persistence module
        
        Args:
            storage_manager: BacktestStorageManager instance
        """
        self.storage = storage_manager
        # Get the actual Supabase client
        if hasattr(storage_manager, 'client'):
            self.client = storage_manager.client
        else:
            # If storage_manager IS the client
            self.client = storage_manager
        self._ensure_analysis_table()
    
    def _ensure_analysis_table(self):
        """Ensure analysis_results table exists"""
        # Note: Table creation should be done in Supabase SQL editor
        logger.info("Ensure analysis_results table exists in Supabase")
    
    def save_results(self, analysis_type: str, results: dict, 
                    ticker_id: str = None) -> bool:
        """
        Save analysis results to database
        
        Args:
            analysis_type: Type of analysis
            results: Analysis results dictionary
            ticker_id: Optional ticker/session identifier
            
        Returns:
            Success status
        """
        try:
            # Extract key metrics
            key_metrics = self._extract_key_metrics(results, analysis_type)
            
            # Make results serializable
            serializable_results = self._make_serializable(results)
            
            # Prepare data
            data = {
                'analysis_type': analysis_type,
                'ticker_id': ticker_id,
                'results': json.dumps(serializable_results),
                'key_metrics': json.dumps(key_metrics),
                'recommendations': results.get('recommendations', [])
            }
            
            # Save to Supabase - use the client's table method
            response = self.client.client.table('analysis_results').insert(data).execute()
            
            logger.info(f"Saved {analysis_type} analysis for {ticker_id or 'all trades'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
            # Try alternative approach if the above fails
            try:
                # Direct table access
                response = self.client.table('analysis_results').insert(data).execute()
                logger.info(f"Saved using alternative method")
                return True
            except:
                logger.error(f"Both save methods failed")
                return False
    
    def load_latest(self, analysis_type: str = None, 
                   ticker_id: str = None) -> Optional[dict]:
        """
        Load the most recent analysis
        
        Args:
            analysis_type: Filter by type
            ticker_id: Filter by ticker
            
        Returns:
            Analysis results or None
        """
        try:
            # Build query
            if hasattr(self.client, 'table'):
                query = self.client.table('analysis_results').select('*')
            else:
                query = self.client.client.table('analysis_results').select('*')
            
            if analysis_type:
                query = query.eq('analysis_type', analysis_type)
            if ticker_id:
                query = query.eq('ticker_id', ticker_id)
            
            query = query.order('analysis_date', desc=True).limit(1)
            response = query.execute()
            
            if response.data:
                result = response.data[0]
                # Parse JSON fields
                result['results'] = json.loads(result['results']) if isinstance(result['results'], str) else result['results']
                result['key_metrics'] = json.loads(result['key_metrics']) if isinstance(result['key_metrics'], str) else result['key_metrics']
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load analysis: {e}")
            return None
    
    def _extract_key_metrics(self, results: dict, analysis_type: str) -> dict:
        """Extract key metrics for quick queries"""
        metrics = {}
        
        # Extract from basic stats if present
        if 'basic_stats' in results and hasattr(results['basic_stats'], '__dict__'):
            stats = results['basic_stats']
            metrics.update({
                'win_rate': getattr(stats, 'win_rate', None),
                'total_trades': getattr(stats, 'total_trades', None),
                'profit_factor': getattr(stats, 'profit_factor', None),
                'avg_r_multiple': getattr(stats, 'avg_r_multiple', None),
                'total_r': getattr(stats, 'total_r', None)
            })
        
        # Extract edge factors count
        if 'edge_factors' in results:
            metrics['edge_count'] = len(results['edge_factors'])
        
        return metrics
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        else:
            return obj