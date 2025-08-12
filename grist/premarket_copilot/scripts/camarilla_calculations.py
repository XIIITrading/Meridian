"""
Camarilla Pivot Calculation Script for Grist Co-Pilot
Calculates daily, weekly, and monthly Camarilla pivot points
Shows only selected levels per timeframe
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

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
class CamarillaPivot:
    """Represents a single Camarilla pivot level"""
    level_name: str
    price: float
    strength: int
    timeframe: str


@dataclass
class CamarillaResult:
    """Container for Camarilla calculation results"""
    timeframe: str
    close: float
    high: float
    low: float
    pivots: List[CamarillaPivot]
    range_type: str
    central_pivot: float
    calculated_from_date: str


class CamarillaCalculator:
    """
    Calculate Camarilla pivot points for different timeframes
    """
    
    # US market holidays for 2024-2025
    US_HOLIDAYS = [
        '2024-01-01', '2024-01-15', '2024-02-19', '2024-03-29',
        '2024-05-27', '2024-06-19', '2024-07-04', '2024-09-02',
        '2024-11-28', '2024-12-25',
        '2025-01-01', '2025-01-20', '2025-02-17', '2025-04-18',
        '2025-05-26', '2025-06-19', '2025-07-04', '2025-09-01',
        '2025-11-27', '2025-12-25',
    ]
    
    def __init__(self, base_url: str = "http://localhost:8200/api/v1"):
        """Initialize with Polygon Bridge"""
        self.bridge = PolygonBridge(base_url=base_url)
        
    def _get_prior_trading_day(self, current_date: pd.Timestamp) -> pd.Timestamp:
        """Get the prior trading day, skipping weekends and holidays"""
        prior_date = current_date - timedelta(days=1)
        
        # Convert holidays to pandas timestamps
        holidays = pd.to_datetime(self.US_HOLIDAYS)
        
        # Keep going back until we find a trading day
        while prior_date.weekday() >= 5 or prior_date.normalize() in holidays:
            prior_date = prior_date - timedelta(days=1)
        
        return prior_date
    
    def calculate_pivots_from_data(self, 
                                  high: float, 
                                  low: float, 
                                  close: float,
                                  timeframe: str) -> CamarillaResult:
        """
        Calculate Camarilla pivots from OHLC values
        
        Args:
            high: High price
            low: Low price  
            close: Close price
            timeframe: Timeframe string
            
        Returns:
            CamarillaResult with calculated pivots
        """
        # Calculate range
        range_val = high - low
        
        # Calculate pivot point (central pivot)
        pivot = (high + low + close) / 3
        
        # Calculate Camarilla levels
        pivots = []
        
        # Resistance levels
        r1 = close + range_val * 1.1 / 12
        r2 = close + range_val * 1.1 / 6
        r3 = close + range_val * 1.1 / 4
        r4 = close + range_val * 1.1 / 2
        r5 = (high / low) * close if low != 0 else close
        r6 = r5 + 1.168 * (r5 - r4)
        
        # Support levels
        s1 = close - range_val * 1.1 / 12
        s2 = close - range_val * 1.1 / 6
        s3 = close - range_val * 1.1 / 4
        s4 = close - range_val * 1.1 / 2
        s5 = close - (r5 - close)
        s6 = close - (r6 - close)
        
        # Add pivots with strength scores
        pivots.extend([
            CamarillaPivot('R6', r6, 6, timeframe),
            CamarillaPivot('R5', r5, 5, timeframe),
            CamarillaPivot('R4', r4, 4, timeframe),
            CamarillaPivot('R3', r3, 3, timeframe),
            CamarillaPivot('R2', r2, 2, timeframe),
            CamarillaPivot('R1', r1, 1, timeframe),
            CamarillaPivot('Pivot', pivot, 0, timeframe),
            CamarillaPivot('S1', s1, 1, timeframe),
            CamarillaPivot('S2', s2, 2, timeframe),
            CamarillaPivot('S3', s3, 3, timeframe),
            CamarillaPivot('S4', s4, 4, timeframe),
            CamarillaPivot('S5', s5, 5, timeframe),
            CamarillaPivot('S6', s6, 6, timeframe),
        ])
        
        # Determine range type
        if close > pivot:
            range_type = 'Bullish'
        elif close < pivot:
            range_type = 'Bearish'
        else:
            range_type = 'Neutral'
        
        return CamarillaResult(
            timeframe=timeframe,
            close=close,
            high=high,
            low=low,
            pivots=pivots,
            range_type=range_type,
            central_pivot=pivot,
            calculated_from_date=""
        )
    
    def calculate_daily_pivots(self, 
                              symbol: str, 
                              analysis_date: date) -> Optional[CamarillaResult]:
        """
        Calculate daily Camarilla pivots using prior trading day's data
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis
            
        Returns:
            CamarillaResult or None
        """
        try:
            # Get prior trading day
            analysis_ts = pd.Timestamp(analysis_date)
            prior_day = self._get_prior_trading_day(analysis_ts)
            
            logger.info(f"Fetching daily data for {symbol} on {prior_day.date()}")
            
            # Fetch daily bar for prior trading day
            df_daily = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=prior_day.strftime('%Y-%m-%d'),
                end_date=prior_day.strftime('%Y-%m-%d'),
                timeframe='1day'
            )
            
            if df_daily is None or df_daily.empty:
                # Try fetching a wider range
                start_date = (prior_day - timedelta(days=5)).strftime('%Y-%m-%d')
                df_daily = self.bridge.fetch_bars(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=prior_day.strftime('%Y-%m-%d'),
                    timeframe='1day'
                )
                
                if df_daily is not None and not df_daily.empty:
                    # Use the last available bar
                    df_daily = df_daily.tail(1)
            
            if df_daily is None or df_daily.empty:
                logger.warning(f"No daily data available for {symbol}")
                return None
            
            # Extract OHLC from the daily bar
            bar = df_daily.iloc[-1]
            high = float(bar['high'])
            low = float(bar['low'])
            close = float(bar['close'])
            
            result = self.calculate_pivots_from_data(high, low, close, 'Daily')
            result.calculated_from_date = prior_day.strftime('%Y-%m-%d')
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating daily pivots: {e}")
            return None
    
    def calculate_weekly_pivots(self, 
                               symbol: str, 
                               analysis_date: date) -> Optional[CamarillaResult]:
        """
        Calculate weekly Camarilla pivots using prior week's data
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis
            
        Returns:
            CamarillaResult or None
        """
        try:
            # Calculate date range for prior week
            analysis_ts = pd.Timestamp(analysis_date)
            days_since_monday = analysis_ts.weekday()
            last_monday = analysis_ts - timedelta(days=days_since_monday + 7)
            last_friday = last_monday + timedelta(days=4)
            
            logger.info(f"Fetching weekly data for {symbol} from {last_monday.date()} to {last_friday.date()}")
            
            # Fetch daily bars for the prior week
            df_weekly = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=last_monday.strftime('%Y-%m-%d'),
                end_date=last_friday.strftime('%Y-%m-%d'),
                timeframe='1day'
            )
            
            if df_weekly is None or df_weekly.empty:
                logger.warning(f"No weekly data available for {symbol}")
                return None
            
            # Aggregate to weekly OHLC
            high = float(df_weekly['high'].max())
            low = float(df_weekly['low'].min())
            close = float(df_weekly.iloc[-1]['close'])  # Friday's close
            
            result = self.calculate_pivots_from_data(high, low, close, 'Weekly')
            result.calculated_from_date = f"{last_monday.strftime('%Y-%m-%d')} to {last_friday.strftime('%Y-%m-%d')}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating weekly pivots: {e}")
            return None
    
    def calculate_monthly_pivots(self, 
                                symbol: str, 
                                analysis_date: date) -> Optional[CamarillaResult]:
        """
        Calculate monthly Camarilla pivots using prior month's data
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis
            
        Returns:
            CamarillaResult or None
        """
        try:
            # Calculate date range for prior month
            analysis_ts = pd.Timestamp(analysis_date)
            first_day_current = analysis_ts.replace(day=1)
            last_day_prior = first_day_current - timedelta(days=1)
            first_day_prior = last_day_prior.replace(day=1)
            
            logger.info(f"Fetching monthly data for {symbol} from {first_day_prior.date()} to {last_day_prior.date()}")
            
            # Fetch daily bars for the prior month
            df_monthly = self.bridge.fetch_bars(
                symbol=symbol,
                start_date=first_day_prior.strftime('%Y-%m-%d'),
                end_date=last_day_prior.strftime('%Y-%m-%d'),
                timeframe='1day'
            )
            
            if df_monthly is None or df_monthly.empty:
                logger.warning(f"No monthly data available for {symbol}")
                return None
            
            # Aggregate to monthly OHLC
            high = float(df_monthly['high'].max())
            low = float(df_monthly['low'].min())
            close = float(df_monthly.iloc[-1]['close'])  # Last day's close
            
            result = self.calculate_pivots_from_data(high, low, close, 'Monthly')
            result.calculated_from_date = f"{first_day_prior.strftime('%Y-%m')}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating monthly pivots: {e}")
            return None
    
    def get_all_pivots(self, 
                      symbol: str, 
                      analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get all Camarilla pivots (daily, weekly, monthly) for a symbol
        
        Args:
            symbol: Stock ticker
            analysis_date: Date for analysis (defaults to today)
            
        Returns:
            Dictionary with all pivot calculations
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
        
        logger.info(f"Calculating Camarilla pivots for {symbol} on {analysis_date}")
        
        results = {
            'symbol': symbol,
            'analysis_date': analysis_date,
            'ticker_id': f"{symbol}.{analysis_date.strftime('%m%d%y')}",
            'daily': None,
            'weekly': None,
            'monthly': None,
            'calculated_at': datetime.now()
        }
        
        # Calculate daily pivots
        daily_result = self.calculate_daily_pivots(symbol, analysis_date)
        if daily_result:
            results['daily'] = daily_result
        
        # Calculate weekly pivots
        weekly_result = self.calculate_weekly_pivots(symbol, analysis_date)
        if weekly_result:
            results['weekly'] = weekly_result
        
        # Calculate monthly pivots
        monthly_result = self.calculate_monthly_pivots(symbol, analysis_date)
        if monthly_result:
            results['monthly'] = monthly_result
        
        return results


def format_pivot_display(pivot: CamarillaPivot) -> str:
    """Format a single pivot for display"""
    return f"{pivot.level_name:6} : {pivot.price:>10.2f}"


def display_results(results: Dict[str, Any]):
    """Display Camarilla pivot results in a formatted way"""
    
    if 'error' in results:
        print(f"\n❌ Error: {results['error']}")
        return
    
    print(f"\n📊 Camarilla Pivot Analysis for {results['symbol']}")
    print(f"📅 Analysis Date: {results['analysis_date']}")
    print(f"🔑 Ticker ID: {results['ticker_id']}")
    print("=" * 60)
    
    # Daily Pivots - Show only: R6, R4, R3, Pivot, S3, S4, S6
    if results['daily']:
        daily = results['daily']
        print(f"\n📈 DAILY PIVOTS (from {daily.calculated_from_date})")
        print(f"   Range: {daily.range_type} | Central Pivot: {daily.central_pivot:.2f}")
        print(f"   H: {daily.high:.2f} | L: {daily.low:.2f} | C: {daily.close:.2f}")
        print("-" * 40)
        
        # Define the levels we want to show for daily
        daily_levels = ['R6', 'R4', 'R3', 'Pivot', 'S3', 'S4', 'S6']
        
        # Create a dict for easy lookup
        pivot_dict = {p.level_name: p for p in daily.pivots}
        
        # Display in order
        for level_name in daily_levels:
            if level_name in pivot_dict:
                pivot = pivot_dict[level_name]
                marker = " ← Central" if pivot.level_name == 'Pivot' else ""
                print(f"   {format_pivot_display(pivot)}{marker}")
    else:
        print("\n❌ Daily pivots not available")
    
    # Weekly Pivots - Show only: R3, R2, R1, Pivot, S1, S2, S3
    if results['weekly']:
        weekly = results['weekly']
        print(f"\n📈 WEEKLY PIVOTS (from {weekly.calculated_from_date})")
        print(f"   Range: {weekly.range_type} | Central Pivot: {weekly.central_pivot:.2f}")
        print(f"   H: {weekly.high:.2f} | L: {weekly.low:.2f} | C: {weekly.close:.2f}")
        print("-" * 40)
        
        # Define the levels we want to show for weekly
        weekly_levels = ['R3', 'R2', 'R1', 'Pivot', 'S1', 'S2', 'S3']
        
        # Create a dict for easy lookup
        pivot_dict = {p.level_name: p for p in weekly.pivots}
        
        # Display in order
        for level_name in weekly_levels:
            if level_name in pivot_dict:
                pivot = pivot_dict[level_name]
                marker = " ← Central" if pivot.level_name == 'Pivot' else ""
                print(f"   {format_pivot_display(pivot)}{marker}")
    else:
        print("\n❌ Weekly pivots not available")
    
    # Monthly Pivots - Show only: R3, R2, R1, Pivot, S1, S2, S3
    if results['monthly']:
        monthly = results['monthly']
        print(f"\n📈 MONTHLY PIVOTS (from {monthly.calculated_from_date})")
        print(f"   Range: {monthly.range_type} | Central Pivot: {monthly.central_pivot:.2f}")
        print(f"   H: {monthly.high:.2f} | L: {monthly.low:.2f} | C: {monthly.close:.2f}")
        print("-" * 40)
        
        # Define the levels we want to show for monthly
        monthly_levels = ['R3', 'R2', 'R1', 'Pivot', 'S1', 'S2', 'S3']
        
        # Create a dict for easy lookup
        pivot_dict = {p.level_name: p for p in monthly.pivots}
        
        # Display in order
        for level_name in monthly_levels:
            if level_name in pivot_dict:
                pivot = pivot_dict[level_name]
                marker = " ← Central" if pivot.level_name == 'Pivot' else ""
                print(f"   {format_pivot_display(pivot)}{marker}")
    else:
        print("\n❌ Monthly pivots not available")
    
    print("\n" + "=" * 60)
    print(f"Calculated at: {results['calculated_at'].strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate Camarilla pivot points')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD)', 
                       default=date.today().strftime('%Y-%m-%d'))
    parser.add_argument('--api-url', help='Polygon API URL',
                       default='http://localhost:8200/api/v1')
    parser.add_argument('--timeframe', help='Specific timeframe (daily/weekly/monthly/all)',
                       default='all', choices=['daily', 'weekly', 'monthly', 'all'])
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Parse date
    analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    
    # Create calculator
    calculator = CamarillaCalculator(base_url=args.api_url)
    
    # Test connection
    connected, msg = calculator.bridge.test_connection()
    if not connected:
        logger.error(f"Failed to connect to Polygon API: {msg}")
        return 1
    
    logger.info(f"Connected to Polygon API: {msg}")
    
    # Calculate pivots based on timeframe argument
    if args.timeframe == 'all':
        results = calculator.get_all_pivots(args.ticker.upper(), analysis_date)
    else:
        results = {
            'symbol': args.ticker.upper(),
            'analysis_date': analysis_date,
            'ticker_id': f"{args.ticker.upper()}.{analysis_date.strftime('%m%d%y')}",
            'calculated_at': datetime.now()
        }
        
        if args.timeframe == 'daily':
            results['daily'] = calculator.calculate_daily_pivots(args.ticker.upper(), analysis_date)
        elif args.timeframe == 'weekly':
            results['weekly'] = calculator.calculate_weekly_pivots(args.ticker.upper(), analysis_date)
        elif args.timeframe == 'monthly':
            results['monthly'] = calculator.calculate_monthly_pivots(args.ticker.upper(), analysis_date)
    
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
        
        # Define which levels to include for each timeframe
        level_filters = {
            'daily': ['R6', 'R4', 'R3', 'Pivot', 'S3', 'S4', 'S6'],
            'weekly': ['R3', 'R2', 'R1', 'Pivot', 'S1', 'S2', 'S3'],
            'monthly': ['R3', 'R2', 'R1', 'Pivot', 'S1', 'S2', 'S3']
        }
        
        for timeframe in ['daily', 'weekly', 'monthly']:
            if timeframe in results and results[timeframe]:
                tf_result = results[timeframe]
                
                # Filter pivots to only include desired levels
                filtered_levels = {}
                for p in tf_result.pivots:
                    if p.level_name in level_filters[timeframe]:
                        filtered_levels[p.level_name] = round(p.price, 2)
                
                json_results[timeframe] = {
                    'high': tf_result.high,
                    'low': tf_result.low,
                    'close': tf_result.close,
                    'central_pivot': tf_result.central_pivot,
                    'range_type': tf_result.range_type,
                    'calculated_from': tf_result.calculated_from_date,
                    'levels': filtered_levels
                }
        
        print(json.dumps(json_results, indent=2))
    else:
        display_results(results)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())