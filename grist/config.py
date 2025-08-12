"""
Configuration for Grist Co-Pilot System
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Grist Configuration
GRIST_API_KEY = os.getenv('GRIST_API_KEY', '')
GRIST_SERVER = os.getenv('GRIST_SERVER', 'http://localhost:8484')
GRIST_DOC_ID = os.getenv('GRIST_DOC_ID', '')

# Polygon Configuration  
POLYGON_API_URL = os.getenv('POLYGON_API_URL', 'http://localhost:8200/api/v1')

# Market Hours (UTC)
MARKET_OPEN_UTC = "13:30"  # 9:30 AM ET
MARKET_CLOSE_UTC = "20:00"  # 4:00 PM ET