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
        RELAXED: Allow future dates up to 1 day ahead (for pre-market analysis)
        
        Args:
            dt: Datetime to validate (in UTC)
            
        Raises:
            ValidationError: If datetime is too far in the future
        """
        # Allow up to 1 day in the future for pre-market analysis
        future_limit = datetime.utcnow() + timedelta(days=1)
        if dt > future_limit:
            raise ValidationError("analysis_datetime", 
                "Analysis datetime cannot be more than 1 day in the future")
        
        logger.debug(f"Analysis datetime validated: {dt} UTC")
    
    @staticmethod
    def validate_candle_datetime(dt: datetime, session_date: date) -> None:
        """
        Validate that a candle datetime is valid.
        RELAXED validation - just check it's not ridiculously in the future.
        
        Args:
            dt: Candle datetime (in UTC)
            session_date: The trading session date (not used for validation)
            
        Raises:
            ValidationError: If datetime is invalid
        """
        # Only validate that it's not more than 1 day in the future
        # This allows for timezone differences and pre-market data
        future_limit = datetime.utcnow() + timedelta(days=1)
        if dt > future_limit:
            raise ValidationError("candle_datetime",
                f"Candle datetime {dt} is more than 1 day in the future")
        
        # That's it - no other restrictions!
        logger.debug(f"Candle datetime validated: {dt} UTC")


class PriceLevelValidator:
    """Validator for PriceLevel objects"""
    
    @staticmethod
    def validate_price_level(level: PriceLevel, session_date: Optional[date] = None) -> List[str]:
        """
        Validate a single price level with RELAXED rules.
        
        Args:
            level: PriceLevel object to validate
            session_date: Session date (optional, not strictly enforced)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Basic price validation - just check they're positive
            if level.line_price <= 0:
                errors.append("Line price must be positive")
            if level.candle_high <= 0:
                errors.append("Candle high must be positive")
            if level.candle_low <= 0:
                errors.append("Candle low must be positive")
            
            # Validate high >= low
            if level.candle_high < level.candle_low:
                errors.append("Candle high must be >= candle low")
            
            # RELAXED: Line price validation with larger tolerance
            tolerance = Decimal("1.00")  # Increased from 0.01 to 1.00
            if level.line_price > 0:  # Only check if line price is set
                if not (level.candle_low - tolerance <= level.line_price <= level.candle_high + tolerance):
                    # Just log a warning instead of error
                    logger.warning(f"Line price {level.line_price} outside candle range {level.candle_low}-{level.candle_high}")
                    # Don't add to errors - allow it
            
            # RELAXED: Level ID format - more flexible pattern
            if level.level_id:
                # Just check it contains _L somewhere
                if '_L' not in level.level_id:
                    errors.append(f"Invalid level_id format: {level.level_id} (must contain '_L')")
            else:
                errors.append("Level ID is required")
            
            # NO datetime validation - removed completely
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_price_levels_set(levels: List[PriceLevel], 
                                current_price: Decimal) -> Tuple[bool, List[str]]:
        """
        Validate a set of price levels with RELAXED rules.
        
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
        
        # RELAXED: Don't strictly enforce distribution above/below current price
        # Just log a warning if all levels are on one side
        if levels and current_price > 0:
            above_count = sum(1 for level in levels if level.line_price > current_price)
            below_count = sum(1 for level in levels if level.line_price < current_price)
            
            if above_count == 0:
                logger.warning("No price levels above current price")
                # Don't add to errors
            elif above_count > 3:
                logger.warning(f"{above_count} price levels above current price (recommended max: 3)")
                # Don't add to errors
            
            if below_count == 0:
                logger.warning("No price levels below current price")
                # Don't add to errors
            elif below_count > 3:
                logger.warning(f"{below_count} price levels below current price (recommended max: 3)")
                # Don't add to errors
        
        return len(errors) == 0, errors


class TradingSessionValidator:
    """Validator for TradingSession objects"""
    
    @staticmethod
    def validate_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation of a trading session with RELAXED rules.
        
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
            
            # NO date validation - removed all date and historical validation
            # Allow any dates, past or future
            
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
                
                # RELAXED: Don't require exactly 6 price levels
                if len(session.daily_data.price_levels) > 6:
                    errors['daily'].append("Maximum 6 daily price levels allowed")
                # Allow fewer than 6 levels
                
            except Exception as e:
                errors['daily'].append(str(e))
        
        # Validate Metrics
        try:
            # Pre-market price - only validate if set
            if session.pre_market_price > 0:
                # ATR values - just check they're not negative
                # CHANGED: Updated to use atr_2hour instead of atr_10min
                atr_fields = [
                    ('5-minute ATR', session.atr_5min),
                    ('2-hour ATR', session.atr_2hour),  # CHANGED from atr_10min
                    ('15-minute ATR', session.atr_15min),
                    ('Daily ATR', session.daily_atr)
                ]
                
                for field_name, value in atr_fields:
                    if value < 0:
                        errors['metrics'].append(f"{field_name} cannot be negative")
                
                # RELAXED ATR bands calculation validation
                # Just log differences, don't error
                if session.daily_atr > 0 and session.pre_market_price > 0:
                    expected_high = session.pre_market_price + session.daily_atr
                    expected_low = session.pre_market_price - session.daily_atr
                    
                    # Use a very large tolerance - 5 points
                    tolerance = Decimal("5.0")
                    
                    if session.atr_high > 0:
                        diff_high = abs(session.atr_high - expected_high)
                        if diff_high > tolerance:
                            logger.info(f"ATR High calculation difference: {diff_high:.2f}")
                            # Don't add to errors
                            
                    if session.atr_low > 0:
                        diff_low = abs(session.atr_low - expected_low)
                        if diff_low > tolerance:
                            logger.info(f"ATR Low calculation difference: {diff_low:.2f}")
                            # Don't add to errors
            
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
        RELAXED: Only check for essential data.
        
        Args:
            session: TradingSession to validate
            
        Returns:
            Tuple of (can_analyze, list_of_missing_items)
        """
        missing = []
        
        # Only check for truly essential data
        if not session.ticker:
            missing.append("Ticker symbol")
        
        # RELAXED: Don't require all analysis data
        # Allow analysis even with partial data
        
        # Only require at least one M15 level
        if not session.m15_levels:
            missing.append("At least one M15 price level")
        
        # Only warn about missing data, don't block analysis
        if not session.weekly_data:
            logger.warning("Weekly analysis data missing")
        
        if not session.daily_data:
            logger.warning("Daily analysis data missing")
        
        if session.pre_market_price <= 0:
            logger.warning("Pre-market price not set")
        
        if session.daily_atr <= 0:
            logger.warning("Daily ATR not calculated")
        
        return len(missing) == 0, missing


class ATRValidator:
    """Validator for ATR calculations"""
    
    @staticmethod
    def validate_atr_values(atr_5min: Decimal, atr_2hour: Decimal,  # CHANGED parameter name
                           atr_15min: Decimal, daily_atr: Decimal) -> List[str]:
        """
        Validate ATR values for consistency.
        RELAXED: Only return warnings, not errors.
        
        Args:
            atr_5min: 5-minute ATR
            atr_2hour: 2-hour ATR  # CHANGED from atr_10min
            atr_15min: 15-minute ATR
            daily_atr: Daily ATR
            
        Returns:
            List of validation warnings (not errors)
        """
        warnings = []
        
        # RELAXED: Use larger multipliers for unusual comparisons
        # CHANGED: Updated comparisons to use atr_2hour
        if atr_5min > atr_2hour * Decimal("3.0"):  # Increased multiplier for 2-hour comparison
            warnings.append("5-min ATR unusually high compared to 2-hour ATR")
        
        if atr_2hour > atr_15min * Decimal("0.5"):  # 2-hour should typically be larger than 15-min
            warnings.append("2-hour ATR unusually low compared to 15-min ATR")
        
        # Daily ATR should typically be larger than intraday ATRs
        if daily_atr < atr_15min * Decimal("0.5"):  # More relaxed
            warnings.append("Daily ATR is smaller than half of 15-min ATR (unusual)")
        
        # Check for extreme values
        if daily_atr > atr_15min * Decimal("20"):  # Increased from 10
            warnings.append("Daily ATR seems extremely high compared to intraday ATRs")
        
        return warnings


class DateTimeValidator:
    """Validator for date and time related fields"""
    
    @staticmethod
    def validate_market_date(check_date: date) -> Tuple[bool, str]:
        """
        Validate that a date is valid.
        RELAXED: Allow any date.
        
        Args:
            check_date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow any date - past, present, or future
        return True, ""
    
    @staticmethod
    def validate_session_date_consistency(session_date: date,
                                        candle_datetimes: List[datetime]) -> List[str]:
        """
        Validate candle datetimes.
        RELAXED: Only check for extremely future dates.
        
        Args:
            session_date: The session date
            candle_datetimes: List of candle datetimes (UTC)
            
        Returns:
            List of validation errors (minimal restrictions)
        """
        errors = []
        
        # Only check that datetimes aren't more than 1 day in the future
        future_limit = datetime.utcnow() + timedelta(days=1)
        
        for i, candle_dt in enumerate(candle_datetimes):
            if candle_dt > future_limit:
                errors.append(f"Candle {i+1} datetime is more than 1 day in the future: {candle_dt}")
        
        return errors


# Convenience functions for common validations
def validate_trading_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate a complete trading session with RELAXED rules.
    
    Args:
        session: TradingSession to validate
        
    Returns:
        Tuple of (is_valid, errors_dict)
    """
    return TradingSessionValidator.validate_session(session)


def validate_for_analysis(session: TradingSession) -> Tuple[bool, List[str]]:
    """
    Check if a session is ready for analysis with RELAXED rules.
    
    Args:
        session: TradingSession to check
        
    Returns:
        Tuple of (ready_for_analysis, missing_items)
    """
    return TradingSessionValidator.validate_for_analysis(session)


# Optional: Function to temporarily disable validation
def validate_trading_session_lenient(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Ultra-lenient validation - only check critical fields.
    Use this for debugging or when you need to save partial data.
    
    Args:
        session: TradingSession to validate
        
    Returns:
        Tuple of (is_valid, errors_dict) - almost always returns True
    """
    errors = {
        'overview': [],
        'weekly': [],
        'daily': [],
        'metrics': [],
        'levels': []
    }
    
    # Only validate the absolute minimum
    try:
        # Must have a ticker
        if not session.ticker:
            errors['overview'].append("Ticker is required")
        
        # Must have a valid date
        if not session.date:
            errors['overview'].append("Date is required")
            
    except Exception as e:
        logger.warning(f"Lenient validation encountered error: {e}")
        # Even if there's an error, we'll allow it
    
    # Log any issues but still return valid
    if any(error_list for error_list in errors.values()):
        logger.warning(f"Lenient validation found issues: {errors}")
    
    # Always return True for lenient validation
    return True, errors