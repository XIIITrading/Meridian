# File: C:\XIIITradingSystems\Meridian\confluence_system\confluence_scanner\calculations\market_structure.py
"""
Market Structure Calculator
Calculates PDH, PDL, PDC, ONH, ONL reference levels
"""

import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import pandas as pd
from decimal import Decimal

logger = logging.getLogger(__name__)


class MarketStructureCalculator:
    """
    Calculates market structure reference levels:
    - Previous Day High (PDH)
    - Previous Day Low (PDL)
    - Previous Day Close (PDC)
    - Overnight High (ONH)
    - Overnight Low (ONL)
    """
    
    def __init__(self):
        """Initialize calculator with market session times"""
        # Market session times in UTC
        self.regular_open = time(13, 30)   # 9:30 AM ET = 13:30 UTC
        self.regular_close = time(20, 0)   # 4:00 PM ET = 20:00 UTC
        self.overnight_start = time(20, 0)  # 4:00 PM ET = 20:00 UTC
        
    def calculate_all_levels(self,
                            daily_data: pd.DataFrame,
                            intraday_data: pd.DataFrame,
                            analysis_datetime: datetime) -> Dict[str, float]:
        """
        Calculate all market structure levels
        
        Args:
            daily_data: DataFrame with daily OHLC data
            intraday_data: DataFrame with intraday (5min or 15min) data
            analysis_datetime: Current analysis time
            
        Returns:
            Dictionary with PDH, PDL, PDC, ONH, ONL values
        """
        levels = {}
        
        # Calculate previous day levels
        pd_levels = self.calculate_previous_day_levels(daily_data, analysis_datetime)
        levels.update(pd_levels)
        
        # Calculate overnight levels
        on_levels = self.calculate_overnight_levels(intraday_data, analysis_datetime)
        levels.update(on_levels)
        
        logger.info(f"Calculated market structure levels: {levels}")
        return levels
    
    def calculate_previous_day_levels(self,
                                     daily_data: pd.DataFrame,
                                     analysis_datetime: datetime) -> Dict[str, float]:
        """
        Calculate PDH, PDL, PDC from previous trading day
        
        Args:
            daily_data: DataFrame with daily OHLC data
            analysis_datetime: Current analysis time
            
        Returns:
            Dictionary with PDH, PDL, PDC
        """
        try:
            if daily_data is None or daily_data.empty:
                logger.warning("No daily data available for previous day calculation")
                return {}
            
            # Get analysis date (just the date part)
            analysis_date = analysis_datetime.date()
            
            # Filter to data before analysis date
            if isinstance(daily_data.index, pd.DatetimeIndex):
                # If index is already datetime
                daily_data = daily_data[daily_data.index.date < analysis_date]
            else:
                # If we have a datetime column
                if 'datetime' in daily_data.columns:
                    daily_data = daily_data[pd.to_datetime(daily_data['datetime']).dt.date < analysis_date]
                elif 'date' in daily_data.columns:
                    daily_data = daily_data[pd.to_datetime(daily_data['date']).dt.date < analysis_date]
            
            if daily_data.empty:
                logger.warning("No previous day data found")
                return {}
            
            # Get the most recent trading day
            prev_day = daily_data.iloc[-1]
            
            levels = {
                'PDH': float(prev_day['high']),
                'PDL': float(prev_day['low']),
                'PDC': float(prev_day['close'])
            }
            
            logger.info(f"Previous day levels - High: ${levels['PDH']:.2f}, "
                       f"Low: ${levels['PDL']:.2f}, Close: ${levels['PDC']:.2f}")
            
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating previous day levels: {e}")
            return {}
    
    def calculate_overnight_levels(self,
                                  intraday_data: pd.DataFrame,
                                  analysis_datetime: datetime) -> Dict[str, float]:
        """
        Calculate ONH and ONL from overnight session
        Overnight session: 20:00 UTC previous day to analysis time
        
        Args:
            intraday_data: DataFrame with intraday OHLC data
            analysis_datetime: Current analysis time
            
        Returns:
            Dictionary with ONH, ONL
        """
        try:
            if intraday_data is None or intraday_data.empty:
                logger.warning("No intraday data available for overnight calculation")
                return {}
            
            # Define overnight session boundaries
            # Start: 20:00 UTC on previous day
            overnight_start = datetime.combine(
                analysis_datetime.date() - timedelta(days=1),
                self.overnight_start
            )
            
            # End: Current analysis time (or market open if after open)
            overnight_end = analysis_datetime
            
            # If analysis is after market open, use market open as end
            market_open = datetime.combine(analysis_datetime.date(), self.regular_open)
            if analysis_datetime > market_open:
                overnight_end = market_open
            
            logger.debug(f"Overnight session: {overnight_start} to {overnight_end}")
            
            # Filter data for overnight session
            if isinstance(intraday_data.index, pd.DatetimeIndex):
                # Ensure index is timezone-naive for comparison
                if intraday_data.index.tz is not None:
                    intraday_data.index = intraday_data.index.tz_localize(None)
                
                overnight_data = intraday_data[
                    (intraday_data.index >= overnight_start) & 
                    (intraday_data.index < overnight_end)
                ]
            else:
                # Use datetime column
                if 'datetime' in intraday_data.columns:
                    dt_col = pd.to_datetime(intraday_data['datetime'])
                    if dt_col.dt.tz is not None:
                        dt_col = dt_col.dt.tz_localize(None)
                    
                    overnight_data = intraday_data[
                        (dt_col >= overnight_start) & 
                        (dt_col < overnight_end)
                    ]
                else:
                    logger.warning("No datetime index or column found")
                    return {}
            
            if overnight_data.empty:
                logger.warning(f"No overnight data found between {overnight_start} and {overnight_end}")
                return {}
            
            # Calculate overnight high and low
            levels = {
                'ONH': float(overnight_data['high'].max()),
                'ONL': float(overnight_data['low'].min())
            }
            
            logger.info(f"Overnight levels - High: ${levels['ONH']:.2f}, Low: ${levels['ONL']:.2f}")
            logger.debug(f"Based on {len(overnight_data)} overnight bars")
            
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating overnight levels: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def format_for_confluence(self,
                            levels: Dict[str, float],
                            atr_5min: float) -> List[Dict]:
        """
        Format market structure levels for confluence engine
        Creates zones using 5-minute ATR
        
        Args:
            levels: Dictionary of calculated levels
            atr_5min: 5-minute ATR for zone width
            
        Returns:
            List of formatted confluence items
        """
        formatted = []
        
        for name, price in levels.items():
            if price and price > 0:
                # Create zone with 5-minute ATR width
                zone_width = atr_5min
                
                formatted.append({
                    'name': name,
                    'level': price,
                    'low': price - zone_width / 2,
                    'high': price + zone_width / 2,
                    'type': 'market-structure',
                    'strength': 1.0  # Base strength for all structure levels
                })
                
                logger.debug(f"Created {name} zone at ${price:.2f} ± ${zone_width/2:.2f}")
        
        return formatted