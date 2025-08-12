"""
HVN (High Volume Node) Calculation Script for Grist Co-Pilot
Calculates 7-day and 14-day top 3 HVN zones
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from scipy.signal import find_peaks

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import PolygonBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PriceLevel:
    """Represents a single price level in the volume profile"""
    index: int
    center: float
    high: float
    low: float
    volume: float
    percent_of_total: float
    rank: int = 0


@dataclass
class HVNZone:
    """Represents a high volume zone"""
    zone_high: float
    zone_low: float
    center_price: float
    volume_percent: float
    rank: int


@dataclass
class TimeframeHVNResult:
    """HVN analysis result for a single timeframe"""
    timeframe_days: int
    price_range: Tuple[float, float]
    top_zones: List[HVNZone]  # Top 3 HVN zones
    total_levels: int
    data_points: int
    calculated_from_date: str


class VolumeProfile:
    """Build volume profile from OHLCV data"""
    
    def __init__(self, levels: int = 100):
        self.levels = levels
        self.hvn_unit = 0
        self.price_range = (0, 0)
    
    def _filter_market_hours(self, 
                            data: pd.DataFrame,
                            include_pre: bool = True,
                            include_post: bool = True) -> pd.DataFrame:
        """
        Filter data based on market hours.
        
        Regular hours: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
        Pre-market: 4:00 AM - 9:30 AM ET (09:00 - 14:30 UTC)
        Post-market: 4:00 PM - 8:00 PM ET (21:00 - 01:00 UTC next day)
        """
        if include_pre and include_post:
            return data  # Return all data
        
        # Ensure timezone-naive for time comparisons
        filtered = data.copy()
        if filtered.index.tz is not None:
            filtered.index = filtered.index.tz_localize(None)
        
        # Define market hours in UTC
        regular_start = pd.Timestamp('14:30:00').time()
        regular_end = pd.Timestamp('21:00:00').time()
        pre_start = pd.Timestamp('09:00:00').time()
        post_end = pd.Timestamp('01:00:00').time()  # Next day
        
        if not include_pre and not include_post:
            # Regular hours only
            mask = (filtered.index.time >= regular_start) & (filtered.index.time <= regular_end)
            return filtered[mask]
        
        elif include_pre and not include_post:
            # Pre-market + regular hours
            mask = (filtered.index.time >= pre_start) & (filtered.index.time <= regular_end)
            return filtered[mask]
        
        elif not include_pre and include_post:
            # Regular + post-market (complex due to day boundary)
            mask1 = (filtered.index.time >= regular_start) & (filtered.index.time <= pd.Timestamp('23:59:59').time())
            mask2 = (filtered.index.time >= pd.Timestamp('00:00:00').time()) & (filtered.index.time <= post_end)
            return filtered[mask1 | mask2]
        
        return data
    
    def build_volume_profile(self, 
                            data: pd.DataFrame,
                            include_pre: bool = True,
                            include_post: bool = True) -> List[PriceLevel]:
        """
        Build volume profile from OHLCV data.
        
        Args:
            data: OHLCV DataFrame
            include_pre: Include pre-market data
            include_post: Include post-market data
            
        Returns:
            List of PriceLevel objects
        """
        if data.empty:
            return []
        
        # Filter by market hours if requested
        filtered_data = self._filter_market_hours(data, include_pre, include_post)
        
        if filtered_data.empty:
            return []
        
        # Calculate price range
        price_high = filtered_data['high'].max()
        price_low = filtered_data['low'].min()
        self.price_range = (price_low, price_high)
        
        # Calculate level width (HVN unit)
        self.hvn_unit = (price_high - price_low) / self.levels
        
        if self.hvn_unit == 0:
            return []
        
        # Initialize volume array
        volume_per_level = np.zeros(self.levels)
        
        # Process each bar
        for _, row in filtered_data.iterrows():
            bar_high = row['high']
            bar_low = row['low']
            bar_volume = row['volume']
            
            # Find level indices this bar spans
            high_level = min(int((bar_high - price_low) / self.hvn_unit), self.levels - 1)
            low_level = max(int((bar_low - price_low) / self.hvn_unit), 0)
            
            # Distribute volume across levels
            levels_touched = high_level - low_level + 1
            if levels_touched > 0:
                volume_per_level_bar = bar_volume / levels_touched
                for level in range(low_level, high_level + 1):
                    volume_per_level[level] += volume_per_level_bar
        
        # Calculate total volume
        total_volume = volume_per_level.sum()
        
        if total_volume == 0:
            return []
        
        # Create PriceLevel objects
        price_levels = []
        for i in range(self.levels):
            level_low = price_low + (i * self.hvn_unit)
            level_high = level_low + self.hvn_unit
            level_center = (level_low + level_high) / 2
            
            price_levels.append(PriceLevel(
                index=i,
                center=level_center,
                high=level_high,
                low=level_low,
                volume=volume_per_level[i],
                percent_of_total=(volume_per_level[i] / total_volume) * 100
            ))
        
        return price_levels


class HVNCalculator:
    """Calculate HVN zones for different timeframes"""
    
    def __init__(self, base_url: str = "http://localhost:8200/api/v1"):
        """Initialize with Polygon Bridge"""
        self.bridge = PolygonBridge(base_url=base_url)
        self.volume_profile = VolumeProfile(levels=100)
        
    def identify_hvn_zones(self, 
                          levels: List[PriceLevel],
                          top_n: int = 3) -> List[HVNZone]:
        """
        Identify top N HVN zones from volume profile.
        
        Args:
            levels: List of price levels from volume profile
            top_n: Number of top zones to return
            
        Returns:
            List of HVNZone objects
        """
        if not levels:
            return []
        
        # Sort levels by volume percentage (descending)
        sorted_levels = sorted(levels, key=lambda x: x.percent_of_total, reverse=True)
        
        # Take top N levels and create zones
        zones = []
        for i, level in enumerate(sorted_levels[:top_n]):
            zone = HVNZone(
                zone_high=level.high,
                zone_low=level.low,
                center_price=level.center,
                volume_percent=level.percent_of_total,
                rank=i + 1
            )
            zones.append(zone)
        
        return zones
    
    def calculate_timeframe_hvn(self, 
                               symbol: str,
                               analysis_date: date,
                               timeframe_days: int) -> Optional[TimeframeHVNResult]:
        """
        Calculate HVN zones for a specific timeframe.
        
        Args:
            symbol: Stock ticker
            analysis_date: End date for analysis
            timeframe_days: Number of days to look back
            
        Returns:
            TimeframeHVNResult or None
        """
        try:
            # Calculate date range
            end_date = analysis_date
            start_date = end_date - timedelta(days=timeframe_days)
            
            logger.info(f"Fetching {timeframe_days}-day data for {symbol} from {start_date} to {end_date}")
            
            # Fetch 5-minute data for volume profile
            df_5min = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                timeframe='5min'
            )
            
            if df_5min is None or df_5min.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Build volume profile
            price_levels = self.volume_profile.build_volume_profile(
                df_5min,
                include_pre=True,
                include_post=True
            )
            
            if not price_levels:
                logger.warning(f"Could not build volume profile for {symbol}")
                return None
            
            # Identify top 3 HVN zones
            top_zones = self.identify_hvn_zones(price_levels, top_n=3)
            
            return TimeframeHVNResult(
                timeframe_days=timeframe_days,
                price_range=self.volume_profile.price_range,
                top_zones=top_zones,
                total_levels=len(price_levels),
                data_points=len(df_5min),
                calculated_from_date=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )
            
        except Exception as e:
            logger.error(f"Error calculating {timeframe_days}-day HVN: {e}")
            return None
    
    def get_all_hvn_zones(self, 
                         symbol: str,
                         analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get HVN zones for 7-day and 14-day timeframes.
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis (defaults to today)
            
        Returns:
            Dictionary with HVN results
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        # Validate ticker
        logger.info(f"Validating ticker {symbol}...")
        if not self.bridge.validate_ticker(symbol):
            return {
                'error': f"Invalid ticker: {symbol}",
                'symbol': symbol,
                'analysis_date': analysis_date
            }
        
        logger.info(f"Calculating HVN zones for {symbol} on {analysis_date}")
        
        results = {
            'symbol': symbol,
            'analysis_date': analysis_date,
            'ticker_id': f"{symbol}.{analysis_date.strftime('%m%d%y')}",
            '7_day': None,
            '14_day': None,
            'calculated_at': datetime.now()
        }
        
        # Calculate 7-day HVN
        hvn_7day = self.calculate_timeframe_hvn(symbol, analysis_date, 7)
        if hvn_7day:
            results['7_day'] = hvn_7day
        
        # Calculate 14-day HVN
        hvn_14day = self.calculate_timeframe_hvn(symbol, analysis_date, 14)
        if hvn_14day:
            results['14_day'] = hvn_14day
        
        return results


def format_zone_display(zone: HVNZone) -> str:
    """Format a single HVN zone for display"""
    return f"   Zone {zone.rank}: ${zone.zone_low:>8.2f} - ${zone.zone_high:>8.2f} | Center: ${zone.center_price:>8.2f} | Volume: {zone.volume_percent:>5.2f}%"


def display_results(results: Dict[str, Any]):
    """Display HVN results in a formatted way"""
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return
    
    print(f"\n📊 HVN Zone Analysis for {results['symbol']}")
    print(f"📅 Analysis Date: {results['analysis_date']}")
    print(f"🔑 Ticker ID: {results['ticker_id']}")
    print("=" * 80)
    
    # 7-Day HVN Zones
    if results['7_day']:
        hvn_7 = results['7_day']
        print(f"\n📈 7-DAY HVN ZONES ({hvn_7.calculated_from_date})")
        print(f"   Price Range: ${hvn_7.price_range[0]:.2f} - ${hvn_7.price_range[1]:.2f}")
        print(f"   Data Points: {hvn_7.data_points:,} bars")
        print("-" * 60)
        print("   Top 3 High Volume Zones:")
        for zone in hvn_7.top_zones:
            print(format_zone_display(zone))
    else:
        print("\n❌ 7-day HVN zones not available")
    
    # 14-Day HVN Zones
    if results['14_day']:
        hvn_14 = results['14_day']
        print(f"\n📈 14-DAY HVN ZONES ({hvn_14.calculated_from_date})")
        print(f"   Price Range: ${hvn_14.price_range[0]:.2f} - ${hvn_14.price_range[1]:.2f}")
        print(f"   Data Points: {hvn_14.data_points:,} bars")
        print("-" * 60)
        print("   Top 3 High Volume Zones:")
        for zone in hvn_14.top_zones:
            print(format_zone_display(zone))
    else:
        print("\n❌ 14-day HVN zones not available")
    
    print("\n" + "=" * 80)
    print(f"Calculated at: {results['calculated_at'].strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate HVN zones')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD)', 
                       default=date.today().strftime('%Y-%m-%d'))
    parser.add_argument('--api-url', help='Polygon API URL',
                       default='http://localhost:8200/api/v1')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Parse date
    analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    
    # Create calculator
    calculator = HVNCalculator(base_url=args.api_url)
    
    # Test connection
    connected, msg = calculator.bridge.test_connection()
    if not connected:
        logger.error(f"Failed to connect to Polygon API: {msg}")
        return 1
    
    logger.info(f"Connected to Polygon API: {msg}")
    
    # Calculate HVN zones
    results = calculator.get_all_hvn_zones(args.ticker.upper(), analysis_date)
    
    # Output results
    if args.json:
        import json
        
        # Convert to JSON-serializable format
        json_results = {
            'symbol': results['symbol'],
            'analysis_date': str(results['analysis_date']),
            'ticker_id': results['ticker_id'],
            'calculated_at': results['calculated_at'].isoformat()
        }
        
        for timeframe in ['7_day', '14_day']:
            if results[timeframe]:
                tf_result = results[timeframe]
                json_results[timeframe] = {
                    'price_range': {
                        'low': tf_result.price_range[0],
                        'high': tf_result.price_range[1]
                    },
                    'data_points': tf_result.data_points,
                    'calculated_from': tf_result.calculated_from_date,
                    'top_zones': [
                        {
                            'rank': zone.rank,
                            'zone_low': round(zone.zone_low, 2),
                            'zone_high': round(zone.zone_high, 2),
                            'center': round(zone.center_price, 2),
                            'volume_percent': round(zone.volume_percent, 2)
                        }
                        for zone in tf_result.top_zones
                    ]
                }
        
        print(json.dumps(json_results, indent=2))
    else:
        display_results(results)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())