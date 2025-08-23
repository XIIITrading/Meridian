"""
Handles user-entered trade data and validates inputs
Updated to work with ticker_id format
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

from core.models import ManualTradeEntry, ValidationResult, TradeDirection
from backtest_config import backtest_config

class ManualTradeHandler:
    """Handles validation and processing of manually entered trades"""
    
    def __init__(self):
        self.fixed_risk = backtest_config.FIXED_RISK_AMOUNT
        self.max_zone_distance = backtest_config.MAX_DISTANCE_TO_ZONE_TICKS
    
    @staticmethod
    def parse_ticker_id(ticker_id: str) -> Dict[str, any]:
        """
        Parse ticker_id format (e.g., "AMD.121824")
        
        Args:
            ticker_id: Ticker ID in format TICKER.MMDDYY
            
        Returns:
            Dictionary with ticker and date components
        """
        try:
            parts = ticker_id.split('.')
            if len(parts) != 2:
                raise ValueError(f"Invalid ticker_id format: {ticker_id}")
            
            ticker = parts[0]
            date_str = parts[1]
            
            # Parse date (MMDDYY)
            if len(date_str) != 6:
                raise ValueError(f"Invalid date format in ticker_id: {date_str}")
            
            month = int(date_str[0:2])
            day = int(date_str[2:4])
            year = 2000 + int(date_str[4:6])
            
            trade_date = datetime(year, month, day)
            
            return {
                'ticker': ticker,
                'date': trade_date,
                'ticker_id': ticker_id
            }
        except Exception as e:
            raise ValueError(f"Error parsing ticker_id '{ticker_id}': {str(e)}")
    
    @staticmethod
    def create_ticker_id(ticker: str, date: datetime) -> str:
        """
        Create ticker_id from ticker and date
        
        Args:
            ticker: Stock symbol
            date: Trade date
            
        Returns:
            Formatted ticker_id (e.g., "AMD.121824")
        """
        date_str = date.strftime("%m%d%y")
        return f"{ticker}.{date_str}"
    
    def validate_trade_inputs(self, trade: ManualTradeEntry) -> ValidationResult:
        """
        Validate user-entered trade data
        
        Args:
            trade: Manual trade entry data
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Time validations
        if trade.entry_candle_time >= trade.exit_candle_time:
            result.errors.append("Exit time must be after entry time")
            result.is_valid = False
        
        # Ensure times are on the same day (for intraday trades)
        if trade.entry_candle_time.date() != trade.exit_candle_time.date():
            result.warnings.append("Entry and exit are on different days")
        
        # Check if times are during market hours
        entry_hour = trade.entry_candle_time.hour + trade.entry_candle_time.minute / 60
        exit_hour = trade.exit_candle_time.hour + trade.exit_candle_time.minute / 60
        
        if entry_hour < 9.5 or entry_hour > 16:
            result.warnings.append("Entry time is outside regular market hours")
        
        if exit_hour < 9.5 or exit_hour > 16:
            result.warnings.append("Exit time is outside regular market hours")
        
        # Price validations
        if trade.trade_direction == TradeDirection.LONG:
            if trade.stop_price >= trade.entry_price:
                result.errors.append("For long trades, stop must be below entry")
                result.is_valid = False
            
            if trade.target_price <= trade.entry_price:
                result.errors.append("For long trades, target must be above entry")
                result.is_valid = False
                
            if trade.exit_price < trade.stop_price:
                result.warnings.append("Exit price is below stop (full loss)")
            
        elif trade.trade_direction == TradeDirection.SHORT:
            if trade.stop_price <= trade.entry_price:
                result.errors.append("For short trades, stop must be above entry")
                result.is_valid = False
            
            if trade.target_price >= trade.entry_price:
                result.errors.append("For short trades, target must be below entry")
                result.is_valid = False
                
            if trade.exit_price > trade.stop_price:
                result.warnings.append("Exit price is above stop (full loss)")
        
        # Risk/Reward validation
        if trade.risk_reward_ratio and trade.risk_reward_ratio < 1.5:
            result.warnings.append(f"Risk/Reward ratio is low: {trade.risk_reward_ratio:.2f}")
        
        # Position size validation
        if trade.shares and trade.shares <= 0:
            result.errors.append("Invalid position size calculated")
            result.is_valid = False
        
        return result
    
    def calculate_position_size(self, entry_price: float, stop_price: float) -> float:
        """
        Calculate position size based on fixed risk amount
        
        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            
        Returns:
            Number of shares to trade
        """
        risk_per_share = abs(entry_price - stop_price)
        
        if risk_per_share == 0:
            raise ValueError("Stop price cannot equal entry price")
        
        shares = self.fixed_risk / risk_per_share
        
        # Round to reasonable lot size
        return round(shares)
    
    def assign_trade_id(self) -> str:
        """Generate unique trade identifier"""
        return str(uuid.uuid4())
    
    def create_trade_record(self, 
                           ticker_id: str,
                           entry_time: datetime,
                           exit_time: datetime,
                           direction: str,
                           entry_price: float,
                           stop_price: float,
                           target_price: float,
                           exit_price: float,
                           notes: Optional[str] = None) -> Tuple[ManualTradeEntry, ValidationResult]:
        """
        Create and validate a complete trade record
        
        Args:
            ticker_id: Ticker ID in format TICKER.MMDDYY
            entry_time: Entry candle time
            exit_time: Exit candle time
            direction: Trade direction ('long' or 'short')
            entry_price: Entry price
            stop_price: Stop price
            target_price: Target price
            exit_price: Exit price
            notes: Optional trade notes
            
        Returns:
            Tuple of (ManualTradeEntry, ValidationResult)
        """
        # Parse ticker_id
        ticker_info = self.parse_ticker_id(ticker_id)
        
        # Ensure entry/exit times are on the correct date
        trade_date = ticker_info['date']
        entry_datetime = datetime.combine(
            trade_date.date(),
            entry_time.time() if isinstance(entry_time, datetime) else entry_time
        )
        exit_datetime = datetime.combine(
            trade_date.date(),
            exit_time.time() if isinstance(exit_time, datetime) else exit_time
        )
        
        # Convert direction string to enum
        trade_direction = TradeDirection.LONG if direction.lower() == 'long' else TradeDirection.SHORT
        
        # Create trade entry
        trade = ManualTradeEntry(
            entry_candle_time=entry_datetime,
            exit_candle_time=exit_datetime,
            trade_direction=trade_direction,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            exit_price=exit_price,
            ticker=ticker_info['ticker'],
            fixed_risk=self.fixed_risk,
            notes=notes
        )
        
        # Add ticker_id to trade
        trade.ticker_id = ticker_id
        
        # Assign unique ID
        trade.trade_id = self.assign_trade_id()
        
        # Validate
        validation_result = self.validate_trade_inputs(trade)
        
        return trade, validation_result
    
    def format_trade_summary(self, trade: ManualTradeEntry) -> str:
        """
        Create a formatted summary of the trade
        
        Args:
            trade: Trade to summarize
            
        Returns:
            Formatted string summary
        """
        direction = "LONG" if trade.trade_direction == TradeDirection.LONG else "SHORT"
        ticker_id = getattr(trade, 'ticker_id', 'N/A')
        
        summary = f"""
Trade Summary
=============
Trade ID: {trade.trade_id}
Ticker ID: {ticker_id}
Direction: {direction}
Ticker: {trade.ticker}

Entry: ${trade.entry_price:.2f} at {trade.entry_candle_time.strftime('%Y-%m-%d %H:%M')}
Stop: ${trade.stop_price:.2f} (Risk: ${abs(trade.entry_price - trade.stop_price) * trade.shares:.2f})
Target: ${trade.target_price:.2f} (Reward: ${abs(trade.target_price - trade.entry_price) * trade.shares:.2f})
Exit: ${trade.exit_price:.2f} at {trade.exit_candle_time.strftime('%Y-%m-%d %H:%M')}

Position Size: {trade.shares} shares
Risk Amount: ${trade.fixed_risk:.2f}
R:R Ratio: {trade.risk_reward_ratio:.2f}

Notes: {trade.notes or 'None'}
"""
        return summary