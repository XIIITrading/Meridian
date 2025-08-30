"""
Enhanced Data Loader for Monte Carlo simulation
Integrates with confluence_system database module
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from polygon import RESTClient

# Add confluence_system to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.service import DatabaseService
from config import (
    POLYGON_API_KEY, TRADING_START_TIME, TRADING_END_TIME,
    MIN_ZONE_SIZE, MAX_ZONE_SIZE
)

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        """Initialize data connections using confluence_system database module"""
        self.polygon_client = RESTClient(api_key=POLYGON_API_KEY)
        self.db_service = DatabaseService()
        
        if not self.db_service.enabled:
            logger.warning("Database service not enabled - some functions may not work")
        
    def fetch_minute_bars_for_date(self, symbol: str, trade_date: str) -> pd.DataFrame:
        """
        Fetch minute bars for a single trading day using Polygon API
        
        Args:
            symbol: Ticker symbol
            trade_date: Trading date (YYYY-MM-DD)
            
        Returns:
            DataFrame with minute bars for that day, filtered to trading hours
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
            df_filtered = df_filtered.drop(['hour', 'minute'], axis=1)
            
            logger.info(f"Loaded {len(df_filtered)} minute bars for trading hours on {trade_date}")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error fetching minute bars: {e}")
            return pd.DataFrame()
    
    def fetch_zones_from_database(self, ticker_id: str) -> List[Dict]:
        """
        Fetch zones using confluence_system database service
        
        Args:
            ticker_id: Ticker ID (e.g., 'AMD.121824')
            
        Returns:
            List of enhanced zone dictionaries with confluence data
        """
        logger.info(f"Fetching zones for {ticker_id} using database service")
        
        if not self.db_service.enabled:
            logger.error("Database service not available")
            return []
        
        try:
            # Get analysis summary which includes zones and confluence details
            summary = self.db_service.get_analysis_summary(ticker_id)
            
            if not summary or not summary.get('zones'):
                logger.warning(f"No zones found for {ticker_id}")
                return []
            
            zones = []
            
            for zone_data in summary['zones']:
                # Validate zone has required data
                zone_high = zone_data.get('high')
                zone_low = zone_data.get('low')
                
                if not zone_high or not zone_low or zone_high <= zone_low:
                    continue
                
                # Calculate zone size
                zone_size = zone_high - zone_low
                
                # Filter by zone size limits
                if zone_size < MIN_ZONE_SIZE or zone_size > MAX_ZONE_SIZE:
                    logger.debug(f"Zone {zone_data['zone_number']} filtered out by size: {zone_size:.2f}")
                    continue
                
                # Create enhanced zone dictionary
                zone = {
                    'id': f"{ticker_id}_zone{zone_data['zone_number']}",
                    'zone_number': zone_data['zone_number'], 
                    'high': float(zone_high),
                    'low': float(zone_low),
                    'center': float(zone_data.get('level', (zone_high + zone_low) / 2)),
                    'size': zone_size,
                    'date': summary['session_date'],
                    'time': '14:30:00',  # Default market open time
                    
                    # Confluence data
                    'confluence_score': float(zone_data.get('score', 0)),
                    'confluence_level': zone_data.get('confluence_level', 'L1'),
                    'confluence_count': len(zone_data.get('sources', [])),
                    'confluence_sources': zone_data.get('sources', []),
                    
                    # Enhanced confluence flags
                    'confluence_flags': zone_data.get('flags', {}),
                    
                    # Trading metrics
                    'expected_edge': self._calculate_expected_edge(zone_data),
                    'risk_adjusted_score': self._calculate_risk_adjusted_score(zone_data)
                }
                
                zones.append(zone)
            
            logger.info(f"Loaded {len(zones)} valid zones with confluence data")
            return zones
            
        except Exception as e:
            logger.error(f"Error fetching zones from database: {e}")
            return []
    
    def _calculate_expected_edge(self, zone_data: Dict) -> float:
        """Calculate expected trading edge based on confluence"""
        base_score = zone_data.get('score', 0)
        confluence_level = zone_data.get('confluence_level', 'L1')
        
        # Apply confluence multipliers
        from config import CONFLUENCE_WEIGHTS
        multiplier = CONFLUENCE_WEIGHTS.get(confluence_level, 1.0)
        
        return base_score * multiplier
    
    def _calculate_risk_adjusted_score(self, zone_data: Dict) -> float:
        """Calculate risk-adjusted score for zone prioritization"""
        score = zone_data.get('score', 0)
        source_count = len(zone_data.get('sources', []))
        
        # Bonus for multiple confluence sources
        source_bonus = min(source_count * 0.1, 0.5)  # Max 0.5 bonus
        
        return score + source_bonus
    
    def get_available_sessions(self, ticker: str = None, 
                             start_date: str = None,
                             end_date: str = None) -> List[Dict]:
        """
        Get available trading sessions using database service
        
        Args:
            ticker: Optional ticker filter
            start_date: Optional start date filter  
            end_date: Optional end date filter
            
        Returns:
            List of available sessions with metadata
        """
        if not self.db_service.enabled:
            logger.error("Database service not available")
            return []
        
        try:
            # Get recent analyses and filter
            analyses = self.db_service.list_recent_analyses(100)
            
            if not analyses:
                return []
            
            # Apply filters
            filtered_analyses = []
            for analysis in analyses:
                # Ticker filter
                if ticker and analysis['ticker'].upper() != ticker.upper():
                    continue
                
                # Date filters
                session_date = analysis.get('session_date', '')
                if start_date and session_date < start_date:
                    continue
                if end_date and session_date > end_date:
                    continue
                
                # Add session metadata
                session = {
                    'ticker_id': analysis['ticker_id'],
                    'ticker': analysis['ticker'],
                    'session_date': session_date,
                    'analysis_datetime': analysis.get('analysis_datetime'),
                    'current_price': analysis.get('current_price'),
                    'has_zones': True  # Assume has zones if in database
                }
                
                filtered_analyses.append(session)
            
            # Sort by date desc
            filtered_analyses.sort(key=lambda x: x['session_date'], reverse=True)
            
            logger.info(f"Found {len(filtered_analyses)} available sessions")
            return filtered_analyses
            
        except Exception as e:
            logger.error(f"Error getting available sessions: {e}")
            return []

    def validate_ticker_id(self, ticker_id: str) -> bool:
        """Validate ticker ID format and data availability"""
        # Check format
        parts = ticker_id.split('.')
        if len(parts) != 2:
            return False
        
        symbol, date_str = parts
        if len(date_str) != 6:
            return False
        
        # Check if data exists in database
        if self.db_service.enabled:
            summary = self.db_service.get_analysis_summary(ticker_id)
            return summary is not None
        
        return True