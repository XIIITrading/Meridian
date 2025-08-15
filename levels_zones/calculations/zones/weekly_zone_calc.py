"""
Weekly Zone Calculator
Location: levels_zones/calculations/zones/weekly_zone_calc.py
Transforms weekly levels (WL1-WL4) into zones using 1-hour ATR bands (30min above/below)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
import pandas as pd
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add src directory to path
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set up logging
logger = logging.getLogger(__name__)


class WeeklyZoneCalculator:
    """Calculator for transforming weekly levels into zones using 1-hour ATR"""
    
    def __init__(self):
        """Initialize the calculator with PolygonBridge"""
        try:
            from data.polygon_bridge import PolygonBridge
            self.bridge = PolygonBridge()
            logger.info("WeeklyZoneCalculator initialized with PolygonBridge")
        except ImportError as e:
            logger.error(f"Failed to import PolygonBridge: {e}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to Polygon"""
        try:
            return self.bridge.test_connection()
        except Exception as e:
            return False, str(e)
    
    def calculate_1hour_atr(self, ticker: str, analysis_date: datetime, period: int = 14) -> Optional[Decimal]:
        """
        Calculate 1-hour ATR for the given ticker and date
        Tries native 1-hour bars first, falls back to resampling from shorter timeframes
        
        Args:
            ticker: Stock ticker symbol
            analysis_date: Date for ATR calculation
            period: ATR period (default 14)
            
        Returns:
            1-hour ATR value as Decimal or None if calculation fails
        """
        try:
            # Calculate date range
            end_date = analysis_date.date()
            # Need enough data for ATR calculation
            # With ~7 1-hour bars per trading day, need about 3-4 days for 14 periods
            # Get extra to be safe
            start_date = end_date - timedelta(days=10)
            
            logger.info(f"Attempting to fetch 1-hour bars for {ticker}")
            
            # Try native 1-hour bars first (if Polygon supports it)
            df_1hour = None
            for timeframe in ['1hour', '60min', '1h']:  # Try different formats
                try:
                    df_1hour = self.bridge.get_historical_bars(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        timeframe=timeframe
                    )
                    if df_1hour is not None and not df_1hour.empty:
                        logger.info(f"Successfully fetched 1-hour bars using timeframe: {timeframe}")
                        break
                except Exception as e:
                    logger.debug(f"Timeframe {timeframe} not available: {e}")
                    continue
            
            # If native 1-hour bars are available and have enough data
            if df_1hour is not None and not df_1hour.empty:
                # Strip timezone info if present
                if df_1hour.index.tz is not None:
                    df_1hour.index = df_1hour.index.tz_localize(None)
                
                if len(df_1hour) >= period + 1:
                    logger.info(f"Using native 1-hour bars: {len(df_1hour)} bars available")
                    return self._calculate_atr_from_data(df_1hour, period)
                else:
                    logger.warning(f"Insufficient native 1-hour bars: {len(df_1hour)}, need {period + 1}")
            
            # Fallback: Try 15-minute bars and resample
            logger.info("Falling back to 15-minute bars for 1-hour ATR calculation")
            
            # Extend date range for resampling to ensure enough data
            extended_start = end_date - timedelta(days=30)
            
            df_15min = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=extended_start,
                end_date=end_date,
                timeframe='15min'
            )
            
            if df_15min is not None and not df_15min.empty:
                # Strip timezone info
                if df_15min.index.tz is not None:
                    df_15min.index = df_15min.index.tz_localize(None)
                
                # Resample to 1-hour (4 x 15min = 60min)
                df_1hour_resampled = df_15min.resample('1H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if len(df_1hour_resampled) >= period + 1:
                    logger.info(f"Using resampled 1-hour bars from 15-min: {len(df_1hour_resampled)} bars")
                    return self._calculate_atr_from_data(df_1hour_resampled, period)
                else:
                    logger.warning(f"Still insufficient data after 15-min resampling: {len(df_1hour_resampled)}")
            
            # Final fallback: Use 5-minute bars with extended range
            logger.info("Final fallback to 5-minute bars for 1-hour ATR calculation")
            
            df_5min = self.bridge.get_historical_bars(
                ticker=ticker,
                start_date=extended_start,
                end_date=end_date,
                timeframe='5min'
            )
            
            if df_5min is not None and not df_5min.empty:
                # Strip timezone info
                if df_5min.index.tz is not None:
                    df_5min.index = df_5min.index.tz_localize(None)
                
                # Resample to 1-hour (12 x 5min = 60min)
                df_1hour_final = df_5min.resample('1H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if len(df_1hour_final) >= period + 1:
                    logger.info(f"Using resampled 1-hour bars from 5-min: {len(df_1hour_final)} bars")
                    return self._calculate_atr_from_data(df_1hour_final, period)
                elif len(df_1hour_final) > 0:
                    # Use what we have with reduced period
                    reduced_period = min(period, len(df_1hour_final) - 1)
                    if reduced_period > 0:
                        logger.warning(f"Using reduced ATR period of {reduced_period} due to limited data")
                        return self._calculate_atr_from_data(df_1hour_final, reduced_period)
            
            logger.error(f"Unable to calculate 1-hour ATR for {ticker} - insufficient data")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating 1-hour ATR for {ticker}: {e}")
            return None
    
    def _calculate_atr_from_data(self, data: pd.DataFrame, period: int) -> Optional[Decimal]:
        """
        Calculate ATR from OHLC data
        
        Args:
            data: DataFrame with OHLC columns
            period: ATR period
            
        Returns:
            ATR value as Decimal or None
        """
        try:
            if len(data) < period + 1:
                logger.warning(f"Insufficient data for ATR calculation: {len(data)} bars, need {period + 1}")
                return None
            
            # Calculate True Range
            high_low = data['high'] - data['low']
            high_close = abs(data['high'] - data['close'].shift(1))
            low_close = abs(data['low'] - data['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Calculate ATR using exponential moving average
            atr = true_range.ewm(span=period, adjust=False).mean()
            
            # Get the latest ATR value
            latest_atr = atr.iloc[-1]
            
            if pd.isna(latest_atr):
                logger.warning("ATR calculation resulted in NaN")
                return None
            
            atr_decimal = Decimal(str(round(latest_atr, 2)))
            logger.info(f"Calculated 1-hour ATR: {atr_decimal}")
            
            return atr_decimal
            
        except Exception as e:
            logger.error(f"Error in ATR calculation: {e}")
            return None
    
    def create_weekly_zones(self, 
                          weekly_levels: List[Decimal], 
                          atr_1hour: Decimal,
                          multiplier: Decimal = Decimal("0.5")) -> List[Dict[str, Decimal]]:
        """
        Create zones from weekly levels using 1-hour ATR
        Uses 0.5 multiplier by default to create 30min above/below zones
        
        Args:
            weekly_levels: List of weekly price levels (WL1-WL4)
            atr_1hour: 1-hour ATR value
            multiplier: ATR multiplier (default 0.5 for 30min zones above/below)
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        for i, level in enumerate(weekly_levels, 1):
            if level and level > 0:
                # Calculate zone boundaries - 30 minutes above and below
                atr_offset = atr_1hour * multiplier
                zone_high = level + atr_offset
                zone_low = level - atr_offset
                
                zone = {
                    'name': f'WL{i}',
                    'level': level,
                    'high': zone_high,
                    'low': zone_low,
                    'zone_size': zone_high - zone_low,
                    'atr_used': atr_1hour,
                    'atr_multiplier': multiplier,
                    'center': level  # Weekly level is the center of the zone
                }
                zones.append(zone)
                
                logger.debug(f"Created zone WL{i}: {zone_low:.2f} - {zone_high:.2f} (center: {level:.2f}, total size: ~1hr ATR)")
        
        return zones
    
    def calculate_zones_from_session(self, 
                                    session_data: Dict,
                                    ticker: str,
                                    analysis_datetime: datetime) -> Optional[Dict[str, any]]:
        """
        Calculate weekly zones from a trading session's weekly data
        
        Args:
            session_data: Trading session data dictionary
            ticker: Stock ticker symbol
            analysis_datetime: DateTime for analysis
            
        Returns:
            Dictionary with zone calculations or None if failed
        """
        try:
            # Extract weekly levels from session data
            weekly_levels = []
            
            if 'weekly' in session_data and 'price_levels' in session_data['weekly']:
                weekly_levels = [Decimal(str(level)) for level in session_data['weekly']['price_levels'] 
                               if level and float(level) > 0]
            else:
                logger.warning("No weekly price levels found in session data")
                return None
            
            if not weekly_levels:
                logger.warning("Weekly price levels are empty or zero")
                return None
            
            logger.info(f"Found {len(weekly_levels)} weekly levels: {[float(l) for l in weekly_levels]}")
            
            # Check if we already have 1-hour ATR in metrics
            atr_1hour = None
            if 'metrics' in session_data and 'atr_1hour' in session_data['metrics']:
                try:
                    atr_1hour = Decimal(str(session_data['metrics']['atr_1hour']))
                    logger.info(f"Using existing 1-hour ATR from metrics: {atr_1hour}")
                except (ValueError, TypeError):
                    logger.warning("Invalid 1-hour ATR in metrics, will recalculate")
            
            # Calculate 1-hour ATR if not available
            if not atr_1hour or atr_1hour <= 0:
                atr_1hour = self.calculate_1hour_atr(ticker, analysis_datetime)
                
                if not atr_1hour:
                    logger.error("Failed to calculate 1-hour ATR")
                    # Use a fallback: daily ATR * 0.15 as approximation
                    if 'metrics' in session_data and 'daily_atr' in session_data['metrics']:
                        daily_atr = Decimal(str(session_data['metrics']['daily_atr']))
                        atr_1hour = daily_atr * Decimal("0.15")
                        logger.warning(f"Using fallback: 15% of daily ATR = {atr_1hour}")
                    else:
                        return None
            
            # Create zones with 30min above/below (total ~1hr ATR zone)
            zones = self.create_weekly_zones(weekly_levels, atr_1hour)
            
            # Get current price for reference
            current_price = Decimal("0")
            if 'pre_market_price' in session_data:
                current_price = Decimal(str(session_data['pre_market_price']))
            elif 'metrics' in session_data and 'current_price' in session_data['metrics']:
                current_price = Decimal(str(session_data['metrics']['current_price']))
            
            # Classify zones relative to current price
            resistance_zones = []
            support_zones = []
            
            for zone in zones:
                if current_price > 0:
                    if zone['center'] > current_price:
                        zone['type'] = 'resistance'
                        zone['distance'] = zone['center'] - current_price
                        zone['distance_pct'] = (zone['distance'] / current_price * 100)
                        resistance_zones.append(zone)
                    else:
                        zone['type'] = 'support'
                        zone['distance'] = current_price - zone['center']
                        zone['distance_pct'] = (zone['distance'] / current_price * 100)
                        support_zones.append(zone)
            
            # Sort by distance from current price
            resistance_zones.sort(key=lambda x: x['distance'])
            support_zones.sort(key=lambda x: x['distance'])
            
            result = {
                'ticker': ticker,
                'analysis_datetime': analysis_datetime,
                'atr_1hour': atr_1hour,
                'zone_width': 'approx_1hour_atr',
                'current_price': current_price,
                'all_zones': zones,
                'resistance_zones': resistance_zones,
                'support_zones': support_zones,
                'zone_count': len(zones)
            }
            
            logger.info(f"Weekly zone calculation complete: {len(zones)} zones created with 1-hour ATR of {atr_1hour:.2f} (30min above/below)")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating weekly zones: {e}")
            return None
    
    def format_zones_for_display(self, zone_result: Dict) -> str:
        """
        Format weekly zones for display in UI
        
        Args:
            zone_result: Result from calculate_zones_from_session
            
        Returns:
            Formatted string for display
        """
        if not zone_result:
            return "No weekly zones calculated"
        
        output = []
        output.append(f"Weekly Zones Analysis for {zone_result['ticker']}")
        output.append(f"1-Hour ATR: ${zone_result['atr_1hour']:.2f}")
        output.append(f"Zone Width: ~1 hour ATR (30min above + 30min below)")
        
        if zone_result['current_price'] > 0:
            output.append(f"Current Price: ${zone_result['current_price']:.2f}")
        
        output.append(f"\nTotal Zones: {zone_result['zone_count']}")
        output.append("-" * 50)
        
        # Display resistance zones
        if zone_result['resistance_zones']:
            output.append("\n📈 RESISTANCE ZONES (above current price):")
            for zone in zone_result['resistance_zones']:
                output.append(f"\n  {zone['name']} Zone:")
                output.append(f"    Level: ${zone['level']:.2f}")
                output.append(f"    Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"    Size: ${zone['zone_size']:.2f} (~1hr ATR)")
                if 'distance_pct' in zone:
                    output.append(f"    Distance: {zone['distance_pct']:.2f}% above")
        
        # Display support zones
        if zone_result['support_zones']:
            output.append("\n📉 SUPPORT ZONES (below current price):")
            for zone in zone_result['support_zones']:
                output.append(f"\n  {zone['name']} Zone:")
                output.append(f"    Level: ${zone['level']:.2f}")
                output.append(f"    Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"    Size: ${zone['zone_size']:.2f} (~1hr ATR)")
                if 'distance_pct' in zone:
                    output.append(f"    Distance: {zone['distance_pct']:.2f}% below")
        
        return "\n".join(output)
    
    def get_zones_for_confluence(self, zone_result: Dict) -> List[Dict]:
        """
        Prepare weekly zones for confluence engine integration
        
        Args:
            zone_result: Result from calculate_zones_from_session
            
        Returns:
            List of zones formatted for confluence checking
        """
        if not zone_result or 'all_zones' not in zone_result:
            return []
        
        confluence_zones = []
        
        for zone in zone_result['all_zones']:
            confluence_zone = {
                'name': f"Weekly_{zone['name']}",
                'type': 'weekly_zone',
                'level': float(zone['level']),
                'high': float(zone['high']),
                'low': float(zone['low']),
                'zone_size': float(zone['zone_size']),
                'source': 'weekly_levels',
                'timeframe': 'weekly',
                'atr_based': True,
                'atr_value': float(zone['atr_used']),
                'atr_type': '1hour',
                'zone_width': '30min_above_below'
            }
            
            # Add position relative to price if available
            if zone.get('type'):
                confluence_zone['position'] = zone['type']
            if zone.get('distance_pct'):
                confluence_zone['distance_pct'] = float(zone['distance_pct'])
            
            confluence_zones.append(confluence_zone)
        
        return confluence_zones


# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Set up logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example session data with weekly levels
    example_session = {
        'ticker': 'AAPL',
        'weekly': {
            'price_levels': [175.50, 178.25, 172.80, 180.00]  # WL1-WL4
        },
        'pre_market_price': 176.00,
        'metrics': {
            'daily_atr': 2.50  # Can be used as fallback
        }
    }
    
    print("Initializing Weekly Zone Calculator...")
    
    # Initialize calculator
    calculator = WeeklyZoneCalculator()
    
    # Test connection
    connected, msg = calculator.test_connection()
    print(f"Connection test: {msg}")
    
    if connected:
        print("\nCalculating weekly zones with 1-hour ATR (30min above/below)...")
        
        # Calculate zones
        result = calculator.calculate_zones_from_session(
            example_session,
            'AAPL',
            datetime.now()
        )
        
        if result:
            # Display formatted output
            print("\n" + calculator.format_zones_for_display(result))
            
            # Get zones for confluence
            confluence_zones = calculator.get_zones_for_confluence(result)
            print(f"\n\nPrepared {len(confluence_zones)} zones for confluence engine")
            
            # Show confluence zone structure
            if confluence_zones:
                print("\nSample confluence zone structure:")
                import json
                print(json.dumps(confluence_zones[0], indent=2, default=str))
        else:
            print("Failed to calculate weekly zones")
    else:
        print("Cannot proceed without connection to Polygon")