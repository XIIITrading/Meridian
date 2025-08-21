"""
Daily Zone Calculator
Location: levels_zones/calculations/zones/daily_zone_calc.py
Transforms daily levels (DL1-DL6) into zones using 5-minute ATR bands (5min above/below)
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


class DailyZoneCalculator:
    """Calculator for transforming daily levels into zones using 5-minute ATR bands"""
    
    def __init__(self):
        """Initialize the calculator with PolygonBridge"""
        try:
            from data.polygon_bridge import PolygonBridge
            self.bridge = PolygonBridge()
            logger.info("DailyZoneCalculator initialized with PolygonBridge")
        except ImportError as e:
            logger.error(f"Failed to import PolygonBridge: {e}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to Polygon"""
        try:
            return self.bridge.test_connection()
        except Exception as e:
            return False, str(e)
    
    def calculate_5min_atr(self, ticker: str, analysis_date: datetime, period: int = 14) -> Optional[Decimal]:
        """
        Calculate 5-minute ATR for the given ticker and date
        
        Args:
            ticker: Stock ticker symbol
            analysis_date: Date for ATR calculation
            period: ATR period (default 14)
            
        Returns:
            5-minute ATR value as Decimal or None if calculation fails
        """
        try:
            # Calculate date range
            end_date = analysis_date.date()
            # For 5-minute bars, we have ~78 bars per trading day
            # Need about 1-2 days for 14 periods
            start_date = end_date - timedelta(days=3)
            
            logger.info(f"Fetching 5-minute bars for {ticker}")
            
            # Try native 5-minute bars
            df_5min = None
            for timeframe in ['5min', '5', '5m']:  # Try different formats
                try:
                    df_5min = self.bridge.get_historical_bars(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        timeframe=timeframe
                    )
                    if df_5min is not None and not df_5min.empty:
                        logger.info(f"Successfully fetched 5-minute bars using timeframe: {timeframe}")
                        break
                except Exception as e:
                    logger.debug(f"Timeframe {timeframe} not available: {e}")
                    continue
            
            # If native 5-minute bars are available and have enough data
            if df_5min is not None and not df_5min.empty:
                # Strip timezone info if present
                if df_5min.index.tz is not None:
                    df_5min.index = df_5min.index.tz_localize(None)
                
                if len(df_5min) >= period + 1:
                    logger.info(f"Using native 5-minute bars: {len(df_5min)} bars available")
                    return self._calculate_atr_from_data(df_5min, period)
                else:
                    logger.warning(f"Insufficient 5-minute bars: {len(df_5min)}, need {period + 1}")
                    # Try extending the date range
                    extended_start = end_date - timedelta(days=10)
                    df_5min_extended = self.bridge.get_historical_bars(
                        ticker=ticker,
                        start_date=extended_start,
                        end_date=end_date,
                        timeframe='5min'
                    )
                    if df_5min_extended is not None and not df_5min_extended.empty:
                        if df_5min_extended.index.tz is not None:
                            df_5min_extended.index = df_5min_extended.index.tz_localize(None)
                        if len(df_5min_extended) >= period + 1:
                            logger.info(f"Using extended 5-minute bars: {len(df_5min_extended)} bars")
                            return self._calculate_atr_from_data(df_5min_extended, period)
                        elif len(df_5min_extended) > 0:
                            # Use what we have with reduced period
                            reduced_period = min(period, len(df_5min_extended) - 1)
                            if reduced_period > 0:
                                logger.warning(f"Using reduced ATR period of {reduced_period}")
                                return self._calculate_atr_from_data(df_5min_extended, reduced_period)
            
            logger.error(f"Unable to calculate 5-minute ATR for {ticker} - insufficient data")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating 5-minute ATR for {ticker}: {e}")
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
            logger.info(f"Calculated 5-minute ATR: {atr_decimal}")
            
            return atr_decimal
            
        except Exception as e:
            logger.error(f"Error in ATR calculation: {e}")
            return None
    
    def create_daily_zones(self, 
                          daily_levels: List[Decimal], 
                          atr_5min: Decimal,
                          multiplier: Decimal = Decimal("1.0")) -> List[Dict[str, Decimal]]:
        """
        Create zones from daily levels using 5-minute ATR
        Creates zones with 5min ATR above and below (10min total zone)
        
        Args:
            daily_levels: List of daily price levels (DL1-DL6)
            atr_5min: 5-minute ATR value
            multiplier: ATR multiplier (default 1.0 for 5min above/below)
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        for i, level in enumerate(daily_levels, 1):
            if level and level > 0:
                # Calculate zone boundaries - 5min ATR above and below
                atr_offset = atr_5min * multiplier
                zone_high = level + atr_offset
                zone_low = level - atr_offset
                
                zone = {
                    'name': f'DL{i}',  # DL1 through DL6
                    'level': level,
                    'high': zone_high,
                    'low': zone_low,
                    'zone_size': zone_high - zone_low,
                    'atr_used': atr_5min,
                    'atr_multiplier': multiplier,
                    'center': level  # Daily level is the center of the zone
                }
                zones.append(zone)
                
                logger.debug(f"Created zone DL{i}: {zone_low:.2f} - {zone_high:.2f} (center: {level:.2f}, 5min above/below)")
        
        return zones
    
    def calculate_zones_from_session(self, 
                                    session_data: Dict,
                                    ticker: str,
                                    analysis_datetime: datetime) -> Optional[Dict[str, any]]:
        """
        Calculate daily zones from a trading session's daily data
        
        Args:
            session_data: Trading session data dictionary
            ticker: Stock ticker symbol
            analysis_datetime: DateTime for analysis
            
        Returns:
            Dictionary with zone calculations or None if failed
        """
        try:
            # Extract daily levels from session data (6 levels)
            daily_levels = []
            
            if 'daily' in session_data and 'price_levels' in session_data['daily']:
                daily_levels = [Decimal(str(level)) for level in session_data['daily']['price_levels'] 
                               if level and float(level) > 0]
            else:
                logger.warning("No daily price levels found in session data")
                return None
            
            if not daily_levels:
                logger.warning("Daily price levels are empty or zero")
                return None
            
            logger.info(f"Found {len(daily_levels)} daily levels: {[float(l) for l in daily_levels]}")
            
            # Check if we already have 5-minute ATR in metrics
            atr_5min = None
            if 'metrics' in session_data and 'atr_5min' in session_data['metrics']:
                try:
                    atr_5min = Decimal(str(session_data['metrics']['atr_5min']))
                    logger.info(f"Using existing 5-minute ATR from metrics: {atr_5min}")
                except (ValueError, TypeError):
                    logger.warning("Invalid 5-minute ATR in metrics, will recalculate")
            
            # Calculate 5-minute ATR if not available
            if not atr_5min or atr_5min <= 0:
                atr_5min = self.calculate_5min_atr(ticker, analysis_datetime)
                
                if not atr_5min:
                    logger.error("Failed to calculate 5-minute ATR")
                    # Use a fallback: 3.3% of daily ATR as approximation (5min is ~1/78 of a day)
                    if 'metrics' in session_data and 'daily_atr' in session_data['metrics']:
                        daily_atr = Decimal(str(session_data['metrics']['daily_atr']))
                        atr_5min = daily_atr * Decimal("0.033")
                        logger.warning(f"Using fallback: 3.3% of daily ATR = {atr_5min}")
                    else:
                        # Final fallback: use a very small percentage of the average level
                        avg_level = sum(daily_levels) / len(daily_levels)
                        atr_5min = avg_level * Decimal("0.001")  # 0.1% of average level
                        logger.warning(f"Using final fallback: 0.1% of average level = {atr_5min}")
            
            # Create zones with 5min above and below
            zones = self.create_daily_zones(daily_levels, atr_5min)
            
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
                'atr_5min': atr_5min,
                'zone_width': '10min_total',
                'zone_description': '5min_above_below',
                'current_price': current_price,
                'all_zones': zones,
                'resistance_zones': resistance_zones,
                'support_zones': support_zones,
                'zone_count': len(zones)
            }
            
            logger.info(f"Daily zone calculation complete: {len(zones)} zones created with 5-minute ATR of {atr_5min:.2f} (5min above/below)")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating daily zones: {e}")
            return None
    
    def format_zones_for_display(self, zone_result: Dict) -> str:
        """
        Format daily zones for display in UI
        
        Args:
            zone_result: Result from calculate_zones_from_session
            
        Returns:
            Formatted string for display
        """
        if not zone_result:
            return "No daily zones calculated"
        
        output = []
        output.append(f"Daily Zones Analysis for {zone_result['ticker']}")
        output.append(f"5-Minute ATR: ${zone_result['atr_5min']:.2f}")
        output.append(f"Zone Width: 10 minutes total (5min above + 5min below)")
        
        if zone_result['current_price'] > 0:
            output.append(f"Current Price: ${zone_result['current_price']:.2f}")
        
        output.append(f"\nTotal Zones: {zone_result['zone_count']}")
        output.append("-" * 50)
        
        # Display resistance zones (3 above)
        if zone_result['resistance_zones']:
            output.append("\n📈 RESISTANCE ZONES (above current price):")
            for zone in zone_result['resistance_zones'][:3]:  # Show top 3 closest
                output.append(f"\n  {zone['name']} Zone:")
                output.append(f"    Level: ${zone['level']:.2f}")
                output.append(f"    Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"    Size: ${zone['zone_size']:.2f} (10min range)")
                if 'distance_pct' in zone:
                    output.append(f"    Distance: {zone['distance_pct']:.2f}% above")
        
        # Display support zones (3 below)
        if zone_result['support_zones']:
            output.append("\n📉 SUPPORT ZONES (below current price):")
            for zone in zone_result['support_zones'][:3]:  # Show top 3 closest
                output.append(f"\n  {zone['name']} Zone:")
                output.append(f"    Level: ${zone['level']:.2f}")
                output.append(f"    Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"    Size: ${zone['zone_size']:.2f} (10min range)")
                if 'distance_pct' in zone:
                    output.append(f"    Distance: {zone['distance_pct']:.2f}% below")
        
        return "\n".join(output)
    
    def get_zones_for_confluence(self, zone_result: Dict) -> List[Dict]:
        """
        Prepare daily zones for confluence engine integration
        
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
                'name': f"Daily_{zone['name']}",
                'type': 'daily_zone',
                'level': float(zone['level']),
                'high': float(zone['high']),
                'low': float(zone['low']),
                'zone_size': float(zone['zone_size']),
                'source': 'daily_levels',
                'timeframe': 'daily',
                'atr_based': True,
                'atr_value': float(zone['atr_used']),
                'atr_type': '5min',
                'zone_width': '5min_above_below'
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
    
    # Example session data with daily levels
    example_session = {
        'ticker': 'AAPL',
        'daily': {
            'price_levels': [175.50, 178.25, 172.80, 180.00, 182.50, 170.25]  # DL1-DL6
        },
        'pre_market_price': 176.00,
        'metrics': {
            'daily_atr': 2.50,  # Can be used as fallback
            'atr_5min': 0.12   # If available, will be used directly
        }
    }
    
    print("Initializing Daily Zone Calculator...")
    
    # Initialize calculator
    calculator = DailyZoneCalculator()
    
    # Test connection
    connected, msg = calculator.test_connection()
    print(f"Connection test: {msg}")
    
    if connected:
        print("\nCalculating daily zones with 5-minute ATR (5min above/below)...")
        
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
            print("Failed to calculate daily zones")
    else:
        print("Cannot proceed without connection to Polygon")