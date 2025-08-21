"""
Data validation layer for Meridian Trading System
Provides comprehensive validation for all data inputs and calculations
UPDATED: Pure Pivot Confluence System - M15 zones removed
"""

import re
from datetime import datetime, date, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, Tuple
import logging
import json

from data.models import (
    TradingSession, WeeklyData, DailyData, PivotConfluenceData,
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
        Validate that a datetime is valid for pivot analysis.
        RELAXED: Allow future dates up to 1 day ahead (for pre-market analysis)
        
        Args:
            dt: Datetime to validate (in UTC)
            
        Raises:
            ValidationError: If datetime is too far in the future
        """
        # Allow up to 1 day in the future for pre-market pivot analysis
        future_limit = datetime.utcnow() + timedelta(days=1)
        if dt > future_limit:
            raise ValidationError("analysis_datetime", 
                "Pivot analysis datetime cannot be more than 1 day in the future")
        
        logger.debug(f"Pivot analysis datetime validated: {dt} UTC")


class PivotConfluenceValidator:
    """Validator for Pivot Confluence data - replaces M15 validators"""
    
    @staticmethod
    def validate_pivot_confluence_data(data: PivotConfluenceData) -> List[str]:
        """
        Validate pivot confluence data structure.
        
        Args:
            data: PivotConfluenceData object to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Check that we have at least some pivot prices
            pivot_prices = [
                data.daily_cam_r6_price, data.daily_cam_r4_price, data.daily_cam_r3_price,
                data.daily_cam_s3_price, data.daily_cam_s4_price, data.daily_cam_s6_price
            ]
            
            valid_prices = [p for p in pivot_prices if p and p > 0]
            if not valid_prices:
                errors.append("No valid Daily Camarilla pivot prices found")
                return errors  # Can't validate further without prices
            
            # Validate individual pivot levels
            levels = ['r6', 'r4', 'r3', 's3', 's4', 's6']
            for level in levels:
                price_attr = f'daily_cam_{level}_price'
                zone_low_attr = f'daily_cam_{level}_zone_low'
                zone_high_attr = f'daily_cam_{level}_zone_high'
                score_attr = f'daily_cam_{level}_confluence_score'
                
                price = getattr(data, price_attr, None)
                zone_low = getattr(data, zone_low_attr, None)
                zone_high = getattr(data, zone_high_attr, None)
                score = getattr(data, score_attr, None)
                
                if price and price > 0:
                    # Validate price is positive
                    if price <= 0:
                        errors.append(f"{level.upper()} pivot price must be positive")
                    
                    # Validate zone ranges if present
                    if zone_low and zone_high:
                        if zone_low >= zone_high:
                            errors.append(f"{level.upper()} zone low must be less than zone high")
                        
                        # Zone should contain the pivot price (with small tolerance)
                        tolerance = Decimal("0.50")  # 50 cents tolerance
                        if not (zone_low - tolerance <= price <= zone_high + tolerance):
                            errors.append(f"{level.upper()} pivot price should be within zone range")
                    
                    # Validate confluence score if present
                    if score is not None:
                        if score < 0:
                            errors.append(f"{level.upper()} confluence score cannot be negative")
                        if score > 100:  # Reasonable upper limit
                            errors.append(f"{level.upper()} confluence score seems too high: {score}")
            
            # Validate price ordering for resistance levels (R6 > R4 > R3)
            resistance_prices = []
            for level in ['r6', 'r4', 'r3']:
                price = getattr(data, f'daily_cam_{level}_price', None)
                if price and price > 0:
                    resistance_prices.append((level.upper(), price))
            
            if len(resistance_prices) >= 2:
                resistance_prices.sort(key=lambda x: x[1], reverse=True)
                expected_order = ['R6', 'R4', 'R3']
                actual_order = [level for level, price in resistance_prices]
                
                # Check if order matches expected descending order
                for i in range(len(actual_order) - 1):
                    current_level = actual_order[i]
                    next_level = actual_order[i + 1]
                    
                    current_idx = expected_order.index(current_level)
                    next_idx = expected_order.index(next_level)
                    
                    if current_idx >= next_idx:
                        errors.append(f"Resistance levels out of order: {current_level} should be higher than {next_level}")
            
            # Validate price ordering for support levels (S3 > S4 > S6)
            support_prices = []
            for level in ['s3', 's4', 's6']:
                price = getattr(data, f'daily_cam_{level}_price', None)
                if price and price > 0:
                    support_prices.append((level.upper(), price))
            
            if len(support_prices) >= 2:
                support_prices.sort(key=lambda x: x[1], reverse=True)
                expected_order = ['S3', 'S4', 'S6']
                actual_order = [level for level, price in support_prices]
                
                # Check if order matches expected descending order
                for i in range(len(actual_order) - 1):
                    current_level = actual_order[i]
                    next_level = actual_order[i + 1]
                    
                    current_idx = expected_order.index(current_level)
                    next_idx = expected_order.index(next_level)
                    
                    if current_idx >= next_idx:
                        errors.append(f"Support levels out of order: {current_level} should be higher than {next_level}")
            
            # Validate JSON settings if present
            if data.pivot_confluence_settings:
                try:
                    settings = json.loads(data.pivot_confluence_settings)
                    if not isinstance(settings, dict):
                        errors.append("Pivot confluence settings must be a JSON object")
                except json.JSONDecodeError:
                    errors.append("Invalid JSON in pivot confluence settings")
            
        except Exception as e:
            errors.append(f"Pivot confluence validation error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_pivot_confluence_settings(settings: Dict[str, Any]) -> List[str]:
        """
        Validate pivot confluence settings from UI.
        
        Args:
            settings: Dictionary of confluence settings
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            expected_levels = ['R6', 'R4', 'R3', 'S3', 'S4', 'S6']
            expected_sources = [
                'hvn_7day', 'hvn_14day', 'hvn_30day',
                'monthly_pivots', 'weekly_pivots', 'weekly_zones',
                'daily_zones', 'atr_zones'
            ]
            
            # Check that all levels are present
            for level in expected_levels:
                if level not in settings:
                    errors.append(f"Missing settings for level {level}")
                    continue
                
                level_settings = settings[level]
                if not isinstance(level_settings, dict):
                    errors.append(f"Settings for level {level} must be an object")
                    continue
                
                # Check that all sources are present for each level
                for source in expected_sources:
                    if source not in level_settings:
                        errors.append(f"Missing {source} setting for level {level}")
                    elif not isinstance(level_settings[source], bool):
                        errors.append(f"{source} setting for level {level} must be boolean")
            
        except Exception as e:
            errors.append(f"Settings validation error: {str(e)}")
        
        return errors


class TradingSessionValidator:
    """Validator for TradingSession objects - Pure Pivot Confluence System"""
    
    @staticmethod
    def validate_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation of a pivot trading session with RELAXED rules.
        
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
            'pivot_confluence': []
        }
        
        # Validate Overview Section
        try:
            # Validate ticker
            session.ticker = FieldValidator.validate_ticker(session.ticker)
            
            # NO date validation - allow any dates, past or future
            
        except ValidationError as e:
            errors['overview'].append(e.message)
        
        # Validate Weekly Data
        if session.weekly_data:
            try:
                # Position structure validation
                if not 0 <= session.weekly_data.position_structure <= 100:
                    errors['weekly'].append("Position structure must be 0-100%")
                
                # Validate weekly price levels (WL1-WL4)
                if hasattr(session.weekly_data, 'price_levels') and session.weekly_data.price_levels:
                    if len(session.weekly_data.price_levels) > 4:
                        errors['weekly'].append("Maximum 4 weekly price levels allowed")
                    
                    for i, level in enumerate(session.weekly_data.price_levels):
                        if level <= 0:
                            errors['weekly'].append(f"Weekly level {i+1} must be positive")
                
            except Exception as e:
                errors['weekly'].append(str(e))
        
        # Validate Daily Data  
        if session.daily_data:
            try:
                # Position structure validation
                if not 0 <= session.daily_data.position_structure <= 100:
                    errors['daily'].append("Position structure must be 0-100%")
                
                # Validate daily price levels (DL1-DL6)
                if session.daily_data.price_levels:
                    if len(session.daily_data.price_levels) > 6:
                        errors['daily'].append("Maximum 6 daily price levels allowed")
                    
                    for i, level in enumerate(session.daily_data.price_levels):
                        if level <= 0:
                            errors['daily'].append(f"Daily level {i+1} must be positive")
                
            except Exception as e:
                errors['daily'].append(str(e))
        
        # Validate Metrics
        try:
            # Pre-market price - only validate if set
            if session.pre_market_price > 0:
                # ATR values - just check they're not negative
                atr_fields = [
                    ('5-minute ATR', session.atr_5min),  # CRITICAL for pivot zones
                    ('2-hour ATR', session.atr_2hour),
                    ('15-minute ATR', session.atr_15min),
                    ('Daily ATR', session.daily_atr)
                ]
                
                for field_name, value in atr_fields:
                    if value < 0:
                        errors['metrics'].append(f"{field_name} cannot be negative")
                
                # Special validation for 5-minute ATR (critical for pivot zones)
                if session.atr_5min <= 0:
                    errors['metrics'].append("5-minute ATR is required for pivot zone creation")
                
                # RELAXED ATR bands calculation validation
                if session.daily_atr > 0 and session.pre_market_price > 0:
                    expected_high = session.pre_market_price + session.daily_atr
                    expected_low = session.pre_market_price - session.daily_atr
                    
                    # Use a very large tolerance - 5 points
                    tolerance = Decimal("5.0")
                    
                    if session.atr_high > 0:
                        diff_high = abs(session.atr_high - expected_high)
                        if diff_high > tolerance:
                            logger.info(f"ATR High calculation difference: {diff_high:.2f}")
                            
                    if session.atr_low > 0:
                        diff_low = abs(session.atr_low - expected_low)
                        if diff_low > tolerance:
                            logger.info(f"ATR Low calculation difference: {diff_low:.2f}")
            
        except Exception as e:
            errors['metrics'].append(str(e))
        
        # Validate Pivot Confluence Data
        if session.pivot_confluence_data:
            pivot_errors = PivotConfluenceValidator.validate_pivot_confluence_data(session.pivot_confluence_data)
            errors['pivot_confluence'].extend(pivot_errors)
        
        # Check if any errors exist
        has_errors = any(error_list for error_list in errors.values())
        
        return not has_errors, errors
    
    @staticmethod
    def validate_for_analysis(session: TradingSession) -> Tuple[bool, List[str]]:
        """
        Validate that a session has all required data for pivot confluence analysis.
        RELAXED: Only check for essential data.
        
        Args:
            session: TradingSession to validate
            
        Returns:
            Tuple of (can_analyze, list_of_missing_items)
        """
        missing = []
        
        # Essential data for pivot confluence analysis
        if not session.ticker:
            missing.append("Ticker symbol")
        
        # Need daily data for Daily Camarilla pivot calculation
        if not session.daily_data or not session.daily_data.price_levels:
            missing.append("Daily price levels (required for Daily Camarilla pivots)")
        
        # Need 5-minute ATR for pivot zone creation
        if session.atr_5min <= 0:
            missing.append("5-minute ATR (required for pivot zone expansion)")
        
        # Current price for confluence scoring
        if session.pre_market_price <= 0:
            missing.append("Current price (pre-market price)")
        
        # Warn about missing optional data, but don't block analysis
        if not session.weekly_data:
            logger.warning("Weekly analysis data missing - some confluence sources unavailable")
        
        if session.daily_atr <= 0:
            logger.warning("Daily ATR not calculated - some ATR zones unavailable")
        
        if session.atr_15min <= 0:
            logger.warning("15-minute ATR not calculated - daily zones may be unavailable")
        
        if session.atr_2hour <= 0:
            logger.warning("2-hour ATR not calculated - weekly zones may be unavailable")
        
        return len(missing) == 0, missing


class ATRValidator:
    """Validator for ATR calculations - Pure Pivot Confluence System"""
    
    @staticmethod
    def validate_atr_values(atr_5min: Decimal, atr_2hour: Decimal,
                           atr_15min: Decimal, daily_atr: Decimal) -> List[str]:
        """
        Validate ATR values for consistency in pivot confluence system.
        RELAXED: Only return warnings, not errors.
        
        Args:
            atr_5min: 5-minute ATR (CRITICAL for pivot zones)
            atr_2hour: 2-hour ATR
            atr_15min: 15-minute ATR
            daily_atr: Daily ATR
            
        Returns:
            List of validation warnings (not errors)
        """
        warnings = []
        
        # Critical validation for 5-minute ATR (used for pivot zones)
        if atr_5min <= 0:
            warnings.append("5-minute ATR is zero or negative - pivot zones cannot be created")
        
        # RELAXED: Use larger multipliers for unusual comparisons
        if atr_5min > atr_2hour * Decimal("3.0"):
            warnings.append("5-min ATR unusually high compared to 2-hour ATR")
        
        if atr_2hour > atr_15min * Decimal("0.5"):
            warnings.append("2-hour ATR unusually low compared to 15-min ATR")
        
        # Daily ATR should typically be larger than intraday ATRs
        if daily_atr < atr_15min * Decimal("0.5"):
            warnings.append("Daily ATR is smaller than half of 15-min ATR (unusual)")
        
        # Check for extreme values
        if daily_atr > atr_15min * Decimal("20"):
            warnings.append("Daily ATR seems extremely high compared to intraday ATRs")
        
        # Pivot-specific warnings
        if atr_5min > daily_atr * Decimal("0.5"):
            warnings.append("5-min ATR is more than 50% of daily ATR (unusual - check data)")
        
        return warnings


class DateTimeValidator:
    """Validator for date and time related fields - Pure Pivot Confluence System"""
    
    @staticmethod
    def validate_market_date(check_date: date) -> Tuple[bool, str]:
        """
        Validate that a date is valid for pivot analysis.
        RELAXED: Allow any date.
        
        Args:
            check_date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow any date - past, present, or future for pivot analysis
        return True, ""
    
    @staticmethod
    def validate_pivot_analysis_timing(analysis_datetime: datetime) -> List[str]:
        """
        Validate timing for pivot confluence analysis.
        RELAXED: Only check for extremely future dates.
        
        Args:
            analysis_datetime: When the pivot analysis is being run (UTC)
            
        Returns:
            List of validation errors (minimal restrictions)
        """
        errors = []
        
        # Only check that analysis time isn't more than 1 day in the future
        future_limit = datetime.utcnow() + timedelta(days=1)
        
        if analysis_datetime > future_limit:
            errors.append(f"Pivot analysis time is more than 1 day in the future: {analysis_datetime}")
        
        return errors


# Convenience functions for common validations
def validate_trading_session(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate a complete trading session with RELAXED rules for pivot confluence.
    
    Args:
        session: TradingSession to validate
        
    Returns:
        Tuple of (is_valid, errors_dict)
    """
    return TradingSessionValidator.validate_session(session)


def validate_for_analysis(session: TradingSession) -> Tuple[bool, List[str]]:
    """
    Check if a session is ready for pivot confluence analysis with RELAXED rules.
    
    Args:
        session: TradingSession to check
        
    Returns:
        Tuple of (ready_for_analysis, missing_items)
    """
    return TradingSessionValidator.validate_for_analysis(session)


def validate_pivot_confluence_settings(settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate pivot confluence settings from UI.
    
    Args:
        settings: Dictionary of confluence settings
        
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = PivotConfluenceValidator.validate_pivot_confluence_settings(settings)
    return len(errors) == 0, errors


# Optional: Function to temporarily disable validation
def validate_trading_session_lenient(session: TradingSession) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Ultra-lenient validation for pivot confluence - only check critical fields.
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
        'pivot_confluence': []
    }
    
    # Only validate the absolute minimum for pivot confluence
    try:
        # Must have a ticker
        if not session.ticker:
            errors['overview'].append("Ticker is required")
        
        # Must have a valid date
        if not session.date:
            errors['overview'].append("Date is required")
        
        # For pivot confluence, we really need 5-minute ATR
        if session.atr_5min <= 0:
            errors['metrics'].append("5-minute ATR is required for pivot zones")
            
    except Exception as e:
        logger.warning(f"Lenient pivot validation encountered error: {e}")
        # Even if there's an error, we'll allow it
    
    # Log any issues but still return valid
    if any(error_list for error_list in errors.values()):
        logger.warning(f"Lenient pivot validation found issues: {errors}")
    
    # Always return True for lenient validation
    return True, errors


# Pivot-specific validation functions
def validate_pivot_zone_creation(daily_camarilla_pivots: List[Decimal], 
                                atr_5min: Decimal,
                                current_price: Decimal) -> Tuple[bool, List[str]]:
    """
    Validate that we have sufficient data to create pivot zones.
    
    Args:
        daily_camarilla_pivots: List of Daily Camarilla pivot prices
        atr_5min: 5-minute ATR for zone expansion
        current_price: Current market price
        
    Returns:
        Tuple of (can_create_zones, error_list)
    """
    errors = []
    
    # Need at least one pivot
    if not daily_camarilla_pivots or all(p <= 0 for p in daily_camarilla_pivots):
        errors.append("No valid Daily Camarilla pivot prices available")
    
    # Need positive 5-minute ATR
    if atr_5min <= 0:
        errors.append("5-minute ATR must be positive to create pivot zones")
    
    # Need current price for reference
    if current_price <= 0:
        errors.append("Current price must be positive")
    
    # Check for reasonable ATR relative to price
    if atr_5min > 0 and current_price > 0:
        atr_percentage = (atr_5min / current_price) * 100
        if atr_percentage > 10:  # 10% seems very high for 5-min ATR
            errors.append(f"5-minute ATR is {atr_percentage:.1f}% of current price (unusually high)")
    
    return len(errors) == 0, errors


def validate_confluence_sources(hvn_results: Dict, camarilla_results: Dict,
                               weekly_zones: List, daily_zones: List, 
                               atr_zones: List) -> Tuple[int, List[str]]:
    """
    Validate and count available confluence sources.
    
    Args:
        hvn_results: HVN analysis results
        camarilla_results: Camarilla pivot results  
        weekly_zones: Weekly zone results
        daily_zones: Daily zone results
        atr_zones: ATR zone results
        
    Returns:
        Tuple of (source_count, warnings_list)
    """
    source_count = 0
    warnings = []
    
    # Count HVN sources
    for timeframe, result in hvn_results.items():
        if result and hasattr(result, 'peaks') and result.peaks:
            source_count += 1
        else:
            warnings.append(f"HVN {timeframe} results unavailable")
    
    # Count Camarilla sources (excluding daily - that's our base)
    for timeframe, result in camarilla_results.items():
        if timeframe != 'daily' and result and hasattr(result, 'pivots') and result.pivots:
            source_count += 1
        else:
            warnings.append(f"Camarilla {timeframe} results unavailable")
    
    # Count zone sources
    if weekly_zones:
        source_count += 1
    else:
        warnings.append("Weekly zones unavailable")
    
    if daily_zones:
        source_count += 1
    else:
        warnings.append("Daily zones unavailable")
    
    if atr_zones:
        source_count += 1
    else:
        warnings.append("ATR zones unavailable")
    
    # Warn if we have very few sources
    if source_count < 3:
        warnings.append(f"Only {source_count} confluence sources available - results may be less reliable")
    
    return source_count, warnings