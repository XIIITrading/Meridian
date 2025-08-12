"""
ATR Calculation Script for Grist Co-Pilot
Pulls 5-min, 15-min, 2-hour, and Daily ATR values
"""

import sys
import os
from datetime import datetime, date, timedelta, time
from decimal import Decimal
import pandas as pd
import logging
from typing import Dict, Optional, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from src.data package
from src.data import PolygonBridge, TradingSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)