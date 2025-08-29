# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\config.py

"""
Configuration for Zone-First M15 Scanner
Simplified version for CLI tool
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Scanner Configuration
class ScannerConfig:
    # API Configuration - FIXED: Remove /api/v1 since server doesn't use that path
    POLYGON_REST_URL = os.getenv('POLYGON_REST_URL', 'http://localhost:8200/api/v1')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
    
    # Scanning parameters
    ATR_SCAN_MULTIPLIER = 2.0  # Scan within 2x ATR bounds
    PRICE_INCREMENT = 0.25  # Price grid increment for zone discovery
    ZONE_SIZE_MULTIPLIER = 0.5  # Zone size = 0.5 * 15min ATR
    MIN_CONFLUENCE_LEVEL = 'L3'  # Minimum confluence level to report
    MAX_ZONES_TO_DISPLAY = 6  # Maximum zones to show
    
    # ATR periods
    ATR_PERIOD = 14
    
    # Timeframes for analysis (in days)
    HVN_TIMEFRAMES = [7, 14, 30]  # Simplified from 5 timeframes
    
    # Zone overlap threshold
    OVERLAP_THRESHOLD = 0.2  # 20% overlap required
    
    # Weight configuration for confluence scoring
    CONFLUENCE_WEIGHTS = {
        'hvn_7day': 1.0,
        'hvn_14day': 2.5,
        'hvn_30day': 5.0,
        'camarilla_daily': 0.8,
        'camarilla_weekly': 2.0,
        'camarilla_monthly': 4.0,
        'weekly_zones': 3.0,
        'daily_zones': 1.5,
        'atr_zones': 0.8,
        'daily_levels': 1.0,
    }
    
    # Confluence level thresholds
    CONFLUENCE_THRESHOLDS = {
        'L5': 12.0,
        'L4': 8.0,
        'L3': 5.0,
        'L2': 2.5,
        'L1': 0.0
    }

# ================================
# HVN POC Anchor Mode Configuration
# ================================

# Enable HVN POC anchoring by default
HVN_POC_MODE_ENABLED = True

# Multi-timeframe configuration: (days, weight)
HVN_POC_TIMEFRAMES = [
    (7, 1.0),   # 7-day: highest weight/priority
    (14, 0.7),  # 14-day: medium weight
    (30, 0.5)   # 30-day: lowest weight
]

# Zone width as multiplier of 15-min ATR
# 0.3 approximates a 5-minute ATR zone width
HVN_POC_ZONE_WIDTH_MULTIPLIER = 0.5

# Minimum POC zones to create per timeframe
HVN_POC_MIN_ZONES = 6

# Overlap threshold for filtering duplicate POCs
# 0.005 = 0.5% price difference threshold
HVN_POC_OVERLAP_THRESHOLD = 0.005

# POC Zone Discovery Weights
# Used when calculating confluence scores in HVN anchor mode
POC_MODE_WEIGHTS = {
    'hvn_poc': 3.0,      # Base weight for POC itself
    'fractal': 2.5,      # Fractal overlap weight
    'cam-monthly': 2.0,  # Monthly Camarilla
    'cam-weekly': 1.5,   # Weekly Camarilla
    'cam-daily': 1.0,    # Daily Camarilla
    'weekly': 2.0,       # Weekly levels
    'daily-zone': 1.0,   # Daily zones
    'daily-level': 0.5,  # Daily levels
    'atr': 1.0,          # ATR zones
    'market-structure': 0.8  # Market structure levels
}

# Logging configuration
import logging

def setup_logging(debug=False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_DIR / 'scanner.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('zone_scanner')

# Validate configuration
def validate_config():
    """Validate required configuration"""
    config = ScannerConfig()
    
    if not config.POLYGON_REST_URL:
        raise ValueError("POLYGON_REST_URL not configured")
    
    # Test if the URL is valid
    if not config.POLYGON_REST_URL.startswith('http'):
        raise ValueError("POLYGON_REST_URL must start with http:// or https://")
    
    return True