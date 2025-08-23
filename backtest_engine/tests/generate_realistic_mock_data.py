"""
Generate mock data that matches the exact database schemas
Creates linked analysis_sessions and backtest_trades records
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import uuid
import json
from typing import Dict, List, Tuple

class RealisticMockDataGenerator:
    """Generate mock data matching exact database schemas"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.sessions = []
        self.trades = []
        
    def generate_analysis_session(self, ticker: str, session_date: date, 
                                 session_number: int) -> Dict:
        """Generate a single analysis session matching the schema"""
        
        session_id = str(uuid.uuid4())
        ticker_id = f"{ticker}.{session_date.strftime('%m%d%y')}"
        
        session = {
            'session_id': session_id,
            'session_name': f"{ticker} Analysis - {session_date}",
            'ticker_id': ticker_id,
            'ticker': ticker,
            'session_date': session_date,
            'levels_zones_id': str(uuid.uuid4()),  # Mock zone ID
            'total_trades': 0,  # Will update after trades
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.00,
            'win_rate': 0.00,
            'avg_winner': 0.00,
            'avg_loser': 0.00,
            'avg_r_multiple': 0.00,
            'profit_factor': 0.00,
            'max_drawdown': 0.00,
            'notes': f"Mock session {session_number} for testing",
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        return session
    
    def generate_backtest_trade(self, session: Dict, trade_number: int, 
                               trade_time: datetime) -> Dict:
        """Generate a single trade matching the backtest_trades schema"""
        
        # Determine trade outcome based on confluence
        confluence_level = np.random.choice(
            ['L1', 'L2', 'L3', 'L4', 'L5'],
            p=[0.1, 0.2, 0.3, 0.25, 0.15]
        )
        
        # Win probability increases with confluence
        win_prob = {
            'L1': 0.3, 'L2': 0.4, 'L3': 0.5, 
            'L4': 0.65, 'L5': 0.75
        }[confluence_level]
        
        is_winner = np.random.random() < win_prob
        
        # Trade direction
        direction = np.random.choice(['long', 'short'])
        
        # Base prices
        base_price = 100.00 + np.random.uniform(-10, 10)
        
        if direction == 'long':
            entry_price = base_price
            stop_price = entry_price * 0.98  # 2% stop
            target_price = entry_price * 1.04  # 4% target
            
            if is_winner:
                exit_price = target_price + np.random.uniform(-0.5, 0.5)
                exit_reason = 'target_hit'
                r_multiple = np.random.uniform(1.5, 3.0)
            else:
                exit_price = stop_price + np.random.uniform(-0.5, 0.5)
                exit_reason = 'stop_hit'
                r_multiple = np.random.uniform(-1.5, -0.5)
        else:  # short
            entry_price = base_price
            stop_price = entry_price * 1.02  # 2% stop
            target_price = entry_price * 0.96  # 4% target
            
            if is_winner:
                exit_price = target_price - np.random.uniform(-0.5, 0.5)
                exit_reason = 'target_hit'
                r_multiple = np.random.uniform(1.5, 3.0)
            else:
                exit_price = stop_price - np.random.uniform(-0.5, 0.5)
                exit_reason = 'stop_hit'
                r_multiple = np.random.uniform(-1.5, -0.5)
        
        # Calculate position sizing
        fixed_risk = 250.00
        shares = fixed_risk / abs(entry_price - stop_price)
        shares = round(shares, 2)
        position_value = shares * entry_price
        
        # Calculate P&L
        if direction == 'long':
            trade_result = (exit_price - entry_price) * shares
        else:
            trade_result = (entry_price - exit_price) * shares
        
        # Zone information
        zone_number = np.random.randint(1, 7)
        zone_type = np.random.choice(['supply', 'demand'])
        distance_from_zone = np.random.randint(-15, 16)
        
        # Confluence sources (JSONB)
        confluence_sources = {
            'moving_average': np.random.random() > 0.5,
            'fibonacci': np.random.random() > 0.5,
            'volume_profile': np.random.random() > 0.5,
            'pivot_point': np.random.random() > 0.5,
            'trend_line': np.random.random() > 0.5,
            'previous_day_level': np.random.random() > 0.6
        }
        
        # Calculate confluence score based on sources
        confluence_score = sum(1 for v in confluence_sources.values() if v) * 20
        
        # Time metrics
        exit_time = trade_time + timedelta(minutes=np.random.randint(5, 180))
        total_minutes = int((exit_time - trade_time).total_seconds() / 60)
        
        # MFE/MAE calculations
        if is_winner:
            mfe_price = exit_price + np.random.uniform(0, 2)
            mae_price = entry_price - np.random.uniform(0, 1) if direction == 'long' else entry_price + np.random.uniform(0, 1)
            mfe_r = r_multiple + np.random.uniform(0.5, 1.5)
            mae_r = np.random.uniform(-0.5, 0)
            first_negative_minute = None if np.random.random() > 0.5 else np.random.randint(1, 20)
            first_profitable_minute = np.random.randint(1, 10)
            minutes_to_target = np.random.randint(10, 60)
            minutes_to_stop = None
        else:
            mfe_price = entry_price + np.random.uniform(0, 1) if direction == 'long' else entry_price - np.random.uniform(0, 1)
            mae_price = exit_price
            mfe_r = np.random.uniform(0, 0.5)
            mae_r = r_multiple - np.random.uniform(0.2, 0.5)
            first_negative_minute = np.random.randint(1, 5)
            first_profitable_minute = None if np.random.random() > 0.3 else np.random.randint(1, 5)
            minutes_to_target = None
            minutes_to_stop = np.random.randint(15, 90)
        
        # Efficiency ratio
        if mfe_r != 0:
            efficiency_ratio = abs(r_multiple / mfe_r)
        else:
            efficiency_ratio = 0
        
        trade = {
            'trade_id': str(uuid.uuid4()),
            'analysis_session_id': session['session_id'],
            'ticker_id': session['ticker_id'],
            'ticker': session['ticker'],
            'trade_date': session['session_date'],
            'entry_candle_time': trade_time,
            'exit_candle_time': exit_time,
            'trade_direction': direction,
            'entry_price': round(entry_price, 4),
            'stop_price': round(stop_price, 4),
            'target_price': round(target_price, 4),
            'exit_price': round(exit_price, 4),
            'shares': shares,
            'fixed_risk': fixed_risk,
            'position_value': round(position_value, 2),
            'zone_number': zone_number,
            'zone_type': zone_type,
            'zone_confluence_level': confluence_level,
            'zone_confluence_score': confluence_score,
            'confluence_sources': confluence_sources,
            'distance_from_zone_ticks': distance_from_zone,
            'zone_high': round(base_price + 1, 4),
            'zone_low': round(base_price - 1, 4),
            'max_favorable_excursion': round(abs(mfe_price - entry_price) * shares, 2),
            'max_adverse_excursion': round(abs(mae_price - entry_price) * shares, 2),
            'mfe_r_multiple': round(mfe_r, 2),
            'mae_r_multiple': round(mae_r, 2),
            'trade_result': round(trade_result, 2),
            'r_multiple': round(r_multiple, 2),
            'risk_reward_ratio': round(abs(target_price - entry_price) / abs(stop_price - entry_price), 2),
            'efficiency_ratio': round(efficiency_ratio, 2),
            'actual_exit_time': exit_time,
            'exit_reason': exit_reason,
            'minutes_to_target': minutes_to_target,
            'minutes_to_stop': minutes_to_stop,
            'minutes_to_exit': total_minutes,
            'total_minutes_in_trade': total_minutes,
            'highest_price': round(mfe_price, 4),
            'lowest_price': round(mae_price, 4),
            'first_profitable_minute': first_profitable_minute,
            'first_negative_minute': first_negative_minute,
            'pivot_validated': np.random.random() > 0.3,
            'pivot_strength': np.random.randint(1, 11),
            'zone_validated': True,
            'minute_data_complete': True,
            'notes': f"Mock trade {trade_number}",
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'trade_type': 'manual'
        }
        
        return trade
    
    def generate_complete_dataset(self, 
                                 tickers: List[str] = ['AMD', 'NVDA', 'SPY'],
                                 trades_per_session: int = 10,
                                 sessions_per_ticker: int = 3) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate complete dataset with sessions and trades
        
        Returns:
            Tuple of (sessions_df, trades_df)
        """
        
        all_sessions = []
        all_trades = []
        
        base_date = datetime.now() - timedelta(days=30)
        
        for ticker in tickers:
            for session_num in range(sessions_per_ticker):
                # Create session
                session_date = (base_date + timedelta(days=session_num * 7)).date()
                session = self.generate_analysis_session(ticker, session_date, session_num + 1)
                
                # Generate trades for this session
                session_trades = []
                trade_time = datetime.combine(session_date, datetime.min.time().replace(hour=9, minute=30))
                
                for trade_num in range(trades_per_session):
                    trade = self.generate_backtest_trade(session, trade_num + 1, trade_time)
                    session_trades.append(trade)
                    trade_time += timedelta(minutes=np.random.randint(15, 60))
                
                # Update session statistics
                session = self._update_session_stats(session, session_trades)
                
                all_sessions.append(session)
                all_trades.extend(session_trades)
        
        sessions_df = pd.DataFrame(all_sessions)
        trades_df = pd.DataFrame(all_trades)
        
        return sessions_df, trades_df
    
    def _update_session_stats(self, session: Dict, trades: List[Dict]) -> Dict:
        """Update session statistics based on trades"""
        
        if not trades:
            return session
        
        winners = [t for t in trades if t['r_multiple'] > 0]
        losers = [t for t in trades if t['r_multiple'] <= 0]
        
        session['total_trades'] = len(trades)
        session['winning_trades'] = len(winners)
        session['losing_trades'] = len(losers)
        session['total_pnl'] = round(sum(t['trade_result'] for t in trades), 2)
        
        if trades:
            session['win_rate'] = round(len(winners) / len(trades) * 100, 2)
            session['avg_r_multiple'] = round(sum(t['r_multiple'] for t in trades) / len(trades), 2)
        
        if winners:
            session['avg_winner'] = round(sum(t['trade_result'] for t in winners) / len(winners), 2)
        
        if losers:
            session['avg_loser'] = round(sum(t['trade_result'] for t in losers) / len(losers), 2)
            
        # Profit factor
        if losers and winners:
            total_wins = sum(t['trade_result'] for t in winners)
            total_losses = abs(sum(t['trade_result'] for t in losers))
            if total_losses > 0:
                session['profit_factor'] = round(total_wins / total_losses, 2)
        elif winners and not losers:
            session['profit_factor'] = 999.99  # Max value for the field
        
        # Max drawdown (simplified)
        cumulative = 0
        max_cum = 0
        max_dd = 0
        for trade in sorted(trades, key=lambda x: x['entry_candle_time']):
            cumulative += trade['trade_result']
            max_cum = max(max_cum, cumulative)
            drawdown = max_cum - cumulative
            max_dd = max(max_dd, drawdown)
        session['max_drawdown'] = round(max_dd, 2)
        
        return session
    
    def create_analysis_results(self, sessions_df: pd.DataFrame, 
                               trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create analysis_results records from the analysis
        """
        results = []
        
        # Create a full analysis result
        all_trades_analysis = {
            'id': 1,
            'analysis_type': 'full',
            'ticker_id': None,
            'analysis_date': datetime.now(),
            'results': {
                'basic_stats': {
                    'total_trades': len(trades_df),
                    'winners': len(trades_df[trades_df['r_multiple'] > 0]),
                    'losers': len(trades_df[trades_df['r_multiple'] <= 0]),
                    'win_rate': round(len(trades_df[trades_df['r_multiple'] > 0]) / len(trades_df) * 100, 2),
                    'avg_r_multiple': round(trades_df['r_multiple'].mean(), 2),
                    'total_r': round(trades_df['r_multiple'].sum(), 2)
                },
                'confluence_analysis': {},
                'time_patterns': [],
                'edge_factors': []
            },
            'key_metrics': {
                'win_rate': round(len(trades_df[trades_df['r_multiple'] > 0]) / len(trades_df) * 100, 2),
                'total_trades': len(trades_df),
                'profit_factor': 0,
                'avg_r_multiple': round(trades_df['r_multiple'].mean(), 2)
            },
            'recommendations': [
                "Focus on L4+ confluence zones",
                "Avoid trades in first 15 minutes",
                "Consider scaling in L5 zones"
            ]
        }
        results.append(all_trades_analysis)
        
        # Create session-specific results
        for _, session in sessions_df.iterrows():
            session_trades = trades_df[trades_df['analysis_session_id'] == session['session_id']]
            
            if len(session_trades) > 0:
                session_analysis = {
                    'id': len(results) + 1,
                    'analysis_type': 'session',
                    'ticker_id': session['ticker_id'],
                    'analysis_date': datetime.now(),
                    'results': {
                        'session_stats': {
                            'total_trades': len(session_trades),
                            'win_rate': session['win_rate'],
                            'avg_r': session['avg_r_multiple'],
                            'total_pnl': session['total_pnl']
                        }
                    },
                    'key_metrics': {
                        'win_rate': session['win_rate'],
                        'total_trades': session['total_trades'],
                        'profit_factor': session['profit_factor'],
                        'avg_r_multiple': session['avg_r_multiple']
                    },
                    'recommendations': []
                }
                results.append(session_analysis)
        
        return pd.DataFrame(results)

def test_with_realistic_data():
    """Test the analysis modules with realistic mock data"""
    
    print("\n" + "="*70)
    print("GENERATING REALISTIC MOCK DATA")
    print("="*70)
    
    # Generate data
    generator = RealisticMockDataGenerator()
    sessions_df, trades_df = generator.generate_complete_dataset(
        tickers=['AMD', 'NVDA', 'SPY'],
        trades_per_session=15,
        sessions_per_ticker=3
    )
    
    print(f"\n✅ Generated {len(sessions_df)} sessions with {len(trades_df)} trades")
    
    # Display session summary
    print("\n[Session Summary]")
    print(sessions_df[['ticker_id', 'total_trades', 'win_rate', 'avg_r_multiple', 'total_pnl']].to_string())
    
    # Display trade statistics by confluence
    print("\n[Trades by Confluence Level]")
    for level in ['L1', 'L2', 'L3', 'L4', 'L5']:
        level_trades = trades_df[trades_df['zone_confluence_level'] == level]
        if len(level_trades) > 0:
            win_rate = len(level_trades[level_trades['r_multiple'] > 0]) / len(level_trades) * 100
            avg_r = level_trades['r_multiple'].mean()
            print(f"  {level}: {len(level_trades)} trades, {win_rate:.1f}% WR, {avg_r:.2f}R")
    
    # Verify schema compliance
    print("\n[Schema Validation]")
    
    # Check required fields
    required_trade_fields = [
        'trade_id', 'analysis_session_id', 'ticker_id', 'ticker',
        'entry_price', 'exit_price', 'stop_price', 'target_price',
        'r_multiple', 'trade_result', 'zone_confluence_level'
    ]
    
    for field in required_trade_fields:
        if field not in trades_df.columns:
            print(f"❌ Missing required field: {field}")
        else:
            print(f"✅ {field}: present")
    
    # Test with analysis modules
    print("\n[Testing with Analysis Modules]")
    
    from test_analysis_integration import MockStorageManager
    mock_storage = MockStorageManager(trades_df)
    
    try:
        from analysis.statistical_analyzer import StatisticalAnalyzer
        
        analyzer = StatisticalAnalyzer(mock_storage)
        results = analyzer.analyze_all_trades(save=False)
        
        print(f"✅ Analysis completed successfully")
        print(f"   Win rate: {results['basic_stats'].win_rate}%")
        print(f"   Avg R: {results['basic_stats'].avg_r_multiple}")
        print(f"   Edge factors found: {len(results.get('edge_factors', []))}")
        
        # Create analysis_results records
        analysis_results_df = generator.create_analysis_results(sessions_df, trades_df)
        print(f"\n✅ Generated {len(analysis_results_df)} analysis_results records")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    return sessions_df, trades_df, analysis_results_df

if __name__ == "__main__":
    sessions_df, trades_df, analysis_results_df = test_with_realistic_data()
    
    # Optional: Save to CSV for inspection
    print("\n[Saving to CSV files]")
    sessions_df.to_csv('mock_sessions.csv', index=False)
    trades_df.to_csv('mock_trades.csv', index=False)
    analysis_results_df.to_csv('mock_analysis_results.csv', index=False)
    print("✅ Saved: mock_sessions.csv, mock_trades.csv, mock_analysis_results.csv")
    
    print("\n" + "="*70)
    print("REALISTIC MOCK DATA GENERATION COMPLETE")
    print("="*70)
    print("\nThe mock data exactly matches your database schemas:")
    print("  • analysis_sessions: session-level summaries")
    print("  • backtest_trades: detailed trade records")
    print("  • analysis_results: analysis output storage")
    print("\nYou can now test with confidence that the data structure is correct!")