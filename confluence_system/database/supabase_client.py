"""
Supabase client for Confluence System
Maintains compatibility with levels_zones for Monte Carlo
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
from decimal import Decimal

from .models import LevelsZonesRecord, ZoneConfluenceDetail, ConfluenceAnalysis

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client with levels_zones compatibility"""
    
    def __init__(self, url: str, key: str):
        """Initialize client"""
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Simple query to test connection
            result = self.client.table('levels_zones').select('id').limit(1).execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def save_to_levels_zones(self, cli_output: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save CLI output to levels_zones table for Monte Carlo compatibility
        
        Args:
            cli_output: Output from confluence_cli.py
            
        Returns:
            Tuple of (success, ticker_id)
        """
        try:
            # Parse analysis time to get date
            analysis_dt = datetime.fromisoformat(cli_output['analysis_time'])
            session_date = analysis_dt.date()
            
            # Create ticker_id in expected format (TICKER.MMDDYY)
            ticker = cli_output['symbol']
            date_str = session_date.strftime('%m%d%y')
            ticker_id = f"{ticker}.{date_str}"
            
            # Build levels_zones record
            record = {
                'ticker_id': ticker_id,
                'ticker': ticker,
                'session_date': session_date.isoformat(),
                'is_live': True,
                'analysis_datetime': datetime.now().isoformat(),
                'analysis_status': 'completed',
                
                # Price and ATR
                'current_price': cli_output['current_price'],
                'pre_market_price': cli_output['current_price'],  # Use current as pre-market
                'atr_daily': cli_output['metrics']['atr_daily'],
                'atr_15min': cli_output['metrics']['atr_15min'],
                
                # Weekly levels
                'weekly_wl1': cli_output['parameters']['weekly_levels'][0],
                'weekly_wl2': cli_output['parameters']['weekly_levels'][1],
                'weekly_wl3': cli_output['parameters']['weekly_levels'][2],
                'weekly_wl4': cli_output['parameters']['weekly_levels'][3],
                
                # Daily levels
                'daily_dl1': cli_output['parameters']['daily_levels'][0],
                'daily_dl2': cli_output['parameters']['daily_levels'][1],
                'daily_dl3': cli_output['parameters']['daily_levels'][2],
                'daily_dl4': cli_output['parameters']['daily_levels'][3],
                
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add M15 zones (up to 6)
            for i, level in enumerate(cli_output['levels'][:6], 1):
                record[f'm15_zone{i}_level'] = (level['low'] + level['high']) / 2
                record[f'm15_zone{i}_high'] = level['high']
                record[f'm15_zone{i}_low'] = level['low']
                record[f'm15_zone{i}_date'] = session_date.isoformat()
                record[f'm15_zone{i}_time'] = analysis_dt.time().isoformat()
                record[f'm15_zone{i}_confluence_score'] = level['score']
                record[f'm15_zone{i}_confluence_level'] = level['confluence']
                record[f'm15_zone{i}_confluence_count'] = level.get('source_count', 0)
            
            # Fill remaining zones with None
            for i in range(len(cli_output['levels']) + 1, 7):
                record[f'm15_zone{i}_level'] = None
                record[f'm15_zone{i}_high'] = None
                record[f'm15_zone{i}_low'] = None
                record[f'm15_zone{i}_date'] = None
                record[f'm15_zone{i}_time'] = None
                record[f'm15_zone{i}_confluence_score'] = None
                record[f'm15_zone{i}_confluence_level'] = None
                record[f'm15_zone{i}_confluence_count'] = None
            
            # Upsert to handle re-runs
            result = self.client.table('levels_zones')\
                .upsert(record, on_conflict='ticker_id')\
                .execute()
            
            if result.data:
                logger.info(f"Saved to levels_zones: {ticker_id}")
                return True, ticker_id
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error saving to levels_zones: {e}")
            return False, None
    
    def save_enhanced_confluence(self, cli_output: Dict[str, Any], 
                                ticker_id: str) -> bool:
        """
        Save enhanced confluence details for advanced analysis
        
        Args:
            cli_output: CLI output dictionary
            ticker_id: Ticker ID from levels_zones
            
        Returns:
            Success boolean
        """
        try:
            # Create enhanced analysis record
            analysis_data = {
                'ticker_id': ticker_id,
                'ticker': cli_output['symbol'],
                'session_date': cli_output['analysis_time'].split('T')[0],
                'analysis_datetime': cli_output['analysis_time'],
                'params': cli_output['parameters'],
                'cli_version': '2.0'
            }
            
            result = self.client.table('confluence_analyses_enhanced')\
                .upsert(analysis_data, on_conflict='ticker_id,analysis_datetime')\
                .execute()
            
            if not result.data:
                logger.error("Failed to save enhanced analysis record")
                return False
            
            analysis_id = result.data[0]['id']
            
            # Delete existing zone details for this analysis
            self.client.table('zone_confluence_details')\
                .delete()\
                .eq('analysis_id', analysis_id)\
                .execute()
            
            # Save zone confluence details
            zone_details = []
            for i, level in enumerate(cli_output['levels'][:6], 1):
                sources = level.get('confluence_sources', [])
                
                detail = {
                    'analysis_id': analysis_id,
                    'zone_number': i,
                    'confluence_sources': sources,
                    'source_details': level.get('source_details', {}),
                    **self._parse_confluence_flags(sources)
                }
                zone_details.append(detail)
            
            if zone_details:
                self.client.table('zone_confluence_details')\
                    .insert(zone_details)\
                    .execute()
            
            logger.info(f"Saved enhanced confluence for {ticker_id} ({len(zone_details)} zones)")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced confluence: {e}")
            return False
    
    def _parse_confluence_flags(self, sources: List[str]) -> Dict[str, bool]:
        """Parse sources into boolean flags"""
        flags = {}
        
        # Initialize all flags to False
        flag_names = [
            'has_hvn_7d', 'has_hvn_14d', 'has_hvn_30d', 'has_hvn_60d',
            'has_cam_daily', 'has_cam_weekly', 'has_cam_monthly',
            'has_cam_h5', 'has_cam_h4', 'has_cam_h3', 'has_cam_l3', 'has_cam_l4', 'has_cam_l5',
            'has_pivot_daily', 'has_pivot_weekly',
            'has_pdh', 'has_pdl', 'has_pdc', 'has_onh', 'has_onl', 'has_pwh', 'has_pwl',
            'has_vwap', 'has_ema_9', 'has_ema_21', 'has_sma_50', 'has_sma_200'
        ]
        
        for flag in flag_names:
            flags[flag] = False
        
        # Parse sources
        for source in sources:
            source_upper = source.upper()
            
            # HVN flags
            if 'HVN_7D' in source_upper or 'HVN_7DAY' in source_upper:
                flags['has_hvn_7d'] = True
            elif 'HVN_14D' in source_upper or 'HVN_14DAY' in source_upper:
                flags['has_hvn_14d'] = True
            elif 'HVN_30D' in source_upper or 'HVN_30DAY' in source_upper:
                flags['has_hvn_30d'] = True
            elif 'HVN_60D' in source_upper or 'HVN_60DAY' in source_upper:
                flags['has_hvn_60d'] = True
            
            # Camarilla flags
            if 'CAM' in source_upper or 'CAMARILLA' in source_upper:
                if 'DAILY' in source_upper:
                    flags['has_cam_daily'] = True
                elif 'WEEKLY' in source_upper:
                    flags['has_cam_weekly'] = True
                elif 'MONTHLY' in source_upper:
                    flags['has_cam_monthly'] = True
                
                # Camarilla levels
                if 'H5' in source_upper or 'R5' in source_upper:
                    flags['has_cam_h5'] = True
                elif 'H4' in source_upper or 'R4' in source_upper:
                    flags['has_cam_h4'] = True
                elif 'H3' in source_upper or 'R3' in source_upper:
                    flags['has_cam_h3'] = True
                elif 'L3' in source_upper or 'S3' in source_upper:
                    flags['has_cam_l3'] = True
                elif 'L4' in source_upper or 'S4' in source_upper:
                    flags['has_cam_l4'] = True
                elif 'L5' in source_upper or 'S5' in source_upper:
                    flags['has_cam_l5'] = True
            
            # Key level flags
            if 'PDH' in source_upper:
                flags['has_pdh'] = True
            elif 'PDL' in source_upper:
                flags['has_pdl'] = True
            elif 'PDC' in source_upper:
                flags['has_pdc'] = True
            elif 'ONH' in source_upper:
                flags['has_onh'] = True
            elif 'ONL' in source_upper:
                flags['has_onl'] = True
            elif 'PWH' in source_upper:
                flags['has_pwh'] = True
            elif 'PWL' in source_upper:
                flags['has_pwl'] = True
            
            # Moving averages
            if 'VWAP' in source_upper:
                flags['has_vwap'] = True
            elif 'EMA_9' in source_upper or 'EMA9' in source_upper:
                flags['has_ema_9'] = True
            elif 'EMA_21' in source_upper or 'EMA21' in source_upper:
                flags['has_ema_21'] = True
            elif 'SMA_50' in source_upper or 'SMA50' in source_upper:
                flags['has_sma_50'] = True
            elif 'SMA_200' in source_upper or 'SMA200' in source_upper:
                flags['has_sma_200'] = True
            
            # Pivot flags
            if 'PIVOT' in source_upper:
                if 'DAILY' in source_upper:
                    flags['has_pivot_daily'] = True
                elif 'WEEKLY' in source_upper:
                    flags['has_pivot_weekly'] = True
        
        return flags
    
    def check_existing(self, ticker_id: str) -> bool:
        """Check if ticker_id already exists in levels_zones"""
        try:
            result = self.client.table('levels_zones')\
                .select('ticker_id')\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error checking existing: {e}")
            return False
    
    def get_levels_zones_record(self, ticker_id: str) -> Optional[Dict[str, Any]]:
        """Get a levels_zones record by ticker_id"""
        try:
            result = self.client.table('levels_zones')\
                .select('*')\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error fetching levels_zones record: {e}")
            return None
    
    def get_confluence_details(self, ticker_id: str) -> List[Dict[str, Any]]:
        """Get confluence details for a ticker_id"""
        try:
            # First get the enhanced analysis
            analysis_result = self.client.table('confluence_analyses_enhanced')\
                .select('id')\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            if not analysis_result.data:
                return []
            
            analysis_id = analysis_result.data[0]['id']
            
            # Get zone confluence details
            details_result = self.client.table('zone_confluence_details')\
                .select('*')\
                .eq('analysis_id', analysis_id)\
                .execute()
            
            return details_result.data if details_result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching confluence details: {e}")
            return []