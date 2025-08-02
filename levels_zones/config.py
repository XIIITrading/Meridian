"""
Configuration management for Meridian Trading System
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Polygon.io Configuration (for future use)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")

# Application Settings
APP_NAME = "Meridian Trading System"
APP_VERSION = "1.0.0"
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"

# Logging Configuration
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Trading Settings
MAX_PRICE_LEVELS = 6  # 3 above, 3 below
DEFAULT_ATR_PERIOD = 14

# Validate required settings
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL not set in environment")
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY not set in environment")
    
    if errors:
        for error in errors:
            logging.error(error)
        return False
    return True

# Initialize logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / "meridian.log"),
        logging.StreamHandler()
    ]
)