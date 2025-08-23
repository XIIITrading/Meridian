"""
Handles all database operations for backtest trades
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
from uuid import UUID

from core.models import ManualTradeEntry, TradeMetrics, ZoneMatch
from data.supabase_client import BacktestSupabaseClient

class BacktestStorageManager:
    """Manages database operations for backtesting"""
    
    def __init__(self, supabase_client: BacktestSupabaseClient):
        self.client = supabase_client
    
    def get_or_create_session(self, ticker_id: str) -> Dict:
        """
        Get existing session or create new one for ticker_id
        
        Args:
            ticker_id: Ticker ID (e.g., "AMD.121824")
            
        Returns:
            Session record dictionary
        """
        # Check if session exists
        existing = self.client.client.table('analysis_sessions').select('*').eq(
            'ticker_id', ticker_id
        ).execute()
        
        if existing.data:
            return existing.data[0]
        
        # Parse ticker_id to get components
        parts = ticker_id.split('.')
        ticker = parts[0]
        date_str = parts[1]
        
        # Convert date string to date
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = 2000 + int(date_str[4:6])
        session_date = datetime(year, month, day).date()
        
        # Get levels_zones record
        levels_zones = self.client.client.table('levels_zones').select('id').eq(
            'ticker_id', ticker_id
        ).execute()
        
        levels_zones_id = levels_zones.data[0]['id'] if levels_zones.data else None
        
        # Create new session
        new_session = {
            'ticker_id': ticker_id,
            'ticker': ticker,
            'session_date': str(session_date),
            'levels_zones_id': levels_zones_id,
            'session_name': f"{ticker} Analysis - {session_date}"
        }
        
        result = self.client.client.table('analysis_sessions').insert(
            new_session
        ).execute()
        
        return result.data[0]
    
    def save_trade(self, 
               ticker_id: str,
               trade: ManualTradeEntry,
               zone_match: Optional[ZoneMatch],
               metrics: Optional[TradeMetrics],
               trade_type: str = 'manual') -> str:
        """
        Save a trade entry with all calculated metrics
        
        Args:
            ticker_id: Ticker ID for the trade
            trade: Trade entry data
            zone_match: Zone alignment results
            metrics: Calculated trade metrics
            trade_type: 'manual' or 'automated'
            
        Returns:
            Saved trade ID
        """
        # Get or create session
        session = self.get_or_create_session(ticker_id)
        
        # Parse trade date from ticker_id
        parts = ticker_id.split('.')
        date_str = parts[1]
        month = int(date_str[0:2])
        day = int(date_str[2:4])
        year = 2000 + int(date_str[4:6])
        trade_date = datetime(year, month, day).date()
        
        # Build trade record
        trade_record = {
            'analysis_session_id': session['session_id'],
            'ticker_id': ticker_id,
            'ticker': trade.ticker,
            'trade_date': str(trade_date),
            'trade_type': trade_type,
            
            # User inputs
            'entry_candle_time': trade.entry_candle_time.isoformat(),
            'exit_candle_time': trade.exit_candle_time.isoformat(),
            'trade_direction': trade.trade_direction.value,
            'entry_price': trade.entry_price,
            'stop_price': trade.stop_price,
            'target_price': trade.target_price,
            'exit_price': trade.exit_price,
            
            # Position info
            'shares': trade.shares,
            'fixed_risk': trade.fixed_risk,
            'position_value': trade.entry_price * trade.shares,
            'risk_reward_ratio': trade.risk_reward_ratio,
            
            # Notes
            'notes': trade.notes
        }
        
        # Add zone information if available
        if zone_match:
            trade_record.update({
                'zone_number': zone_match.zone_number,
                'zone_type': zone_match.zone_type,
                'zone_confluence_level': zone_match.confluence_level,
                'zone_confluence_score': zone_match.confluence_score,
                'confluence_sources': zone_match.confluence_sources,
                'distance_from_zone_ticks': zone_match.distance_from_zone_ticks,
                'zone_high': zone_match.zone_high,
                'zone_low': zone_match.zone_low,
                'zone_validated': zone_match.is_valid_entry
            })
        
        # Add metrics if available
        if metrics:
            trade_record.update({
                'max_favorable_excursion': metrics.max_favorable_excursion,
                'max_adverse_excursion': metrics.max_adverse_excursion,
                'mfe_r_multiple': metrics.mfe_r_multiple,
                'mae_r_multiple': metrics.mae_r_multiple,
                'trade_result': metrics.trade_result,
                'r_multiple': metrics.r_multiple,
                'efficiency_ratio': metrics.efficiency_ratio,
                'actual_exit_time': metrics.actual_exit_time.isoformat(),
                'exit_reason': metrics.exit_reason.value,
                'minutes_to_target': metrics.minutes_to_target,
                'minutes_to_stop': metrics.minutes_to_stop,
                'total_minutes_in_trade': metrics.total_minutes_in_trade,
                'pivot_strength': metrics.pivot_strength,
                'highest_price': metrics.highest_price,
                'lowest_price': metrics.lowest_price,
                'first_profitable_minute': metrics.first_profitable_minute,
                'first_negative_minute': metrics.first_negative_minute,
                'minute_data_complete': True
            })
        
        # Save to database
        result = self.client.client.table('backtest_trades').insert(
            trade_record
        ).execute()
        
        trade_id = result.data[0]['trade_id']
        
        # Update session statistics in Python (replacing database trigger)
        self.update_session_metrics(session['session_id'])
        
        return trade_id
    
    def get_session_trades(self, ticker_id: str, trade_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get all trades for a ticker_id
        
        Args:
            ticker_id: Ticker ID to query
            trade_type: Optional filter for 'manual' or 'automated' trades
            
        Returns:
            DataFrame with trade data
        """
        # Get session
        session = self.client.client.table('analysis_sessions').select('session_id').eq(
            'ticker_id', ticker_id
        ).execute()
        
        if not session.data:
            return pd.DataFrame()
        
        session_id = session.data[0]['session_id']
        
        # Build query
        query = self.client.client.table('backtest_trades').select('*').eq(
            'analysis_session_id', session_id
        )
        
        # Add trade_type filter if specified
        if trade_type:
            query = query.eq('trade_type', trade_type)
        
        # Execute query
        trades = query.order('entry_candle_time').execute()
        
        if not trades.data:
            return pd.DataFrame()
        
        return pd.DataFrame(trades.data)
    
    def get_all_trades(self, 
                      ticker: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      trade_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get trades across multiple sessions with filters
        
        Args:
            ticker: Optional ticker filter
            start_date: Optional start date filter
            end_date: Optional end date filter  
            trade_type: Optional 'manual' or 'automated' filter
            
        Returns:
            DataFrame with trade data
        """
        query = self.client.client.table('backtest_trades').select('*')
        
        if ticker:
            query = query.eq('ticker', ticker)
        
        if start_date:
            query = query.gte('trade_date', start_date.strftime('%Y-%m-%d'))
        
        if end_date:
            query = query.lte('trade_date', end_date.strftime('%Y-%m-%d'))
        
        if trade_type:
            query = query.eq('trade_type', trade_type)
        
        result = query.order('entry_candle_time').execute()
        
        if not result.data:
            return pd.DataFrame()
        
        return pd.DataFrame(result.data)
    
    def get_session_summary(self, ticker_id: str) -> Dict:
        """
        Get session summary statistics
        
        Args:
            ticker_id: Ticker ID
            
        Returns:
            Dictionary with session statistics
        """
        session = self.client.client.table('analysis_sessions').select('*').eq(
            'ticker_id', ticker_id
        ).execute()
        
        if not session.data:
            return {}
        
        return session.data[0]
    
    def get_levels_zones_data(self, ticker_id: str) -> Dict:
        """
        Get levels and zones data for a ticker_id
        
        Args:
            ticker_id: Ticker ID
            
        Returns:
            Dictionary with levels_zones record
        """
        result = self.client.client.table('levels_zones').select('*').eq(
            'ticker_id', ticker_id
        ).execute()
        
        if result.data:
            return result.data[0]
        
        return {}
    
    def save_minute_bars(self, ticker: str, bars: pd.DataFrame):
        """
        Cache minute bar data
        
        Args:
            ticker: Stock symbol
            bars: DataFrame with minute bars
        """
        if bars.empty:
            return
        
        # Prepare records
        records = []
        for timestamp, row in bars.iterrows():
            records.append({
                'ticker': ticker,
                'bar_timestamp': timestamp.isoformat(),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': int(row.get('volume', 0)),
                'vwap': row.get('vwap')
            })
        
        # Bulk insert (upsert to handle duplicates)
        self.client.client.table('minute_bars_cache').upsert(
            records
        ).execute()
    
    def delete_trade(self, trade_id: str) -> bool:
        """
        Delete a trade by ID
        
        Args:
            trade_id: UUID of trade to delete
            
        Returns:
            True if successful
        """
        result = self.client.client.table('backtest_trades').delete().eq(
            'trade_id', trade_id
        ).execute()
        
        return len(result.data) > 0
    
    def update_trade_notes(self, trade_id: str, notes: str) -> bool:
        """
        Update notes for a trade
        
        Args:
            trade_id: UUID of trade
            notes: New notes text
            
        Returns:
            True if successful
        """
        result = self.client.client.table('backtest_trades').update({
            'notes': notes,
            'updated_at': datetime.now().isoformat()
        }).eq('trade_id', trade_id).execute()
        
        return len(result.data) > 0
    
    def update_session_metrics(self, session_id: str) -> None:
        """
        Update session statistics based on all trades in the session
        
        Args:
            session_id: The session UUID to update
        """
        # Get all trades for this session
        trades_query = self.client.client.table('backtest_trades').select('*').eq(
            'analysis_session_id', session_id
        ).order('entry_candle_time').execute()
        
        trades = trades_query.data if trades_query.data else []
        
        # Calculate statistics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.get('trade_result', 0) > 0)
        losing_trades = sum(1 for t in trades if t.get('trade_result', 0) <= 0)
        total_pnl = sum(t.get('trade_result', 0) for t in trades)
        
        # Calculate win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average R-multiple (excluding None values)
        r_multiples = [t.get('r_multiple') for t in trades if t.get('r_multiple') is not None]
        avg_r_multiple = sum(r_multiples) / len(r_multiples) if r_multiples else None
        
        # Calculate additional metrics
        avg_winner = None
        avg_loser = None
        profit_factor = None
        max_drawdown = 0
        
        if winning_trades > 0:
            winning_pnl = [t.get('trade_result', 0) for t in trades if t.get('trade_result', 0) > 0]
            avg_winner = sum(winning_pnl) / len(winning_pnl)
        
        if losing_trades > 0:
            losing_pnl = [abs(t.get('trade_result', 0)) for t in trades if t.get('trade_result', 0) < 0]
            avg_loser = sum(losing_pnl) / len(losing_pnl)
            
            # Calculate profit factor
            total_wins = sum(t.get('trade_result', 0) for t in trades if t.get('trade_result', 0) > 0)
            total_losses = abs(sum(t.get('trade_result', 0) for t in trades if t.get('trade_result', 0) < 0))
            profit_factor = (total_wins / total_losses) if total_losses > 0 else None
        
        # Calculate max drawdown if we have trades
        if trades:
            cumulative_pnl = 0
            peak = 0
            max_drawdown = 0
            
            for trade in trades:
                cumulative_pnl += trade.get('trade_result', 0)
                
                # Update peak if we have a new high
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                
                # Calculate drawdown from peak
                drawdown = peak - cumulative_pnl
                
                # Update max drawdown if this is worse
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # Update the session
        update_data = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': round(total_pnl, 2) if total_pnl else 0,
            'win_rate': round(win_rate, 2),
            'avg_r_multiple': round(avg_r_multiple, 2) if avg_r_multiple else None,
            'avg_winner': round(avg_winner, 2) if avg_winner else None,
            'avg_loser': round(avg_loser, 2) if avg_loser else None,
            'profit_factor': round(profit_factor, 2) if profit_factor else None,
            'max_drawdown': round(max_drawdown, 2),
            'updated_at': datetime.now().isoformat()
        }
        
        self.client.client.table('analysis_sessions').update(
            update_data
        ).eq('session_id', session_id).execute()