#!/usr/bin/env python3
"""
Polygon Bridge Diagnostic Test
Tests data fetching from 08-01-25 21:00:00 UTC to 08-05-25 12:15:00 UTC
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from data.polygon_bridge import PolygonBridge

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'polygon_diagnostic.log'))
    ]
)

logger = logging.getLogger(__name__)


class PolygonDiagnostic:
    """Diagnostic tool for Polygon Bridge issues"""
    
    def __init__(self):
        self.bridge = PolygonBridge()
        self.test_ticker = "PLTR"  # Using PLTR from your logs
        
        # Test date range from your request
        self.start_datetime = datetime(2025, 8, 1, 21, 0, 0)  # 08-01-25 21:00:00 UTC
        self.end_datetime = datetime(2025, 8, 5, 12, 15, 0)   # 08-05-25 12:15:00 UTC
        
    def run_full_diagnostic(self):
        """Run complete diagnostic suite"""
        print("=" * 80)
        print("POLYGON BRIDGE DIAGNOSTIC TEST")
        print("=" * 80)
        print(f"Ticker: {self.test_ticker}")
        print(f"Start: {self.start_datetime} UTC")
        print(f"End: {self.end_datetime} UTC")
        print(f"Duration: {self.end_datetime - self.start_datetime}")
        print("=" * 80)
        
        # Test 1: Connection
        self.test_connection()
        
        # Test 2: Raw API fetch with different timeframes
        self.test_raw_api_calls()
        
        # Test 3: Bridge method calls
        self.test_bridge_methods()
        
        # Test 4: Date range calculations
        self.test_date_calculations()
        
        # Test 5: Specific candle lookups
        self.test_specific_candles()
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC COMPLETE - Check logs for detailed analysis")
        print("=" * 80)
    
    def test_connection(self):
        """Test basic connection to Polygon REST API"""
        print("\n--- TEST 1: CONNECTION ---")
        
        try:
            connected, message = self.bridge.test_connection()
            print(f"Connection Status: {'✓ SUCCESS' if connected else '✗ FAILED'}")
            print(f"Message: {message}")
            
            if not connected:
                print("❌ Cannot proceed with tests - connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
            
        return True
    
    def test_raw_api_calls(self):
        """Test raw API calls with different timeframes"""
        print("\n--- TEST 2: RAW API CALLS ---")
        
        # Test different timeframes
        timeframes = ['5min', '15min', '1day']
        
        for timeframe in timeframes:
            print(f"\n🔍 Testing {timeframe} data...")
            
            try:
                # Use string dates for API call
                start_date = self.start_datetime.strftime('%Y-%m-%d')
                end_date = self.end_datetime.strftime('%Y-%m-%d')
                
                print(f"  API Call: {self.test_ticker}, {start_date} to {end_date}, {timeframe}")
                
                df = self.bridge.fetch_bars(
                    symbol=self.test_ticker,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe
                )
                
                if df is not None and not df.empty:
                    print(f"  ✓ SUCCESS: {len(df)} bars fetched")
                    print(f"  📊 Data range: {df.index[0]} to {df.index[-1]}")
                    
                    # Show sample data
                    print(f"  📈 Sample data (first 3 bars):")
                    for i in range(min(3, len(df))):
                        bar = df.iloc[i]
                        timestamp = df.index[i]
                        print(f"    {timestamp}: O={bar['open']:.2f} H={bar['high']:.2f} L={bar['low']:.2f} C={bar['close']:.2f}")
                        
                else:
                    print(f"  ❌ FAILED: No data returned")
                    
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                logger.error(f"Raw API call failed for {timeframe}: {e}", exc_info=True)
    
    def test_bridge_methods(self):
        """Test bridge method calls"""
        print("\n--- TEST 3: BRIDGE METHODS ---")
        
        # Test get_historical_bars method (used by analysis)
        print("\n🔍 Testing get_historical_bars method...")
        
        try:
            start_date = self.start_datetime.date()
            end_date = self.end_datetime.date()
            
            df = self.bridge.get_historical_bars(
                ticker=self.test_ticker,
                start_date=start_date,
                end_date=end_date,
                timeframe='5min'
            )
            
            if not df.empty:
                print(f"  ✓ SUCCESS: {len(df)} bars from get_historical_bars")
                print(f"  📊 Data range: {df.index[0]} to {df.index[-1]}")
                
                # Check timezone info
                tz_info = df.index.tz
                print(f"  🕒 Timezone: {tz_info}")
                
            else:
                print(f"  ❌ FAILED: No data from get_historical_bars")
                
        except Exception as e:
            print(f"  ❌ ERROR in get_historical_bars: {str(e)}")
            logger.error(f"get_historical_bars failed: {e}", exc_info=True)
        
        # Test get_session_data method
        print("\n🔍 Testing get_session_data method...")
        
        try:
            session_data = self.bridge.get_session_data(
                symbol=self.test_ticker,
                session_datetime=self.start_datetime
            )
            
            print(f"  📊 Session data keys: {list(session_data.keys())}")
            
            for key, value in session_data.items():
                if value is not None and key != 'error':
                    if isinstance(value, Decimal):
                        print(f"    {key}: {float(value):.4f}")
                    else:
                        print(f"    {key}: {value}")
                        
            if session_data.get('error'):
                print(f"  ❌ Session data error: {session_data['error']}")
                
        except Exception as e:
            print(f"  ❌ ERROR in get_session_data: {str(e)}")
            logger.error(f"get_session_data failed: {e}", exc_info=True)
    
    def test_date_calculations(self):
        """Test date range calculations that might be causing issues"""
        print("\n--- TEST 4: DATE CALCULATIONS ---")
        
        print("🔍 Testing date range logic...")
        
        # Test the date calculations that might be causing issues
        test_cases = [
            # Case 1: Same day start and end
            (datetime(2025, 8, 5, 10, 0, 0), datetime(2025, 8, 5, 15, 0, 0)),
            # Case 2: Multi-day range
            (datetime(2025, 8, 4, 21, 0, 0), datetime(2025, 8, 5, 12, 0, 0)),
            # Case 3: Your original range
            (self.start_datetime, self.end_datetime),
        ]
        
        for i, (start_dt, end_dt) in enumerate(test_cases, 1):
            print(f"\n  Test Case {i}:")
            print(f"    Start: {start_dt}")
            print(f"    End: {end_dt}")
            
            # Test different date calculation approaches
            approaches = [
                ("Direct date strings", 
                 start_dt.strftime('%Y-%m-%d'), 
                 end_dt.strftime('%Y-%m-%d')),
                ("Date objects to strings", 
                 start_dt.date().strftime('%Y-%m-%d'), 
                 end_dt.date().strftime('%Y-%m-%d')),
                ("Add buffer for intraday", 
                 (start_dt.date() - timedelta(days=1)).strftime('%Y-%m-%d'), 
                 end_dt.date().strftime('%Y-%m-%d')),
            ]
            
            for name, start_str, end_str in approaches:
                print(f"    {name}: {start_str} to {end_str}")
                
                # Check for same date issue
                if start_str == end_str:
                    print(f"      ⚠️  WARNING: Same start and end date - this causes API errors!")
                else:
                    print(f"      ✓ Different dates - should work")
    
    def test_specific_candles(self):
        """Test specific candle lookups that were failing"""
        print("\n--- TEST 5: SPECIFIC CANDLE LOOKUPS ---")
        
        # Test cases from your log that were failing
        failing_cases = [
            datetime(2025, 8, 5, 11, 0, 0),    # Zone 1 from logs
            datetime(2025, 8, 4, 21, 30, 0),   # Zone 2 from logs  
            datetime(2025, 8, 4, 19, 15, 0),   # Zone 3 from logs
            datetime(2025, 8, 5, 12, 15, 0),   # Zone 4 from logs
            datetime(2025, 8, 4, 15, 30, 0),   # Zone 5 from logs
            datetime(2025, 8, 1, 22, 15, 0),   # Zone 6 from logs
        ]
        
        for i, target_dt in enumerate(failing_cases, 1):
            print(f"\n🎯 Testing specific candle lookup {i}: {target_dt}")
            
            try:
                # Test get_candle_at_datetime method
                candle = self.bridge.get_candle_at_datetime(
                    symbol=self.test_ticker,
                    target_datetime=target_dt,
                    timeframe='15min'
                )
                
                if candle:
                    print(f"    ✓ SUCCESS: Found candle data")
                    print(f"      Time: {candle['datetime']}")
                    print(f"      OHLC: O={candle['open']} H={candle['high']} L={candle['low']} C={candle['close']}")
                else:
                    print(f"    ❌ FAILED: No candle data found")
                    
                    # Try to understand why by fetching broader range
                    print(f"    🔍 Investigating with broader date range...")
                    
                    # Get a 2-day window around the target
                    buffer_start = (target_dt - timedelta(hours=4)).strftime('%Y-%m-%d')
                    buffer_end = target_dt.strftime('%Y-%m-%d')
                    
                    if buffer_start == buffer_end:
                        # Same day issue - extend the range
                        buffer_end = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                        print(f"      📅 Adjusted range: {buffer_start} to {buffer_end}")
                    
                    df = self.bridge.fetch_bars(
                        symbol=self.test_ticker,
                        start_date=buffer_start,
                        end_date=buffer_end,
                        timeframe='15min'
                    )
                    
                    if df is not None and not df.empty:
                        print(f"      📊 Found {len(df)} bars in broader range")
                        print(f"      📈 Range: {df.index[0]} to {df.index[-1]}")
                        
                        # Find nearest candle
                        target_ts = pd.Timestamp(target_dt)
                        if df.index.tz is not None and target_ts.tz is None:
                            target_ts = target_ts.tz_localize('UTC')
                            
                        time_diffs = abs(df.index - target_ts)
                        nearest_idx = time_diffs.argmin()
                        nearest_time = df.index[nearest_idx]
                        delta_minutes = abs(nearest_time - target_ts).total_seconds() / 60
                        
                        print(f"      🎯 Nearest candle: {nearest_time} (Δ {delta_minutes:.1f} min)")
                        
                    else:
                        print(f"      ❌ No data even in broader range")
                        
            except Exception as e:
                print(f"    ❌ ERROR: {str(e)}")
                logger.error(f"Specific candle lookup failed for {target_dt}: {e}", exc_info=True)


def main():
    """Run the diagnostic"""
    try:
        diagnostic = PolygonDiagnostic()
        diagnostic.run_full_diagnostic()
        
    except Exception as e:
        print(f"❌ DIAGNOSTIC FAILED: {e}")
        logger.error(f"Diagnostic failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()