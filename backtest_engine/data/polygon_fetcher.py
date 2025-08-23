# data/polygon_fetcher.py
"""
Enhanced Polygon data fetcher for backtesting
Maps to existing polygon_bridge.py implementation
"""

import os
import logging
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import json

import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from data.supabase_client import BacktestSupabaseClient
from core.models import SignalType, TICK_SIZE

logger = logging.getLogger(__name__)

class PolygonBacktestFetcher:
    """
    Polygon data fetcher for backtesting that uses the existing REST API bridge
    Inherits patterns from polygon_bridge.py
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:8200/api/v1",
                 supabase_client: BacktestSupabaseClient = None,
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize Polygon fetcher using REST API bridge
        
        Args:
            base_url: Base URL for the Polygon REST API server
            supabase_client: Supabase client for caching
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.supabase = supabase_client or BacktestSupabaseClient()
        
        # Configure session with retry strategy (same as polygon_bridge.py)
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
        
        logger.info(f"PolygonBacktestFetcher initialized with base URL: {self.base_url}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the REST API server"""
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
    
    def fetch_bars(self, 
               symbol: str,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None,
               timeframe: str = "5min",
               limit: Optional[int] = None,
               use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV bars for a symbol (matches polygon_bridge.py)
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Bar timeframe (1min, 5min, 15min, 1hour, 1day)
            limit: Maximum number of bars to return
            use_cache: Whether to use cache
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            # FIX: Handle same-day queries by extending end date
            if start_date and end_date and start_date == end_date:
                from datetime import datetime, timedelta
                # Parse the end date and add one day
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.debug(f"Adjusted same-day query: start={start_date}, end={end_date}")
            
            # Prepare request payload (matching polygon_bridge.py format)
            payload = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "use_cache": use_cache,
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
    
    def fetch_minute_bars(self, ticker: str, start_time: datetime, end_time: datetime, use_cache: bool = False) -> pd.DataFrame:
        """
        Fetch 1-minute bars for a given time range
        
        Args:
            ticker: Stock symbol
            start_time: Start datetime
            end_time: End datetime
            use_cache: Whether to use cached data (default: False to ensure fresh data)
            
        Returns:
            DataFrame with OHLCV data indexed by timestamp
        """
        try:
            # Skip Supabase cache check if not using cache
            if use_cache and self.supabase and hasattr(self.supabase, 'client'):
                try:
                    cached = self.supabase.client.table('minute_bars_cache').select('*').eq(
                        'ticker', ticker
                    ).gte(
                        'bar_timestamp', start_time.isoformat()
                    ).lte(
                        'bar_timestamp', end_time.isoformat()
                    ).order('bar_timestamp').execute()
                    
                    if cached.data and len(cached.data) > 0:
                        df = pd.DataFrame(cached.data)
                        df['bar_timestamp'] = pd.to_datetime(df['bar_timestamp'])
                        df.set_index('bar_timestamp', inplace=True)
                        df.index.name = 'timestamp'
                        logger.info(f"Using cached minute data: {len(df)} bars")
                        return df[['open', 'high', 'low', 'close', 'volume', 'vwap']]
                except Exception as e:
                    logger.debug(f"Cache lookup failed: {e}")
            
            # HARD CODED TRADING HOURS: Always fetch full trading day
            # 12:30 UTC (8:30 AM ET) to 20:00 UTC (4:00 PM ET)
            trade_date = start_time.date()
            
            # Create hard-coded start and end times for the full trading day
            market_start = datetime.combine(trade_date, time(12, 30))  # 12:30 UTC
            market_end = datetime.combine(trade_date, time(20, 0))     # 20:00 UTC
            
            logger.info(f"Fetching full trading day data: {market_start} to {market_end} UTC")
            
            # Convert to date strings for the API
            start_date_str = trade_date.strftime('%Y-%m-%d')
            end_date_str = (trade_date + timedelta(days=1)).strftime('%Y-%m-%d')  # Always next day to avoid same-day issue
            
            # Fetch full day's data from REST API bridge
            df = self.fetch_bars(
                symbol=ticker,
                start_date=start_date_str,
                end_date=end_date_str,
                timeframe='1min',
                use_cache=use_cache  # Respect cache parameter
            )
            
            if df is not None and not df.empty:
                # Filter to trading hours (12:30 UTC to 20:00 UTC)
                import pytz
                
                # Ensure our filter times are UTC aware
                market_start_utc = pytz.UTC.localize(market_start)
                market_end_utc = pytz.UTC.localize(market_end)
                
                # Filter to market hours
                df_market = df[(df.index >= market_start_utc) & (df.index <= market_end_utc)]
                
                logger.info(f"Filtered to market hours: {len(df_market)} bars from {len(df)} total")
                
                # Now filter to the requested time range
                if start_time.tzinfo is None:
                    start_time_utc = pytz.UTC.localize(start_time)
                else:
                    start_time_utc = start_time.astimezone(pytz.UTC)
                    
                if end_time.tzinfo is None:
                    end_time_utc = pytz.UTC.localize(end_time)
                else:
                    end_time_utc = end_time.astimezone(pytz.UTC)
                
                # Final filter to requested range
                df_filtered = df_market[(df_market.index >= start_time_utc) & (df_market.index <= end_time_utc)]
                
                # Ensure we have the required columns
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in required_cols:
                    if col not in df_filtered.columns:
                        logger.warning(f"Missing column {col} in data")
                        df_filtered[col] = 0
                
                # Add VWAP if not present
                if 'vwap' not in df_filtered.columns or df_filtered['vwap'].isna().all():
                    df_filtered['vwap'] = self._calculate_vwap(df_filtered)
                
                logger.info(f"Returning {len(df_filtered)} minute bars for {ticker} from {start_time} to {end_time}")
                
                if len(df_filtered) == 0:
                    logger.warning(f"No data in requested range {start_time_utc} to {end_time_utc}")
                    if len(df_market) > 0:
                        logger.info(f"Market hours data available: {df_market.index[0]} to {df_market.index[-1]}")
                
                return df_filtered
            else:
                logger.warning(f"No minute data returned for {ticker}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching minute bars: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def fetch_m5_candles(self, ticker: str, session_date: date, 
                        start_time: time = time(9, 30), 
                        end_time: time = time(16, 0),
                        use_cache: bool = True) -> pd.DataFrame:
        """
        Fetch M5 candles for a trading session
        
        Args:
            ticker: Stock ticker
            session_date: Trading date
            start_time: Session start time
            end_time: Session end time
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with OHLCV + VWAP data
        """
        # First check Supabase cache
        if use_cache:
            cached_data = self.supabase.get_cached_polygon_data(
                ticker, session_date, "M5"
            )
            if cached_data:
                logger.debug(f"Using cached M5 data for {ticker} on {session_date}")
                df = pd.DataFrame(cached_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
        
        # Fetch from REST API bridge
        try:
            # Use the fetch_bars method that matches polygon_bridge.py
            start_str = session_date.strftime('%Y-%m-%d')
            end_str = session_date.strftime('%Y-%m-%d')
            
            df = self.fetch_bars(
                symbol=ticker,
                start_date=start_str,
                end_date=end_str,
                timeframe='5min',
                use_cache=use_cache
            )
            
            if df is not None and not df.empty:
                # Filter to session hours
                session_start = pd.Timestamp.combine(session_date, start_time)
                session_end = pd.Timestamp.combine(session_date, end_time)
                
                # Handle timezone if present
                if df.index.tz is not None:
                    session_start = session_start.tz_localize(df.index.tz)
                    session_end = session_end.tz_localize(df.index.tz)
                
                df = df[(df.index >= session_start) & (df.index <= session_end)]
                
                # Calculate VWAP if not present
                if 'vwap' not in df.columns or df['vwap'].isna().all():
                    df['vwap'] = self._calculate_vwap(df)
                
                # Cache in Supabase
                if use_cache and not df.empty:
                    cache_data = df.reset_index().to_dict('records')
                    for record in cache_data:
                        record['timestamp'] = record['timestamp'].isoformat()
                    
                    self.supabase.cache_polygon_data(
                        ticker, session_date, "M5", cache_data
                    )
                
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching M5 data: {e}")
            return pd.DataFrame()
    
    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        """Get the latest price for a symbol"""
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
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[Decimal]:
        """
        Calculate Average True Range (ATR) from OHLC data
        Matches polygon_bridge.py implementation
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
    
    def identify_pivot_candles(self, df: pd.DataFrame, 
                              lookback: int = 3) -> List[Dict[str, Any]]:
        """
        Identify M5 pivot highs and lows
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of candles to look back/forward for pivot
            
        Returns:
            List of pivot candles with details
        """
        if df.empty or len(df) < (lookback * 2 + 1):
            return []
        
        pivots = []
        
        for i in range(lookback, len(df) - lookback):
            current_idx = df.index[i]
            current = df.iloc[i]
            
            # Check for pivot high
            is_pivot_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df.iloc[j]['high'] >= current['high']:
                    is_pivot_high = False
                    break
            
            if is_pivot_high:
                strength = self._calculate_pivot_strength(df, i, 'high')
                
                pivots.append({
                    'timestamp': current_idx,
                    'type': SignalType.PIVOT_HIGH,
                    'price': float(current['high']),
                    'open': float(current['open']),
                    'high': float(current['high']),
                    'low': float(current['low']),
                    'close': float(current['close']),
                    'volume': int(current['volume']),
                    'vwap': float(current.get('vwap', 0)),
                    'strength': strength
                })
            
            # Check for pivot low
            is_pivot_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df.iloc[j]['low'] <= current['low']:
                    is_pivot_low = False
                    break
            
            if is_pivot_low:
                strength = self._calculate_pivot_strength(df, i, 'low')
                
                pivots.append({
                    'timestamp': current_idx,
                    'type': SignalType.PIVOT_LOW,
                    'price': float(current['low']),
                    'open': float(current['open']),
                    'high': float(current['high']),
                    'low': float(current['low']),
                    'close': float(current['close']),
                    'volume': int(current['volume']),
                    'vwap': float(current.get('vwap', 0)),
                    'strength': strength
                })
        
        logger.info(f"Identified {len(pivots)} pivot points")
        return pivots
    
    def _calculate_pivot_strength(self, df: pd.DataFrame, pivot_idx: int, 
                                 pivot_type: str) -> int:
        """Calculate pivot strength on 1-3 scale"""
        strength = 1
        
        # Check volume (above average = +1)
        if pivot_idx >= 20:
            avg_volume = df['volume'].iloc[pivot_idx-20:pivot_idx].mean()
            if df.iloc[pivot_idx]['volume'] > avg_volume * 1.5:
                strength += 1
        
        # Check price movement magnitude
        if pivot_type == 'high':
            recent_low = df.iloc[max(0, pivot_idx-10):pivot_idx]['low'].min()
            move_pct = (df.iloc[pivot_idx]['high'] - recent_low) / recent_low * 100
        else:
            recent_high = df.iloc[max(0, pivot_idx-10):pivot_idx]['high'].max()
            move_pct = (recent_high - df.iloc[pivot_idx]['low']) / recent_high * 100
        
        if move_pct > 1.0:  # More than 1% move
            strength += 1
        
        return min(strength, 3)
    
    def _find_nearest_time(self, 
                          df: pd.DataFrame, 
                          target_time: datetime,
                          max_delta_minutes: int = 30) -> Optional[pd.Timestamp]:
        """
        Find the nearest time in DataFrame index to target time
        Matches polygon_bridge.py implementation
        """
        try:
            # Convert target to pandas timestamp
            target_ts = pd.Timestamp(target_time)
            
            # Ensure both timestamps have the same timezone handling
            if df.index.tz is not None and target_ts.tz is None:
                target_ts = target_ts.tz_localize('UTC')
            elif df.index.tz is None and target_ts.tz is not None:
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
    
    def _calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP from OHLCV data"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    def get_candle_at_datetime(self, 
                               symbol: str,
                               target_datetime: datetime,
                               timeframe: str = '15min') -> Optional[Dict[str, Any]]:
        """Get full candle data at a specific datetime"""
        try:
            # Calculate date range - matching polygon_bridge.py fix
            target_date = target_datetime.date()
            start_date = (target_datetime - timedelta(hours=4)).strftime('%Y-%m-%d')
            end_date = target_datetime.strftime('%Y-%m-%d')
            
            # If same day, extend end date to next day
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
    
    def get_session_data(self, symbol: str, session_datetime: datetime) -> Dict[str, Any]:
        """
        Get all required data for a trading session
        Matches polygon_bridge.py implementation
        """
        result = {
            'symbol': symbol,
            'session_datetime': session_datetime,
            'current_price': None,
            'pre_market_price': None,
            'open_price': None,
            'atr_5min': None,
            'atr_2hour': None,  # Changed from atr_10min
            'atr_15min': None,
            'daily_atr': None,
            'atr_high': None,
            'atr_low': None,
            'error': None
        }
        
        try:
            session_date = session_datetime.date()
            
            # For ATR calculations, we need historical data
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
                result['daily_atr'] = self.calculate_atr(daily_df, period=14)
                
                # Get opening price
                try:
                    daily_df_dates = daily_df.index.strftime('%Y-%m-%d')
                    if session_date_str in daily_df_dates:
                        idx = daily_df_dates.tolist().index(session_date_str)
                        result['open_price'] = Decimal(str(float(daily_df.iloc[idx]['open'])))
                    else:
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
                
                # Get pre-market price
                session_day_data = df_5min[df_5min.index.date == session_date]
                if not session_day_data.empty:
                    result['pre_market_price'] = Decimal(str(session_day_data.iloc[0]['open']))
                
                # Calculate 2-hour ATR from 5-min data
                logger.info(f"Calculating 2-hour ATR for {symbol}")
                df_2hour = df_5min.resample('2H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if not df_2hour.empty:
                    result['atr_2hour'] = self.calculate_atr(df_2hour, period=14)
            
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
            
            # Calculate ATR bands
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
    
    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """Clear cache for a symbol or all symbols"""
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

# Utility function for batch fetching
def batch_fetch_with_cache(fetcher: PolygonBacktestFetcher, 
                          requests: List[Dict]) -> Dict[str, pd.DataFrame]:
    """
    Batch fetch data with caching
    
    Args:
        fetcher: PolygonBacktestFetcher instance
        requests: List of request dictionaries
        
    Returns:
        Dictionary of results keyed by request ID
    """
    results = {}
    
    for request in requests:
        request_id = request.get('id', str(len(results)))
        ticker = request['ticker']
        date = request['date']
        
        df = fetcher.fetch_m5_candles(
            ticker=ticker,
            session_date=date,
            start_time=request.get('start_time', time(9, 30)),
            end_time=request.get('end_time', time(16, 0))
        )
        
        results[request_id] = df
    
    return results