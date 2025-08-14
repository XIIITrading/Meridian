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
            # Note: weekly_data and daily_data are stored in separate tables
            session_data = {
                'ticker': session.ticker,
                'ticker_id': session.ticker_id,
                'date': session.date.isoformat(),
                'is_live': session.is_live,
                'historical_date': session.historical_date.isoformat() if session.historical_date else None,
                'historical_time': session.historical_time.isoformat() if session.historical_time else None,
                'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': float(session.atr_5min) if session.atr_5min else None,
                'atr_10min': float(session.atr_10min) if session.atr_10min else None,
                'atr_15min': float(session.atr_15min) if session.atr_15min else None,
                'daily_atr': float(session.daily_atr) if session.daily_atr else None,
                'atr_high': float(session.atr_high) if session.atr_high else None,
                'atr_low': float(session.atr_low) if session.atr_low else None
            }
            
            # Insert into trading_sessions table
            result = self.client.table('trading_sessions').insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created session {session.ticker_id} with ID: {session_id}")
                
                # Save price levels if any exist
                if session.m15_levels:
                    self._save_price_levels(session_id, session.m15_levels)
                
                # Save weekly analysis to separate table
                if session.weekly_data:
                    self.save_weekly_analysis(session_id, session)
                
                # Save daily analysis to separate table
                if session.daily_data:
                    self.save_daily_analysis(session_id, session)
                
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
                
                # Load weekly analysis from separate table
                weekly_data = self._get_weekly_analysis(session_id)
                if weekly_data:
                    session.weekly_data = weekly_data
                
                # Load daily analysis from separate table
                daily_data = self._get_daily_analysis(session_id)
                if daily_data:
                    session.daily_data = daily_data
                
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
            
            # Prepare update data - NO weekly_data or daily_data here
            update_data = {
                'is_live': session.is_live,
                'historical_date': session.historical_date.isoformat() if session.historical_date else None,
                'historical_time': session.historical_time.isoformat() if session.historical_time else None,
                'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': float(session.atr_5min) if session.atr_5min else None,
                'atr_10min': float(session.atr_10min) if session.atr_10min else None,
                'atr_15min': float(session.atr_15min) if session.atr_15min else None,
                'daily_atr': float(session.daily_atr) if session.daily_atr else None,
                'atr_high': float(session.atr_high) if session.atr_high else None,
                'atr_low': float(session.atr_low) if session.atr_low else None
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
            
            # Update weekly analysis in separate table
            if session.weekly_data:
                self.save_weekly_analysis(session_id, session)
            
            # Update daily analysis in separate table
            if session.daily_data:
                self.save_daily_analysis(session_id, session)
            
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
    
    # ==================== Weekly Analysis Operations ====================
    
    def save_weekly_analysis(self, session_id: str, session: TradingSession) -> bool:
        """
        Save weekly analysis data to separate table
        
        Args:
            session_id: The trading session UUID
            session: TradingSession object with weekly data
            
        Returns:
            bool: Success status
        """
        try:
            if not session.weekly_data:
                logger.info("No weekly data to save")
                return True
                
            # Prepare weekly analysis data
            weekly_record = {
                'session_id': session_id,
                'ticker': session.ticker,
                'date': session.date.isoformat(),
                'ticker_id': session.ticker_id,
                'trend_direction': session.weekly_data.trend_direction.value,
                'internal_trend': session.weekly_data.internal_trend.value,
                'position_structure': float(session.weekly_data.position_structure),
                'eow_bias': session.weekly_data.eow_bias.value,
                'notes': session.weekly_data.notes
            }
            
            # Extract weekly levels if they exist
            if hasattr(session.weekly_data, 'price_levels') and session.weekly_data.price_levels:
                levels = session.weekly_data.price_levels
                # Map first 4 levels to wl1-wl4
                for i, level in enumerate(levels[:4], 1):
                    if level and float(level) > 0:  # Only add non-zero levels
                        weekly_record[f'wl{i}'] = float(level)
            
            # Check if we need to update or insert
            existing = self.client.table('weekly_analysis')\
                .select("id")\
                .eq('session_id', session_id)\
                .execute()
            
            if existing.data:
                # Update existing record
                result = self.client.table('weekly_analysis')\
                    .update(weekly_record)\
                    .eq('session_id', session_id)\
                    .execute()
                logger.info(f"Updated weekly analysis for session {session_id}")
            else:
                # Insert new record
                result = self.client.table('weekly_analysis')\
                    .insert(weekly_record)\
                    .execute()
                logger.info(f"Created weekly analysis for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving weekly analysis: {e}")
            return False
    
    def _get_weekly_analysis(self, session_id: str) -> Optional[WeeklyData]:
        """
        Retrieve weekly analysis data for a session
        
        Args:
            session_id: The trading session UUID
            
        Returns:
            WeeklyData object or None if not found
        """
        try:
            result = self.client.table('weekly_analysis')\
                .select("*")\
                .eq('session_id', session_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                
                # Extract price levels (wl1-wl4)
                price_levels = []
                for i in range(1, 5):  # wl1 through wl4
                    level_key = f'wl{i}'
                    if level_key in data and data[level_key]:
                        price_levels.append(Decimal(str(data[level_key])))
                
                # Create WeeklyData object
                weekly_data = WeeklyData(
                    trend_direction=TrendDirection(data['trend_direction']),
                    internal_trend=TrendDirection(data['internal_trend']),
                    position_structure=float(data['position_structure']),
                    eow_bias=TrendDirection(data['eow_bias']),
                    notes=data.get('notes', '')
                )
                
                # Set price_levels if the object supports it
                if hasattr(weekly_data, 'price_levels'):
                    weekly_data.price_levels = price_levels
                
                return weekly_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving weekly analysis: {e}")
            return None
    
    # ==================== Daily Analysis Operations ====================
    
    def save_daily_analysis(self, session_id: str, session: TradingSession) -> bool:
        """
        Save daily analysis data to separate table
        
        Args:
            session_id: The trading session UUID
            session: TradingSession object with daily data
            
        Returns:
            bool: Success status
        """
        try:
            if not session.daily_data:
                logger.info("No daily data to save")
                return True
                
            # Prepare daily analysis data
            daily_record = {
                'session_id': session_id,
                'ticker': session.ticker,
                'date': session.date.isoformat(),
                'ticker_id': session.ticker_id,
                'trend_direction': session.daily_data.trend_direction.value,
                'internal_trend': session.daily_data.internal_trend.value,
                'position_structure': float(session.daily_data.position_structure),
                'eod_bias': session.daily_data.eod_bias.value,
                'notes': session.daily_data.notes
            }
            
            # Extract daily price levels if they exist
            if session.daily_data.price_levels:
                levels = session.daily_data.price_levels
                # Map first 6 levels to dl1-dl6
                for i, level in enumerate(levels[:6], 1):
                    if level and float(level) > 0:  # Only add non-zero levels
                        daily_record[f'dl{i}'] = float(level)
            
            # Check if we need to update or insert
            existing = self.client.table('daily_analysis')\
                .select("id")\
                .eq('session_id', session_id)\
                .execute()
            
            if existing.data:
                # Update existing record
                result = self.client.table('daily_analysis')\
                    .update(daily_record)\
                    .eq('session_id', session_id)\
                    .execute()
                logger.info(f"Updated daily analysis for session {session_id}")
            else:
                # Insert new record
                result = self.client.table('daily_analysis')\
                    .insert(daily_record)\
                    .execute()
                logger.info(f"Created daily analysis for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving daily analysis: {e}")
            return False
    
    def _get_daily_analysis(self, session_id: str) -> Optional[DailyData]:
        """
        Retrieve daily analysis data for a session
        
        Args:
            session_id: The trading session UUID
            
        Returns:
            DailyData object or None if not found
        """
        try:
            result = self.client.table('daily_analysis')\
                .select("*")\
                .eq('session_id', session_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                
                # Extract price levels (dl1-dl6)
                price_levels = []
                for i in range(1, 7):  # dl1 through dl6
                    level_key = f'dl{i}'
                    if level_key in data and data[level_key]:
                        price_levels.append(Decimal(str(data[level_key])))
                
                # Create DailyData object
                daily_data = DailyData(
                    trend_direction=TrendDirection(data['trend_direction']),
                    internal_trend=TrendDirection(data['internal_trend']),
                    position_structure=float(data['position_structure']),
                    eod_bias=TrendDirection(data['eod_bias']),
                    price_levels=price_levels,
                    notes=data.get('notes', '')
                )
                
                return daily_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving daily analysis: {e}")
            return None
    
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
    
    # ==================== Private Helper Methods ====================
    
    def _session_from_db(self, data: Dict[str, Any]) -> TradingSession:
        """
        Convert database record to TradingSession object.
        Note: weekly_data and daily_data are loaded separately from their own tables
        
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
        
        # Set metrics
        if data.get('pre_market_price'):
            session.pre_market_price = Decimal(str(data['pre_market_price']))
        if data.get('atr_5min'):
            session.atr_5min = Decimal(str(data['atr_5min']))
        if data.get('atr_10min'):
            session.atr_10min = Decimal(str(data['atr_10min']))
        if data.get('atr_15min'):
            session.atr_15min = Decimal(str(data['atr_15min']))
        if data.get('daily_atr'):
            session.daily_atr = Decimal(str(data['daily_atr']))
        if data.get('atr_high'):
            session.atr_high = Decimal(str(data['atr_high']))
        if data.get('atr_low'):
            session.atr_low = Decimal(str(data['atr_low']))
        
        # Set timestamps
        if data.get('created_at'):
            created_str = data['created_at'].replace('Z', '')
            if '+' not in created_str and not created_str.endswith('00:00'):
                created_str += '+00:00'
            session.created_at = datetime.fromisoformat(created_str)
            
        if data.get('updated_at'):
            updated_str = data['updated_at'].replace('Z', '')
            if '+' not in updated_str and not updated_str.endswith('00:00'):
                updated_str += '+00:00'
            session.updated_at = datetime.fromisoformat(updated_str)
        
        # Note: weekly_data and daily_data are loaded separately via
        # _get_weekly_analysis() and _get_daily_analysis()
        
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
                    'line_price': float(level.line_price),
                    'candle_datetime': level.candle_datetime.isoformat(),
                    'candle_high': float(level.candle_high),
                    'candle_low': float(level.candle_low)
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
                    line_price=Decimal(str(level_data['line_price'])),
                    candle_datetime=datetime.fromisoformat(level_data['candle_datetime']),
                    candle_high=Decimal(str(level_data['candle_high'])),
                    candle_low=Decimal(str(level_data['candle_low'])),
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