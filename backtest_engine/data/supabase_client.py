# data/supabase_client.py
"""
Supabase client for backtesting database operations
With caching support for Polygon data
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid

from supabase import create_client, Client
import pandas as pd

from core.models import (
    BacktestSession, ZoneDetail, MarketContext, 
    EntrySignal, TradeExecution, PerformanceMetrics
)

logger = logging.getLogger(__name__)

class BacktestSupabaseClient:
    """Extended Supabase client for backtesting operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    # ============= Levels/Zones Operations =============
    
    def get_levels_zones_record(self, ticker: str, session_date: date) -> Optional[Dict]:
        """Fetch a levels_zones record by ticker and date"""
        try:
            response = self.client.table('levels_zones')\
                .select("*")\
                .eq('ticker', ticker)\
                .eq('session_date', session_date.isoformat())\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            logger.warning(f"No levels_zones record found for {ticker} on {session_date}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching levels_zones record: {e}")
            return None
    
    def get_levels_zones_by_id(self, record_id: str) -> Optional[Dict]:
        """Fetch a levels_zones record by ID"""
        try:
            response = self.client.table('levels_zones')\
                .select("*")\
                .eq('id', record_id)\
                .single()\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching levels_zones by ID: {e}")
            return None
    
    def list_available_sessions(self, ticker: Optional[str] = None, 
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> List[Dict]:
        """List available levels_zones records for backtesting"""
        try:
            query = self.client.table('levels_zones').select("id, ticker, session_date, analysis_status")
            
            if ticker:
                query = query.eq('ticker', ticker)
            if start_date:
                query = query.gte('session_date', start_date.isoformat())
            if end_date:
                query = query.lte('session_date', end_date.isoformat())
            
            response = query.order('session_date', desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    # ============= Backtest Session Operations =============
    
    def create_backtest_session(self, session: BacktestSession) -> str:
        """Create a new backtest session"""
        try:
            data = session.to_db_dict()
            
            response = self.client.table('backtest_sessions')\
                .insert(data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                session_id = response.data[0]['id']
                logger.info(f"Created backtest session: {session_id}")
                return session_id
            
            raise Exception("Failed to create backtest session")
            
        except Exception as e:
            logger.error(f"Error creating backtest session: {e}")
            raise
    
    def update_backtest_session(self, session_id: str, updates: Dict) -> bool:
        """Update a backtest session"""
        try:
            response = self.client.table('backtest_sessions')\
                .update(updates)\
                .eq('id', session_id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error updating backtest session: {e}")
            return False
    
    def get_backtest_session(self, session_id: str) -> Optional[Dict]:
        """Get a backtest session by ID"""
        try:
            response = self.client.table('backtest_sessions')\
                .select("*")\
                .eq('id', session_id)\
                .single()\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching backtest session: {e}")
            return None
    
    # ============= Entry Signals Operations =============
    
    def save_entry_signals(self, signals: List[EntrySignal]) -> bool:
        """Bulk save entry signals"""
        try:
            if not signals:
                return True
            
            data = []
            for signal in signals:
                signal_dict = {
                    'session_id': signal.session_id,
                    'signal_timestamp': signal.signal_timestamp.isoformat(),
                    'signal_type': signal.signal_type.value if signal.signal_type else None,
                    'pivot_strength': signal.pivot_strength,
                    'm5_open': float(signal.m5_open) if signal.m5_open else None,
                    'm5_high': float(signal.m5_high) if signal.m5_high else None,
                    'm5_low': float(signal.m5_low) if signal.m5_low else None,
                    'm5_close': float(signal.m5_close) if signal.m5_close else None,
                    'm5_volume': signal.m5_volume,
                    'm5_vwap': float(signal.m5_vwap) if signal.m5_vwap else None,
                    'zone_number': signal.zone_number,
                    'zone_high': float(signal.zone_high) if signal.zone_high else None,
                    'zone_low': float(signal.zone_low) if signal.zone_low else None,
                    'zone_confluence_level': signal.zone_confluence_level,
                    'zone_confluence_score': float(signal.zone_confluence_score) if signal.zone_confluence_score else None,
                    'distance_to_zone_ticks': float(signal.distance_to_zone_ticks) if signal.distance_to_zone_ticks else None,
                    'is_valid': signal.is_valid,
                    'validation_reason': signal.validation_reason,
                    'user_marked': signal.user_marked,
                    'calculation_details': json.dumps(signal.calculation_details)
                }
                data.append(signal_dict)
            
            response = self.client.table('backtest_entry_signals')\
                .insert(data)\
                .execute()
            
            logger.info(f"Saved {len(signals)} entry signals")
            return True
            
        except Exception as e:
            logger.error(f"Error saving entry signals: {e}")
            return False
    
    def get_entry_signals(self, session_id: str) -> List[Dict]:
        """Get all entry signals for a session"""
        try:
            response = self.client.table('backtest_entry_signals')\
                .select("*")\
                .eq('session_id', session_id)\
                .order('signal_timestamp')\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error fetching entry signals: {e}")
            return []
    
    # ============= Trade Operations =============
    
    def save_trade(self, trade: TradeExecution) -> Optional[str]:
        """Save a single trade"""
        try:
            data = {
                'session_id': trade.session_id,
                'entry_signal_id': trade.entry_signal_id,
                'trade_number': trade.trade_number,
                'trade_direction': trade.trade_direction,
                'entry_timestamp': trade.entry_timestamp.isoformat(),
                'entry_price': float(trade.entry_price),
                'entry_zone_number': trade.entry_zone_number,
                'entry_confluence_level': trade.entry_confluence_level,
                'entry_confluence_score': float(trade.entry_confluence_score) if trade.entry_confluence_score else None,
                'entry_slippage': float(trade.entry_slippage),
                'position_size': trade.position_size,
                'risk_amount': float(trade.risk_amount) if trade.risk_amount else None,
                'initial_stop_price': float(trade.initial_stop_price),
                'current_stop_price': float(trade.current_stop_price) if trade.current_stop_price else None,
                'target1_price': float(trade.target_prices[0]) if len(trade.target_prices) > 0 else None,
                'target2_price': float(trade.target_prices[1]) if len(trade.target_prices) > 1 else None,
                'target3_price': float(trade.target_prices[2]) if len(trade.target_prices) > 2 else None,
                'status': trade.status,
                'bar_data': json.dumps(trade.bar_data),
                'trade_metadata': json.dumps({})
            }
            
            # Add exit data if trade is closed
            if trade.exit_timestamp:
                data.update({
                    'exit_timestamp': trade.exit_timestamp.isoformat(),
                    'exit_price': float(trade.exit_price),
                    'exit_reason': trade.exit_reason,
                    'exit_slippage': float(trade.exit_slippage),
                    'pnl_dollars': float(trade.pnl_dollars),
                    'pnl_ticks': float(trade.pnl_ticks),
                    'pnl_r_multiple': float(trade.pnl_r_multiple),
                    'is_winner': trade.is_winner,
                    'duration_minutes': trade.duration_minutes
                })
            
            # Add MFE/MAE if available
            if trade.mfe_price:
                data.update({
                    'mfe_price': float(trade.mfe_price),
                    'mfe_r_multiple': float(trade.mfe_r_multiple),
                    'mae_price': float(trade.mae_price),
                    'mae_r_multiple': float(trade.mae_r_multiple)
                })
            
            response = self.client.table('backtest_trades')\
                .insert(data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return None
    
    def update_trade(self, trade_id: str, updates: Dict) -> bool:
        """Update a trade"""
        try:
            response = self.client.table('backtest_trades')\
                .update(updates)\
                .eq('id', trade_id)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            return False
    
    def get_session_trades(self, session_id: str) -> List[Dict]:
        """Get all trades for a session"""
        try:
            response = self.client.table('backtest_trades')\
                .select("*")\
                .eq('session_id', session_id)\
                .order('entry_timestamp')\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error fetching session trades: {e}")
            return []
    
    # ============= Performance Operations =============
    
    def save_performance_metrics(self, metrics: PerformanceMetrics) -> bool:
        """Save or update performance metrics for a session"""
        try:
            data = {
                'session_id': metrics.session_id,
                'total_trades': metrics.total_trades,
                'winning_trades': metrics.winning_trades,
                'losing_trades': metrics.losing_trades,
                'win_rate': float(metrics.win_rate),
                'gross_pnl': float(metrics.gross_pnl),
                'net_pnl': float(metrics.net_pnl),
                'avg_win_dollars': float(metrics.avg_win),
                'avg_loss_dollars': float(metrics.avg_loss),
                'profit_factor': float(metrics.profit_factor),
                'avg_win_r': float(metrics.avg_win_r),
                'avg_loss_r': float(metrics.avg_loss_r),
                'max_drawdown_dollars': float(metrics.max_drawdown),
                'sharpe_ratio': float(metrics.sharpe_ratio),
                'sortino_ratio': float(metrics.sortino_ratio),
                'detailed_metrics': json.dumps(metrics.detailed_metrics)
            }
            
            # Try to update first, then insert if not exists
            response = self.client.table('backtest_performance')\
                .upsert(data, on_conflict='session_id')\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
            return False
    
    # ============= Polygon Data Cache Operations =============
    
    def cache_polygon_data(self, ticker: str, date: date, timeframe: str, data: Dict) -> bool:
        """Cache Polygon data in Supabase"""
        try:
            # Create a cache table if it doesn't exist
            cache_data = {
                'ticker': ticker,
                'date': date.isoformat(),
                'timeframe': timeframe,
                'data': json.dumps(data),
                'cached_at': datetime.now().isoformat()
            }
            
            # We'll use a polygon_cache table (needs to be created)
            response = self.client.table('polygon_cache')\
                .upsert(cache_data, on_conflict='ticker,date,timeframe')\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error caching Polygon data: {e}")
            return False
    
    def get_cached_polygon_data(self, ticker: str, date: date, timeframe: str) -> Optional[Dict]:
        """Get cached Polygon data from Supabase"""
        try:
            response = self.client.table('polygon_cache')\
                .select("data, cached_at")\
                .eq('ticker', ticker)\
                .eq('date', date.isoformat())\
                .eq('timeframe', timeframe)\
                .single()\
                .execute()
            
            if response.data:
                # Check if cache is not too old (30 days)
                cached_at = datetime.fromisoformat(response.data['cached_at'])
                if datetime.now() - cached_at < timedelta(days=30):
                    return json.loads(response.data['data'])
            
            return None
            
        except Exception as e:
            logger.debug(f"No cached data found: {e}")
            return None
    
    # ============= Analysis Queries =============
    
    def get_confluence_performance(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """Get performance statistics by confluence level"""
        try:
            query = self.client.table('v_confluence_performance').select("*")
            
            if ticker:
                # Join with sessions to filter by ticker
                query = self.client.rpc('get_confluence_performance_by_ticker', {'p_ticker': ticker})
            
            response = query.execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching confluence performance: {e}")
            return pd.DataFrame()
    
    def get_trade_summary(self, session_id: Optional[str] = None, 
                          ticker: Optional[str] = None) -> pd.DataFrame:
        """Get trade summary from view"""
        try:
            query = self.client.table('v_backtest_trade_summary').select("*")
            
            if session_id:
                query = query.eq('session_id', session_id)
            if ticker:
                query = query.eq('ticker', ticker)
            
            response = query.order('entry_timestamp', desc=True).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching trade summary: {e}")
            return pd.DataFrame()

# Create SQL for the polygon_cache table
POLYGON_CACHE_TABLE_SQL = """
-- Create polygon_cache table for storing API data
CREATE TABLE IF NOT EXISTS public.polygon_cache (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    data JSONB NOT NULL,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT polygon_cache_pkey PRIMARY KEY (id),
    CONSTRAINT polygon_cache_unique UNIQUE (ticker, date, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_polygon_cache_lookup 
    ON public.polygon_cache(ticker, date, timeframe);
    
CREATE INDEX IF NOT EXISTS idx_polygon_cache_cached_at 
    ON public.polygon_cache(cached_at);
"""