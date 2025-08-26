"""
ATR Zone Calculator
Location: levels_zones/calculations/zones/atr_zone_calc.py
Creates dynamic volatility-based zones using ATR levels and 5-minute ATR bands
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set up logging
logger = logging.getLogger(__name__)


class ATRZoneCalculator:
    """Calculator for creating ATR-based zones using 5-minute ATR"""
    
    def __init__(self):
        """Initialize the calculator"""
        logger.info("ATRZoneCalculator initialized")
    
    def create_atr_zones(self, 
                        atr_high: Decimal, 
                        atr_low: Decimal,
                        atr_5min: Decimal,
                        current_price: Decimal) -> List[Dict[str, Decimal]]:
        """
        Create zones from ATR levels using 5-minute ATR
        
        Args:
            atr_high: Current price + daily ATR (resistance level)
            atr_low: Current price - daily ATR (support level)
            atr_5min: 5-minute ATR value for zone width
            current_price: Current market price
            
        Returns:
            List of zone dictionaries with high/low boundaries
        """
        zones = []
        
        # Create ATR High Zone (resistance zone)
        if atr_high and atr_high > 0:
            zone_high = atr_high + atr_5min
            zone_low = atr_high - atr_5min
            
            zone = {
                'name': 'ATR_High_Zone',
                'level': atr_high,
                'high': zone_high,
                'low': zone_low,
                'zone_size': zone_high - zone_low,
                'type': 'resistance',
                'atr_used': atr_5min,
                'center': atr_high,
                'distance': atr_high - current_price,
                'distance_pct': ((atr_high - current_price) / current_price * 100) if current_price > 0 else 0
            }
            zones.append(zone)
            
            logger.debug(f"Created ATR High Zone: {zone_low:.2f} - {zone_high:.2f} (center: {atr_high:.2f})")
        
        # Create ATR Low Zone (support zone)
        if atr_low and atr_low > 0:
            zone_high = atr_low + atr_5min
            zone_low = atr_low - atr_5min
            
            zone = {
                'name': 'ATR_Low_Zone',
                'level': atr_low,
                'high': zone_high,
                'low': zone_low,
                'zone_size': zone_high - zone_low,
                'type': 'support',
                'atr_used': atr_5min,
                'center': atr_low,
                'distance': current_price - atr_low,
                'distance_pct': ((current_price - atr_low) / current_price * 100) if current_price > 0 else 0
            }
            zones.append(zone)
            
            logger.debug(f"Created ATR Low Zone: {zone_low:.2f} - {zone_high:.2f} (center: {atr_low:.2f})")
        
        return zones
    
    def calculate_zones_from_session(self, 
                                    session_data: Dict,
                                    ticker: str,
                                    analysis_datetime: datetime) -> Optional[Dict[str, any]]:
        """
        Calculate ATR zones from a trading session's metrics
        
        Args:
            session_data: Trading session data dictionary
            ticker: Stock ticker symbol
            analysis_datetime: DateTime for analysis
            
        Returns:
            Dictionary with zone calculations or None if failed
        """
        try:
            # Extract required metrics
            if 'metrics' not in session_data:
                logger.warning("No metrics found in session data")
                return None
            
            metrics = session_data['metrics']
            
            # Get ATR values
            daily_atr = Decimal(str(metrics.get('daily_atr', 0)))
            atr_5min = Decimal(str(metrics.get('atr_5min', 0)))
            
            if not daily_atr or daily_atr <= 0:
                logger.warning("Daily ATR is not available or zero")
                return None
            
            if not atr_5min or atr_5min <= 0:
                logger.warning("5-minute ATR is not available or zero")
                return None
            
            # Get current price
            current_price = Decimal("0")
            if 'pre_market_price' in session_data:
                current_price = Decimal(str(session_data['pre_market_price']))
            elif 'current_price' in metrics:
                current_price = Decimal(str(metrics['current_price']))
            
            if current_price <= 0:
                logger.warning("Current price is not available or zero")
                return None
            
            # Calculate ATR levels
            atr_high = current_price + daily_atr
            atr_low = current_price - daily_atr
            
            logger.info(f"Calculating ATR zones - Price: {current_price:.2f}, Daily ATR: {daily_atr:.2f}, 5-min ATR: {atr_5min:.2f}")
            
            # Create zones
            zones = self.create_atr_zones(atr_high, atr_low, atr_5min, current_price)
            
            # Separate into resistance and support
            resistance_zones = [z for z in zones if z['type'] == 'resistance']
            support_zones = [z for z in zones if z['type'] == 'support']
            
            result = {
                'ticker': ticker,
                'analysis_datetime': analysis_datetime,
                'atr_5min': atr_5min,
                'daily_atr': daily_atr,
                'current_price': current_price,
                'atr_high_level': atr_high,
                'atr_low_level': atr_low,
                'all_zones': zones,
                'resistance_zones': resistance_zones,
                'support_zones': support_zones,
                'zone_count': len(zones)
            }
            
            logger.info(f"ATR zone calculation complete: {len(zones)} zones created with 5-minute ATR of {atr_5min:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating ATR zones: {e}")
            return None
    
    def format_zones_for_display(self, zone_result: Dict) -> str:
        """
        Format ATR zones for display in UI
        
        Args:
            zone_result: Result from calculate_zones_from_session
            
        Returns:
            Formatted string for display
        """
        if not zone_result:
            return "No ATR zones calculated"
        
        output = []
        output.append(f"ATR Zones Analysis for {zone_result['ticker']}")
        output.append(f"5-Minute ATR: ${zone_result['atr_5min']:.2f}")
        output.append(f"Daily ATR: ${zone_result['daily_atr']:.2f}")
        output.append(f"Current Price: ${zone_result['current_price']:.2f}")
        output.append("-" * 50)
        
        # Display ATR High Zone
        for zone in zone_result['resistance_zones']:
            if zone['name'] == 'ATR_High_Zone':
                output.append("\n📈 ATR HIGH ZONE:")
                output.append(f"  Level: ${zone['level']:.2f} (Current + Daily ATR)")
                output.append(f"  Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"  Size: ${zone['zone_size']:.2f}")
                output.append(f"  Distance: {zone['distance_pct']:.2f}% above")
        
        # Display ATR Low Zone
        for zone in zone_result['support_zones']:
            if zone['name'] == 'ATR_Low_Zone':
                output.append("\n📉 ATR LOW ZONE:")
                output.append(f"  Level: ${zone['level']:.2f} (Current - Daily ATR)")
                output.append(f"  Zone: ${zone['low']:.2f} - ${zone['high']:.2f}")
                output.append(f"  Size: ${zone['zone_size']:.2f}")
                output.append(f"  Distance: {zone['distance_pct']:.2f}% below")
        
        return "\n".join(output)
    
    def get_zones_for_confluence(self, zone_result: Dict) -> List[Dict]:
        """
        Prepare ATR zones for confluence engine integration
        
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
                'name': zone['name'],
                'type': 'atr_zone',
                'level': float(zone['level']),
                'high': float(zone['high']),
                'low': float(zone['low']),
                'zone_size': float(zone['zone_size']),
                'source': 'atr_levels',
                'timeframe': 'dynamic',
                'atr_based': True,
                'atr_value': float(zone['atr_used']),
                'position': zone['type']  # 'resistance' or 'support'
            }
            
            # Add distance percentage if available
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
    
    # Example session data with metrics
    example_session = {
        'ticker': 'AAPL',
        'pre_market_price': 176.00,
        'metrics': {
            'daily_atr': 2.50,
            'atr_5min': 0.18,
            'current_price': 176.00
        }
    }
    
    print("Initializing ATR Zone Calculator...")
    
    # Initialize calculator
    calculator = ATRZoneCalculator()
    
    print("\nCalculating ATR zones...")
    
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
        print("Failed to calculate ATR zones")