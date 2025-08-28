# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\data\polygon_client.py

"""
Simplified Polygon Client for Zone Scanner
Focused on essential data fetching operations
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PolygonClient:
    """
    Simplified Polygon Bridge for Zone Scanner
    Connects to local Polygon REST API server
    """
    
    def __init__(self, base_url: str = "http://localhost:8200/api/v1"):
        self.base_url = base_url.rstrip('/')
        
        # Configure session with retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Polygon Client initialized: {self.base_url}")
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to REST API"""
        try:
            # Since we know the server structure, let's test a simple endpoint
            # Try the docs at root level
            response = self.session.get("http://localhost:8200/docs", timeout=2, allow_redirects=True)
            if response.status_code in [200, 307]:
                return True, f"Connected to Polygon server at {self.base_url}"
            
            # If that fails, just try a HEAD request to see if server responds
            response = self.session.head("http://localhost:8200", timeout=5)
            if response.status_code < 500:
                return True, f"Connected to Polygon server"
                
            return False, f"Server returned status {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to server at http://localhost:8200"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def fetch_bars(self, 
                   symbol: str,
                   start_date: str,
                   end_date: str,
                   timeframe: str = "5min") -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV bars for a symbol
        
        Args:
            symbol: Stock ticker
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD  
            timeframe: Bar timeframe
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert timeframe format if needed
            # The server might expect "1day" instead of "day"
            timeframe_map = {
                'day': '1day',
                '1day': '1day',
                '5min': '5min',
                '15min': '15min',
                '1hour': '1hour',
                '2hour': '2hour'
            }
            
            actual_timeframe = timeframe_map.get(timeframe, timeframe)
            
            payload = {
                "symbol": symbol.upper(),
                "timeframe": actual_timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "use_cache": True,
                "validate": False
            }
            
            logger.debug(f"Fetching bars with payload: {payload}")
            
            response = self.session.post(
                f"{self.base_url}/bars",
                json=payload,
                timeout=30
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # The server returns data in a 'data' field
                if 'data' in data and data['data']:
                    df = pd.DataFrame(data['data'])
                    
                    # Convert timestamp to datetime index
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                    
                    # Ensure we have the required columns
                    required_cols = ['open', 'high', 'low', 'close']
                    if all(col in df.columns for col in required_cols):
                        logger.info(f"Successfully fetched {len(df)} bars for {symbol}")
                        return df
                    else:
                        logger.error(f"Missing required columns in response. Got: {df.columns.tolist()}")
                        return pd.DataFrame()
                else:
                    logger.warning(f"No data returned for {symbol} from {start_date} to {end_date}")
                    return pd.DataFrame()
            
            else:
                # Log error if not successful
                logger.error(f"Failed to fetch bars: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    logger.error(f"Error details: {error_detail}")
                except:
                    logger.error(f"Error response: {response.text[:200]}")
                    
                return pd.DataFrame()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching bars: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching bars: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        try:
            # First try the latest endpoint
            response = self.session.get(
                f"{self.base_url}/latest/{symbol}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get("price", 0))
            
            # If that doesn't work, try getting recent bars
            logger.info(f"Latest endpoint failed, trying recent bars for {symbol}")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            df = self.fetch_bars(symbol, start_date, end_date, '5min')
            if df is not None and not df.empty:
                return float(df.iloc[-1]['close'])
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate ATR from OHLC data"""
        try:
            if df is None or df.empty or len(df) < period + 1:
                return None
            
            # True Range calculation
            df_copy = df.copy()
            df_copy['high_low'] = df_copy['high'] - df_copy['low']
            df_copy['high_close'] = abs(df_copy['high'] - df_copy['close'].shift(1))
            df_copy['low_close'] = abs(df_copy['low'] - df_copy['close'].shift(1))
            
            df_copy['true_range'] = df_copy[['high_low', 'high_close', 'low_close']].max(axis=1)
            
            # Calculate ATR using exponential moving average
            df_copy['atr'] = df_copy['true_range'].ewm(span=period, adjust=False).mean()
            
            # Return the last ATR value
            atr_value = df_copy['atr'].iloc[-1]
            
            if pd.isna(atr_value):
                return None
                
            return float(atr_value)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return None
    
    def get_m15_candle(self, 
                       symbol: str, 
                       target_datetime: datetime) -> Optional[Dict[str, float]]:
        """Get M15 candle at specific datetime"""
        try:
            # Fetch data around target time
            start = (target_datetime - timedelta(hours=2))
            end = target_datetime
            
            # Adjust for same-day issue
            if start.date() == end.date():
                end = end + timedelta(days=1)
            
            df = self.fetch_bars(
                symbol,
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d'),
                '15min'
            )
            
            if df is not None and not df.empty:
                # Find nearest candle
                target_ts = pd.Timestamp(target_datetime)
                if df.index.tz is not None:
                    target_ts = target_ts.tz_localize(df.index.tz)
                    
                time_diff = abs(df.index - target_ts)
                nearest_idx = time_diff.argmin()
                
                if time_diff[nearest_idx] <= pd.Timedelta(minutes=15):
                    candle = df.iloc[nearest_idx]
                    return {
                        'datetime': df.index[nearest_idx],
                        'open': float(candle['open']),
                        'high': float(candle['high']),
                        'low': float(candle['low']),
                        'close': float(candle['close']),
                        'volume': int(candle.get('volume', 0))
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting M15 candle: {e}")
            return None