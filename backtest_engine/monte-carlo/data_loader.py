"""
Data loading functions for Monte Carlo simulation
Using levels_zones table for zone data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from polygon import RESTClient
from supabase import create_client, Client

from config import (
    POLYGON_API_KEY, SUPABASE_URL, SUPABASE_KEY,
    TRADING_START_TIME, TRADING_END_TIME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        """Initialize data connections"""
        self.polygon_client = RESTClient(api_key=POLYGON_API_KEY)
        self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def fetch_minute_bars_for_date(self, symbol: str, trade_date: str) -> pd.DataFrame:
        """
        Fetch minute bars for a single trading day
        
        Args:
            symbol: Ticker symbol
            trade_date: Trading date (YYYY-MM-DD)
            
        Returns:
            DataFrame with minute bars for that day
        """
        logger.info(f"Fetching minute bars for {symbol} on {trade_date}")
        
        all_bars = []
        
        try:
            # Fetch data from Polygon for single day
            aggs = self.polygon_client.list_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="minute",
                from_=trade_date,
                to=trade_date,
                limit=50000
            )
            
            for agg in aggs:
                all_bars.append({
                    'timestamp': pd.Timestamp(agg.timestamp, unit='ms', tz='UTC'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            if not all_bars:
                logger.warning(f"No data returned for {symbol} on {trade_date}")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(all_bars)
            df.set_index('timestamp', inplace=True)
            
            # Filter to trading hours only (13:30 - 19:50 UTC)
            df['hour'] = df.index.hour
            df['minute'] = df.index.minute
            
            # Filter to trading window
            mask = (
                (df['hour'] > 13) | 
                ((df['hour'] == 13) & (df['minute'] >= 30))
            ) & (
                (df['hour'] < 19) | 
                ((df['hour'] == 19) & (df['minute'] <= 50))
            )
            
            df_filtered = df[mask].copy()
            
            logger.info(f"Loaded {len(df_filtered)} minute bars for {trade_date}")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error fetching minute bars: {e}")
            return pd.DataFrame()
    
    def fetch_zones_from_levels_zones(self, ticker_id: str) -> List[Dict]:
        """
        Fetch zones from levels_zones table
        
        Args:
            ticker_id: Ticker ID (e.g., 'AMD.121824')
            
        Returns:
            List of zone dictionaries extracted from levels_zones
        """
        logger.info(f"Fetching zones for {ticker_id} from levels_zones table")
        
        try:
            # Query levels_zones table
            response = self.supabase_client.table('levels_zones').select('*').eq(
                'ticker_id', ticker_id
            ).execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning(f"No levels_zones record found for {ticker_id}")
                return []
            
            record = response.data[0]
            zones = []
            
            # Extract all 6 M15 zones
            for i in range(1, 7):
                zone_high = record.get(f'm15_zone{i}_high')
                zone_low = record.get(f'm15_zone{i}_low')
                zone_date = record.get(f'm15_zone{i}_date')
                zone_time = record.get(f'm15_zone{i}_time')
                confluence_score = record.get(f'm15_zone{i}_confluence_score', 0)
                confluence_level = record.get(f'm15_zone{i}_confluence_level', 'L1')
                
                # Only add zones that have valid data
                if zone_high and zone_low and zone_high > zone_low:
                    zones.append({
                        'id': f"{ticker_id}_zone{i}",
                        'zone_number': i,
                        'high': float(zone_high),
                        'low': float(zone_low),
                        'date': zone_date or record['session_date'],
                        'time': zone_time,
                        'confluence_score': float(confluence_score) if confluence_score else 0,
                        'confluence_level': confluence_level,
                        'size': float(zone_high) - float(zone_low)
                    })
            
            logger.info(f"Extracted {len(zones)} valid zones from levels_zones")
            return zones
            
        except Exception as e:
            logger.error(f"Error fetching zones from levels_zones: {e}")
            return []
    
    def get_available_sessions(self, ticker: str = None, 
                             start_date: str = None,
                             end_date: str = None) -> List[Dict]:
        """
        Get list of available trading sessions from levels_zones
        
        Args:
            ticker: Optional ticker filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of available sessions
        """
        try:
            query = self.supabase_client.table('levels_zones').select(
                'ticker_id', 'ticker', 'session_date', 'analysis_status'
            )
            
            if ticker:
                query = query.eq('ticker', ticker)
            if start_date:
                query = query.gte('session_date', start_date)
            if end_date:
                query = query.lte('session_date', end_date)
            
            response = query.order('session_date', desc=True).execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting available sessions: {e}")
            return []