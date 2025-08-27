"""
Fractal Engine Configuration
User-adjustable parameters for market structure analysis
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from Meridian root
env_path = Path('C:/XIIITradingSystems/Meridian/.env')
load_dotenv(dotenv_path=env_path)

# API Configuration
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
POLYGON_SERVER_URL = "http://localhost:8200"  # Local Polygon server

# Fractal Detection Parameters
FRACTAL_LENGTH = 11  # Number of bars on each side of pivot (must be odd) - 5 bars on each side
LOOKBACK_DAYS = 30  # Number of days of historical data to analyze

# Validation Parameters
ATR_PERIOD = 14  # Period for ATR calculation
MIN_FRACTAL_DISTANCE_ATR = 1.0  # Minimum ATR multiples between valid fractals
TIMEFRAME = "15"  # Timeframe in minutes
AGGREGATION_MULTIPLIER = 15  # For Polygon API

# Display Filters
CHECK_PRICE_OVERLAP = True  # Filter out swings with overlapping price ranges in display
MAX_DISPLAY_SWINGS = 10  # Maximum swings to show in structure analysis

# Output Configuration
OUTPUT_FORMAT = "terminal"  # Options: "terminal", "csv", "json"
SHOW_INVALID_FRACTALS = False  # Display fractals that failed ATR distance check
DECIMAL_PLACES = 5  # Price decimal precision

# Display Settings
TIMEZONE = "UTC"  # All times in UTC
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"