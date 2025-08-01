"""
Configuration management for Meridian Trading System
Handles all environment variables and application settings
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

# Add src to Python path for imports
sys.path.insert(0, str(SRC_DIR))

# Load environment variables
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

class Config:
    """Central configuration class"""
    
    # API Configuration
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    POLYGON_API_KEY: str = os.getenv('POLYGON_API_KEY', '')
    
    # Application Settings
    APP_NAME: str = "Meridian Pre-Market Trading System"
    APP_VERSION: str = "1.0.0"
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Trading Parameters
    DEFAULT_ATR_PERIOD: int = 14
    HVN_PERCENTILE_THRESHOLD: int = 80
    MAX_PRICE_LEVELS: int = 6  # 3 above, 3 below
    
    # UI Configuration
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 900
    THEME: str = 'Fusion'
    
    # Data Settings
    DECIMAL_PLACES: int = 2
    CACHE_EXPIRY_MINUTES: int = 5
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        missing = []
        
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.POLYGON_API_KEY:
            missing.append("POLYGON_API_KEY")
            
        if missing:
            print(f"Missing configuration: {', '.join(missing)}")
            print("Please check your .env file")
            return False
            
        return True
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Get data directory path"""
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir