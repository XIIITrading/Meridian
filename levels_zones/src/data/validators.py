"""
Data validation layer for Meridian Trading System
Provides comprehensive validation for all data inputs and calculations
"""

import re
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
import logging
import pytz

from data.models import (
    TradingSession, PriceLevel, WeeklyData, DailyData,
    TrendDirection
)

# Set up logging
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class FieldValidator:
    """Base class for field-specific validators"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """
        Validate that a required field has a value.
        
        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            
        Raises:
            ValidationError: If value is None or empty
        """
        if value is None:
            raise ValidationError(field_name, "This field is required")
        
        # Check for empty strings
        if isinstance(value, str) and not value.strip():
            raise ValidationError(field_name, "This field cannot be empty")
    
    @staticmethod
    def validate_decimal(value: Any, field_name: str, 
                        min_value: Optional[Decimal] = None,
                        max_value: Optional[Decimal] = None,
                        decimal_places: int = 2) -> Decimal:
        """
        Validate and convert a value to Decimal.
        
        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            decimal_places: Maximum decimal places allowed
            
        Returns:
            Decimal: Validated decimal value
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Convert to Decimal
            if isinstance(value, Decimal):
                decimal_value = value
            else:
                decimal_value = Decimal(str(value))
            
            # Check for NaN or Infinity
            if not decimal_value.is_finite():
                raise ValidationError(field_name, "Invalid numeric value")
            
            # Check min/max bounds
            if min_value is not None and decimal_value < min_value:
                raise ValidationError(field_name, f"Value must be at least {min_value}")
            
            if max_value is not None and decimal_value > max_value:
                raise ValidationError(field_name, f"Value must be at most {max_value}")
            
            # Check decimal places
            sign, digits, exponent = decimal_value.as_tuple()
            if exponent < -decimal_places:
                raise ValidationError(field_name, 
                    f"Maximum {decimal_places} decimal places allowed")
            
            return decimal_value
            
        except (InvalidOperation, ValueError):
            raise ValidationError(field_name, "Invalid decimal value")
    
    @staticmethod
    def validate_percentage(value: Any, field_name: str) -> float:
        """
        Validate a percentage value (0-100).
        
        Args:
            value: The value to validate
            field_name: Name of the field for error messages
            
        Returns:
            float: Validated percentage
            
        Raises:
            ValidationError: If not between 0 and 100
        """
        try:
            float_value = float(value)
            if not 0 <= float_value <= 100:
                raise ValidationError(field_name, "Percentage must be between 0 and 100")
            return float_value
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Invalid percentage value")
    
    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """
        Validate a ticker symbol.
        
        Args:
            ticker: Ticker symbol to validate
            
        Returns:
            str: Uppercase ticker symbol
            
        Raises:
            ValidationError: If ticker is invalid
        """
        if not ticker:
            raise ValidationError("ticker", "Ticker symbol is required")
        
        # Remove whitespace and convert to uppercase
        ticker = ticker.strip().upper()
        
        # Check length
        if len(ticker) > 10:
            raise ValidationError("ticker", "Ticker symbol too long (max 10 characters)")
        
        # Check format (letters, numbers, and some special chars allowed)
        if not re.match(r'^[A-Z0-9\-\.]+$', ticker):
            raise ValidationError("ticker", 
                "Invalid ticker format. Use letters, numbers, hyphens, or periods only")
        
        return ticker
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date, 
                           field_name: str = "date_range") -> None:
        """
        Validate that start date is before or equal to end date.
        
        Args:
            start_date: Start date
            end_date: End date
            field_name: Field name for error messages
            
        Raises:
            ValidationError: If date range is invalid
        """
        if start_date > end_date:
            raise ValidationError(field_name, "Start date must be before or equal to end date")
    
    @staticmethod
    def validate_analysis_datetime(dt: datetime) -> None:
        """
        Validate that a datetime is valid for running analysis.
        Analysis can be run at any time during weekdays (for pre-market analysis).
        
        Args:
            dt: Datetime to validate (assumed to be in UTC)
            
        Raises:
            ValidationError: If datetime is on a weekend
        """
        # Convert UTC to Eastern Time for weekday check
        eastern = pytz.timezone('US/Eastern')
        et_dt = dt.astimezone(eastern)
        
        # Check if it's a weekend in Eastern Time
        if et_dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            raise ValidationError("analysis_datetime", 
                "Analysis cannot be run on weekends (market closed)")
        
        # Note: We're NOT checking time of day since pre-market analysis 
        # needs to run outside regular trading hours
        logger.debug(f"Analysis datetime validated: {dt} UTC ({et_dt} ET)")
    
    @staticmethod
    def validate_candle_datetime(dt: datetime, session_date: date) -> None:
        """
        Validate that a candle datetime is valid for the given session.
        Candle data should be from market hours and align with session date.
        
        Args:
            dt: Candle datetime (in UTC)
            session_date: The trading session date
            
        Raises:
            ValidationError: If candle datetime is invalid
        """
        # Convert UTC to Eastern Time for validation
        eastern = pytz.timezone('US/Eastern')
        et_dt = dt.astimezone(eastern)
        
        # Check if it's a weekend
        if et_dt.weekday() >= 5:
            raise ValidationError("candle_datetime", 
                "Candle data cannot be from weekends")
        
        # Define market hours in Eastern Time
        # Pre-market: 4:00 AM - 9:30 AM ET
        # Regular: 9:30 AM - 4:00 PM ET  
        # After-hours: 4:00 PM - 8:00 PM ET
        market_open = time(4, 0)    # 4:00 AM ET
        market_close = time(20, 0)  # 8:00 PM ET
        
        candle_time = et_dt.time()
        if not (market_open <= candle_time <= market_close):
            raise ValidationError("candle_datetime",
                f"Candle time {candle_time} ET is outside market hours (4:00 AM - 8:00 PM ET)")
        
        # Validate date alignment
        candle_date = et_dt.date()
        days_diff = (session_date - candle_date).days
        
        if days_diff < 0:
            raise ValidationError("candle_datetime",
                f"Candle date {candle_date} is after session date {session_date}")
        elif days_diff > 1:
            raise ValidationError("candle_datetime",
                f"Candle date {candle_date} is more than 1 day before session date {session_date}")


class PriceLevelValidator:
    """Validator for PriceLevel objects"""
    
    @staticmethod
    def validate_price_level(level: PriceLevel, session_date: Optional[date] = None) -> List[str]:
        """
        Validate a single price level.
        
        Args:
            level: PriceLevel object to validate
            session_date: Session date for datetime validation
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Validate prices are positive
            if level.line_price <= 0:
                errors.append("Line price must be positive")
            if level.candle_high <= 0:
                errors.append("Candle high must be positive")
            if level.candle_low <= 0:
                errors.append("Candle low must be positive")
            
            # Validate high >= low
            if level.candle_high < level.candle_low:
                errors.append("Candle high must be >= candle low")
            
            # Validate line price is within candle range (with small tolerance)
            tolerance = Decimal("0.01")
            if not (level.candle_low - tolerance <= level.line_price <= level.candle_high + tolerance):
                errors.append("Line price should be within candle range")
            
            # Validate level_id format
            if not re.match(r'^[A-Z0-9]+\.\d{6}_L\d{3}$', level.level_id):
                errors.append(f"Invalid level_id format: {level.level_id}")
            
            # Validate candle datetime if session date provided
            if session_date:
                try:
                    FieldValidator.validate_candle_datetime(level.candle_datetime, session_date)
                except ValidationError as e:
                    errors.append(f"Candle datetime: {e.message}")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_price_levels_set(levels: List[PriceLevel], 
                                 current_price: Decimal,
                                 session_date: Optional[date] = None) -> Tuple[bool, List[str]]:
        """
        Validate a set of price levels.
        
        Args:
            levels: List of PriceLevel objects
            current_price: Current market price for reference
            session_date: Session date for datetime validation
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check count (max 6 levels)
        if len(levels) > 6:
            errors.append("Maximum 6 price levels allowed (3 above, 3 below)")
        
        # Validate each level
        for i, level in enumerate(levels):
            level_errors = PriceLevelValidator.validate_price_level(level, session_date)
            if level_errors:
                errors.extend([f"Level {i+1}: {err}" for err in level_errors])
        
        # Check for duplicate prices (with tolerance)
        prices = [level.line_price for level in levels]
        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                if abs(prices[i] - prices[j]) < Decimal("0.01"):
                    errors.append(f"Duplicate price levels: {prices[i]} and {prices[j]}")
        
        # Validate distribution (should have levels both above and below current price)
        if levels and current_price > 0:
            above_count = sum(1 for level in levels if level.line_price > current_price)
            below_count = sum(1 for level in levels if level.line_price < current_price)
            
            if above_count == 0:
                errors.append("No price levels above current price")
            elif above_count > 3:
                errors.append("Maximum 3 price levels above current price")
            
            if below_count == 0:
                errors.append("No price levels below current price")
            elif below_count > 3:
                errors.append("Maximum 3 price levels below current price")
        
        return len(errors) == 0, errors


class TradingSessionValidator:
    """Validator for TradingSession objects"""
    
    @staticmethod
    def validate_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation of a trading session.
        
        Args:
            session: TradingSession object to validate
            
        Returns:
            Tuple of (is_valid, dict_of_errors_by_section)
        """
        errors = {
            'overview': [],
            'weekly': [],
            'daily': [],
            'metrics': [],
            'levels': []
        }
        
        # Validate Overview Section
        try:
            # Validate ticker
            session.ticker = FieldValidator.validate_ticker(session.ticker)
            
            # Validate date (not future)
            if session.date > date.today():
                errors['overview'].append("Session date cannot be in the future")
            
            # Validate that session date is a weekday
            if session.date.weekday() >= 5:
                errors['overview'].append("Session date must be a weekday (market closed on weekends)")
            
            # Validate historical data consistency
            if not session.is_live:
                if not session.historical_date:
                    errors['overview'].append("Historical date required for non-live sessions")
                elif session.historical_date >= session.date:
                    errors['overview'].append("Historical date must be before session date")
            
        except ValidationError as e:
            errors['overview'].append(e.message)
        
        # Validate Weekly Data
        if session.weekly_data:
            try:
                # Position structure validation is in the model
                if not 0 <= session.weekly_data.position_structure <= 100:
                    errors['weekly'].append("Position structure must be 0-100%")
            except Exception as e:
                errors['weekly'].append(str(e))
        
        # Validate Daily Data  
        if session.daily_data:
            try:
                # Position structure validation
                if not 0 <= session.daily_data.position_structure <= 100:
                    errors['daily'].append("Position structure must be 0-100%")
                
                # Price levels count
                if len(session.daily_data.price_levels) != 6:
                    errors['daily'].append("Exactly 6 daily price levels required")
                
            except Exception as e:
                errors['daily'].append(str(e))
        
        # Validate Metrics
        try:
            # Pre-market price
            if session.pre_market_price <= 0:
                errors['metrics'].append("Pre-market price must be positive")
            
            # ATR values
            atr_fields = [
                ('5-minute ATR', session.atr_5min),
                ('10-minute ATR', session.atr_10min),
                ('15-minute ATR', session.atr_15min),
                ('Daily ATR', session.daily_atr)
            ]
            
            for field_name, value in atr_fields:
                if value < 0:
                    errors['metrics'].append(f"{field_name} cannot be negative")
            
            # Validate ATR bands calculation
            expected_high = session.pre_market_price + session.daily_atr
            expected_low = session.pre_market_price - session.daily_atr
            
            if abs(session.atr_high - expected_high) > Decimal("0.01"):
                errors['metrics'].append("ATR High calculation mismatch")
            
            if abs(session.atr_low - expected_low) > Decimal("0.01"):
                errors['metrics'].append("ATR Low calculation mismatch")
            
        except Exception as e:
            errors['metrics'].append(str(e))
        
        # Validate M15 Levels
        if session.m15_levels:
            is_valid, level_errors = PriceLevelValidator.validate_price_levels_set(
                session.m15_levels, session.pre_market_price, session.date
            )
            if not is_valid:
                errors['levels'].extend(level_errors)
        
        # Check if any errors exist
        has_errors = any(error_list for error_list in errors.values())
        
        return not has_errors, errors
    
    @staticmethod
    def validate_for_analysis(session: TradingSession) -> Tuple[bool, List[str]]:
        """
        Validate that a session has all required data for analysis.
        
        Args:
            session: TradingSession to validate
            
        Returns:
            Tuple of (can_analyze, list_of_missing_items)
        """
        missing = []
        
        # Check required data
        if not session.weekly_data:
            missing.append("Weekly analysis data")
        
        if not session.daily_data:
            missing.append("Daily analysis data")
        
        if not session.m15_levels:
            missing.append("M15 price levels")
        elif len(session.m15_levels) < 2:
            missing.append("At least 2 M15 price levels required")
        
        if session.pre_market_price <= 0:
            missing.append("Valid pre-market price")
        
        if session.daily_atr <= 0:
            missing.append("Valid daily ATR")
        
        return len(missing) == 0, missing


class ATRValidator:
    """Validator for ATR calculations"""
    
    @staticmethod
    def validate_atr_values(atr_5min: Decimal, atr_10min: Decimal, 
                           atr_15min: Decimal, daily_atr: Decimal) -> List[str]:
        """
        Validate ATR values for consistency.
        
        Args:
            atr_5min: 5-minute ATR
            atr_10min: 10-minute ATR
            atr_15min: 15-minute ATR
            daily_atr: Daily ATR
            
        Returns:
            List of validation warnings (not errors)
        """
        warnings = []
        
        # Generally, longer timeframe ATRs should be larger
        if atr_5min > atr_10min * Decimal("1.5"):
            warnings.append("5-min ATR unusually high compared to 10-min ATR")
        
        if atr_10min > atr_15min * Decimal("1.5"):
            warnings.append("10-min ATR unusually high compared to 15-min ATR")
        
        # Daily ATR should typically be larger than intraday ATRs
        if daily_atr < atr_15min:
            warnings.append("Daily ATR is smaller than 15-min ATR (unusual)")
        
        # Check for extreme values
        if daily_atr > atr_15min * Decimal("10"):
            warnings.append("Daily ATR seems extremely high compared to intraday ATRs")
        
        return warnings
    
    @staticmethod
    def validate_atr_calculation(high_values: List[Decimal], 
                               low_values: List[Decimal],
                               close_values: List[Decimal],
                               calculated_atr: Decimal,
                               period: int = 14) -> bool:
        """
        Validate that an ATR calculation is correct.
        
        Args:
            high_values: List of high prices
            low_values: List of low prices  
            close_values: List of close prices
            calculated_atr: The ATR value to validate
            period: ATR period (default 14)
            
        Returns:
            bool: True if calculation appears correct
        """
        if len(high_values) < period or len(low_values) < period or len(close_values) < period:
            return False
        
        # Calculate true ranges
        true_ranges = []
        for i in range(1, len(high_values)):
            high_low = high_values[i] - low_values[i]
            high_close = abs(high_values[i] - close_values[i-1])
            low_close = abs(low_values[i] - close_values[i-1])
            
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return False
        
        # Calculate ATR (simple moving average of true ranges)
        atr = sum(true_ranges[-period:]) / period
        
        # Allow small tolerance for rounding
        tolerance = Decimal("0.01")
        return abs(atr - calculated_atr) <= tolerance


class DateTimeValidator:
    """Validator for date and time related fields"""
    
    @staticmethod
    def validate_market_date(check_date: date) -> Tuple[bool, str]:
        """
        Validate that a date is a valid market day (weekday).
        
        Args:
            check_date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if weekend
        if check_date.weekday() >= 5:
            return False, "Market is closed on weekends"
        
        # TODO: Add holiday checking here if needed
        # Could integrate with a market calendar API
        
        return True, ""
    
    @staticmethod
    def validate_session_date_consistency(session_date: date,
                                        candle_datetimes: List[datetime]) -> List[str]:
        """
        Validate that candle datetimes are consistent with session date.
        All datetimes should be in UTC.
        
        Args:
            session_date: The session date
            candle_datetimes: List of candle datetimes from price levels (UTC)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Convert to Eastern timezone for date comparison
        eastern = pytz.timezone('US/Eastern')
        
        for i, candle_dt in enumerate(candle_datetimes):
            # Convert UTC to Eastern for date extraction
            et_candle_dt = candle_dt.astimezone(eastern)
            candle_date = et_candle_dt.date()
            
            # For regular sessions, candles should be from the same day
            # or previous day (for pre-market levels)
            days_diff = (session_date - candle_date).days
            
            if days_diff < 0:
                errors.append(f"Candle {i+1} is from future date: {candle_date}")
            elif days_diff > 1:
                errors.append(f"Candle {i+1} is too old: {candle_date} (session date: {session_date})")
        
        return errors
    
    @staticmethod
    def convert_market_time_to_utc(market_dt: datetime) -> datetime:
        """
        Convert Eastern Time datetime to UTC.
        
        Args:
            market_dt: Datetime in Eastern Time
            
        Returns:
            Datetime in UTC
        """
        eastern = pytz.timezone('US/Eastern')
        
        # If datetime is naive, localize it to Eastern
        if market_dt.tzinfo is None:
            market_dt = eastern.localize(market_dt)
        
        # Convert to UTC
        return market_dt.astimezone(pytz.UTC)
    
    @staticmethod
    def convert_utc_to_market_time(utc_dt: datetime) -> datetime:
        """
        Convert UTC datetime to Eastern Time.
        
        Args:
            utc_dt: Datetime in UTC
            
        Returns:
            Datetime in Eastern Time
        """
        if utc_dt.tzinfo is None:
            utc_dt = pytz.UTC.localize(utc_dt)
            
        eastern = pytz.timezone('US/Eastern')
        return utc_dt.astimezone(eastern)


# Convenience functions for common validations
def validate_trading_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate a complete trading session.
    
    Args:
        session: TradingSession to validate
        
    Returns:
        Tuple of (is_valid, errors_dict)
    """
    return TradingSessionValidator.validate_session(session)


def validate_for_analysis(session: TradingSession) -> Tuple[bool, List[str]]:
    """
    Check if a session is ready for analysis.
    
    Args:
        session: TradingSession to check
        
    Returns:
        Tuple of (ready_for_analysis, missing_items)
    """
    return TradingSessionValidator.validate_for_analysis(session)


def validate_price_level(level: PriceLevel, session_date: Optional[date] = None) -> List[str]:
    """
    Validate a single price level.
    
    Args:
        level: PriceLevel to validate
        session_date: Optional session date for datetime validation
        
    Returns:
        List of validation errors
    """
    return PriceLevelValidator.validate_price_level(level, session_date)


def is_market_open_now() -> bool:
    """
    Check if the market is currently open (including extended hours).
    
    Returns:
        bool: True if market is open
    """
    now_utc = datetime.now(pytz.UTC)
    eastern = pytz.timezone('US/Eastern')
    now_et = now_utc.astimezone(eastern)
    
    # Check if weekend
    if now_et.weekday() >= 5:
        return False
    
    # Check time (4 AM - 8 PM ET)
    current_time = now_et.time()
    market_open = time(4, 0)
    market_close = time(20, 0)
    
    return market_open <= current_time <= market_close