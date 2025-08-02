Meridian Pre-Market Trading System - Updated Implementation Plan
Project Overview
Project Name: Meridian Pre-Market Trading System
Location: levels_zones/
Purpose: A PyQt6 desktop application for pre-market trading analysis that combines manual data entry with automated confluence calculations using Polygon.io market data and Supabase for storage.
Current Status
Phase: Phase 3 - UI Development (COMPLETED)
Last Updated: August 2, 2025
✅ Phase 1: Project Foundation (COMPLETED)

✅ Created directory structure
✅ Set up virtual environment
✅ Created base configuration files (config.py, requirements.txt, .env.example)
✅ Initialized version control
✅ Created main.py entry point

✅ Phase 2: Data Models & Database Schema (COMPLETED)

✅ Created Python data models (models.py)

TrendDirection enum
PriceLevel dataclass with unique level_id
WeeklyData and DailyData dataclasses
TradingSession main container class
CalculatedMetrics for storing calculations


✅ Designed Supabase database schema with historical tracking
✅ Created Supabase client wrapper (supabase_client.py)
✅ Created data validation layer (validators.py)

Field validators
Price level validators
Trading session validators
ATR validators
DateTime validators with UTC support



✅ Phase 3: UI Development (COMPLETED)

✅ Created main application window (main_window.py)
✅ Created dark theme configuration (dark_theme.py)

RGB(35,35,35) main background
Multiple grey shades for UI elements
Zone-specific colors
Complete stylesheets for all components


✅ Built Overview widget (overview_widget.py)

Session info section (ticker, live toggle, datetime)
Weekly analysis data entry
Daily analysis data entry
ATR metrics display (calculated fields)
M15 zone data entry table (6 fixed rows)
Calculations display area (HVN & Camarilla)
M15 zones ranked section
Save to Supabase button


✅ Removed need for separate Weekly/Daily/M15 widgets (integrated into overview)
✅ All data entry consolidated into single scrollable interface

🔄 Phase 4: Database Integration (NEXT - 0% Complete)

⏳ Implement save functionality to Supabase
⏳ Add session loading from database
⏳ Create session list/picker dialog
⏳ Implement data synchronization
⏳ Add error handling for database operations
⏳ Test database connectivity

⏳ Phase 5: Polygon.io Integration (NOT STARTED)

⏳ Create Polygon API client wrapper (polygon_client.py)
⏳ Implement historical data fetching
⏳ Add real-time data capabilities
⏳ Create data caching layer
⏳ Implement ATR calculations from market data
⏳ Fetch current/open price based on datetime

⏳ Phase 6: Calculation Engines (NOT STARTED)

⏳ Implement HVN (High Volume Node) calculator

7-day, 14-day, 30-day analysis
Zone detection and ranking


⏳ Create Camarilla pivot calculator

Daily, weekly, monthly pivots
Support/resistance levels


⏳ Build ATR calculation module

5-min, 10-min, 15-min, daily ATR
ATR bands calculation


⏳ Develop confluence scoring algorithm

M15 zone ranking
Multi-factor analysis
Confluence detection



⏳ Phase 7: Integration & Testing (NOT STARTED)

⏳ Connect all components
⏳ Add comprehensive error handling
⏳ Create unit tests
⏳ Perform integration testing
⏳ Add logging and monitoring
⏳ Performance optimization

Updated Project Structure
levels_zones/
├── README.md                    # Project documentation
├── .env                        # ✅ Environment variables (local)
├── .gitignore                  # ✅ Git ignore file
├── requirements.txt            # ✅ Python dependencies
├── setup.py                    # ✅ Package setup file
├── main.py                     # ✅ Application entry point
├── config.py                   # ✅ Configuration management
│
├── src/
│   ├── __init__.py            # ✅
│   │
│   ├── ui/                     # User Interface components
│   │   ├── __init__.py        # ✅
│   │   ├── main_window.py     # ✅ Main application window
│   │   ├── dark_theme.py      # ✅ Dark theme configuration
│   │   └── widgets/           # Custom widget components
│   │       ├── __init__.py    # ✅
│   │       └── overview_widget.py  # ✅ Complete data entry interface
│   │
│   ├── data/                   # Data layer
│   │   ├── __init__.py        # ✅
│   │   ├── models.py          # ✅ Data structures/classes
│   │   ├── supabase_client.py # ✅ Database operations (needs connection)
│   │   ├── validators.py      # ✅ Data validation
│   │   ├── polygon_client.py  # ⏳ Market data API
│   │   └── cache.py           # ⏳ Caching layer
│   │
│   ├── calculations/           # Calculation engines
│   │   ├── __init__.py        # ✅
│   │   ├── hvn_calculator.py  # ⏳ High Volume Node calculations
│   │   ├── pivot_calculator.py # ⏳ Camarilla pivot calculations
│   │   ├── atr_calculator.py  # ⏳ ATR calculations
│   │   └── confluence.py      # ⏳ Confluence scoring algorithm
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py        # ✅
│       ├── validators.py      # ⏳ Additional validators
│       ├── formatters.py      # ⏳ Data formatting
│       └── logger.py          # ⏳ Logging configuration
│
├── tests/                      # Test suite
│   ├── __init__.py            # ✅
│   ├── test_models.py         # ⏳
│   ├── test_calculations.py   # ⏳
│   └── test_integration.py    # ⏳
│
└── docs/                       # Additional documentation
    ├── setup_guide.md         # ⏳
    ├── user_manual.md         # ⏳
    └── api_reference.md       # ⏳
Key Accomplishments

Complete UI implementation with all data entry fields
Professional dark theme matching original wireframe
Consolidated interface for efficient data entry
Data models ready for database integration
Validation layer implemented
Proper signal/slot architecture for UI interactions

Next Priority: Phase 4 - Database Integration

Connect Supabase client with actual credentials
Implement save_session method in supabase_client.py
Wire up Save to Supabase button to actual database operations
Create session loading functionality
Test database connectivity with sample data
Add error handling for database operations

Technical Stack

UI Framework: PyQt6 with custom dark theme
Database: Supabase (PostgreSQL)
Market Data: Polygon.io (pending)
Data Types: Decimal for price precision
Architecture: MVC pattern with signal/slot communication


Snippet for Next Conversation
I'm working on the Meridian Pre-Market Trading System. We've completed the UI (Phase 3) with a PyQt6 dark-themed interface that includes:
- Session info (ticker, datetime, live toggle)
- Weekly/Daily analysis data entry
- M15 zone entry table
- Calculated metrics display
- Save to Supabase button

Current structure:
- main_window.py: Main application window
- overview_widget.py: Complete data entry interface
- models.py: Data models (TradingSession, WeeklyData, DailyData, etc.)
- supabase_client.py: Database client wrapper (skeleton)
- validators.py: Data validation

We need to implement Phase 4 - Database Integration:
1. Connect the Supabase client with actual credentials
2. Implement the save_session method to store TradingSession data
3. Wire up the "Save to Supabase" button to actually save data
4. Add session loading functionality
5. Test the database connection

The save button emits a signal with this data structure:
{
    'ticker': str,
    'is_live': bool,
    'datetime': datetime,
    'weekly': {
        'trend_direction': str,
        'internal_trend': str,
        'position_structure': int,
        'eow_bias': str,
        'notes': str
    },
    'daily': {
        'trend_direction': str,
        'internal_trend': str,
        'position_structure': int,
        'eod_bias': str,
        'price_levels': list[float],  # 6 levels
        'notes': str
    },
    'zones': list[{
        'zone_number': int,
        'datetime': str,
        'level': str,
        'high': str,
        'low': str
    }],
    'timestamp': datetime
}

Please help implement the database connection and save functionality.