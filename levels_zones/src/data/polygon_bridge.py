# levels_zones/src/data/polygon_bridge.py
"""
Polygon Bridge for Meridian Trading System
Connects to the local Polygon REST API server to fetch market data
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from data.models import TradingSession, PriceLevel

logger = logging.getLogger(__name__)


class PolygonBridge:
    """
    Bridge between Meridian Trading System and Polygon REST API.
    Handles data fetching, ATR calculations, and price analysis.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:8200/api/v1",
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize Polygon Bridge with REST API connection.
        
        Args:
            base_url: Base URL for the Polygon REST API server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Polygon Bridge initialized with base URL: {self.base_url}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to the REST API server.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/rate-limit",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, f"Connected! Rate limit: {data.get('remaining', 'N/A')} remaining"
            else:
                return False, f"Server returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Polygon REST API server"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate if a ticker symbol is valid.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            bool: True if valid
        """
        try:
            response = self.session.post(
                f"{self.base_url}/validate",
                json={"symbols": [ticker], "detailed": False},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get(ticker, {}).get("valid", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating ticker {ticker}: {e}")
            return False
    
    def fetch_bars(self, 
               symbol: str,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None,
               timeframe: str = "5min",
               limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV bars for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Bar timeframe (1min, 5min, 15min, 1hour, 1day)
            limit: Maximum number of bars to return
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            # Prepare request payload
            payload = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,  # Just the string, not {"value": timeframe}
                "use_cache": True,
                "validate": False
            }
            
            if start_date:
                payload["start_date"] = start_date
            if end_date:
                payload["end_date"] = end_date
            if limit:
                payload["limit"] = limit
            
            # Make request
            response = self.session.post(
                f"{self.base_url}/bars",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to DataFrame
                if data.get("data"):
                    df = pd.DataFrame(data["data"])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    logger.info(f"Fetched {len(df)} bars for {symbol}")
                    return df
                else:
                    logger.warning(f"No data returned for {symbol}")
                    return pd.DataFrame()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {e}")
            return None
        
    def get_historical_bars(self, 
                       ticker: str,
                       start_date: date,
                       end_date: date,
                       timeframe: str = '5min') -> pd.DataFrame:
        """
        Fetch historical bars from Polygon REST API.
        Compatibility method that maps to fetch_bars.
        
        Args:
            ticker: Stock symbol
            start_date: Start date (date object)
            end_date: End date (date object)
            timeframe: Bar timeframe ('5min', 'day', etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        # Convert date objects to strings
        start_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, date) else start_date
        end_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, date) else end_date
        
        # Map timeframe format if needed
        timeframe_map = {
            '5min': '5min',
            '10min': '10min', 
            '15min': '15min',
            'day': '1day',
            '1day': '1day'
        }
        
        mapped_timeframe = timeframe_map.get(timeframe, timeframe)
        
        # Call the existing fetch_bars method
        result = self.fetch_bars(
            symbol=ticker,
            start_date=start_str,
            end_date=end_str,
            timeframe=mapped_timeframe
        )
        
        # Return empty DataFrame if None
        return result if result is not None else pd.DataFrame()
    
    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Latest price as Decimal or None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/latest/{symbol}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                price = data.get("price")
                if price is not None:
                    return Decimal(str(price))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    def calculate_atr(self, 
                     df: pd.DataFrame, 
                     period: int = 14) -> Optional[Decimal]:
        """
        Calculate Average True Range (ATR) from OHLC data.
        
        Args:
            df: DataFrame with OHLC columns
            period: ATR period (default 14)
            
        Returns:
            ATR value as Decimal or None
        """
        try:
            if len(df) < period + 1:
                logger.warning(f"Insufficient data for ATR calculation: {len(df)} bars")
                return None
            
            # Calculate True Range
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate ATR (exponential moving average)
            atr = true_range.ewm(span=period, adjust=False).mean()
            
            # Return the latest ATR value
            latest_atr = atr.iloc[-1]
            return Decimal(str(round(latest_atr, 2)))
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None
    
    def get_session_data(self, 
                        symbol: str,
                        session_datetime: datetime) -> Dict[str, Any]:
        """
        Get all required data for a trading session.
        
        Args:
            symbol: Stock ticker symbol
            session_datetime: DateTime for the session
            
        Returns:
            Dictionary with session data including prices and ATRs
        """
        result = {
            'symbol': symbol,
            'session_datetime': session_datetime,
            'current_price': None,
            'pre_market_price': None,
            'open_price': None,
            'atr_5min': None,
            'atr_10min': None,
            'atr_15min': None,
            'daily_atr': None,
            'atr_high': None,
            'atr_low': None,
            'error': None
        }
        
        try:
            # Validate ticker first
            if not self.validate_ticker(symbol):
                result['error'] = f"Invalid ticker symbol: {symbol}"
                return result
            
            # Determine date range for data fetching
            session_date = session_datetime.date()
            
            # For ATR calculations, we need historical data
            # Daily ATR needs 20+ days, intraday ATRs need 2-3 days
            daily_start = session_date - timedelta(days=30)
            intraday_start = session_date - timedelta(days=3)
            
            # Format dates
            daily_start_str = daily_start.strftime('%Y-%m-%d')
            intraday_start_str = intraday_start.strftime('%Y-%m-%d')
            session_date_str = session_date.strftime('%Y-%m-%d')
            
            # Fetch daily data for daily ATR
            logger.info(f"Fetching daily data for {symbol}")
            daily_df = self.fetch_bars(
                symbol=symbol,
                start_date=daily_start_str,
                end_date=session_date_str,
                timeframe='1day'
            )

            if daily_df is not None and not daily_df.empty:
                # Calculate daily ATR
                result['daily_atr'] = self.calculate_atr(daily_df, period=14)
                
                # Get the opening price from session date or most recent
                try:
                    # Check if we have data for the specific session date
                    daily_df_dates = daily_df.index.strftime('%Y-%m-%d')
                    if session_date_str in daily_df_dates:
                        # Use the open price from the exact session date
                        idx = daily_df_dates.tolist().index(session_date_str)
                        result['open_price'] = Decimal(str(float(daily_df.iloc[idx]['open'])))
                    else:
                        # Use the most recent available open price
                        result['open_price'] = Decimal(str(float(daily_df.iloc[-1]['open'])))
                except Exception as e:
                    logger.warning(f"Could not get open price: {e}")
            
            # Fetch 5-minute data
            logger.info(f"Fetching 5-minute data for {symbol}")
            df_5min = self.fetch_bars(
                symbol=symbol,
                start_date=intraday_start_str,
                end_date=session_date_str,
                timeframe='5min'
            )
            
            if df_5min is not None and not df_5min.empty:
                result['atr_5min'] = self.calculate_atr(df_5min, period=14)
                
                # Get price at session datetime
                nearest_time = self._find_nearest_time(df_5min, session_datetime)
                if nearest_time is not None:
                    result['current_price'] = Decimal(str(df_5min.loc[nearest_time]['close']))
                
                # Get pre-market price (first bar of the day)
                session_day_data = df_5min[df_5min.index.date == session_date]
                if not session_day_data.empty:
                    result['pre_market_price'] = Decimal(str(session_day_data.iloc[0]['open']))
            
            # Fetch 10-minute data (aggregate from 5-min if not available)
            logger.info(f"Calculating 10-minute ATR for {symbol}")
            if df_5min is not None and not df_5min.empty:
                # Resample 5-min to 10-min
                df_10min = df_5min.resample('10min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if not df_10min.empty:
                    result['atr_10min'] = self.calculate_atr(df_10min, period=14)
            
            # Fetch 15-minute data
            logger.info(f"Fetching 15-minute data for {symbol}")
            df_15min = self.fetch_bars(
                symbol=symbol,
                start_date=intraday_start_str,
                end_date=session_date_str,
                timeframe='15min'
            )
            
            if df_15min is not None and not df_15min.empty:
                result['atr_15min'] = self.calculate_atr(df_15min, period=14)
            
            # Calculate ATR bands if we have price and daily ATR
            if result['current_price'] and result['daily_atr']:
                result['atr_high'] = result['current_price'] + result['daily_atr']
                result['atr_low'] = result['current_price'] - result['daily_atr']
            elif result['pre_market_price'] and result['daily_atr']:
                result['atr_high'] = result['pre_market_price'] + result['daily_atr']
                result['atr_low'] = result['pre_market_price'] - result['daily_atr']
            
            # Get latest price if current price not found
            if result['current_price'] is None:
                result['current_price'] = self.get_latest_price(symbol)
            
            logger.info(f"Session data collection complete for {symbol}")
            
        except Exception as e:
            logger.error(f"Error getting session data for {symbol}: {e}")
            result['error'] = str(e)
        
        return result
    
    def get_price_at_datetime(self, 
                             symbol: str, 
                             target_datetime: datetime,
                             timeframe: str = '5min') -> Optional[Decimal]:
        """
        Get price at a specific datetime.
        
        Args:
            symbol: Stock ticker symbol
            target_datetime: Target datetime
            timeframe: Timeframe for data
            
        Returns:
            Price at datetime or None
        """
        try:
            # Fetch data around the target time
            start_date = (target_datetime - timedelta(hours=2)).strftime('%Y-%m-%d')
            end_date = target_datetime.strftime('%Y-%m-%d')
            
            df = self.fetch_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            if df is not None and not df.empty:
                nearest_time = self._find_nearest_time(df, target_datetime)
                if nearest_time is not None:
                    return Decimal(str(df.loc[nearest_time]['close']))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting price at datetime: {e}")
            return None
    
    def get_candle_at_datetime(self, 
                          symbol: str,
                          target_datetime: datetime,
                          timeframe: str = '15min') -> Optional[Dict[str, Any]]:
        """Get full candle data at a specific datetime."""
        try:
            # Calculate date range - FIXED VERSION
            target_date = target_datetime.date()
            start_date = (target_datetime - timedelta(hours=4)).strftime('%Y-%m-%d')
            end_date = target_datetime.strftime('%Y-%m-%d')
            
            # FIX: If same day, extend end date to next day
            if start_date == end_date:
                end_date = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.debug(f"Adjusted date range to avoid same-day error: {start_date} to {end_date}")
            
            df = self.fetch_bars(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            if df is not None and not df.empty:
                nearest_time = self._find_nearest_time(df, target_datetime)
                if nearest_time is not None:
                    candle = df.loc[nearest_time]
                    return {
                        'datetime': nearest_time,
                        'open': Decimal(str(candle['open'])),
                        'high': Decimal(str(candle['high'])),
                        'low': Decimal(str(candle['low'])),
                        'close': Decimal(str(candle['close'])),
                        'volume': int(candle['volume'])
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting candle at datetime: {e}")
            return None
    
    def update_session_metrics(self, session: TradingSession) -> bool:
        """
        Update a TradingSession object with calculated metrics from market data.
        
        Args:
            session: TradingSession object to update
            
        Returns:
            bool: True if successful
        """
        try:
            # Get session data
            session_datetime = datetime.combine(session.date, datetime.min.time())
            if session.historical_time:
                session_datetime = datetime.combine(session.date, session.historical_time)
            
            data = self.get_session_data(session.ticker, session_datetime)
            
            if data.get('error'):
                logger.error(f"Failed to get session data: {data['error']}")
                return False
            
            # Update metrics
            if data['pre_market_price']:
                session.pre_market_price = data['pre_market_price']
            if data['atr_5min']:
                session.atr_5min = data['atr_5min']
            if data['atr_10min']:
                session.atr_10min = data['atr_10min']
            if data['atr_15min']:
                session.atr_15min = data['atr_15min']
            if data['daily_atr']:
                session.daily_atr = data['daily_atr']
            
            # Calculate ATR bands
            session.calculate_atr_bands()
            
            logger.info(f"Updated metrics for session {session.ticker_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session metrics: {e}")
            return False
    
    # levels_zones/src/data/polygon_bridge.py
    def _find_nearest_time(self, 
                        df: pd.DataFrame, 
                        target_time: datetime,
                        max_delta_minutes: int = 30) -> Optional[pd.Timestamp]:
        """
        Find the nearest time in DataFrame index to target time.
        """
        try:
            # Convert target to pandas timestamp
            target_ts = pd.Timestamp(target_time)
            
            # Ensure both timestamps have the same timezone handling
            if df.index.tz is not None and target_ts.tz is None:
                # If df index is tz-aware and target is naive, localize target to UTC
                target_ts = target_ts.tz_localize('UTC')
            elif df.index.tz is None and target_ts.tz is not None:
                # If df index is naive and target is tz-aware, remove timezone from target
                target_ts = target_ts.tz_localize(None)
            
            # If target is in index, return it
            if target_ts in df.index:
                return target_ts
            
            # Find nearest
            time_diff = abs(df.index - target_ts)
            nearest_idx = time_diff.argmin()
            nearest_time = df.index[nearest_idx]
            
            # Check if within max delta
            delta = abs(nearest_time - target_ts)
            if delta <= timedelta(minutes=max_delta_minutes):
                return nearest_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding nearest time: {e}")
            return None
    
    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols by name or ticker.
        
        Args:
            query: Search query
            
        Returns:
            List of matching symbols
        """
        try:
            response = self.session.get(
                f"{self.base_url}/search",
                params={"query": query, "active_only": True},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            return []
    
    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """
        Clear cache for a symbol or all symbols.
        
        Args:
            symbol: Specific symbol to clear or None for all
            
        Returns:
            bool: True if successful
        """
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            response = self.session.delete(
                f"{self.base_url}/cache",
                params=params,
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize bridge
    bridge = PolygonBridge()
    
    # Test connection
    connected, message = bridge.test_connection()
    print(f"Connection test: {message}")
    
    if connected:
        # Test getting session data
        session_data = bridge.get_session_data("AAPL", datetime.now())
        print("\nSession data for AAPL:")
        for key, value in session_data.items():
            if value is not None and key != 'error':
                print(f"  {key}: {value}")