"""
Database service layer for Meridian Trading System
Handles communication between UI and database
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from PyQt6.QtCore import QObject, pyqtSignal

from data.models import (
    TradingSession, PriceLevel, WeeklyData, DailyData, TrendDirection
)
from data.supabase_client import SupabaseClient
from data.validators import validate_trading_session
import config

logger = logging.getLogger(__name__)


class DatabaseService(QObject):
    """Service class for database operations with Qt signal support"""
    
    # Signals for UI feedback
    save_started = pyqtSignal()
    save_completed = pyqtSignal(str)  # session_id
    save_failed = pyqtSignal(str)  # error message
    
    load_started = pyqtSignal()
    load_completed = pyqtSignal(dict)  # session data
    load_failed = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client"""
        try:
            if config.validate_config():
                self.client = SupabaseClient(
                    url=config.SUPABASE_URL,
                    key=config.SUPABASE_KEY
                )
                logger.info("Database service initialized successfully")
            else:
                logger.error("Failed to initialize database - missing configuration")
        except Exception as e:
            logger.error(f"Failed to initialize database client: {e}")
    
    def save_session(self, session_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save a trading session from UI data format.
        
        Args:
            session_data: Dictionary from UI with session data
            
        Returns:
            Tuple of (success, session_id or error message)
        """
        if not self.client:
            error_msg = "Database client not initialized"
            self.save_failed.emit(error_msg)
            return False, error_msg
        
        self.save_started.emit()
        
        try:
            # Convert UI data to model objects
            session = self._create_session_from_ui_data(session_data)
            
            # Validate the session
            is_valid, errors = validate_trading_session(session)
            if not is_valid:
                error_msg = "Validation failed: " + str(errors)
                self.save_failed.emit(error_msg)
                return False, error_msg
            
            # Check if session already exists
            existing = self.client.get_session(session.ticker_id)
            
            if existing:
                # Update existing session
                success = self.client.update_session(session)
                if success:
                    self.save_completed.emit(session.ticker_id)
                    return True, session.ticker_id
                else:
                    error_msg = "Failed to update session"
                    self.save_failed.emit(error_msg)
                    return False, error_msg
            else:
                # Create new session
                success, session_id = self.client.create_session(session)
                if success:
                    self.save_completed.emit(session_id)
                    return True, session_id
                else:
                    error_msg = "Failed to create session"
                    self.save_failed.emit(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"Error saving session: {str(e)}"
            logger.error(error_msg)
            self.save_failed.emit(error_msg)
            return False, error_msg
    
    def load_session(self, ticker_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a trading session and convert to UI format.
        
        Args:
            ticker_id: Session identifier (e.g., "AAPL.120124")
            
        Returns:
            Dictionary in UI format or None
        """
        if not self.client:
            self.load_failed.emit("Database client not initialized")
            return None
        
        self.load_started.emit()
        
        try:
            session = self.client.get_session(ticker_id)
            if session:
                ui_data = self._convert_session_to_ui_format(session)
                self.load_completed.emit(ui_data)
                return ui_data
            else:
                self.load_failed.emit(f"Session not found: {ticker_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error loading session: {str(e)}"
            logger.error(error_msg)
            self.load_failed.emit(error_msg)
            return None
    
    def list_sessions(self, ticker: Optional[str] = None,
                     start_date: Optional[date] = None,
                     end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        List available sessions with optional filters.
        
        Returns:
            List of session summaries for UI display
        """
        if not self.client:
            return []
        
        try:
            sessions = self.client.list_sessions(ticker, start_date, end_date)
            
            # Convert to summary format for UI
            summaries = []
            for session in sessions:
                summary = {
                    'ticker': session.ticker,
                    'ticker_id': session.ticker_id,
                    'date': session.date,
                    'is_live': session.is_live,
                    'has_weekly': session.weekly_data is not None,
                    'has_daily': session.daily_data is not None,
                    'level_count': len(session.m15_levels),
                    'created_at': session.created_at
                }
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def _create_session_from_ui_data(self, data: Dict[str, Any]) -> TradingSession:
        """Convert UI data format to TradingSession model"""
        # Parse the datetime - already in UTC
        session_datetime = data['datetime']
        session_date = session_datetime.date()
        
        # Create the session
        session = TradingSession(
            ticker=data['ticker'],
            date=session_date,
            is_live=data['is_live']
        )
        
        # If not live, use the entered date/time as historical date/time
        if not data['is_live']:
            session.historical_date = session_date
            session.historical_time = session_datetime.time()
        
        # Add timestamps - in UTC
        session.created_at = data.get('timestamp', datetime.utcnow())
        session.updated_at = datetime.utcnow()
        
        # Add weekly data if present
        if data.get('weekly'):
            weekly = data['weekly']
            session.weekly_data = WeeklyData(
                trend_direction=TrendDirection.from_string(weekly['trend_direction']),
                internal_trend=TrendDirection.from_string(weekly['internal_trend']),
                position_structure=float(weekly['position_structure']),
                eow_bias=TrendDirection.from_string(weekly['eow_bias']),
                notes=weekly.get('notes', '')
            )
        
        # Add daily data if present
        if data.get('daily'):
            daily = data['daily']
            session.daily_data = DailyData(
                trend_direction=TrendDirection.from_string(daily['trend_direction']),
                internal_trend=TrendDirection.from_string(daily['internal_trend']),
                position_structure=float(daily['position_structure']),
                eod_bias=TrendDirection.from_string(daily['eod_bias']),
                price_levels=[Decimal(str(level)) for level in daily.get('price_levels', [])],
                notes=daily.get('notes', '')
            )
        
        # Add metrics - IMPORTANT: These need to be collected from the UI
        # Get pre_market_price from the data if provided
        if data.get('pre_market_price'):
            session.pre_market_price = Decimal(str(data['pre_market_price']))
        
        # Get ATR values if they exist in the metrics frame
        if data.get('metrics'):
            metrics = data['metrics']
            if 'atr_5min' in metrics:
                session.atr_5min = Decimal(str(metrics['atr_5min']))
            if 'atr_10min' in metrics:
                session.atr_10min = Decimal(str(metrics['atr_10min']))
            if 'atr_15min' in metrics:
                session.atr_15min = Decimal(str(metrics['atr_15min']))
            if 'daily_atr' in metrics:
                session.daily_atr = Decimal(str(metrics['daily_atr']))
            if 'atr_high' in metrics:
                session.atr_high = Decimal(str(metrics['atr_high']))
            if 'atr_low' in metrics:
                session.atr_low = Decimal(str(metrics['atr_low']))
        
        # Simplified M15 zones handling
        if data.get('zones'):
            for zone in data['zones']:
                zone_num = zone['zone_number']
                
                # Create level_id
                level_id = session.generate_level_id(len(session.m15_levels))
                
                # Default to session datetime
                zone_datetime = session_datetime
                
                # Simple date/time parsing
                try:
                    date_str = zone.get('date', '')
                    time_str = zone.get('time', '')
                    
                    # Only parse if we have valid looking data
                    if (date_str and date_str != 'yyyy-mm-dd' and 
                        time_str and time_str != 'hh:mm:ss'):
                        
                        # Simple parsing
                        date_parts = date_str.split('-')
                        time_parts = time_str.split(':')
                        
                        if len(date_parts) == 3 and len(time_parts) >= 2:
                            year = int(date_parts[0])
                            month = int(date_parts[1])
                            day = int(date_parts[2])
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            second = int(time_parts[2]) if len(time_parts) > 2 else 0
                            
                            zone_datetime = datetime(year, month, day, hour, minute, second)
                            
                except Exception as e:
                    logger.debug(f"Using session datetime for zone {zone_num}: {e}")
                
                # Create price level with default values for empty fields
                try:
                    level_value = Decimal(str(zone.get('level', 0))) if zone.get('level') else Decimal("0")
                    high_value = Decimal(str(zone.get('high', 0))) if zone.get('high') else Decimal("0")
                    low_value = Decimal(str(zone.get('low', 0))) if zone.get('low') else Decimal("0")
                    
                    # If high/low are 0, use level value
                    if high_value == 0 and level_value > 0:
                        high_value = level_value
                    if low_value == 0 and level_value > 0:
                        low_value = level_value
                    
                    level = PriceLevel(
                        line_price=level_value,
                        candle_datetime=zone_datetime,
                        candle_high=high_value,
                        candle_low=low_value,
                        level_id=level_id
                    )
                    session.m15_levels.append(level)
                    
                except Exception as e:
                    logger.warning(f"Skipping zone {zone_num} due to error: {e}")
        
        return session
    
    def _convert_session_to_ui_format(self, session: TradingSession) -> Dict[str, Any]:
        """Convert TradingSession model to UI data format"""
        ui_data = {
            'ticker': session.ticker,
            'is_live': session.is_live,
            'datetime': datetime.combine(session.date, datetime.min.time()),
            'timestamp': session.created_at or datetime.now()
        }
        
        # Add weekly data
        if session.weekly_data:
            ui_data['weekly'] = {
                'trend_direction': session.weekly_data.trend_direction.value,
                'internal_trend': session.weekly_data.internal_trend.value,
                'position_structure': session.weekly_data.position_structure,
                'eow_bias': session.weekly_data.eow_bias.value,
                'notes': session.weekly_data.notes
            }
        
        # Add daily data
        if session.daily_data:
            ui_data['daily'] = {
                'trend_direction': session.daily_data.trend_direction.value,
                'internal_trend': session.daily_data.internal_trend.value,
                'position_structure': session.daily_data.position_structure,
                'eod_bias': session.daily_data.eod_bias.value,
                'price_levels': [float(level) for level in session.daily_data.price_levels],
                'notes': session.daily_data.notes
            }
        
        # Add M15 zones - UPDATED SECTION
        zones = []
        for i, level in enumerate(session.m15_levels):
            zone = {
                'zone_number': i + 1,
                'date': level.candle_datetime.strftime('%Y-%m-%d'),
                'time': level.candle_datetime.strftime('%H:%M:%S'),
                'level': str(level.line_price),
                'high': str(level.candle_high),
                'low': str(level.candle_low)
            }
            zones.append(zone)
        ui_data['zones'] = zones
        
        return ui_data