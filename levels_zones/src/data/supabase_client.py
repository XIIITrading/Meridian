"""
Supabase client wrapper for Meridian Trading System
Handles all database operations and data persistence
"""

import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import logging

from supabase import create_client, Client
from postgrest.exceptions import APIError

from data.models import (
    TradingSession, PriceLevel, WeeklyData, DailyData,
    TrendDirection
)

# Set up logging
logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper class for all Supabase database operations.
    Provides methods for CRUD operations on trading sessions and related data.
    """
    
    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client with credentials.
        
        Args:
            url: Supabase project URL
            key: Supabase anon/service key
        """
        # Create the Supabase client instance
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    # ==================== Trading Session Operations ====================
    
    def create_session(self, session: TradingSession) -> Tuple[bool, Optional[str]]:
        """
        Create a new trading session in the database.
        
        Args:
            session: TradingSession object to save
            
        Returns:
            Tuple of (success: bool, session_id: Optional[str])
        """
        try:
            # Convert the session object to a dictionary for database insertion
            session_data = {
                'ticker': session.ticker,
                'ticker_id': session.ticker_id,
                'date': session.date.isoformat(),
                'is_live': session.is_live,
                'historical_date': session.historical_date.isoformat() if session.historical_date else None,
                'historical_time': session.historical_time.isoformat() if session.historical_time else None,
                'weekly_data': session.weekly_data.to_dict() if session.weekly_data else None,
                'daily_data': session.daily_data.to_dict() if session.daily_data else None,
                'pre_market_price': str(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': str(session.atr_5min) if session.atr_5min else None,
                'atr_10min': str(session.atr_10min) if session.atr_10min else None,
                'atr_15min': str(session.atr_15min) if session.atr_15min else None,
                'daily_atr': str(session.daily_atr) if session.daily_atr else None,
                'atr_high': str(session.atr_high) if session.atr_high else None,
                'atr_low': str(session.atr_low) if session.atr_low else None
            }
            
            # Insert into trading_sessions table
            result = self.client.table('trading_sessions').insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created session {session.ticker_id} with ID: {session_id}")
                
                # Save price levels if any exist
                if session.m15_levels:
                    self._save_price_levels(session_id, session.m15_levels)
                
                return True, session_id
            
            return False, None
            
        except APIError as e:
            logger.error(f"API error creating session: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            return False, None
    
    def get_session(self, ticker_id: str) -> Optional[TradingSession]:
        """
        Retrieve a trading session by ticker_id.
        
        Args:
            ticker_id: Unique identifier (e.g., "AAPL.120124")
            
        Returns:
            TradingSession object or None if not found
        """
        try:
            # Query the trading_sessions table
            result = self.client.table('trading_sessions')\
                .select("*")\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                session_id = session_data['id']
                
                # Convert database record to TradingSession object
                session = self._session_from_db(session_data)
                
                # Load associated price levels
                price_levels = self._get_price_levels(session_id)
                session.m15_levels = price_levels
                
                return session
            
            logger.warning(f"Session not found: {ticker_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {ticker_id}: {e}")
            return None
    
    def update_session(self, session: TradingSession) -> bool:
        """
        Update an existing trading session.
        
        Args:
            session: TradingSession object with updated data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, get the session ID
            existing = self.client.table('trading_sessions')\
                .select("id")\
                .eq('ticker_id', session.ticker_id)\
                .execute()
            
            if not existing.data:
                logger.error(f"Session not found for update: {session.ticker_id}")
                return False
            
            session_id = existing.data[0]['id']
            
            # Prepare update data
            update_data = {
                'weekly_data': session.weekly_data.to_dict() if session.weekly_data else None,
                'daily_data': session.daily_data.to_dict() if session.daily_data else None,
                'pre_market_price': str(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': str(session.atr_5min) if session.atr_5min else None,
                'atr_10min': str(session.atr_10min) if session.atr_10min else None,
                'atr_15min': str(session.atr_15min) if session.atr_15min else None,
                'daily_atr': str(session.daily_atr) if session.daily_atr else None,
                'atr_high': str(session.atr_high) if session.atr_high else None,
                'atr_low': str(session.atr_low) if session.atr_low else None
            }
            
            # Update the session
            result = self.client.table('trading_sessions')\
                .update(update_data)\
                .eq('id', session_id)\
                .execute()
            
            # Update price levels (delete and re-insert for simplicity)
            if session.m15_levels:
                self._delete_price_levels(session_id)
                self._save_price_levels(session_id, session.m15_levels)
            
            logger.info(f"Updated session: {session.ticker_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session.ticker_id}: {e}")
            return False
    
    def list_sessions(self, ticker: Optional[str] = None, 
                     start_date: Optional[date] = None,
                     end_date: Optional[date] = None) -> List[TradingSession]:
        """
        List trading sessions with optional filters.
        
        Args:
            ticker: Filter by ticker symbol
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of TradingSession objects
        """
        try:
            # Build query
            query = self.client.table('trading_sessions').select("*")
            
            # Apply filters
            if ticker:
                query = query.eq('ticker', ticker.upper())
            if start_date:
                query = query.gte('date', start_date.isoformat())
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            # Execute query with ordering
            result = query.order('date', desc=True).execute()
            
            sessions = []
            for session_data in result.data:
                session = self._session_from_db(session_data)
                sessions.append(session)
            
            logger.info(f"Retrieved {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    # ==================== Analysis Run Operations ====================
    
    def create_analysis_run(self, session_id: str, run_type: str = 'manual') -> Optional[str]:
        """
        Create a new analysis run record for tracking calculations.
        
        Args:
            session_id: ID of the trading session
            run_type: Type of run ('manual', 'scheduled', 'recalculation')
            
        Returns:
            Analysis run ID or None if failed
        """
        try:
            run_data = {
                'session_id': session_id,
                'run_type': run_type,
                'status': 'running',
                'metadata': {
                    'started_by': 'user',
                    'version': '1.0'
                }
            }
            
            result = self.client.table('analysis_runs').insert(run_data).execute()
            
            if result.data:
                run_id = result.data[0]['id']
                logger.info(f"Created analysis run: {run_id}")
                return run_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating analysis run: {e}")
            return None
    
    def complete_analysis_run(self, run_id: str, status: str = 'completed') -> bool:
        """
        Mark an analysis run as completed.
        
        Args:
            run_id: Analysis run ID
            status: Final status ('completed' or 'failed')
            
        Returns:
            bool: Success status
        """
        try:
            update_data = {
                'status': status,
                'completion_timestamp': datetime.now().isoformat()
            }
            
            self.client.table('analysis_runs')\
                .update(update_data)\
                .eq('id', run_id)\
                .execute()
            
            logger.info(f"Completed analysis run {run_id} with status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing analysis run: {e}")
            return False
    
    # ==================== Calculated Data Operations ====================
    
    def save_hvn_zones(self, session_id: str, run_id: str, 
                      zones: List[Dict[str, Any]]) -> bool:
        """
        Save HVN (High Volume Node) zones for a session.
        
        Args:
            session_id: Trading session ID
            run_id: Analysis run ID
            zones: List of HVN zone dictionaries
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare zone data for insertion
            zone_records = []
            for zone in zones:
                record = {
                    'session_id': session_id,
                    'analysis_run_id': run_id,
                    'zone_high': str(zone['zone_high']),
                    'zone_low': str(zone['zone_low']),
                    'volume_profile': zone.get('volume_profile', {}),
                    'percentile_rank': zone.get('percentile_rank', 0),
                    'is_primary_zone': zone.get('is_primary', False),
                    'timeframe': zone.get('timeframe', '15min')
                }
                zone_records.append(record)
            
            # Insert all zones
            if zone_records:
                self.client.table('hvn_zones').insert(zone_records).execute()
                logger.info(f"Saved {len(zone_records)} HVN zones")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving HVN zones: {e}")
            return False
    
    def save_camarilla_levels(self, session_id: str, run_id: str,
                             levels: Dict[str, Decimal]) -> bool:
        """
        Save Camarilla pivot levels for a session.
        
        Args:
            session_id: Trading session ID
            run_id: Analysis run ID
            levels: Dictionary of Camarilla levels
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare Camarilla data
            camarilla_data = {
                'session_id': session_id,
                'analysis_run_id': run_id,
                'pivot_point': str(levels['pivot']),
                'r1': str(levels['r1']),
                'r2': str(levels['r2']),
                'r3': str(levels['r3']),
                'r4': str(levels['r4']),
                's1': str(levels['s1']),
                's2': str(levels['s2']),
                's3': str(levels['s3']),
                's4': str(levels['s4']),
                'calculated_from_date': levels['calculated_from_date'].isoformat()
            }
            
            self.client.table('camarilla_levels').insert(camarilla_data).execute()
            logger.info("Saved Camarilla levels")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Camarilla levels: {e}")
            return False
    
    def save_confluence_scores(self, session_id: str, run_id: str,
                              scores: List[Dict[str, Any]]) -> bool:
        """
        Save confluence scores for price levels.
        
        Args:
            session_id: Trading session ID
            run_id: Analysis run ID
            scores: List of confluence score dictionaries
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare score records
            score_records = []
            for idx, score in enumerate(scores):
                record = {
                    'session_id': session_id,
                    'analysis_run_id': run_id,
                    'price_level': str(score['price_level']),
                    'score': score['score'],
                    'contributing_factors': score['factors'],
                    'level_type': score.get('level_type', 'unknown'),
                    'rank': idx + 1  # Assuming scores are pre-sorted
                }
                score_records.append(record)
            
            # Insert all scores
            if score_records:
                self.client.table('confluence_scores').insert(score_records).execute()
                logger.info(f"Saved {len(score_records)} confluence scores")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving confluence scores: {e}")
            return False
    
    # ==================== Private Helper Methods ====================
    
    def _session_from_db(self, data: Dict[str, Any]) -> TradingSession:
        """
        Convert database record to TradingSession object.
        
        Args:
            data: Database record dictionary
            
        Returns:
            TradingSession object
        """
        # Create base session
        session = TradingSession(
            ticker=data['ticker'],
            date=date.fromisoformat(data['date']),
            is_live=data.get('is_live', True)
        )
        
        # Set optional dates
        if data.get('historical_date'):
            session.historical_date = date.fromisoformat(data['historical_date'])
        if data.get('historical_time'):
            session.historical_time = time.fromisoformat(data['historical_time'])
        
        # Set analysis data
        if data.get('weekly_data'):
            session.weekly_data = WeeklyData.from_dict(data['weekly_data'])
        if data.get('daily_data'):
            session.daily_data = DailyData.from_dict(data['daily_data'])
        
        # Set metrics
        if data.get('pre_market_price'):
            session.pre_market_price = Decimal(data['pre_market_price'])
        if data.get('atr_5min'):
            session.atr_5min = Decimal(data['atr_5min'])
        if data.get('atr_10min'):
            session.atr_10min = Decimal(data['atr_10min'])
        if data.get('atr_15min'):
            session.atr_15min = Decimal(data['atr_15min'])
        if data.get('daily_atr'):
            session.daily_atr = Decimal(data['daily_atr'])
        if data.get('atr_high'):
            session.atr_high = Decimal(data['atr_high'])
        if data.get('atr_low'):
            session.atr_low = Decimal(data['atr_low'])
        
        # Set timestamps
        if data.get('created_at'):
            session.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('updated_at'):
            session.updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return session
    
    def _save_price_levels(self, session_id: str, levels: List[PriceLevel]) -> bool:
        """
        Save price levels for a session.
        
        Args:
            session_id: Trading session ID
            levels: List of PriceLevel objects
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare level records
            level_records = []
            for level in levels:
                record = {
                    'session_id': session_id,
                    'level_id': level.level_id,
                    'line_price': str(level.line_price),
                    'candle_datetime': level.candle_datetime.isoformat(),
                    'candle_high': str(level.candle_high),
                    'candle_low': str(level.candle_low)
                }
                level_records.append(record)
            
            # Insert all levels
            if level_records:
                self.client.table('price_levels').insert(level_records).execute()
                logger.info(f"Saved {len(level_records)} price levels")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving price levels: {e}")
            return False
    
    def _get_price_levels(self, session_id: str) -> List[PriceLevel]:
        """
        Retrieve price levels for a session.
        
        Args:
            session_id: Trading session ID
            
        Returns:
            List of PriceLevel objects
        """
        try:
            result = self.client.table('price_levels')\
                .select("*")\
                .eq('session_id', session_id)\
                .execute()
            
            levels = []
            for level_data in result.data:
                level = PriceLevel(
                    line_price=Decimal(level_data['line_price']),
                    candle_datetime=datetime.fromisoformat(level_data['candle_datetime']),
                    candle_high=Decimal(level_data['candle_high']),
                    candle_low=Decimal(level_data['candle_low']),
                    level_id=level_data['level_id']
                )
                levels.append(level)
            
            return levels
            
        except Exception as e:
            logger.error(f"Error retrieving price levels: {e}")
            return []
    
    def _delete_price_levels(self, session_id: str) -> bool:
        """
        Delete all price levels for a session.
        
        Args:
            session_id: Trading session ID
            
        Returns:
            bool: Success status
        """
        try:
            self.client.table('price_levels')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting price levels: {e}")
            return False