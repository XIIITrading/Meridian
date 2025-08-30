"""
Database service layer - orchestrates all database operations
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from .supabase_client import SupabaseClient
from .config import SUPABASE_URL, SUPABASE_KEY, validate_config

logger = logging.getLogger(__name__)

class DatabaseService:
    """High-level database service"""
    
    def __init__(self):
        """Initialize service"""
        self.client = None
        self.enabled = False
        
        try:
            if validate_config():
                self.client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
                # Test the connection
                if self.client.test_connection():
                    self.enabled = True
                    logger.info("Database service initialized and connected")
                else:
                    logger.error("Database connection test failed")
        except Exception as e:
            logger.warning(f"Database service disabled: {e}")
    
    def save_cli_output(self, cli_output: Dict[str, Any], 
                       skip_existing: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Save CLI output to both levels_zones and enhanced tables
        
        Args:
            cli_output: Output from confluence_cli
            skip_existing: Skip if already exists
            
        Returns:
            Tuple of (success, ticker_id)
        """
        if not self.enabled:
            logger.warning("Database service is disabled")
            return False, None
        
        try:
            # Generate ticker_id
            ticker = cli_output['symbol']
            date = datetime.fromisoformat(cli_output['analysis_time']).date()
            ticker_id = f"{ticker}.{date.strftime('%m%d%y')}"
            
            # Check existing if requested
            if skip_existing and self.client.check_existing(ticker_id):
                logger.info(f"Skipping existing {ticker_id}")
                return True, ticker_id  # Return True since record exists
            
            # Save to levels_zones (for Monte Carlo compatibility)
            success, returned_ticker_id = self.client.save_to_levels_zones(cli_output)
            
            if success and returned_ticker_id:
                # Also save enhanced confluence details
                enhanced_success = self.client.save_enhanced_confluence(cli_output, returned_ticker_id)
                
                if enhanced_success:
                    logger.info(f"Successfully saved {returned_ticker_id} (with enhanced details)")
                else:
                    logger.warning(f"Saved {returned_ticker_id} but enhanced details failed")
                
                return True, returned_ticker_id
            
            logger.error("Failed to save to levels_zones")
            return False, None
            
        except Exception as e:
            logger.error(f"Error saving CLI output: {e}")
            return False, None
    
    def get_analysis_summary(self, ticker_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis summary for a ticker_id"""
        if not self.enabled:
            return None
        
        try:
            # Get levels_zones record
            levels_record = self.client.get_levels_zones_record(ticker_id)
            if not levels_record:
                return None
            
            # Get confluence details
            confluence_details = self.client.get_confluence_details(ticker_id)
            
            # Extract zone information
            zones = []
            for i in range(1, 7):
                zone_level = levels_record.get(f'm15_zone{i}_level')
                if zone_level:
                    zone_detail = next(
                        (cd for cd in confluence_details if cd['zone_number'] == i), 
                        None
                    )
                    
                    zones.append({
                        'zone_number': i,
                        'level': zone_level,
                        'high': levels_record.get(f'm15_zone{i}_high'),
                        'low': levels_record.get(f'm15_zone{i}_low'),
                        'score': levels_record.get(f'm15_zone{i}_confluence_score'),
                        'confluence_level': levels_record.get(f'm15_zone{i}_confluence_level'),
                        'confluence_count': levels_record.get(f'm15_zone{i}_confluence_count'),
                        'sources': zone_detail.get('confluence_sources', []) if zone_detail else [],
                        'flags': {k: v for k, v in zone_detail.items() 
                                if k.startswith('has_') and v} if zone_detail else {}
                    })
            
            return {
                'ticker_id': ticker_id,
                'ticker': levels_record['ticker'],
                'session_date': levels_record['session_date'],
                'current_price': levels_record.get('current_price'),
                'atr_daily': levels_record.get('atr_daily'),
                'atr_15min': levels_record.get('atr_15min'),
                'zones': zones,
                'zone_count': len(zones)
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis summary: {e}")
            return None
    
    def list_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent analyses"""
        if not self.enabled:
            return []
        
        try:
            result = self.client.client.table('levels_zones')\
                .select('ticker_id, ticker, session_date, analysis_datetime, current_price')\
                .order('analysis_datetime', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing recent analyses: {e}")
            return []
    
    def save_cli_output(self, ticker: str, session_date: str, 
                       analysis_time: str, results: Dict[str, Any], 
                       skip_existing: bool = False) -> Dict[str, Any]:
        """
        Save CLI output to database
        
        Args:
            ticker: Ticker symbol
            session_date: Session date (YYYY-MM-DD)
            analysis_time: Analysis time (HH:MM)
            results: CLI analysis results
            skip_existing: Skip if analysis already exists
            
        Returns:
            Dict with success status and details
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Database service not enabled'
            }
        
        try:
            # Create ticker_id
            date_obj = datetime.strptime(session_date, '%Y-%m-%d')
            ticker_id = f"{ticker}.{date_obj.strftime('%m%d%y')}"
            
            # Check if exists and skip if requested
            if skip_existing:
                existing = self.client.get_levels_zones_record(ticker_id)
                if existing:
                    return {
                        'success': True,
                        'skipped': 1,
                        'ticker_id': ticker_id
                    }
            
            # Save to levels_zones
            success_levels, saved_ticker_id = self.client.save_to_levels_zones(results)
            
            # Save enhanced confluence details if levels saved successfully
            confluence_saved = False
            if success_levels:
                confluence_saved = self.client.save_enhanced_confluence(results, saved_ticker_id)
            
            return {
                'success': success_levels,
                'levels_zones_saved': 1 if success_levels else 0,
                'confluence_saved': confluence_saved,
                'ticker_id': saved_ticker_id,
                'error': None if success_levels else 'Failed to save to levels_zones'
            }
            
        except Exception as e:
            logger.error(f"Error in save_cli_output: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get database connection status for debugging"""
        return {
            'enabled': self.enabled,
            'client_initialized': self.client is not None,
            'config_valid': validate_config(),
            'connection_test': self.client.test_connection() if self.client else False
        }