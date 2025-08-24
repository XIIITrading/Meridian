"""
Configuration for Monte Carlo intraday backtesting
"""
import os
from datetime import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Trading Parameters (All times in UTC)
TRADING_START_TIME = time(13, 30)  # 1:30 PM UTC (9:30 AM ET)
TRADING_END_TIME = time(19, 30)    # 7:30 PM UTC (3:30 PM ET)
POSITION_CLOSE_TIME = time(19, 50) # 7:50 PM UTC (3:50 PM ET)

# Zone Parameters
STOP_OFFSET = 0.05  # Stop loss offset beyond zone boundary
MIN_ZONE_SIZE = 0.10  # Minimum zone size to trade
MAX_ZONE_SIZE = 5.00  # Maximum zone size to trade

# Batch Processing
BATCH_SIZE = 1000  # Records per database insert
PROGRESS_INTERVAL = 100  # Show progress every N trades

# Default Symbol
DEFAULT_SYMBOL = 'AMD'