"""
Core Monte Carlo trade simulation logic
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from config import STOP_OFFSET, POSITION_CLOSE_TIME

logger = logging.getLogger(__name__)

class TradeSimulator:
    def __init__(self):
        """Initialize trade simulator"""
        self.trades = []
        self.trade_id = 0
    
    def run_monte_carlo_simulation(self, bars_df: pd.DataFrame, zones_list: List[Dict]) -> List[Dict]:
        """
        Run Monte Carlo simulation on all possible trades
        
        Args:
            bars_df: DataFrame of minute bars
            zones_list: List of zone dictionaries
            
        Returns:
            List of all simulated trades
        """
        all_trades = []
        
        # Group zones by date for faster lookup
        zones_by_date = {}
        for zone in zones_list:
            date_key = zone['date']
            if date_key not in zones_by_date:
                zones_by_date[date_key] = []
            zones_by_date[date_key].append(zone)
        
        # Iterate through every minute bar
        total_bars = len(bars_df)
        for entry_idx, (timestamp, entry_bar) in enumerate(bars_df.iterrows()):
            
            # Progress logging
            if entry_idx % 1000 == 0:
                logger.info(f"Processing bar {entry_idx}/{total_bars} ({entry_idx/total_bars*100:.1f}%)")
            
            # Time filter - only enter trades during valid hours
            if not self._is_valid_entry_time(timestamp):
                continue
            
            # Get zones active for this bar's date
            bar_date = timestamp.date().strftime('%Y-%m-%d')
            active_zones = zones_by_date.get(bar_date, [])
            
            # Test each zone independently
            for zone in active_zones:
                # Check if price interacted with zone
                bar_touched_zone = (
                    entry_bar['low'] <= zone['high'] and 
                    entry_bar['high'] >= zone['low']
                )
                
                if not bar_touched_zone:
                    continue
                
                # LONG SETUP - breakout above zone
                if entry_bar['high'] > zone['high']:
                    trade = self.simulate_single_trade(
                        future_bars=bars_df.iloc[entry_idx:],
                        entry_time=timestamp,
                        entry_price=zone['high'],
                        stop_price=zone['low'] - STOP_OFFSET,
                        direction='LONG',
                        zone=zone
                    )
                    if trade:
                        all_trades.append(trade)
                
                # SHORT SETUP - breakdown below zone
                if entry_bar['low'] < zone['low']:
                    trade = self.simulate_single_trade(
                        future_bars=bars_df.iloc[entry_idx:],
                        entry_time=timestamp,
                        entry_price=zone['low'],
                        stop_price=zone['high'] + STOP_OFFSET,
                        direction='SHORT',
                        zone=zone
                    )
                    if trade:
                        all_trades.append(trade)
        
        logger.info(f"Completed simulation. Generated {len(all_trades)} trades")
        return all_trades
    
    def simulate_single_trade(self, future_bars: pd.DataFrame, entry_time: datetime,
                         entry_price: float, stop_price: float, 
                         direction: str, zone: Dict) -> Optional[Dict]:
        """
        Simulate a single trade tracking highest/lowest prices
        
        Args:
            future_bars: Bars from entry forward
            entry_time: Entry timestamp
            entry_price: Entry price
            stop_price: Stop loss price
            direction: 'LONG' or 'SHORT'
            zone: Zone dictionary
            
        Returns:
            Trade result dictionary
        """
        # Initialize tracking variables
        highest_price = entry_price
        lowest_price = entry_price
        exit_price = None
        exit_time = None
        exit_reason = None
        bars_in_trade = 0
        
        # Walk forward through bars
        for idx, (timestamp, bar) in enumerate(future_bars.iterrows()):
            # Skip entry bar
            if idx == 0:
                continue
            
            bars_in_trade += 1
            
            # Update price extremes
            highest_price = max(highest_price, bar['high'])
            lowest_price = min(lowest_price, bar['low'])
            
            # Check stop hit (STOP TAKES PRECEDENCE)
            if direction == 'LONG' and bar['low'] <= stop_price:
                exit_price = stop_price
                exit_time = timestamp
                exit_reason = 'STOP_HIT'
                break
            elif direction == 'SHORT' and bar['high'] >= stop_price:
                exit_price = stop_price
                exit_time = timestamp
                exit_reason = 'STOP_HIT'
                break
            
            # Check time stop at 19:50 UTC
            if timestamp.time() >= POSITION_CLOSE_TIME:
                exit_price = bar['close']
                exit_time = timestamp
                exit_reason = 'TIME_EXIT'
                break
        
        # If we never exited (shouldn't happen), use last bar
        if exit_price is None:
            if len(future_bars) > 1:
                last_bar = future_bars.iloc[-1]
                exit_price = last_bar['close']
                exit_time = future_bars.index[-1]
                exit_reason = 'END_DATA'
            else:
                return None  # Can't simulate trade
        
        # Calculate metrics
        risk_per_unit = abs(entry_price - stop_price)
        
        if direction == 'LONG':
            max_favorable_excursion = highest_price - entry_price
            max_adverse_excursion = entry_price - lowest_price
            actual_pnl = exit_price - entry_price
        else:  # SHORT
            max_favorable_excursion = entry_price - lowest_price
            max_adverse_excursion = highest_price - entry_price
            actual_pnl = entry_price - exit_price
        
        # Calculate R-multiples
        mfe_r = max_favorable_excursion / risk_per_unit if risk_per_unit > 0 else 0
        mae_r = max_adverse_excursion / risk_per_unit if risk_per_unit > 0 else 0
        actual_r = actual_pnl / risk_per_unit if risk_per_unit > 0 else 0
        
        # Optimal R is the MFE_R
        optimal_r = mfe_r
        
        # Calculate time in trade
        time_in_trade = int((exit_time - entry_time).total_seconds() / 60)
        
        return {
        'entry_time': entry_time,
        'exit_time': exit_time,
        'entry_price': round(entry_price, 5),
        'stop_price': round(stop_price, 5),
        'exit_price': round(exit_price, 5),
        'exit_reason': exit_reason,
        'direction': direction,
        'zone_id': zone['id'],
        'zone_number': zone.get('zone_number', 0),  # ADD THIS LINE
        'zone_high': zone['high'],
        'zone_low': zone['low'],
        'zone_confluence_level': zone.get('confluence_level', 'L1'),  # ADD THIS
        'zone_confluence_score': zone.get('confluence_score', 0),     # ADD THIS
        'highest_price': round(highest_price, 5),
        'lowest_price': round(lowest_price, 5),
        'max_favorable_excursion': round(max_favorable_excursion, 5),
        'max_adverse_excursion': round(max_adverse_excursion, 5),
        'mfe_r_multiple': round(mfe_r, 3),
        'mae_r_multiple': round(mae_r, 3),
        'actual_r_multiple': round(actual_r, 3),
        'optimal_r_multiple': round(optimal_r, 3),
        'risk_per_unit': round(risk_per_unit, 5),
        'zone_size': round(zone['high'] - zone['low'], 5),
        'time_in_trade_minutes': time_in_trade,
        'entry_hour': entry_time.hour,
        'day_of_week': entry_time.weekday()
    }
    
    def _is_valid_entry_time(self, timestamp: datetime) -> bool:
        """Check if timestamp is during valid trading hours"""
        hour_decimal = timestamp.hour + timestamp.minute / 60
        # Trade between 13:30 and 19:30 UTC
        return 13.5 <= hour_decimal <= 19.5