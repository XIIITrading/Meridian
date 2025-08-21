"""
Corrected M15 Zone Calculator 
Location: levels_zones/calculations/candlestick/m15_zone_calc.py
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
import pandas as pd

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
            
            logger.info(f"Fetching M15 candle for {ticker} at {zone_datetime} UTC")
            
            # Method 1: Use direct date range approach (most reliable)
            try:
                # Calculate date range with buffer to avoid same-date issues
                start_date = date_obj - timedelta(days=1)  # Previous day
                end_date = date_obj + timedelta(days=1)    # Next day
                
                logger.debug(f"Using date range: {start_date} to {end_date}")
                
                df = self.bridge.get_historical_bars(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe='15min'
                )
                
                if df is not None and not df.empty:
                    # Find the closest candle to our target time
                    target_time = pd.Timestamp(zone_datetime).tz_localize('UTC')
                    
                    # Ensure DataFrame index is timezone-aware
                    if df.index.tz is None:
                        df.index = df.index.tz_localize('UTC')
                    elif df.index.tz != pd.Timestamp.now().tz:
                        df.index = df.index.tz_convert('UTC')
                    
                    # Find nearest candle (within 15 minutes)
                    time_diffs = abs(df.index - target_time)
                    min_diff_idx = time_diffs.argmin()
                    min_diff = time_diffs.iloc[min_diff_idx]
                    
                    # Only accept if within 15 minutes (900 seconds)
                    if min_diff <= pd.Timedelta(minutes=15):
                        nearest_candle = df.iloc[min_diff_idx]
                        actual_time = df.index[min_diff_idx]
                        
                        logger.info(f"Found candle (requested: {zone_datetime}, actual: {actual_time})")
                        
                        return {
                            'high': Decimal(str(nearest_candle['high'])),
                            'low': Decimal(str(nearest_candle['low'])),
                            'mid': (Decimal(str(nearest_candle['high'])) + Decimal(str(nearest_candle['low']))) / 2,
                            'open': Decimal(str(nearest_candle['open'])),
                            'close': Decimal(str(nearest_candle['close'])),
                            'volume': int(nearest_candle['volume']),
                            'timestamp': zone_datetime.isoformat(),
                            'actual_timestamp': actual_time.isoformat()
                        }
                    else:
                        logger.warning(f"Nearest candle is {min_diff} away, too far from target")
                
            except Exception as e:
                logger.error(f"Date range method failed: {e}")
            
            # Method 2: Try the bridge's get_candle_at_datetime method (if available)
            if hasattr(self.bridge, 'get_candle_at_datetime'):
                try:
                    candle = self.bridge.get_candle_at_datetime(ticker, zone_datetime, '15min')
                    
                    if candle and isinstance(candle, dict):
                        high = Decimal(str(candle.get('high', 0)))
                        low = Decimal(str(candle.get('low', 0)))
                        
                        if high > 0 and low > 0:
                            logger.info(f"Found candle via get_candle_at_datetime")
                            return {
                                'high': high,
                                'low': low,
                                'mid': (high + low) / 2,
                                'open': Decimal(str(candle.get('open', 0))),
                                'close': Decimal(str(candle.get('close', 0))),
                                'volume': candle.get('volume', 0),
                                'timestamp': zone_datetime.isoformat()
                            }
                            
                except Exception as e:
                    logger.error(f"get_candle_at_datetime failed: {e}")
            
            # Method 3: Last resort - price estimation
            try:
                if hasattr(self.bridge, 'get_price_at_datetime'):
                    price = self.bridge.get_price_at_datetime(ticker, zone_datetime, '15min')
                    if price and price > 0:
                        price_decimal = Decimal(str(price))
                        
                        # Use 0.15% spread for estimation
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
                logger.error(f"Price estimation failed: {e}")
            
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