"""
Polygon Data Fetcher
Retrieves historical price data from local Polygon server
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
from . import config

class DataFetcher:
    def __init__(self, server_url: str = config.POLYGON_SERVER_URL):
        """Initialize connection to local Polygon server"""
        self.server_url = server_url
        self.api_key = config.POLYGON_API_KEY
        
    def fetch_bars(self, 
                   ticker: str, 
                   end_date: datetime,
                   lookback_days: int = 30,
                   timeframe: str = "minute",
                   multiplier: int = 15) -> pd.DataFrame:
        """
        Fetch historical bars from local Polygon server
        
        Args:
            ticker: Stock symbol
            end_date: End date for data retrieval (UTC)
            lookback_days: Number of days to look back
            timeframe: Aggregation timeframe
            multiplier: Aggregation multiplier (15 for 15-minute bars)
            
        Returns:
            DataFrame with OHLCV data in UTC
        """
        start_date = end_date - timedelta(days=lookback_days)
        
        # Format dates for API (YYYY-MM-DD format)
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Use your server's actual endpoint
        endpoint = f"{self.server_url}/api/v1/bars"
        
        # Create timeframe string (e.g., "15min" or "15m")
        # Try different formats your server might accept
        timeframe_str = f"{multiplier}min"  # Try "15min" format first
        
        # Request body based on BarsRequest schema
        request_body = {
            "symbol": ticker,  # Note: "symbol" not "ticker"
            "timeframe": timeframe_str,
            "start_date": from_date,
            "end_date": to_date,
            "limit": 50000,
            "use_cache": True,
            "validate": True
        }
        
        # Headers for JSON request
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key to headers if it exists
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            # Or try as a header directly
            headers["X-API-Key"] = self.api_key
        
        try:
            print(f"  Requesting: {endpoint}")
            print(f"  Request body: symbol={ticker}, timeframe={timeframe_str}, dates={from_date} to {to_date}")
            
            # Make POST request to server
            response = requests.post(
                endpoint, 
                json=request_body,
                headers=headers,
                timeout=30
            )
            
            # Check for errors
            if response.status_code != 200:
                print(f"  Server response: {response.status_code}")
                print(f"  Response content: {response.text[:500]}")
                
                # If 15min doesn't work, try other formats
                if response.status_code == 400 and "timeframe" in response.text.lower():
                    print(f"  Trying alternative timeframe format...")
                    
                    # Try different timeframe formats
                    for tf_format in [f"{multiplier}m", f"{multiplier}minute", f"{multiplier}minutes"]:
                        request_body["timeframe"] = tf_format
                        response = requests.post(endpoint, json=request_body, headers=headers, timeout=30)
                        if response.status_code == 200:
                            break
                        
            response.raise_for_status()
            
            data = response.json()
            
            # Check response status
            if 'status' in data and data['status'] != 'OK':
                error_msg = data.get('error', data.get('message', 'Unknown error'))
                raise ValueError(f"API Error: {error_msg}")
            
            # Get results - handle different possible response formats
            bars_list = None
            
            if 'results' in data:
                bars_list = data['results']
            elif 'bars' in data:
                bars_list = data['bars']
            elif 'data' in data:
                bars_list = data['data']
            elif isinstance(data, list):
                bars_list = data
            else:
                raise ValueError(f"Unexpected response format. Response keys: {list(data.keys())}")
            
            if not bars_list:
                raise ValueError(f"No data returned for {ticker} between {from_date} and {to_date}")
            
            print(f"  Received {len(bars_list)} bars from server")
            
            # Convert to DataFrame
            bars_data = []
            for bar in bars_list:
                # Handle different timestamp formats
                if 't' in bar:
                    timestamp = pd.to_datetime(bar['t'], unit='ms', utc=True)
                elif 'timestamp' in bar:
                    if isinstance(bar['timestamp'], (int, float)):
                        timestamp = pd.to_datetime(bar['timestamp'], unit='ms', utc=True)
                    else:
                        timestamp = pd.to_datetime(bar['timestamp'], utc=True)
                elif 'time' in bar:
                    timestamp = pd.to_datetime(bar['time'], utc=True)
                elif 'datetime' in bar:
                    timestamp = pd.to_datetime(bar['datetime'], utc=True)
                else:
                    raise ValueError(f"No timestamp field found in bar data: {bar.keys()}")
                
                # Handle different field names for OHLCV
                bars_data.append({
                    'datetime': timestamp,
                    'open': bar.get('o', bar.get('open')),
                    'high': bar.get('h', bar.get('high')),
                    'low': bar.get('l', bar.get('low')),
                    'close': bar.get('c', bar.get('close')),
                    'volume': bar.get('v', bar.get('volume', bar.get('vol', 0)))
                })
            
            df = pd.DataFrame(bars_data)
            
            # Keep datetime in UTC (remove timezone info for consistency but maintain UTC values)
            df['datetime'] = df['datetime'].dt.tz_localize(None)
            
            # Filter to only include bars within our date range (in case server returns extra)
            df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
            
            print(f"SUCCESS: Fetched {len(df)} bars")
            
            return df.sort_values('datetime').reset_index(drop=True)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 405:
                # Try GET request as fallback
                print(f"  POST failed, trying GET request...")
                return self._fetch_bars_get(ticker, start_date, end_date, multiplier, timeframe_str)
            elif e.response.status_code == 404:
                raise Exception(
                    f"Endpoint not found at {endpoint}.\n"
                    f"Please check if the server is running and the endpoint exists."
                )
            else:
                raise Exception(f"HTTP Error from server: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Polygon server at {self.server_url}: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing expected field in response: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing data: {str(e)}")
    
    def _fetch_bars_get(self, ticker, start_date, end_date, multiplier, timeframe_str):
        """Fallback GET request method"""
        endpoint = f"{self.server_url}/api/v1/bars"
        
        params = {
            'symbol': ticker,  # Try 'symbol' instead of 'ticker'
            'timeframe': timeframe_str,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'limit': 50000,
            'use_cache': 'true',
            'validate': 'true'
        }
        
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Process the response similar to above
        if 'results' in data:
            bars_list = data['results']
        elif 'bars' in data:
            bars_list = data['bars']
        elif 'data' in data:
            bars_list = data['data']
        elif isinstance(data, list):
            bars_list = data
        else:
            raise ValueError(f"Unexpected response format")
        
        bars_data = []
        for bar in bars_list:
            if 't' in bar:
                timestamp = pd.to_datetime(bar['t'], unit='ms', utc=True)
            elif 'timestamp' in bar:
                timestamp = pd.to_datetime(bar['timestamp'], utc=True)
            else:
                timestamp = pd.to_datetime(bar.get('time', bar.get('datetime')), utc=True)
            
            bars_data.append({
                'datetime': timestamp,
                'open': bar.get('o', bar.get('open')),
                'high': bar.get('h', bar.get('high')),
                'low': bar.get('l', bar.get('low')),
                'close': bar.get('c', bar.get('close')),
                'volume': bar.get('v', bar.get('volume', 0))
            })
        
        df = pd.DataFrame(bars_data)
        df['datetime'] = df['datetime'].dt.tz_localize(None)
        
        return df.sort_values('datetime').reset_index(drop=True)
    
    def test_connection(self) -> bool:
        """Test connection to local Polygon server"""
        try:
            # Try the health endpoint first (we know this exists from diagnostics)
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                return True
                
            # Try the status endpoint
            response = requests.get(f"{self.server_url}/status", timeout=5)
            if response.status_code == 200:
                return True
                
            # Try root endpoint
            response = requests.get(f"{self.server_url}/", timeout=5)
            if response.status_code == 200:
                return True
                
            return False
            
        except Exception as e:
            print(f"  Debug: Connection test failed with error: {str(e)}")
            return False