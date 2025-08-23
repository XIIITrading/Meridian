"""
Command-line interface for manual trade entry with navigation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, time
from typing import Optional, Any, Dict
import json
import logging
logging.basicConfig(level=logging.DEBUG)

from core.manual_trade_handler import ManualTradeHandler
from core.zone_alignment_analyzer import ZoneAlignmentAnalyzer
from core.minute_data_analyzer import MinuteDataAnalyzer
from core.confluence_reconstructor import ConfluenceReconstructor
from data.polygon_fetcher import PolygonBacktestFetcher
from data.supabase_client import BacktestSupabaseClient
from data.backtest_storage_manager import BacktestStorageManager

class CLITradeEntry:
    """Command-line interface for entering trades with navigation"""
    
    def __init__(self):
        # Initialize components
        self.handler = ManualTradeHandler()
        self.supabase = BacktestSupabaseClient()
        self.storage = BacktestStorageManager(self.supabase)
        self.reconstructor = ConfluenceReconstructor()
        self.zone_analyzer = ZoneAlignmentAnalyzer(self.reconstructor)
        self.polygon = PolygonBacktestFetcher()
        self.minute_analyzer = MinuteDataAnalyzer(self.polygon)
        self.debug = False
        self.polygon_available = False
        
        # Store inputs for navigation
        self.inputs = {}
        self.input_order = []
        
        # Test Polygon connection
        self._test_polygon_connection()
    
    def _test_polygon_connection(self):
        """Test if Polygon REST API is available"""
        try:
            connected, message = self.polygon.test_connection()
            if connected:
                print(f"✓ Polygon API: {message}")
                self.polygon_available = True
            else:
                print(f"⚠ Polygon API: {message}")
                print("  Minute data and metrics will not be available")
                self.polygon_available = False
        except Exception as e:
            print(f"⚠ Polygon API unavailable: {e}")
            print("  Minute data and metrics will not be available")
            self.polygon_available = False
    
    def get_input_with_back(self, prompt: str, field_name: str, validator=None, converter=None) -> Any:
        """
        Get input with ability to go back
        
        Args:
            prompt: The prompt to show
            field_name: Name of the field for storage
            validator: Optional validation function
            converter: Optional conversion function
            
        Returns:
            The validated and converted input
        """
        # Show current value if it exists
        if field_name in self.inputs:
            print(f"  Current value: {self.inputs[field_name]}")
            print("  (Enter new value, 'back' to go to previous field, or press Enter to keep current)")
        else:
            print("  (Type 'back' or 'b' to go to previous field)")
        
        while True:
            user_input = input(f"{prompt}: ").strip()
            
            # Handle navigation commands
            if user_input.lower() in ['back', 'b']:
                return 'BACK'
            
            # Handle keeping current value
            if not user_input and field_name in self.inputs:
                return self.inputs[field_name]
            
            # Handle empty required field
            if not user_input and field_name not in self.inputs:
                if field_name == 'notes':  # Notes are optional
                    return None
                print("This field is required. Please enter a value.")
                continue
            
            # Validate and convert
            try:
                if validator and not validator(user_input):
                    print("Invalid input. Please try again.")
                    continue
                
                if converter:
                    return converter(user_input)
                else:
                    return user_input
                    
            except Exception as e:
                print(f"Error: {e}. Please try again.")
                continue
    
    def get_time_input_with_back(self, prompt: str, field_name: str) -> Any:
        """Get time input with navigation"""
        def time_converter(time_str):
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        
        def time_validator(time_str):
            try:
                parts = time_str.split(':')
                if len(parts) != 2:
                    return False
                hour, minute = map(int, parts)
                return 0 <= hour <= 23 and 0 <= minute <= 59
            except:
                return False
        
        return self.get_input_with_back(
            f"{prompt} (HH:MM UTC)",
            field_name,
            validator=time_validator,
            converter=time_converter
        )
    
    def get_float_input_with_back(self, prompt: str, field_name: str) -> Any:
        """Get float input with navigation"""
        def float_converter(value_str):
            return float(value_str.replace('$', '').replace(',', ''))
        
        def float_validator(value_str):
            try:
                float(value_str.replace('$', '').replace(',', ''))
                return True
            except:
                return False
        
        return self.get_input_with_back(
            f"{prompt} ($)",
            field_name,
            validator=float_validator,
            converter=float_converter
        )
    
    def show_summary(self):
        """Show current input summary"""
        print("\n" + "="*60)
        print("CURRENT INPUTS")
        print("="*60)
        
        if not self.inputs:
            print("No inputs yet")
            return
        
        for field in self.input_order:
            if field in self.inputs:
                value = self.inputs[field]
                if isinstance(value, time):
                    value = value.strftime("%H:%M")
                elif isinstance(value, float):
                    value = f"${value:.2f}"
                print(f"{field}: {value}")
    
    def collect_trade_inputs(self) -> bool:
        """
        Collect all trade inputs with navigation
        
        Returns:
            True if all inputs collected successfully, False if user wants to quit
        """
        # Define the input sequence
        input_sequence = [
            ('ticker_id', 'text'),
            ('entry_time', 'time'),
            ('exit_time', 'time'),
            ('direction', 'choice'),
            ('entry_price', 'float'),
            ('stop_price', 'float'),
            ('target_price', 'float'),
            ('exit_price', 'float'),
            ('notes', 'optional_text')
        ]
        
        current_index = 0
        
        while current_index < len(input_sequence):
            field_name, field_type = input_sequence[current_index]
            
            # Track order for summary
            if field_name not in self.input_order:
                self.input_order.append(field_name)
            
            # Clear screen and show progress
            print("\n" + "-"*40)
            print(f"FIELD {current_index + 1}/{len(input_sequence)}")
            print("-"*40)
            
            # Show summary if we have inputs
            if self.inputs:
                self.show_summary()
                print("\n" + "-"*40)
            
            # Get the appropriate input
            result = None
            
            if field_name == 'ticker_id':
                result = self.get_input_with_back(
                    "Enter Ticker ID (e.g., AMD.121824)",
                    field_name,
                    validator=lambda x: '.' in x and len(x.split('.')[1]) == 6,
                    converter=lambda x: x.upper()
                )
                
            elif field_name == 'entry_time':
                result = self.get_time_input_with_back("Entry candle time", field_name)
                
            elif field_name == 'exit_time':
                result = self.get_time_input_with_back("Exit candle time", field_name)
                
            elif field_name == 'direction':
                result = self.get_input_with_back(
                    "Trade direction (long/short)",
                    field_name,
                    validator=lambda x: x.lower() in ['long', 'short'],
                    converter=lambda x: x.lower()
                )
                
            elif field_name == 'entry_price':
                result = self.get_float_input_with_back("Entry price", field_name)
                
            elif field_name == 'stop_price':
                result = self.get_float_input_with_back("Stop price", field_name)
                
            elif field_name == 'target_price':
                result = self.get_float_input_with_back("Target price", field_name)
                
            elif field_name == 'exit_price':
                result = self.get_float_input_with_back("Exit price", field_name)
                
            elif field_name == 'notes':
                print("  (Optional - press Enter to skip)")
                result = self.get_input_with_back("Notes", field_name, converter=lambda x: x if x else None)
            
            # Handle navigation
            if result == 'BACK':
                if current_index > 0:
                    current_index -= 1
                    print("\n⬆ Going back to previous field...")
                else:
                    print("\n⚠ Already at first field")
            else:
                # Store the input and move forward
                self.inputs[field_name] = result
                current_index += 1
        
        return True
    
    def run(self):
        """Run the CLI trade entry interface"""
        print("\n" + "="*60)
        print("BACKTEST TRADE ENTRY SYSTEM")
        print("="*60)
        print("Navigation: Type 'back' or 'b' to go to previous field")
        print("Note: All times should be entered in UTC")
        print("Market Hours: 14:30-21:00 UTC (9:30 AM - 4:00 PM ET)")
        print("-"*60)
        
        # Ask about debug mode
        debug_mode = input("Enable debug mode? (y/n): ").strip().lower()
        self.debug = (debug_mode == 'y')
        
        # Collect all inputs
        if not self.collect_trade_inputs():
            print("\nExiting...")
            return
        
        # Show final summary
        print("\n" + "="*60)
        print("FINAL TRADE DETAILS")
        self.show_summary()
        print("="*60)
        
        confirm = input("\nIs this correct? (y/n/restart): ").strip().lower()
        if confirm == 'restart':
            self.inputs = {}
            self.input_order = []
            self.run()
            return
        elif confirm != 'y':
            print("\nTrade cancelled.")
            return
        
        # Parse ticker_id
        try:
            ticker_info = ManualTradeHandler.parse_ticker_id(self.inputs['ticker_id'])
            print(f"\n✓ Trading {ticker_info['ticker']} on {ticker_info['date'].strftime('%Y-%m-%d')}")
        except ValueError as e:
            print(f"✗ Error: {e}")
            return
        
        # Check if levels_zones data exists
        zones_data = self.storage.get_levels_zones_data(self.inputs['ticker_id'])
        if not zones_data:
            print(f"⚠ Warning: No levels_zones data found for {self.inputs['ticker_id']}")
            proceed = input("Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                return
        else:
            print(f"✓ Found levels_zones data for {self.inputs['ticker_id']}")
        
        # Create trade record
        trade, validation = self.handler.create_trade_record(
            ticker_id=self.inputs['ticker_id'],
            entry_time=self.inputs['entry_time'],
            exit_time=self.inputs['exit_time'],
            direction=self.inputs['direction'],
            entry_price=self.inputs['entry_price'],
            stop_price=self.inputs['stop_price'],
            target_price=self.inputs['target_price'],
            exit_price=self.inputs['exit_price'],
            notes=self.inputs.get('notes')
        )
        
        # Show validation results
        print("\n" + "-"*40)
        print("VALIDATION RESULTS")
        print("-"*40)
        
        if validation.is_valid:
            print("✓ Trade validation PASSED")
        else:
            print("✗ Trade validation FAILED:")
            for error in validation.errors:
                print(f"  ERROR: {error}")
        
        if validation.warnings:
            for warning in validation.warnings:
                print(f"  ⚠ WARNING: {warning}")
        
        if not validation.is_valid:
            print("\nTrade not saved due to validation errors.")
            retry = input("Would you like to correct the errors? (y/n): ").strip().lower()
            if retry == 'y':
                self.run()
            return
        
        # Show trade summary
        print(self.handler.format_trade_summary(trade))
        
        # Analyze zone alignment if data exists
        zone_match = None
        if zones_data:
            print("\n" + "-"*40)
            print("ZONE ANALYSIS")
            print("-"*40)
            
            try:
                # Parse zones from database
                parse_result = self.reconstructor.parse_levels_zones_record(zones_data)
                
                # Handle tuple return (zones, market_context)
                if isinstance(parse_result, tuple):
                    zones, market_context = parse_result
                else:
                    zones = parse_result
                    market_context = None
                
                # Find matching zone
                if zones and isinstance(zones, list):
                    zone_match = self.zone_analyzer.find_entry_zone(
                        entry_price=trade.entry_price,
                        zones=zones,
                        direction=trade.trade_direction
                    )
                    
                    if zone_match:
                        print(self.zone_analyzer.get_zone_analysis_summary(zone_match))
                    else:
                        print("⚠ No matching zone found for entry price")
                else:
                    print("⚠ No valid zones found in data")
                    
            except Exception as e:
                print(f"⚠ Error during zone analysis: {e}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
        
        # Fetch and analyze minute data (only if Polygon is available)
        metrics = None
        minute_data_fetched = False
        
        if self.polygon_available:
            print("\n" + "-"*40)
            print("FETCHING MINUTE DATA...")
            print("-"*40)
            
            try:
                minute_data = self.minute_analyzer.fetch_trade_period_data(
                    ticker=trade.ticker,
                    start=trade.entry_candle_time,
                    end=trade.exit_candle_time
                )
                
                if minute_data is not None and not minute_data.empty:
                    print(f"✓ Fetched {len(minute_data)} minute bars")
                    minute_data_fetched = True
                    
                    # Calculate metrics
                    metrics = self.minute_analyzer.calculate_trade_metrics(trade, minute_data)
                    
                    # Cache the minute data
                    try:
                        self.storage.save_minute_bars(trade.ticker, minute_data)
                        if self.debug:
                            print("  ✓ Minute data cached")
                    except Exception as e:
                        if self.debug:
                            print(f"  ⚠ Could not cache minute data: {e}")
                    
                    # Display key metrics
                    print(f"\nPERFORMANCE METRICS:")
                    print(f"  Trade Result: ${metrics.trade_result:.2f}")
                    print(f"  R-Multiple: {metrics.r_multiple:.2f}R")
                    print(f"  MFE: ${metrics.max_favorable_excursion:.2f} ({metrics.mfe_r_multiple:.2f}R)")
                    print(f"  MAE: ${metrics.max_adverse_excursion:.2f} ({metrics.mae_r_multiple:.2f}R)")
                    print(f"  Exit Reason: {metrics.exit_reason.value}")
                    print(f"  Efficiency: {metrics.efficiency_ratio:.1%}")
                else:
                    print("⚠ No minute data returned - will save without metrics")
                    
            except Exception as e:
                print(f"⚠ Error fetching minute data: {e}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
                print("Will continue without minute data metrics")
        else:
            print("\n" + "-"*40)
            print("MINUTE DATA")
            print("-"*40)
            print("⚠ Polygon API not available - skipping minute data")
            print("  Trade will be saved without MFE/MAE metrics")
        
        # Save to database
        print("\n" + "-"*40)
        print("SAVE TO DATABASE")
        print("-"*40)
        
        # Show what will be saved
        save_info = []
        save_info.append("✓ Trade details")
        if zone_match:
            save_info.append("✓ Zone alignment data")
        else:
            save_info.append("○ No zone data")
        if metrics:
            save_info.append("✓ Performance metrics (MFE/MAE)")
        else:
            save_info.append("○ No performance metrics")
        
        print("\nData to save:")
        for info in save_info:
            print(f"  {info}")
        
        save = input("\nSave this trade to database? (y/n): ").strip().lower()
        
        if save == 'y':
            try:
                print("\nSaving trade to Supabase...")
                trade_id = self.storage.save_trade(
                    ticker_id=self.inputs['ticker_id'],
                    trade=trade,
                    zone_match=zone_match,
                    metrics=metrics,
                    trade_type='manual'
                )
                print(f"\n✓ Trade saved successfully to Supabase!")
                print(f"  Trade ID: {trade_id}")
                
                # Show session summary
                try:
                    summary = self.storage.get_session_summary(self.inputs['ticker_id'])
                    if summary and 'session_id' in summary:
                        print(f"\nSESSION SUMMARY ({self.inputs['ticker_id']}):")
                        
                        # Get trade count for this session
                        trades_df = self.storage.get_session_trades(self.inputs['ticker_id'])
                        if not trades_df.empty:
                            total_trades = len(trades_df)
                            winners = trades_df[trades_df['exit_price'] != trades_df['entry_price']]
                            
                            # Calculate based on direction
                            winning_trades = 0
                            total_pnl = 0
                            
                            for _, t in trades_df.iterrows():
                                if t['trade_direction'] == 'long':
                                    pnl = (t['exit_price'] - t['entry_price']) * t.get('shares', 100)
                                else:  # short
                                    pnl = (t['entry_price'] - t['exit_price']) * t.get('shares', 100)
                                
                                total_pnl += pnl
                                if pnl > 0:
                                    winning_trades += 1
                            
                            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                            
                            print(f"  Total Trades: {total_trades}")
                            print(f"  Winning Trades: {winning_trades}")
                            print(f"  Win Rate: {win_rate:.1f}%")
                            print(f"  Total P&L: ${total_pnl:.2f}")
                            
                except Exception as e:
                    if self.debug:
                        print(f"Could not get session summary: {e}")
                    
            except Exception as e:
                print(f"\n✗ Error saving trade to Supabase: {e}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
                    
                retry_save = input("\nWould you like to try saving again without metrics? (y/n): ").strip().lower()
                if retry_save == 'y':
                    # Try again with minimal data
                    try:
                        trade_id = self.storage.save_trade(
                            ticker_id=self.inputs['ticker_id'],
                            trade=trade,
                            zone_match=None,  # Skip zone data
                            metrics=None,     # Skip metrics
                            trade_type='manual'
                        )
                        print(f"\n✓ Trade saved (basic data only)")
                        print(f"  Trade ID: {trade_id}")
                    except Exception as e2:
                        print(f"\n✗ Still unable to save: {e2}")
        else:
            print("\n✓ Trade not saved (user choice)")
        
        # Ask if user wants to enter another trade
        print("\n" + "="*60)
        another = input("Enter another trade? (y/n): ").strip().lower()
        if another == 'y':
            self.inputs = {}  # Clear inputs for new trade
            self.input_order = []
            # Re-test Polygon connection for new trade
            self._test_polygon_connection()
            self.run()

if __name__ == "__main__":
    try:
        cli = CLITradeEntry()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()