"""
Configuration for Monte Carlo intraday backtesting
Enhanced for Confluence System Integration
"""
import os
import sys
from datetime import time
from pathlib import Path

# Add confluence_system to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.config import SUPABASE_URL, SUPABASE_KEY
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration - Use same as database module
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

# Database Configuration - Use confluence_system database module
SUPABASE_URL = SUPABASE_URL
SUPABASE_ANON_KEY = SUPABASE_KEY

# Trading Parameters (All times in UTC)
TRADING_START_TIME = time(13, 30)  # 1:30 PM UTC (9:30 AM ET)
TRADING_END_TIME = time(19, 30)    # 7:30 PM UTC (3:30 PM ET)  
POSITION_CLOSE_TIME = time(19, 50) # 7:50 PM UTC (3:50 PM ET)

# Zone Parameters
STOP_OFFSET = 0.05  # Stop loss offset beyond zone boundary
MIN_ZONE_SIZE = 0.10  # Minimum zone size to trade
MAX_ZONE_SIZE = 5.00  # Maximum zone size to trade

# Simulation Parameters
DEFAULT_POSITION_SIZE = 1000  # Default position size in shares
MIN_R_MULTIPLE = -3.0  # Minimum R multiple to consider
MAX_R_MULTIPLE = 10.0  # Maximum R multiple to consider

# Confluence Scoring Weights (for enhanced analysis)
CONFLUENCE_WEIGHTS = {
    'L1': 1.0,  # Minimal confluence
    'L2': 1.2,  # Low confluence 
    'L3': 1.5,  # Medium confluence
    'L4': 2.0,  # High confluence
    'L5': 2.5,  # Highest confluence
}

# Batch Processing
BATCH_SIZE = 1000  # Records per database insert
PROGRESS_INTERVAL = 100  # Show progress every N trades

# Default Symbol
DEFAULT_SYMBOL = 'AMD'

# Output Configuration
EXPORT_CSV = True  # Export results to CSV by default
CSV_OUTPUT_DIR = 'output/monte_carlo'  # Output directory for CSV files

# Validation Configuration
def validate_config():
    """Validate required configuration"""
    errors = []
    
    if not POLYGON_API_KEY:
        errors.append("POLYGON_API_KEY is required")
    
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is required")
        
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY is required")
    
    return errors

def get_config_summary():
    """Get configuration summary for display"""
    return {
        'polygon_configured': bool(POLYGON_API_KEY),
        'supabase_configured': bool(SUPABASE_URL and SUPABASE_KEY),
        'trading_hours': f"{TRADING_START_TIME} - {TRADING_END_TIME} UTC",
        'stop_offset': STOP_OFFSET,
        'min_zone_size': MIN_ZONE_SIZE,
        'max_zone_size': MAX_ZONE_SIZE,
        'batch_size': BATCH_SIZE
    }