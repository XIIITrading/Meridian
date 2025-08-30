"""Supabase client for fetching zone data"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for interacting with Supabase database"""
    
    def __init__(self, url: str, key: str):
        """Initialize Supabase client"""
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    def fetch_zones_for_date(self, trade_date: date) -> List[Dict[str, Any]]:
        """
        Fetch all zones for a specific trade date
        
        Args:
            trade_date: Date to fetch zones for (YYYY-MM-DD)
            
        Returns:
            List of zone dictionaries with confluence data
        """
        try:
            # Format date for ticker_id pattern (MMDDYY)
            date_suffix = trade_date.strftime('.%m%d%y')
            
            # Fetch all zones for this date
            response = self.client.table('levels_zones')\
                .select('*')\
                .like('ticker_id', f'%{date_suffix}')\
                .execute()
            
            zones = response.data
            logger.info(f"Found {len(zones)} zone records for date {trade_date}")
            
            if not zones:
                logger.warning(f"No zones found for date {trade_date}")
                return []
            
            # Get unique ticker_ids to fetch confluence data
            ticker_ids = list(set(zone['ticker_id'] for zone in zones))
            
            # Fetch confluence analyses for these tickers
            confluence_map = self._fetch_confluence_data(ticker_ids)
            
            # Process zones and merge confluence data
            enriched_zones = []
            for zone_record in zones:
                ticker_id = zone_record['ticker_id']
                
                # Extract individual M15 zones (up to 6)
                for i in range(1, 7):
                    zone_level = zone_record.get(f'm15_zone{i}_level')
                    zone_high = zone_record.get(f'm15_zone{i}_high')
                    zone_low = zone_record.get(f'm15_zone{i}_low')
                    
                    if zone_level is not None and zone_high is not None and zone_low is not None:
                        # Create zone entry
                        zone_entry = {
                            'ticker_id': ticker_id,
                            'ticker': zone_record['ticker'],
                            'zone_number': i,
                            'high': zone_high,
                            'low': zone_low,
                            'level': zone_level,
                            'confluence_level': zone_record.get(f'm15_zone{i}_confluence_level', 'L3'),
                            'confluence_score': zone_record.get(f'm15_zone{i}_confluence_score', 0),
                            'confluence_count': zone_record.get(f'm15_zone{i}_confluence_count', 0),
                            'session_date': zone_record.get('session_date'),
                            'current_price': zone_record.get('current_price')
                        }
                        
                        # Add confluence details if available
                        if ticker_id in confluence_map and i in confluence_map[ticker_id]:
                            zone_entry['confluence_data'] = confluence_map[ticker_id][i]
                        else:
                            zone_entry['confluence_data'] = {
                                'confluence_score': zone_entry['confluence_score'],
                                'sources': [],
                                'source_count': zone_entry['confluence_count']
                            }
                        
                        enriched_zones.append(zone_entry)
            
            logger.info(f"Processed {len(enriched_zones)} individual zones")
            return enriched_zones
            
        except Exception as e:
            logger.error(f"Error fetching zones: {e}")
            raise
    
    def _fetch_confluence_data(self, ticker_ids: List[str]) -> Dict[str, Dict[int, Dict[str, Any]]]:
        """
        Fetch confluence data for given ticker IDs
        
        Returns:
            Dictionary mapping ticker_id -> zone_number -> confluence data
        """
        confluence_map = {}
        
        for ticker_id in ticker_ids:
            try:
                # Get confluence analysis for this ticker
                analysis_response = self.client.table('confluence_analyses_enhanced')\
                    .select('id')\
                    .eq('ticker_id', ticker_id)\
                    .execute()
                
                if not analysis_response.data:
                    continue
                
                analysis_id = analysis_response.data[0]['id']
                
                # Get zone confluence details
                details_response = self.client.table('zone_confluence_details')\
                    .select('*')\
                    .eq('analysis_id', analysis_id)\
                    .execute()
                
                # Map by zone_number
                ticker_confluence = {}
                for detail in details_response.data:
                    zone_number = detail.get('zone_number')
                    if zone_number:
                        ticker_confluence[zone_number] = {
                            'confluence_score': detail.get('confluence_score', 0),
                            'sources': detail.get('confluence_sources', []),
                            'source_count': detail.get('source_count', 0),
                            'has_fractal': detail.get('has_fractal_confluence', False),
                            'has_hvn': detail.get('has_hvn_confluence', False),
                            'has_market_structure': detail.get('has_market_structure_confluence', False),
                            'has_atr': detail.get('has_atr_confluence', False)
                        }
                
                confluence_map[ticker_id] = ticker_confluence
                logger.info(f"Loaded confluence data for {ticker_id}: {len(ticker_confluence)} zones")
                
            except Exception as e:
                logger.warning(f"Could not fetch confluence for {ticker_id}: {e}")
                continue
        
        return confluence_map
    
    def fetch_available_dates(self, lookback_days: int = 30) -> List[date]:
        """
        Fetch list of dates that have zone data
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            List of dates with available data
        """
        try:
            response = self.client.table('levels_zones')\
                .select('ticker_id, session_date')\
                .order('session_date', desc=True)\
                .limit(lookback_days * 10)\
                .execute()
            
            # Extract unique dates
            dates = set()
            for row in response.data:
                if row.get('session_date'):
                    # Parse session_date directly
                    session_date = datetime.fromisoformat(row['session_date'].replace('Z', '+00:00')).date()
                    dates.add(session_date)
                else:
                    # Fallback: extract from ticker_id format (e.g., TSLA.082825)
                    ticker_id = row['ticker_id']
                    if '.' in ticker_id:
                        date_part = ticker_id.split('.')[1]
                        # Convert MMDDYY to date
                        if len(date_part) == 6:
                            month = int(date_part[:2])
                            day = int(date_part[2:4])
                            year = 2000 + int(date_part[4:6])  # YY to YYYY
                            dates.add(date(year, month, day))
            
            sorted_dates = sorted(list(dates), reverse=True)
            logger.info(f"Found {len(sorted_dates)} unique dates with zone data")
            return sorted_dates[:lookback_days]
            
        except Exception as e:
            logger.error(f"Error fetching available dates: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            response = self.client.table('levels_zones')\
                .select('id')\
                .limit(1)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False