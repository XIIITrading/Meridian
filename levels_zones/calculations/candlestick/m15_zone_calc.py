"""
Fixed M15 Zone Calculator with workaround for PolygonBridge date issue
Location: levels_zones/calculations/candlestick/m15_zone_calc.py
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
import pytz

# Set up logging
logger = logging.getLogger(__name__)

class M15ZoneCalculator:
    """Calculator for M15 zone candle data"""
    
    def __init__(self):
        """Initialize the calculator with PolygonBridge"""
        try:
            from data.polygon_bridge import PolygonBridge
            self.bridge = PolygonBridge()
            logger.info("M15ZoneCalculator initialized with PolygonBridge")
        except ImportError as e:
            logger.error(f"Failed to import PolygonBridge: {e}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to Polygon"""
        try:
            return self.bridge.test_connection()
        except Exception as e:
            return False, str(e)
    
    def fetch_candle_for_zone(self, ticker: str, zone_date: str, zone_time: str) -> Optional[Dict[str, Decimal]]:
        """
        Fetch M15 candle data for a specific zone datetime
        
        Args:
            ticker: Stock ticker symbol
            zone_date: Date in YYYY-MM-DD format
            zone_time: Time in HH:MM:SS format (UTC)
            
        Returns:
            Dict with 'high', 'low', 'mid' prices or None if not found
        """
        try:
            # Parse date and time
            date_obj = datetime.strptime(zone_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(zone_time, '%H:%M:%S').time()
            
            # Combine into UTC datetime
            zone_datetime = datetime.combine(date_obj, time_obj)
            zone_datetime = pytz.UTC.localize(zone_datetime)
            
            logger.info(f"Fetching M15 candle for {ticker} at {zone_datetime} UTC")
            
            # WORKAROUND: Since get_historical_bars has date issues, let's try different approaches
            
            # Method 1: Try to get the candle directly if the bridge has this method
            if hasattr(self.bridge, 'get_candle_at_datetime'):
                try:
                    # Try using the next day as end_date to avoid the date equality issue
                    next_day = date_obj + timedelta(days=1)
                    
                    # Call with modified parameters
                    candle = self.bridge.get_candle_at_datetime(ticker, zone_datetime)
                    
                    if candle and isinstance(candle, dict):
                        high = Decimal(str(candle.get('h', candle.get('high', 0))))
                        low = Decimal(str(candle.get('l', candle.get('low', 0))))
                        
                        if high > 0 and low > 0:
                            return {
                                'high': high,
                                'low': low,
                                'mid': (high + low) / 2,
                                'open': Decimal(str(candle.get('o', candle.get('open', 0)))),
                                'close': Decimal(str(candle.get('c', candle.get('close', 0)))),
                                'volume': candle.get('v', candle.get('volume', 0)),
                                'timestamp': zone_datetime.isoformat()
                            }
                except Exception as e:
                    logger.error(f"get_candle_at_datetime failed: {e}")
            
            # Method 2: Try with date range spanning to next day
            try:
                # Use previous day to next day to ensure we get data
                prev_day = date_obj - timedelta(days=1)
                next_day = date_obj + timedelta(days=1)
                
                bars = self.bridge.get_historical_bars(
                    ticker=ticker,
                    start_date=prev_day,
                    end_date=next_day,
                    timeframe='15min'
                )
                
                # Process the bars
                if hasattr(bars, 'empty') and not bars.empty:
                    bars_list = bars.to_dict('records') if hasattr(bars, 'to_dict') else bars
                elif isinstance(bars, list):
                    bars_list = bars
                else:
                    bars_list = []
                
                # Find the candle at our target time with improved matching
                target_timestamp = int(zone_datetime.timestamp() * 1000)
                
                best_match = None
                best_time_diff = float('inf')
                
                for bar in bars_list:
                    bar_time = bar.get('t', bar.get('timestamp', 0))
                    time_diff = abs(bar_time - target_timestamp)
                    
                    # If this bar is within 15 minutes and closer than previous matches
                    if time_diff < 900000 and time_diff < best_time_diff:
                        best_match = bar
                        best_time_diff = time_diff
                        
                        # If we find an exact match (within 1 second), use it immediately
                        if time_diff < 1000:
                            break
                
                if best_match:
                    bar = best_match
                    high = Decimal(str(bar.get('h', bar.get('high', 0))))
                    low = Decimal(str(bar.get('l', bar.get('low', 0))))
                    
                    if high > 0 and low > 0:
                        # Log the actual vs requested time
                        actual_time = datetime.fromtimestamp(bar.get('t', 0) / 1000, tz=pytz.UTC)
                        logger.info(f"Found candle via date range method (requested: {zone_datetime}, actual: {actual_time})")
                        
                        return {
                            'high': high,
                            'low': low,
                            'mid': (high + low) / 2,
                            'open': Decimal(str(bar.get('o', bar.get('open', 0)))),
                            'close': Decimal(str(bar.get('c', bar.get('close', 0)))),
                            'volume': bar.get('v', bar.get('volume', 0)),
                            'timestamp': zone_datetime.isoformat(),
                            'actual_timestamp': actual_time.isoformat()
                        }
                
            except Exception as e:
                logger.error(f"Date range method failed: {e}")
            
            # Method 3: Last resort - use price estimation
            try:
                price = self.bridge.get_price_at_datetime(ticker, zone_datetime)
                if price and price > 0:
                    price_decimal = Decimal(str(price))
                    
                    # For 15-minute bars, typical spread is 0.1-0.3% for liquid stocks
                    # We'll use 0.15% as a reasonable estimate
                    spread_pct = Decimal('0.0015')
                    spread = price_decimal * spread_pct
                    
                    logger.info(f"Using price estimate for {ticker} at {zone_datetime}: ${price}")
                    
                    return {
                        'high': price_decimal + spread,
                        'low': price_decimal - spread,
                        'mid': price_decimal,
                        'open': price_decimal,
                        'close': price_decimal,
                        'volume': 0,
                        'timestamp': zone_datetime.isoformat(),
                        'estimated': True
                    }
            except Exception as e:
                logger.error(f"Price estimation also failed: {e}")
            
            logger.warning(f"No candle data found for {ticker} at {zone_datetime}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching candle for {ticker} at {zone_date} {zone_time}: {e}")
            return None
    
    def fetch_all_zone_candles(self, ticker: str, zones: List[Dict[str, str]]) -> List[Tuple[int, Optional[Dict[str, Decimal]]]]:
        """
        Fetch candle data for all zones
        
        Args:
            ticker: Stock ticker symbol
            zones: List of zone dictionaries with 'date' and 'time' keys
            
        Returns:
            List of tuples (zone_index, candle_data)
        """
        results = []
        
        for idx, zone in enumerate(zones):
            zone_date = zone.get('date', '')
            zone_time = zone.get('time', '')
            
            # Skip empty zones
            if not zone_date or not zone_time or \
               zone_date == 'yyyy-mm-dd' or \
               zone_time in ['hh:mm:ss', 'hh:mm:ss UTC']:
                results.append((idx, None))
                continue
            
            # Clean up time format if it has UTC suffix
            if zone_time.endswith(' UTC'):
                zone_time = zone_time.replace(' UTC', '')
            
            candle_data = self.fetch_candle_for_zone(ticker, zone_date, zone_time)
            results.append((idx, candle_data))
            
            if candle_data:
                if candle_data.get('estimated'):
                    logger.info(f"Zone {idx + 1}: Using estimated data based on price")
                else:
                    logger.info(f"Zone {idx + 1}: Found actual candle data")
            else:
                logger.warning(f"Zone {idx + 1}: No candle data found")
        
        return results
    
    def validate_market_hours(self, zone_datetime: datetime) -> Tuple[bool, str]:
        """
        Validate if the datetime is within market hours
        
        Args:
            zone_datetime: Datetime to validate (should be UTC)
            
        Returns:
            Tuple of (is_valid, market_session)
        """
        hour = zone_datetime.hour
        minute = zone_datetime.minute
        time_minutes = hour * 60 + minute
        
        # Pre-market: 4:00 AM - 9:30 AM ET (8:00 - 13:30 UTC)
        if 480 <= time_minutes < 810:  # 8:00 - 13:30 UTC
            return True, "Pre-market"
        
        # Regular market: 9:30 AM - 4:00 PM ET (13:30 - 20:00 UTC)  
        elif 810 <= time_minutes < 1200:  # 13:30 - 20:00 UTC
            return True, "Regular"
        
        # After-hours: 4:00 PM - 8:00 PM ET (20:00 - 00:00 UTC)
        elif 1200 <= time_minutes <= 1440:  # 20:00 - 24:00 UTC
            return True, "After-hours"
        
        else:
            return False, "Closed"