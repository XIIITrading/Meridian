"""
Minute-level data analysis for backtesting
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import pytz  # Add this import

from core.models import ManualTradeEntry, TradeMetrics, ExitReason

logger = logging.getLogger(__name__)

class MinuteDataAnalyzer:
    """Analyzes minute-level price data for trade metrics"""
    
    def __init__(self, polygon_fetcher):
        """
        Initialize with Polygon data fetcher
        
        Args:
            polygon_fetcher: Instance of PolygonBacktestFetcher
        """
        self.fetcher = polygon_fetcher
    
    def fetch_trade_period_data(self, ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Fetch minute bars for the trade period
        
        Args:
            ticker: Stock symbol
            start: Start datetime (entry time)
            end: End datetime (exit time)
            
        Returns:
            DataFrame with minute bars
        """
        try:
            # Ensure datetimes are timezone-aware (UTC)
            if start.tzinfo is None:
                start = pytz.UTC.localize(start)
            if end.tzinfo is None:
                end = pytz.UTC.localize(end)
            
            # Add buffer for analysis (5 minutes before and after)
            buffer_start = start - timedelta(minutes=5)
            buffer_end = end + timedelta(minutes=5)
            
            # Fetch minute bars
            df = self.fetcher.fetch_minute_bars(
                ticker=ticker,
                start_time=buffer_start,
                end_time=buffer_end
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching trade period data: {e}")
            return pd.DataFrame()
    
    def calculate_trade_metrics(self, trade: ManualTradeEntry, minute_data: pd.DataFrame) -> TradeMetrics:
        """
        Calculate detailed trade metrics from minute data
        """
        if minute_data.empty:
            logger.warning("No minute data available for metrics calculation")
            return self._create_basic_metrics(trade)
        
        try:
            # Ensure trade times are timezone-aware for comparison
            entry_time = trade.entry_candle_time
            exit_time = trade.exit_candle_time
            
            if entry_time.tzinfo is None:
                entry_time = pytz.UTC.localize(entry_time)
            if exit_time.tzinfo is None:
                exit_time = pytz.UTC.localize(exit_time)
            
            # Filter data to trade period
            trade_data = minute_data[(minute_data.index >= entry_time) & 
                                    (minute_data.index <= exit_time)].copy()
            
            if trade_data.empty:
                logger.warning("No data within trade period")
                return self._create_basic_metrics(trade)
            
            # DEBUG: Log trade parameters
            logger.debug(f"Trade direction: {trade.trade_direction.value}")
            logger.debug(f"Entry price: {trade.entry_price}, Stop: {trade.stop_price}, Target: {trade.target_price}")
            logger.debug(f"Trade data has {len(trade_data)} bars")
            
            # Calculate MFE/MAE based on direction
            if trade.trade_direction.value == 'long':
                # For long trades
                trade_data['excursion'] = trade_data['high'] - trade.entry_price
                trade_data['adverse'] = trade.entry_price - trade_data['low']
                
                mfe_price = trade_data['high'].max()
                mae_price = trade_data['low'].min()
                
            else:  # short
                # For short trades
                trade_data['excursion'] = trade.entry_price - trade_data['low']
                trade_data['adverse'] = trade_data['high'] - trade.entry_price
                
                mfe_price = trade_data['low'].min()
                mae_price = trade_data['high'].max()
            
            # Calculate max favorable and adverse excursions
            mfe = trade_data['excursion'].max()
            mae = trade_data['adverse'].max()
            
            # Calculate R-multiples
            risk_per_share = abs(trade.entry_price - trade.stop_price)
            mfe_r = mfe / risk_per_share if risk_per_share > 0 else 0
            mae_r = mae / risk_per_share if risk_per_share > 0 else 0
            
            # Actual trade result
            if trade.trade_direction.value == 'long':
                trade_result_per_share = trade.exit_price - trade.entry_price
            else:
                trade_result_per_share = trade.entry_price - trade.exit_price
            
            trade_result = trade_result_per_share * trade.shares
            r_multiple = trade_result_per_share / risk_per_share if risk_per_share > 0 else 0
            
            # Determine exit reason
            exit_reason = self._determine_exit_reason(
                trade, trade_data, mfe_price, mae_price
            )
            
            # Calculate efficiency (how much of MFE was captured)
            efficiency = abs(r_multiple / mfe_r) if mfe_r > 0 else 0
            
            # Find time to key events - ENHANCED WITH DEBUGGING
            minutes_to_target = None
            minutes_to_stop = None
            
            for i, (timestamp, row) in enumerate(trade_data.iterrows()):
                # Check if target was hit
                if trade.trade_direction.value == 'long':
                    # DEBUG: Log first few bars
                    if i < 3:
                        logger.debug(f"Bar {i+1}: High={row['high']:.2f}, Low={row['low']:.2f}, Target={trade.target_price:.2f}, Stop={trade.stop_price:.2f}")
                    
                    if row['high'] >= trade.target_price and minutes_to_target is None:
                        minutes_to_target = i + 1
                        logger.debug(f"Target hit at minute {minutes_to_target}")
                        
                    if row['low'] <= trade.stop_price and minutes_to_stop is None:
                        minutes_to_stop = i + 1
                        logger.debug(f"Stop hit at minute {minutes_to_stop}")
                        
                else:  # short
                    # DEBUG: Log first few bars
                    if i < 3:
                        logger.debug(f"Bar {i+1}: High={row['high']:.2f}, Low={row['low']:.2f}, Target={trade.target_price:.2f}, Stop={trade.stop_price:.2f}")
                    
                    if row['low'] <= trade.target_price and minutes_to_target is None:
                        minutes_to_target = i + 1
                        logger.debug(f"Target hit at minute {minutes_to_target}")
                        
                    if row['high'] >= trade.stop_price and minutes_to_stop is None:
                        minutes_to_stop = i + 1
                        logger.debug(f"Stop hit at minute {minutes_to_stop}")
            
            # Calculate total minutes in trade (market hours only) - ENHANCED
            total_minutes_in_trade = self.calculate_market_minutes(trade_data)
            minutes_to_exit = len(trade_data)  # Keep raw count for comparison
            
            # DEBUG
            logger.debug(f"Total minutes in trade (market hours): {total_minutes_in_trade}")
            logger.debug(f"Total bars in trade data: {minutes_to_exit}")
            
            # Find first profitable and negative minutes - ENHANCED
            first_profitable = None
            first_negative = None
            
            for i, (timestamp, row) in enumerate(trade_data.iterrows()):
                mid_price = (row['high'] + row['low']) / 2
                
                if trade.trade_direction.value == 'long':
                    pnl = mid_price - trade.entry_price
                else:
                    pnl = trade.entry_price - mid_price
                
                # DEBUG: Log first few PnL calculations
                if i < 3:
                    logger.debug(f"Bar {i+1}: Mid price={mid_price:.2f}, PnL={pnl:.4f}")
                
                if pnl > 0 and first_profitable is None:
                    first_profitable = i + 1
                    logger.debug(f"First profitable at minute {first_profitable}")
                    
                if pnl < 0 and first_negative is None:
                    first_negative = i + 1
                    logger.debug(f"First negative at minute {first_negative}")
            
            # Calculate pivot strength using full minute data
            pivot_strength = self.calculate_pivot_strength(
                entry_price=trade.entry_price,
                entry_time=trade.entry_candle_time,
                minute_data=minute_data,
                direction=trade.trade_direction.value
            )
            
            # Get actual exit time (last bar in trade period)
            actual_exit_time = trade_data.index[-1]
            
            # Create metrics object with all fields
            metrics = TradeMetrics(
                max_favorable_excursion=float(mfe),
                max_adverse_excursion=float(mae),
                mfe_r_multiple=float(mfe_r),
                mae_r_multiple=float(mae_r),
                trade_result=float(trade_result),
                r_multiple=float(r_multiple),
                efficiency_ratio=float(efficiency),
                actual_exit_time=actual_exit_time.to_pydatetime(),
                exit_reason=exit_reason,
                minutes_to_target=minutes_to_target,
                minutes_to_stop=minutes_to_stop,
                minutes_to_exit=minutes_to_exit,
                total_minutes_in_trade=total_minutes_in_trade,
                pivot_strength=pivot_strength,
                highest_price=float(trade_data['high'].max()),
                lowest_price=float(trade_data['low'].min()),
                first_profitable_minute=first_profitable,
                first_negative_minute=first_negative
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating trade metrics: {e}")
            import traceback
            traceback.print_exc()
            return self._create_basic_metrics(trade)
    
    def _create_basic_metrics(self, trade: ManualTradeEntry) -> TradeMetrics:
        """Create basic metrics when minute data is not available"""
        # Calculate basic metrics from trade entry/exit
        if trade.trade_direction.value == 'long':
            trade_result_per_share = trade.exit_price - trade.entry_price
        else:
            trade_result_per_share = trade.entry_price - trade.exit_price
        
        trade_result = trade_result_per_share * trade.shares
        risk_per_share = abs(trade.entry_price - trade.stop_price)
        r_multiple = trade_result_per_share / risk_per_share if risk_per_share > 0 else 0
        
        # Determine basic exit reason
        if abs(trade.exit_price - trade.target_price) < 0.01:
            exit_reason = ExitReason.TARGET_HIT
        elif abs(trade.exit_price - trade.stop_price) < 0.01:
            exit_reason = ExitReason.STOP_HIT
        else:
            exit_reason = ExitReason.MANUAL_EXIT
        
        return TradeMetrics(
            max_favorable_excursion=0,
            max_adverse_excursion=0,
            mfe_r_multiple=0,
            mae_r_multiple=0,
            trade_result=float(trade_result),
            r_multiple=float(r_multiple),
            efficiency_ratio=0,
            actual_exit_time=trade.exit_candle_time,
            exit_reason=exit_reason,
            minutes_to_target=None,
            minutes_to_stop=None,
            minutes_to_exit=None,
            total_minutes_in_trade=None,  # ADD THIS
            pivot_strength=None,  # ADD THIS
            highest_price=float(trade.entry_price),
            lowest_price=float(trade.entry_price),
            first_profitable_minute=None,
            first_negative_minute=None
        )
    
    def _determine_exit_reason(self, trade: ManualTradeEntry, 
                              trade_data: pd.DataFrame,
                              mfe_price: float, 
                              mae_price: float) -> ExitReason:
        """Determine the reason for trade exit"""
        # Check if stop was hit
        if trade.trade_direction.value == 'long':
            if mae_price <= trade.stop_price:
                return ExitReason.STOP_HIT
            if mfe_price >= trade.target_price:
                if abs(trade.exit_price - trade.target_price) < 0.50:
                    return ExitReason.TARGET_HIT
                else:
                    return ExitReason.PARTIAL_TARGET
        else:  # short
            if mae_price >= trade.stop_price:
                return ExitReason.STOP_HIT
            if mfe_price <= trade.target_price:
                if abs(trade.exit_price - trade.target_price) < 0.50:
                    return ExitReason.TARGET_HIT
                else:
                    return ExitReason.PARTIAL_TARGET
        
        # Check if it was a time exit
        if len(trade_data) > 0:
            last_time = trade_data.index[-1]
            if last_time.time() >= pd.Timestamp("20:50", tz=last_time.tz).time():
                return ExitReason.TIME_EXIT
        
        return ExitReason.MANUAL_EXIT
    
    def calculate_pivot_strength(self, entry_price: float, entry_time: datetime, 
                            minute_data: pd.DataFrame, direction: str,
                            lookback: int = 10) -> int:
        """
        Calculate strength of pivot structure at entry
        
        Args:
            entry_price: Trade entry price
            entry_time: Entry timestamp
            minute_data: Full minute data including pre-entry
            direction: 'long' or 'short'
            lookback: Bars to analyze before entry
            
        Returns:
            Pivot strength score (0-10)
        """
        try:
            # Get bars before entry
            if entry_time.tzinfo is None:
                entry_time = pytz.UTC.localize(entry_time)
            
            pre_entry = minute_data[minute_data.index < entry_time].tail(lookback)
            
            if len(pre_entry) < 3:
                return 0
            
            strength = 0
            
            # 1. Check for pivot structure (0-3 points)
            highs = pre_entry['high'].values
            lows = pre_entry['low'].values
            
            if len(highs) >= 3:
                if direction == 'short':
                    # Look for pivot high: high[1] > high[0] and high[1] > high[2]
                    for i in range(1, len(highs) - 1):
                        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                            # Found pivot high
                            strength += 3
                            break
                else:  # long
                    # Look for pivot low: low[1] < low[0] and low[1] < low[2]
                    for i in range(1, len(lows) - 1):
                        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                            # Found pivot low
                            strength += 3
                            break
            
            # 2. Volume surge at pivot (0-3 points)
            if 'volume' in pre_entry.columns and len(pre_entry) > 0:
                avg_volume = pre_entry['volume'].mean()
                last_few_bars = pre_entry.tail(3)
                
                if len(last_few_bars) > 0:
                    max_recent_volume = last_few_bars['volume'].max()
                    if avg_volume > 0:
                        volume_ratio = max_recent_volume / avg_volume
                        if volume_ratio > 2.0:
                            strength += 3
                        elif volume_ratio > 1.5:
                            strength += 2
                        elif volume_ratio > 1.2:
                            strength += 1
            
            # 3. Price rejection wicks (0-2 points)
            last_bar = pre_entry.iloc[-1]
            bar_range = last_bar['high'] - last_bar['low']
            body = abs(last_bar['close'] - last_bar['open'])
            
            if bar_range > 0:
                wick_ratio = (bar_range - body) / bar_range
                
                # Check if wick is in right direction
                if direction == 'long':
                    lower_wick = last_bar['open'] - last_bar['low'] if last_bar['close'] > last_bar['open'] else last_bar['close'] - last_bar['low']
                    if lower_wick > body * 0.5:  # Lower wick > 50% of body
                        strength += 2 if wick_ratio > 0.6 else 1
                else:  # short
                    upper_wick = last_bar['high'] - last_bar['close'] if last_bar['close'] > last_bar['open'] else last_bar['high'] - last_bar['open']
                    if upper_wick > body * 0.5:  # Upper wick > 50% of body
                        strength += 2 if wick_ratio > 0.6 else 1
            
            # 4. Price level confluence (0-2 points)
            # Check for round numbers
            cents = (entry_price * 100) % 100
            if cents <= 10 or cents >= 90:  # Within 10 cents of round dollar
                strength += 1
            if cents <= 5 or cents >= 95:  # Within 5 cents of round dollar
                strength += 1
            
            return min(strength, 10)
            
        except Exception as e:
            logger.error(f"Error calculating pivot strength: {e}")
            return 0

    def calculate_market_minutes(self, trade_data: pd.DataFrame) -> int:
        """
        Calculate minutes during regular market hours only
        
        Args:
            trade_data: DataFrame of minute bars during trade
            
        Returns:
            Number of minutes during market hours (9:30-16:00 ET)
        """
        try:
            if trade_data.empty:
                return 0
            
            # Convert to Eastern time for market hours check
            eastern = pytz.timezone('US/Eastern')
            trade_data_et = trade_data.copy()
            trade_data_et.index = trade_data_et.index.tz_convert(eastern)
            
            # Filter for market hours (9:30 AM - 4:00 PM ET)
            market_open = pd.Timestamp("09:30", tz=eastern).time()
            market_close = pd.Timestamp("16:00", tz=eastern).time()
            
            market_minutes = 0
            for timestamp in trade_data_et.index:
                if market_open <= timestamp.time() < market_close:
                    market_minutes += 1
            
            return market_minutes
            
        except Exception as e:
            logger.error(f"Error calculating market minutes: {e}")
            return len(trade_data)  # Fallback to total minutes