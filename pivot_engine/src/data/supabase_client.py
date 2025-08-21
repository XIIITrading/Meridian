"""
Supabase client wrapper for Meridian Trading System
Handles all database operations and data persistence
UPDATED: Pure Pivot Confluence System - M15 zones removed
"""

import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import logging
import json

from supabase import create_client, Client
from postgrest.exceptions import APIError

from data.models import (
    TradingSession, WeeklyData, DailyData, PivotConfluenceData,
    TrendDirection
)

import traceback

# Set up logging
logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper class for all Supabase database operations - Pure Pivot Confluence System.
    Provides methods for CRUD operations on trading sessions and pivot confluence data.
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
        logger.info("Supabase client initialized (Pivot Confluence System)")
    
    # ==================== Trading Session Operations ====================
    
    def create_session(self, session: TradingSession) -> Tuple[bool, Optional[str]]:
        """
        Create a new pivot trading session in the database.
        
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
                'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': float(session.atr_5min) if session.atr_5min else None,
                'atr_2hour': float(session.atr_2hour) if session.atr_2hour else None,
                'atr_15min': float(session.atr_15min) if session.atr_15min else None,
                'daily_atr': float(session.daily_atr) if session.daily_atr else None,
                'atr_high': float(session.atr_high) if session.atr_high else None,
                'atr_low': float(session.atr_low) if session.atr_low else None
            }
            
            # Insert into trading_sessions table
            result = self.client.table('trading_sessions').insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created pivot session {session.ticker_id} with ID: {session_id}")
                
                # Save weekly analysis to separate table
                if session.weekly_data:
                    self.save_weekly_analysis(session_id, session)
                
                # Save daily analysis to separate table
                if session.daily_data:
                    self.save_daily_analysis(session_id, session)
                
                # Save to denormalized pivots_zones table
                pivot_confluence_results = getattr(session, 'pivot_confluence_results', None)
                pivot_confluence_text = getattr(session, 'pivot_confluence_text', None)
                pivot_confluence_settings = getattr(session, 'pivot_confluence_settings', None)
                
                self.save_to_pivots_zones(session, pivot_confluence_results, pivot_confluence_text, pivot_confluence_settings)
                
                return True, session_id
            
            return False, None
            
        except APIError as e:
            logger.error(f"API error creating pivot session: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error creating pivot session: {e}")
            return False, None
    
    def get_session(self, ticker_id: str) -> Optional[TradingSession]:
        """
        Retrieve a pivot trading session by ticker_id.
        
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
                
                # Load weekly analysis from separate table
                weekly_data = self._get_weekly_analysis(session_id)
                if weekly_data:
                    session.weekly_data = weekly_data
                
                # Load daily analysis from separate table
                daily_data = self._get_daily_analysis(session_id)
                if daily_data:
                    session.daily_data = daily_data
                
                # Load pivot confluence data from pivots_zones table
                pivot_data = self._get_pivot_confluence_data(ticker_id)
                if pivot_data:
                    session.pivot_confluence_data = pivot_data
                
                return session
            
            logger.warning(f"Pivot session not found: {ticker_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving pivot session {ticker_id}: {e}")
            return None
    
    def update_session(self, session: TradingSession) -> bool:
        """
        Update an existing pivot trading session.
        
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
                logger.error(f"Pivot session not found for update: {session.ticker_id}")
                return False
            
            session_id = existing.data[0]['id']
            
            # Prepare update data
            update_data = {
                'is_live': session.is_live,
                'historical_date': session.historical_date.isoformat() if session.historical_date else None,
                'historical_time': session.historical_time.isoformat() if session.historical_time else None,
                'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
                'atr_5min': float(session.atr_5min) if session.atr_5min else None,
                'atr_2hour': float(session.atr_2hour) if session.atr_2hour else None,
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
            
            # Update weekly analysis in separate table
            if session.weekly_data:
                self.save_weekly_analysis(session_id, session)
            
            # Update daily analysis in separate table
            if session.daily_data:
                self.save_daily_analysis(session_id, session)
            
            # Save to denormalized pivots_zones table
            pivot_confluence_results = getattr(session, 'pivot_confluence_results', None)
            pivot_confluence_text = getattr(session, 'pivot_confluence_text', None)
            pivot_confluence_settings = getattr(session, 'pivot_confluence_settings', None)
            
            self.save_to_pivots_zones(session, pivot_confluence_results, pivot_confluence_text, pivot_confluence_settings)
            
            logger.info(f"Updated pivot session: {session.ticker_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating pivot session {session.ticker_id}: {e}")
            return False
    
    def save_to_pivots_zones(self, session: TradingSession, 
                            pivot_confluence_results: Optional[Any] = None,
                            pivot_confluence_text: Optional[str] = None,
                            pivot_confluence_settings: Optional[str] = None) -> bool:
        """
        Save session data to denormalized pivots_zones table.
        Maps all available fields from session object to single row format.
        Includes pivot confluence analysis results, settings, and formatted text.
        
        Args:
            session: TradingSession object with all data
            pivot_confluence_results: Raw pivot confluence analysis object
            pivot_confluence_text: Formatted display text from analysis
            pivot_confluence_settings: User confluence checkbox settings (JSON)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Saving to pivots_zones table: {session.ticker_id}")
            
            # Prepare the data record for pivots_zones table
            pivots_zones_data = {
                # Primary identification
                'ticker_id': session.ticker_id,
                'ticker': session.ticker,
                'session_date': session.date.isoformat(),
                'is_live': session.is_live,
                'historical_datetime': datetime.combine(
                    session.historical_date, session.historical_time
                ).isoformat() if session.historical_date and session.historical_time else None,
                'analysis_datetime': datetime.now().isoformat(),
                'analysis_status': 'completed' if pivot_confluence_results or pivot_confluence_text else 'pending',
                
                # Weekly Analysis (5 fields + price levels)
                'weekly_trend_direction': session.weekly_data.trend_direction.value if session.weekly_data else None,
                'weekly_internal_trend': session.weekly_data.internal_trend.value if session.weekly_data else None,
                'weekly_position_structure': float(session.weekly_data.position_structure) if session.weekly_data else None,
                'weekly_eow_bias': session.weekly_data.eow_bias.value if session.weekly_data else None,
                'weekly_notes': session.weekly_data.notes if session.weekly_data else None,
                
                # Daily Analysis (5 fields + price levels)
                'daily_trend_direction': session.daily_data.trend_direction.value if session.daily_data else None,
                'daily_internal_trend': session.daily_data.internal_trend.value if session.daily_data else None,
                'daily_position_structure': float(session.daily_data.position_structure) if session.daily_data else None,
                'daily_eod_bias': session.daily_data.eod_bias.value if session.daily_data else None,
                'daily_notes': session.daily_data.notes if session.daily_data else None,
                
                # Pivot Confluence Settings (JSON)
                'pivot_confluence_settings': pivot_confluence_settings,
                
                # Price and ATR data (8 fields)
                'pre_market_price': float(session.pre_market_price) if session.pre_market_price else None,
                'current_price': float(session.pre_market_price) if session.pre_market_price else None,  # Using pre_market as current
                'atr_5min': float(session.atr_5min) if session.atr_5min else None,
                'atr_2hour': float(session.atr_2hour) if session.atr_2hour else None,
                'atr_15min': float(session.atr_15min) if session.atr_15min else None,
                'daily_atr': float(session.daily_atr) if session.daily_atr else None,
                'atr_high': float(session.atr_high) if session.atr_high else None,
                'atr_low': float(session.atr_low) if session.atr_low else None,
                
                # Analysis results text
                'pivot_confluence_text': pivot_confluence_text if isinstance(pivot_confluence_text, str) else None,
                
                # Timestamps
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add weekly price levels (wl1-wl4)
            if session.weekly_data and hasattr(session.weekly_data, 'price_levels'):
                for i, level in enumerate(session.weekly_data.price_levels[:4], 1):
                    if level and float(level) > 0:
                        pivots_zones_data[f'weekly_wl{i}'] = float(level)
            
            # Add daily price levels (dl1-dl6)
            if session.daily_data and session.daily_data.price_levels:
                for i, level in enumerate(session.daily_data.price_levels[:6], 1):
                    if level and float(level) > 0:
                        pivots_zones_data[f'daily_dl{i}'] = float(level)
            
            # Add Daily Camarilla pivot data if available
            if pivot_confluence_results and hasattr(pivot_confluence_results, 'pivot_zones'):
                logger.debug(f"Processing {len(pivot_confluence_results.pivot_zones)} pivot zones")
                
                for zone in pivot_confluence_results.pivot_zones:
                    level_name = zone.level_name.lower()  # r6, r4, r3, s3, s4, s6
                    
                    # Pivot prices
                    pivots_zones_data[f'daily_cam_{level_name}_price'] = float(zone.pivot_price) if zone.pivot_price else None
                    
                    # Zone ranges (pivot ± 5min ATR)
                    pivots_zones_data[f'daily_cam_{level_name}_zone_low'] = float(zone.zone_low) if zone.zone_low else None
                    pivots_zones_data[f'daily_cam_{level_name}_zone_high'] = float(zone.zone_high) if zone.zone_high else None
                    
                    # Confluence scores and levels
                    pivots_zones_data[f'daily_cam_{level_name}_confluence_score'] = float(zone.confluence_score) if zone.confluence_score else None
                    
                    # Handle confluence_level (might be enum)
                    if hasattr(zone.level_designation, 'value'):
                        confluence_level_str = f"L{zone.level_designation.value}"
                    else:
                        confluence_level_str = f"L{zone.level_designation}"
                    pivots_zones_data[f'daily_cam_{level_name}_confluence_level'] = confluence_level_str
                    
                    # Confluence count (number of sources that contributed)
                    pivots_zones_data[f'daily_cam_{level_name}_confluence_count'] = int(zone.confluence_count) if hasattr(zone, 'confluence_count') else 0
                    
                    logger.debug(f"Pivot {zone.level_name}: price=${zone.pivot_price:.2f}, "
                               f"zone=${zone.zone_low:.2f}-${zone.zone_high:.2f}, "
                               f"score={zone.confluence_score:.1f}, level={confluence_level_str}")
            
            # Debug: Verify all values are JSON serializable
            try:
                json.dumps(pivots_zones_data)
                logger.debug("pivots_zones_data is JSON serializable")
            except TypeError as e:
                logger.error(f"pivots_zones_data contains non-serializable data: {e}")
                # Log which fields are problematic
                for key, value in pivots_zones_data.items():
                    try:
                        json.dumps({key: value})
                    except:
                        logger.error(f"Field {key} is not JSON serializable: type={type(value)}, value={value}")
                return False
            
            # Use INSERT ... ON CONFLICT UPDATE for idempotency
            result = self.client.table('pivots_zones')\
                .upsert(pivots_zones_data, on_conflict='ticker_id')\
                .execute()
            
            if result.data:
                logger.info(f"Successfully saved to pivots_zones: {session.ticker_id}")
                return True
            else:
                logger.warning(f"No data returned when saving to pivots_zones: {session.ticker_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving to pivots_zones table: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _get_pivot_confluence_data(self, ticker_id: str) -> Optional[PivotConfluenceData]:
        """
        Retrieve pivot confluence data from pivots_zones table.
        
        Args:
            ticker_id: Unique identifier (e.g., "AAPL.120124")
            
        Returns:
            PivotConfluenceData object or None if not found
        """
        try:
            result = self.client.table('pivots_zones')\
                .select("*")\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                
                # Create PivotConfluenceData object
                pivot_data = PivotConfluenceData()
                
                # Map Daily Camarilla pivot prices
                levels = ['r6', 'r4', 'r3', 's3', 's4', 's6']
                for level in levels:
                    # Pivot prices
                    price_field = f'daily_cam_{level}_price'
                    if data.get(price_field):
                        setattr(pivot_data, price_field, Decimal(str(data[price_field])))
                    
                    # Zone ranges
                    low_field = f'daily_cam_{level}_zone_low'
                    high_field = f'daily_cam_{level}_zone_high'
                    if data.get(low_field):
                        setattr(pivot_data, low_field, Decimal(str(data[low_field])))
                    if data.get(high_field):
                        setattr(pivot_data, high_field, Decimal(str(data[high_field])))
                    
                    # Confluence scores and levels
                    score_field = f'daily_cam_{level}_confluence_score'
                    level_field = f'daily_cam_{level}_confluence_level'
                    count_field = f'daily_cam_{level}_confluence_count'
                    
                    if data.get(score_field):
                        setattr(pivot_data, score_field, Decimal(str(data[score_field])))
                    if data.get(level_field):
                        setattr(pivot_data, level_field, data[level_field])
                    if data.get(count_field):
                        setattr(pivot_data, count_field, int(data[count_field]))
                
                # Settings and text
                if data.get('pivot_confluence_settings'):
                    pivot_data.pivot_confluence_settings = data['pivot_confluence_settings']
                if data.get('pivot_confluence_text'):
                    pivot_data.pivot_confluence_text = data['pivot_confluence_text']
                
                logger.debug(f"Loaded pivot confluence data for {ticker_id}")
                return pivot_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving pivot confluence data: {e}")
            return None
    
    def list_sessions(self, ticker: Optional[str] = None, 
                     start_date: Optional[date] = None,
                     end_date: Optional[date] = None) -> List[TradingSession]:
        """
        List pivot trading sessions with optional filters.
        
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
            
            logger.info(f"Retrieved {len(sessions)} pivot sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing pivot sessions: {e}")
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
        Create a new analysis run record for tracking pivot calculations.
        
        Args:
            session_id: ID of the trading session
            run_type: Type of run ('manual', 'scheduled', 'pivot_recalculation')
            
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
                    'version': '2.0',
                    'analysis_type': 'pivot_confluence'
                }
            }
            
            result = self.client.table('analysis_runs').insert(run_data).execute()
            
            if result.data:
                run_id = result.data[0]['id']
                logger.info(f"Created pivot analysis run: {run_id}")
                return run_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating pivot analysis run: {e}")
            return None
    
    def complete_analysis_run(self, run_id: str, status: str = 'completed') -> bool:
        """
        Mark a pivot analysis run as completed.
        
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
            
            logger.info(f"Completed pivot analysis run {run_id} with status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing pivot analysis run: {e}")
            return False
    
    # ==================== Private Helper Methods ====================
    
    def _session_from_db(self, data: Dict[str, Any]) -> TradingSession:
        """
        Convert database record to TradingSession object.
        Note: weekly_data, daily_data, and pivot_confluence_data are loaded separately
        
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
        if data.get('atr_2hour'):
            session.atr_2hour = Decimal(str(data['atr_2hour']))
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
        
        # Note: weekly_data, daily_data, and pivot_confluence_data are loaded separately
        
        return session