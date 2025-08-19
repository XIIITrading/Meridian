"""
Database service layer for Meridian Trading System
Handles communication between UI and database with enhanced debugging
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import traceback
import json

from PyQt6.QtCore import QObject, pyqtSignal

from data.models import (
    TradingSession, PriceLevel, WeeklyData, DailyData, TrendDirection
)
from data.supabase_client import SupabaseClient
from data.validators import validate_trading_session
import config

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseService(QObject):
    """Service class for database operations with Qt signal support and debugging"""
    
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
        """Initialize the Supabase client with debugging"""
        logger.info("="*60)
        logger.info("INITIALIZING DATABASE CLIENT")
        logger.info("="*60)
        
        try:
            logger.debug("Checking configuration...")
            logger.debug(f"Config URL exists: {bool(config.SUPABASE_URL)}")
            logger.debug(f"Config Key exists: {bool(config.SUPABASE_KEY)}")
            
            if config.SUPABASE_URL:
                # Show partial URL for security
                url_preview = config.SUPABASE_URL[:30] + "..." if len(config.SUPABASE_URL) > 30 else config.SUPABASE_URL
                logger.debug(f"URL preview: {url_preview}")
            
            if config.validate_config():
                logger.info("Configuration validated")
                
                self.client = SupabaseClient(
                    url=config.SUPABASE_URL,
                    key=config.SUPABASE_KEY
                )
                logger.info("Database client initialized successfully")
            else:
                logger.error("Configuration validation failed")
                logger.error("Please check your .env file has SUPABASE_URL and SUPABASE_KEY")
                
        except Exception as e:
            logger.error(f"Failed to initialize database client: {e}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
        finally:
            logger.info("="*60)
    
    def save_session(self, session_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save a trading session with detailed debugging
        """
        logger.info("="*60)
        logger.info("DATABASE SERVICE: SAVE SESSION START")
        logger.info("="*60)
        
        if not self.client:
            error_msg = "Database client not initialized - check your .env file"
            logger.error(error_msg)
            self.save_failed.emit(error_msg)
            return False, error_msg
        
        self.save_started.emit()
        
        try:
            # Step 1: Log incoming data
            logger.info("Step 1: Analyzing incoming session data...")
            self._log_data_structure(session_data)
            
            # Step 2: Create session from UI data
            logger.info("Step 2: Creating TradingSession object from UI data...")
            session = self._create_session_from_ui_data(session_data)
            logger.info(f"Session created: ticker_id = {session.ticker_id}")
            
            # Step 3: Log session object details
            logger.info("Step 3: Validating session object...")
            self._log_session_object(session)
            
            # Step 4: Validate the session
            logger.info("Step 4: Running validation checks...")
            is_valid, errors = validate_trading_session(session)
            if not is_valid:
                error_msg = f"Validation failed: {errors}"
                logger.error(error_msg)
                self._log_validation_errors(errors)
                self.save_failed.emit(error_msg)
                return False, error_msg
            logger.info("Validation passed")
            
            # Step 5: Check for existing session
            logger.info(f"Step 5: Checking if session exists: {session.ticker_id}")
            try:
                existing = self.client.get_session(session.ticker_id)
                logger.info(f"Existing session found: {existing is not None}")
            except Exception as e:
                logger.warning(f"Error checking for existing session: {e}")
                existing = None
            
            # Step 6: Save to database
            if existing:
                logger.info(f"Step 6: Updating existing session: {session.ticker_id}")
                success = self.client.update_session(session)
                if success:
                    logger.info(f"Session updated successfully: {session.ticker_id}")
                    self.save_completed.emit(session.ticker_id)
                    return True, session.ticker_id
                else:
                    error_msg = "Failed to update session in database"
                    logger.error(error_msg)
                    self.save_failed.emit(error_msg)
                    return False, error_msg
            else:
                logger.info(f"Step 6: Creating new session: {session.ticker_id}")
                success, session_id = self.client.create_session(session)
                if success:
                    logger.info(f"Session created successfully with ID: {session_id}")
                    self.save_completed.emit(session_id)
                    return True, session_id
                else:
                    error_msg = "Failed to create session in database - check Supabase logs"
                    logger.error(error_msg)
                    self.save_failed.emit(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"Error saving session: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            self.save_failed.emit(error_msg)
            return False, error_msg
        finally:
            logger.info("="*60)
            logger.info("DATABASE SERVICE: SAVE SESSION END")
            logger.info("="*60)
    
    def _log_data_structure(self, data: Dict[str, Any], indent: int = 0):
        """Log the structure of incoming data"""
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                logger.debug(f"{prefix}{key}: <dict> with {len(value)} keys")
                if indent < 2:
                    self._log_data_structure(value, indent + 1)
            elif isinstance(value, list):
                logger.debug(f"{prefix}{key}: <list> with {len(value)} items")
                if value and isinstance(value[0], dict) and indent < 2:
                    logger.debug(f"{prefix}  First item:")
                    self._log_data_structure(value[0], indent + 2)
            elif isinstance(value, datetime):
                logger.debug(f"{prefix}{key}: {value.isoformat()} (datetime)")
            else:
                # Show value preview
                if isinstance(value, str) and len(value) > 50:
                    logger.debug(f"{prefix}{key}: '{value[:50]}...' ({type(value).__name__})")
                else:
                    logger.debug(f"{prefix}{key}: {value} ({type(value).__name__})")
    
    def _log_session_object(self, session: TradingSession):
        """Log details of the session object"""
        logger.debug("Session object details:")
        logger.debug(f"  ticker: {session.ticker}")
        logger.debug(f"  ticker_id: {session.ticker_id}")
        logger.debug(f"  date: {session.date}")
        logger.debug(f"  is_live: {session.is_live}")
        logger.debug(f"  historical_date: {session.historical_date}")
        logger.debug(f"  historical_time: {session.historical_time}")
        
        # Log weekly data
        if session.weekly_data:
            logger.debug("  weekly_data: Present")
            logger.debug(f"    trend_direction: {session.weekly_data.trend_direction}")
            logger.debug(f"    internal_trend: {session.weekly_data.internal_trend}")
            logger.debug(f"    position_structure: {session.weekly_data.position_structure}")
            logger.debug(f"    eow_bias: {session.weekly_data.eow_bias}")
            if hasattr(session.weekly_data, 'price_levels'):
                logger.debug(f"    price_levels: {session.weekly_data.price_levels}")
            logger.debug(f"    notes length: {len(session.weekly_data.notes) if session.weekly_data.notes else 0}")
        else:
            logger.debug("  weekly_data: None")
        
        # Log daily data
        if session.daily_data:
            logger.debug("  daily_data: Present")
            logger.debug(f"    trend_direction: {session.daily_data.trend_direction}")
            logger.debug(f"    price_levels count: {len(session.daily_data.price_levels) if session.daily_data.price_levels else 0}")
        else:
            logger.debug("  daily_data: None")
        
        # Log metrics - UPDATED to use atr_2hour
        logger.debug(f"  pre_market_price: {session.pre_market_price}")
        logger.debug(f"  ATR metrics: 5m={session.atr_5min}, 2hr={session.atr_2hour}, 15m={session.atr_15min}")
        logger.debug(f"  daily_atr: {session.daily_atr}, high={session.atr_high}, low={session.atr_low}")
        
        # Log M15 levels
        logger.debug(f"  m15_levels: {len(session.m15_levels)} levels")
        for i, level in enumerate(session.m15_levels[:3]):  # Log first 3
            logger.debug(f"    Level {i+1}: price={level.line_price}, high={level.candle_high}, low={level.candle_low}")
    
    def _log_validation_errors(self, errors: Dict[str, Any]):
        """Log validation errors in detail"""
        logger.error("Validation Error Details:")
        if isinstance(errors, dict):
            for field, error in errors.items():
                logger.error(f"  {field}: {error}")
        else:
            logger.error(f"  {errors}")
    
    def _create_session_from_ui_data(self, data: Dict[str, Any]) -> TradingSession:
        """Convert UI data format to TradingSession model with debugging"""
        logger.debug("Converting UI data to TradingSession...")
        
        # Parse the datetime
        session_datetime = data['datetime']
        session_date = session_datetime.date()
        logger.debug(f"Session datetime: {session_datetime}, date: {session_date}")
        
        # Create the session
        session = TradingSession(
            ticker=data['ticker'],
            date=session_date,
            is_live=data['is_live']
        )
        logger.debug(f"Base session created: {session.ticker_id}")
        
        # If not live, use the entered date/time as historical
        if not data['is_live']:
            session.historical_date = session_date
            session.historical_time = session_datetime.time()
            logger.debug(f"Historical date/time set: {session.historical_date} {session.historical_time}")
        
        # Add timestamps
        session.created_at = data.get('timestamp', datetime.utcnow())
        session.updated_at = datetime.utcnow()
        
        # Add weekly data if present
        if data.get('weekly'):
            logger.debug("Processing weekly data...")
            weekly = data['weekly']
            
            try:
                # Create WeeklyData object
                session.weekly_data = WeeklyData(
                    trend_direction=TrendDirection.from_string(weekly['trend_direction']),
                    internal_trend=TrendDirection.from_string(weekly['internal_trend']),
                    position_structure=float(weekly['position_structure']),
                    eow_bias=TrendDirection.from_string(weekly['eow_bias']),
                    notes=weekly.get('notes', '')
                )
                
                # Add price_levels if present
                if 'price_levels' in weekly:
                    price_levels = []
                    for level in weekly['price_levels']:
                        if level > 0:  # Only add non-zero levels
                            price_levels.append(Decimal(str(level)))
                    
                    # Set price_levels if WeeklyData supports it
                    if hasattr(session.weekly_data, 'price_levels'):
                        session.weekly_data.price_levels = price_levels
                        logger.debug(f"Added {len(price_levels)} weekly price levels")
                    else:
                        logger.warning("WeeklyData doesn't have price_levels attribute")
                
                logger.debug("Weekly data added successfully")
            except Exception as e:
                logger.error(f"Error processing weekly data: {e}")
                raise
        
        # Add daily data if present
        if data.get('daily'):
            logger.debug("Processing daily data...")
            daily = data['daily']
            
            try:
                session.daily_data = DailyData(
                    trend_direction=TrendDirection.from_string(daily['trend_direction']),
                    internal_trend=TrendDirection.from_string(daily['internal_trend']),
                    position_structure=float(daily['position_structure']),
                    eod_bias=TrendDirection.from_string(daily['eod_bias']),
                    price_levels=[Decimal(str(level)) for level in daily.get('price_levels', []) if level > 0],
                    notes=daily.get('notes', '')
                )
                logger.debug("Daily data added successfully")
            except Exception as e:
                logger.error(f"Error processing daily data: {e}")
                raise
        
        # Add metrics
        if data.get('pre_market_price'):
            session.pre_market_price = Decimal(str(data['pre_market_price']))
            logger.debug(f"Pre-market price: {session.pre_market_price}")
        
        if data.get('metrics'):
            metrics = data['metrics']
            if 'atr_5min' in metrics:
                session.atr_5min = Decimal(str(metrics['atr_5min']))
            if 'atr_2hour' in metrics:  # Using atr_2hour consistently
                session.atr_2hour = Decimal(str(metrics['atr_2hour']))
                logger.debug(f"ATR 2-hour set: {session.atr_2hour}")
            if 'atr_15min' in metrics:
                session.atr_15min = Decimal(str(metrics['atr_15min']))
            if 'daily_atr' in metrics:
                session.daily_atr = Decimal(str(metrics['daily_atr']))
            if 'atr_high' in metrics:
                session.atr_high = Decimal(str(metrics['atr_high']))
            if 'atr_low' in metrics:
                session.atr_low = Decimal(str(metrics['atr_low']))
            
            logger.debug(f"Metrics set - 5min: {session.atr_5min}, 2hr: {session.atr_2hour}, 15min: {session.atr_15min}")
        
        # Process M15 zones
        if data.get('zones'):
            logger.debug(f"Processing {len(data['zones'])} M15 zones...")
            successful_zones = 0
            
            for i, zone in enumerate(data['zones']):
                try:
                    zone_num = zone.get('zone_number', i + 1)
                    level_value = Decimal(str(zone.get('level', 0))) if zone.get('level') else Decimal("0")
                    
                    if level_value > 0:  # Only add non-zero levels
                        level_id = session.generate_level_id(len(session.m15_levels))
                        
                        high_value = Decimal(str(zone.get('high', 0))) if zone.get('high') else level_value
                        low_value = Decimal(str(zone.get('low', 0))) if zone.get('low') else level_value
                        
                        level = PriceLevel(
                            line_price=level_value,
                            candle_datetime=session_datetime,
                            candle_high=high_value,
                            candle_low=low_value,
                            level_id=level_id
                        )
                        session.m15_levels.append(level)
                        successful_zones += 1
                        logger.debug(f"  Zone {zone_num}: level={level_value}, high={high_value}, low={low_value}")
                        
                except Exception as e:
                    logger.warning(f"Error processing zone {i}: {e}")
            
            logger.debug(f"Added {successful_zones} M15 zones")
        
        logger.info(f"Session creation complete: {session.ticker_id}")
        return session
    
    def load_session(self, ticker_id: str) -> Optional[Dict[str, Any]]:
        """Load a trading session and convert to UI format"""
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
        """List available sessions with optional filters"""
        if not self.client:
            return []
        
        try:
            sessions = self.client.list_sessions(ticker, start_date, end_date)
            
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
    
    def _convert_session_to_ui_format(self, session: TradingSession) -> Dict[str, Any]:
        """Convert TradingSession model to UI data format"""
        ui_data = {
            'ticker': session.ticker,
            'is_live': session.is_live,
            'datetime': datetime.combine(session.date, datetime.min.time()),
            'timestamp': session.created_at or datetime.now()
        }
        
        # Add metrics - UPDATED to use atr_2hour
        ui_data['metrics'] = {
            'atr_5min': float(session.atr_5min) if session.atr_5min else 0,
            'atr_2hour': float(session.atr_2hour) if session.atr_2hour else 0,  # Changed from atr_10min
            'atr_15min': float(session.atr_15min) if session.atr_15min else 0,
            'daily_atr': float(session.daily_atr) if session.daily_atr else 0,
            'atr_high': float(session.atr_high) if session.atr_high else 0,
            'atr_low': float(session.atr_low) if session.atr_low else 0
        }
        
        # Add pre-market price
        if session.pre_market_price:
            ui_data['pre_market_price'] = float(session.pre_market_price)
        
        # Add weekly data
        if session.weekly_data:
            ui_data['weekly'] = {
                'trend_direction': session.weekly_data.trend_direction.value,
                'internal_trend': session.weekly_data.internal_trend.value,
                'position_structure': session.weekly_data.position_structure,
                'eow_bias': session.weekly_data.eow_bias.value,
                'notes': session.weekly_data.notes
            }
            
            # Add price_levels if present
            if hasattr(session.weekly_data, 'price_levels'):
                ui_data['weekly']['price_levels'] = [float(level) for level in session.weekly_data.price_levels]
        
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
        
        # Add M15 zones
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