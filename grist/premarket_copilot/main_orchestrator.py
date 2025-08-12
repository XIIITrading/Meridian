"""
Main Orchestrator for Grist Co-Pilot System
Coordinates data fetching, calculations, and Grist updates
"""

import sys
import os
from datetime import datetime, date
import logging
from typing import Optional

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data import PolygonBridge, TradingSession
from scripts.atr_calculations import ATRCalculator
from scripts.grist_integration import GristUpdater
from config import GRIST_API_KEY, GRIST_SERVER, GRIST_DOC_ID

logger = logging.getLogger(__name__)

def process_session(ticker: str, analysis_date: Optional[date] = None):
    """Process a complete trading session"""
    
    if analysis_date is None:
        analysis_date = date.today()
    
    ticker_id = f"{ticker}.{analysis_date.strftime('%m%d%y')}"
    
    print(f"Processing {ticker_id}...")
    
    # Step 1: Calculate ATRs
    print("Calculating ATR values...")
    calculator = ATRCalculator()
    atr_results = calculator.get_all_atrs(ticker, analysis_date)
    
    if 'error' in atr_results:
        print(f"Error: {atr_results['error']}")
        return False
    
    # Display results
    print(f"\n📊 ATR Results for {ticker_id}")
    print("-" * 40)
    if atr_results['atr_5min']:
        print(f"5-Minute ATR:  {atr_results['atr_5min']:.4f}")
    if atr_results['atr_15min']:
        print(f"15-Minute ATR: {atr_results['atr_15min']:.4f}")
    if atr_results['atr_2hr']:
        print(f"2-Hour ATR:    {atr_results['atr_2hr']:.4f}")
    if atr_results['daily_atr']:
        print(f"Daily ATR:     {atr_results['daily_atr']:.4f}")
    print("-" * 40)
    
    # Step 2: Update Grist (if configured)
    if GRIST_API_KEY and GRIST_SERVER and GRIST_DOC_ID:
        print("\nUpdating Grist...")
        updater = GristUpdater(GRIST_API_KEY, GRIST_SERVER, GRIST_DOC_ID)
        if updater.update_market_metrics(ticker_id, ticker, analysis_date):
            print("✅ Grist updated successfully")
        else:
            print("❌ Failed to update Grist")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process trading session')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--date', help='Analysis date (YYYY-MM-DD)', 
                       default=date.today().strftime('%Y-%m-%d'))
    
    args = parser.parse_args()
    
    # Parse date
    analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    
    # Process session
    success = process_session(args.ticker.upper(), analysis_date)
    sys.exit(0 if success else 1)