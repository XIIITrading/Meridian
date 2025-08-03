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

# Application Settings Class (for compatibility with tests and UI)
class Config:
    """Application configuration class"""
    APP_NAME = "Meridian Trading System"
    APP_VERSION = "1.0.0"
    LOG_LEVEL = "INFO"
    DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
    
    # Trading Settings
    MAX_PRICE_LEVELS = 6  # 3 above, 3 below
    DEFAULT_ATR_PERIOD = 14
    
    @staticmethod
    def validate():
        """Validate configuration"""
        return validate_config()

# Module-level variables (for backward compatibility)
APP_NAME = Config.APP_NAME
APP_VERSION = Config.APP_VERSION
DEBUG_MODE = Config.DEBUG_MODE
MAX_PRICE_LEVELS = Config.MAX_PRICE_LEVELS
DEFAULT_ATR_PERIOD = Config.DEFAULT_ATR_PERIOD

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Polygon Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
POLYGON_REST_URL = os.getenv("POLYGON_REST_URL", "http://localhost:8200")  # Updated to port 8200

# Logging Configuration
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

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