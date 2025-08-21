Meridian Pre-Market Trading System - Complete Project Documentation
Project Overview
Project Name: Meridian Pre-Market Trading System
Location: levels_zones/
Purpose: A PyQt6 desktop application for pre-market trading analysis that combines manual data entry with automated confluence calculations using Polygon.io market data and Supabase for storage.
Project Context Document
Background
The Meridian pre-market system builds confluence around M15 Market Structure analysis to identify high-probability trading opportunities. This systematic approach combines multiple timeframe analysis with precise entry and exit models for intraday trading.
Key Features

Manual Data Entry: Weekly/Daily trend analysis, M15 market structure levels
Automated Calculations: HVN zones, Camarilla pivots, ATR calculations
Confluence Algorithm: Ranks trading levels by probability of significance
Data Persistence: Supabase integration for storing and retrieving analysis
Market Data Integration: Polygon.io Max tier for real-time and historical data

Current Project Status
Phase: Initial Setup
Completed: Project planning and architecture design
Next Step: Create project structure and base files
Complete Implementation Plan
Phase 1: Project Foundation (Current Phase)

 Define project architecture
 Create directory structure
 Set up development environment
 Create base configuration files
 Initialize version control

Phase 2: Data Models & Database Schema

 Define Python data models (dataclasses)
 Create Supabase database schema
 Set up database migrations
 Create data validation layer

Phase 3: UI Development

 Create main application window
 Build Overview section widget
 Build Weekly Data section widget
 Build Daily Data section widget
 Build M15 Market Structure widget
 Create calculated metrics display tabs

Phase 4: Supabase Integration

 Implement Supabase client wrapper
 Create CRUD operations for trading sessions
 Add save/load functionality to UI
 Implement data synchronization

Phase 5: Polygon.io Integration

 Create Polygon API client wrapper
 Implement historical data fetching
 Add real-time data capabilities
 Create data caching layer

Phase 6: Calculation Engines

 Implement HVN (High Volume Node) calculator
 Create Camarilla pivot calculator
 Build ATR calculation module
 Develop confluence scoring algorithm

Phase 7: Integration & Testing

 Connect all components
 Add comprehensive error handling
 Create unit tests
 Perform integration testing
 Add logging and monitoring

Project Directory Structure
levels_zones/
├── README.md                    # Project documentation
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup file
├── main.py                     # Application entry point
├── config.py                   # Configuration management
│
├── src/
│   ├── __init__.py
│   │
│   ├── ui/                     # User Interface components
│   │   ├── __init__.py
│   │   ├── main_window.py     # Main application window
│   │   ├── styles.py          # UI styling constants
│   │   └── widgets/           # Custom widget components
│   │       ├── __init__.py
│   │       ├── overview_widget.py
│   │       ├── weekly_widget.py
│   │       ├── daily_widget.py
│   │       ├── m15_widget.py
│   │       └── metrics_widget.py
│   │
│   ├── data/                   # Data layer
│   │   ├── __init__.py
│   │   ├── models.py          # Data structures/classes
│   │   ├── supabase_client.py # Database operations
│   │   ├── polygon_client.py  # Market data API
│   │   └── cache.py           # Caching layer
│   │
│   ├── calculations/           # Calculation engines
│   │   ├── __init__.py
│   │   ├── hvn_calculator.py  # High Volume Node calculations
│   │   ├── pivot_calculator.py # Camarilla pivot calculations
│   │   ├── atr_calculator.py  # ATR calculations
│   │   └── confluence.py      # Confluence scoring algorithm
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── validators.py      # Data validation
│       ├── formatters.py      # Data formatting
│       └── logger.py          # Logging configuration
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_calculations.py
│   └── test_integration.py
│
└── docs/                       # Additional documentation
    ├── setup_guide.md
    ├── user_manual.md
    └── api_reference.md
Step-by-Step Implementation Guide
Step 1: Initialize Project Structure
bash# Create the main project directory
mkdir levels_zones
cd levels_zones

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Create directory structure
mkdir -p src/{ui/widgets,data,calculations,utils} tests docs
Step 2: Create Base Files
requirements.txt:
# Core Dependencies
PyQt6==6.5.0
python-dotenv==1.0.0

# Database
supabase==2.0.0
psycopg2-binary==2.9.9

# Market Data
polygon-api-client==1.12.6

# Data Processing
pandas==2.0.3
numpy==1.24.3

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# Development
pytest==7.4.0
black==23.7.0
flake8==6.1.0
.env.example:
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Polygon.io Configuration
POLYGON_API_KEY=your_polygon_api_key

# Application Settings
DEBUG_MODE=True
LOG_LEVEL=INFO
config.py:
python"""
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
Data Models Documentation
Core Data Structures
python# src/data/models.py
from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional, Dict
from enum import Enum

class TrendDirection(Enum):
    BULL = "Bull"
    BEAR = "Bear"
    RANGE = "Range"

@dataclass
class PriceLevel:
    """Represents a significant price level"""
    line_price: Decimal
    candle_datetime: datetime
    candle_high: Decimal
    candle_low: Decimal
    level_type: str  # 'above' or 'below'
    level_number: int  # 1, 2, or 3

@dataclass
class WeeklyData:
    """Weekly analysis data"""
    trend_direction: TrendDirection
    internal_trend: TrendDirection
    position_structure: float  # Percentage
    eow_bias: TrendDirection
    notes: str

@dataclass
class DailyData:
    """Daily analysis data"""
    trend_direction: TrendDirection
    internal_trend: TrendDirection
    position_structure: float  # Percentage
    eod_bias: TrendDirection
    price_levels: List[Decimal]
    notes: str

@dataclass
class TradingSession:
    """Complete trading session data"""
    # Identification
    ticker: str
    date: date
    ticker_id: str  # Generated: TICKER.MMDDYY
    
    # Session type
    is_live: bool = True
    historical_date: Optional[date] = None
    historical_time: Optional[time] = None
    
    # Analysis data
    weekly_data: Optional[WeeklyData] = None
    daily_data: Optional[DailyData] = None
    m15_levels: List[PriceLevel] = field(default_factory=list)
    
    # Metrics
    pre_market_price: Decimal = Decimal("0.00")
    atr_5min: Decimal = Decimal("0.00")
    atr_10min: Decimal = Decimal("0.00")
    atr_15min: Decimal = Decimal("0.00")
    daily_atr: Decimal = Decimal("0.00")
    
    # Calculated fields
    atr_high: Decimal = Decimal("0.00")
    atr_low: Decimal = Decimal("0.00")
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
Database Schema
sql-- Supabase PostgreSQL Schema

-- Main trading sessions table
CREATE TABLE trading_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker_id TEXT UNIQUE NOT NULL,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    is_live BOOLEAN DEFAULT true,
    historical_date DATE,
    historical_time TIME,
    
    -- JSON columns for complex data
    weekly_data JSONB,
    daily_data JSONB,
    
    -- Metrics
    pre_market_price DECIMAL(10,2),
    atr_5min DECIMAL(10,2),
    atr_10min DECIMAL(10,2),
    atr_15min DECIMAL(10,2),
    daily_atr DECIMAL(10,2),
    atr_high DECIMAL(10,2),
    atr_low DECIMAL(10,2),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price levels table
CREATE TABLE price_levels (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    level_type TEXT NOT NULL CHECK (level_type IN ('daily', 'm15')),
    position TEXT NOT NULL CHECK (position IN ('above', 'below')),
    level_number INTEGER NOT NULL CHECK (level_number BETWEEN 1 AND 3),
    line_price DECIMAL(10,2) NOT NULL,
    candle_datetime TIMESTAMP,
    candle_high DECIMAL(10,2),
    candle_low DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calculated metrics storage
CREATE TABLE calculated_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES trading_sessions(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    timeframe TEXT,
    data JSONB NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_trading_sessions_ticker_date ON trading_sessions(ticker, date);
CREATE INDEX idx_price_levels_session_type ON price_levels(session_id, level_type);
CREATE INDEX idx_calculated_metrics_session_type ON calculated_metrics(session_id, metric_type);
Next Steps for Implementation
To Continue Development:

Copy this entire document to a new AI conversation
Tell the AI: "Continue implementing the Meridian Pre-Market Trading System. We are currently at Phase 1 and need to create the initial project files."
The AI will have full context about:

Project structure
Current progress
Next implementation steps
Code standards and patterns



Specific Next Tasks:

Create all directory structure
Set up virtual environment and install dependencies
Create the main.py entry point
Build the first UI component (Overview widget)
Set up Supabase connection and test

Key Implementation Notes:

Always use Decimal for price calculations
Implement proper error handling from the start
Create unit tests alongside each component
Document all calculation algorithms thoroughly
Use type hints throughout the codebase