"""
Enhanced Monte Carlo trade simulation logic with confluence integration
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from config import STOP_OFFSET, POSITION_CLOSE_TIME, CONFLUENCE_WEIGHTS

logger = logging.getLogger(__name__)

class TradeSimulator:
    def __init__(self):
        """Initialize enhanced trade simulator"""
        self.trades = []
        self.trade_id = 0
    
    def run_monte_carlo_simulation(self, bars_df: pd.DataFrame, zones_list: List[Dict]) -> List[Dict]:
        """
        Run enhanced Monte Carlo simulation with confluence weighting
        
        Args:
            bars_df: DataFrame of minute bars
            zones_list: List of enhanced zone dictionaries with confluence data
            
        Returns:
            List of all simulated trades with confluence metrics
        """
        all_trades = []
        
        # Group zones by date for faster lookup
        zones_by_date = {}
        for zone in zones_list:
            date_key = zone['date']
            if date_key not in zones_by_date:
                zones_by_date[date_key] = []
            zones_by_date[date_key].append(zone)
        
        # Sort zones by expected edge (prioritize high confluence)
        for date_key in zones_by_date:
            zones_by_date[date_key].sort(
                key=lambda z: z.get('expected_edge', 0), 
                reverse=True
            )
        
        total_bars = len(bars_df)
        logger.info(f"Starting simulation with {total_bars} bars and {len(zones_list)} zones")
        
        # Iterate through every minute bar
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
        Simulate a single trade with enhanced confluence metrics
        
        Args:
            future_bars: Bars from entry forward
            entry_time: Entry timestamp
            entry_price: Entry price
            stop_price: Stop loss price
            direction: 'LONG' or 'SHORT'
            zone: Enhanced zone dictionary with confluence data
            
        Returns:
            Enhanced trade result dictionary with confluence metrics
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
        
        # Calculate basic metrics
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
        
        # Calculate confluence-adjusted metrics
        confluence_multiplier = CONFLUENCE_WEIGHTS.get(zone.get('confluence_level', 'L1'), 1.0)
        weighted_optimal_r = optimal_r * confluence_multiplier
        
        # Calculate time in trade
        time_in_trade = int((exit_time - entry_time).total_seconds() / 60)
        
        # Build enhanced trade record
        trade_record = {
            # Basic trade data
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': round(entry_price, 5),
            'stop_price': round(stop_price, 5),
            'exit_price': round(exit_price, 5),
            'exit_reason': exit_reason,
            'direction': direction,
            
            # Zone identification
            'zone_id': zone['id'],
            'zone_number': zone.get('zone_number', 0),
            'zone_high': zone['high'],
            'zone_low': zone['low'],
            'zone_center': zone.get('center', (zone['high'] + zone['low']) / 2),
            'zone_size': round(zone['high'] - zone['low'], 5),
            
            # Enhanced confluence data
            'confluence_level': zone.get('confluence_level', 'L1'),
            'confluence_score': zone.get('confluence_score', 0),
            'confluence_count': zone.get('confluence_count', 0),
            'confluence_sources': zone.get('confluence_sources', []),
            'expected_edge': zone.get('expected_edge', 0),
            'risk_adjusted_score': zone.get('risk_adjusted_score', 0),
            
            # Price action metrics
            'highest_price': round(highest_price, 5),
            'lowest_price': round(lowest_price, 5),
            'max_favorable_excursion': round(max_favorable_excursion, 5),
            'max_adverse_excursion': round(max_adverse_excursion, 5),
            
            # R-multiple calculations
            'mfe_r_multiple': round(mfe_r, 3),
            'mae_r_multiple': round(mae_r, 3),
            'actual_r_multiple': round(actual_r, 3),
            'optimal_r_multiple': round(optimal_r, 3),
            'weighted_optimal_r': round(weighted_optimal_r, 3),
            'confluence_multiplier': round(confluence_multiplier, 3),
            
            # Trade metrics
            'risk_per_unit': round(risk_per_unit, 5),
            'time_in_trade_minutes': time_in_trade,
            'entry_hour': entry_time.hour,
            'entry_minute': entry_time.minute,
            'day_of_week': entry_time.weekday(),
            'bars_in_trade': bars_in_trade,
            
            # Additional confluence flags (for detailed analysis)
            'has_high_confluence': zone.get('confluence_score', 0) >= 8.0,
            'has_multiple_sources': zone.get('confluence_count', 0) >= 3,
            'confluence_flags': zone.get('confluence_flags', {})
        }
        
        return trade_record
    
    def _is_valid_entry_time(self, timestamp: datetime) -> bool:
        """Check if timestamp is during valid trading hours"""
        hour_decimal = timestamp.hour + timestamp.minute / 60
        # Trade between 13:30 and 19:30 UTC (9:30 AM - 3:30 PM ET)
        return 13.5 <= hour_decimal <= 19.5
    
    def _calculate_confluence_edge(self, zone: Dict) -> float:
        """Calculate expected edge based on confluence factors"""
        base_score = zone.get('confluence_score', 0)
        confluence_level = zone.get('confluence_level', 'L1')
        source_count = zone.get('confluence_count', 0)
        
        # Base edge from confluence score
        edge = base_score * 0.1
        
        # Multiplier from confluence level
        level_multiplier = CONFLUENCE_WEIGHTS.get(confluence_level, 1.0)
        edge *= level_multiplier
        
        # Bonus for multiple sources
        if source_count >= 3:
            edge *= 1.2
        elif source_count >= 2:
            edge *= 1.1
        
        # Bonus for specific high-value confluence types
        sources = zone.get('confluence_sources', [])
        high_value_sources = ['HVN_30D', 'CAM_MONTHLY', 'PDH', 'PDL', 'VWAP']
        high_value_count = sum(1 for source in sources if any(hvs in source.upper() for hvs in high_value_sources))
        
        if high_value_count >= 2:
            edge *= 1.3
        elif high_value_count >= 1:
            edge *= 1.15
        
        return min(edge, 10.0)  # Cap at 10.0