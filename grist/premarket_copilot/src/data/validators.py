"""
Data validation layer for Meridian Trading System
Provides comprehensive validation for all data inputs and calculations
"""

import re
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
import logging

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
        Validate that a datetime is valid for analysis.
        All timestamps are in UTC - no timezone conversion needed.
        
        Args:
            dt: Datetime to validate (in UTC)
            
        Raises:
            ValidationError: If datetime is in the future
        """
        if dt > datetime.utcnow():
            raise ValidationError("analysis_datetime", 
                "Analysis datetime cannot be in the future")
        
        logger.debug(f"Analysis datetime validated: {dt} UTC")
    
    @staticmethod
    def validate_candle_datetime(dt: datetime, session_date: date) -> None:
        """
        Validate that a candle datetime is valid.
        Minimal validation - just check it's a valid datetime.
        
        Args:
            dt: Candle datetime (in UTC)
            session_date: The trading session date (not used for validation)
            
        Raises:
            ValidationError: If datetime is invalid
        """
        # Only validate that it's not in the future
        if dt > datetime.utcnow():
            raise ValidationError("candle_datetime",
                "Candle datetime cannot be in the future")
        
        # That's it - no other restrictions!
        logger.debug(f"Candle datetime validated: {dt} UTC")


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
                                current_price: Decimal) -> Tuple[bool, List[str]]:
        """
        Validate a set of price levels.
        
        Args:
            levels: List of PriceLevel objects
            current_price: Current market price for reference
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check count (max 6 levels)
        if len(levels) > 6:
            errors.append("Maximum 6 price levels allowed (3 above, 3 below)")
        
        # Validate each level - no date validation
        for i, level in enumerate(levels):
            level_errors = PriceLevelValidator.validate_price_level(level)
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
            
            # REMOVED ALL DATE AND HISTORICAL VALIDATION
            # No validation for dates or is_live flag
            
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
            # Pre-market price - only validate if set
            if session.pre_market_price > 0:
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
                
                # RELAXED ATR bands calculation validation
                # Only validate if both daily_atr and pre_market_price are set
                if session.daily_atr > 0 and session.pre_market_price > 0:
                    expected_high = session.pre_market_price + session.daily_atr
                    expected_low = session.pre_market_price - session.daily_atr
                    
                    # Use a larger tolerance
                    tolerance = Decimal("1.0")
                    
                    # Only log warnings instead of errors
                    if session.atr_high > 0 and abs(session.atr_high - expected_high) > tolerance:
                        logger.warning(f"ATR High calculation difference: {abs(session.atr_high - expected_high)}")
                        
                    if session.atr_low > 0 and abs(session.atr_low - expected_low) > tolerance:
                        logger.warning(f"ATR Low calculation difference: {abs(session.atr_low - expected_low)}")
            
        except Exception as e:
            errors['metrics'].append(str(e))
        
        # Validate M15 Levels - with relaxed date validation
        if session.m15_levels:
            # Don't pass session date for validation anymore
            is_valid, level_errors = PriceLevelValidator.validate_price_levels_set(
                session.m15_levels, session.pre_market_price
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


class DateTimeValidator:
    """Validator for date and time related fields"""
    
    @staticmethod
    def validate_market_date(check_date: date) -> Tuple[bool, str]:
        """
        Validate that a date is valid.
        Minimal validation.
        
        Args:
            check_date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow any date - past or present
        return True, ""
    
    @staticmethod
    def validate_session_date_consistency(session_date: date,
                                        candle_datetimes: List[datetime]) -> List[str]:
        """
        Validate candle datetimes.
        No restrictions on dates - allow any historical data.
        
        Args:
            session_date: The session date
            candle_datetimes: List of candle datetimes (UTC)
            
        Returns:
            List of validation errors (empty - no restrictions)
        """
        errors = []
        
        # Only check that datetimes aren't in the future
        for i, candle_dt in enumerate(candle_datetimes):
            if candle_dt > datetime.utcnow():
                errors.append(f"Candle {i+1} has future datetime: {candle_dt}")
        
        return errors


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


# In the PriceLevelValidator class, update validate_price_level method:

@staticmethod
def validate_price_level(level: PriceLevel, session_date: Optional[date] = None) -> List[str]:
    """
    Validate a single price level.
    
    Args:
        level: PriceLevel object to validate
        session_date: Session date (not used for validation anymore)
        
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
        
        # NO MORE DATETIME VALIDATION - removed completely
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return errors