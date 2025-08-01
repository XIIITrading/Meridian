Meridian Pre-Market Trading System - Updated Project Documentation
Project Overview
Project Name: Meridian Pre-Market Trading System
Location: levels_zones/
Purpose: A PyQt6 desktop application for pre-market trading analysis that combines manual data entry with automated confluence calculations using Polygon.io market data and Supabase for storage.
Current Status
Phase: Phase 2 - Data Models & Database Schema
Completed:

✅ Phase 1: Project Foundation (Complete)

Created directory structure
Set up virtual environment
Created base configuration files
Initialized version control


✅ Phase 2: Data Models & Database Schema (Partially Complete)

Created Python data models (models.py)
Designed Supabase database schema with historical tracking
Created Supabase client wrapper (supabase_client.py)



Next Step: Create data validation layer, then move to Phase 3 (UI Development)
Trading System Context
Overview
The Meridian pre-market system builds confluence around M15 Market Structure analysis to identify high-probability trading opportunities. This systematic approach combines multiple timeframe analysis with precise entry and exit models for intraday trading.
Core Purpose

Build confluence around M15 Market Structure system
Identify areas of interest within price action and structure on the 15-minute timeframe
Utilize Order Blocks to outline zones where significant price movements occur
Achieve favorable risk-to-reward ratios through structured zone analysis

Key Features

Manual Data Entry: Weekly/Daily trend analysis, M15 market structure levels
Automated Calculations: HVN zones, Camarilla pivots, ATR calculations
Confluence Algorithm: Ranks trading levels by probability of significance
Data Persistence: Supabase integration for storing and retrieving analysis
Market Data Integration: Polygon.io Max tier for real-time and historical data

Complete Implementation Plan
✅ Phase 1: Project Foundation (COMPLETED)

✅ Define project architecture
✅ Create directory structure
✅ Set up development environment
✅ Create base configuration files
✅ Initialize version control

🔄 Phase 2: Data Models & Database Schema (IN PROGRESS)

✅ Define Python data models (dataclasses)
✅ Create Supabase database schema
✅ Create Supabase client wrapper
⏳ Create data validation layer
⏳ Set up database migrations

Phase 3: UI Development

Create main application window
Build Overview section widget
Build Weekly Data section widget
Build Daily Data section widget
Build M15 Market Structure widget
Create calculated metrics display tabs

Phase 4: Complete Integration

Implement save/load functionality in UI
Add data synchronization
Connect UI to Supabase client

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

Project Structure
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
│   │   ├── models.py          # ✅ CREATED - Data structures/classes
│   │   ├── supabase_client.py # ✅ CREATED - Database operations
│   │   ├── polygon_client.py  # Market data API
│   │   ├── validators.py      # ⏳ NEXT - Data validation
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
Created Files Summary
1. Configuration Files

requirements.txt - Python dependencies
.env.example - Environment variable template
.gitignore - Git ignore patterns
config.py - Central configuration class
main.py - Application entry point
setup.py - Package setup

2. Data Models (src/data/models.py)
Created comprehensive data models including:

TrendDirection enum
PriceLevel dataclass with unique level_id
WeeklyData and DailyData dataclasses
TradingSession main container class
CalculatedMetrics for storing calculations

3. Supabase Client (src/data/supabase_client.py)
Created database wrapper with methods for:

CRUD operations on trading sessions
Analysis run tracking
Saving calculated metrics (HVN, Camarilla, Confluence)
Historical data preservation

4. Database Schema
Designed complete PostgreSQL schema with:

Trading sessions table
Price levels table with unique IDs
Analysis runs tracking
HVN zones, Camarilla levels, Confluence scores tables
Performance metrics tracking
Useful views for querying

Key Technical Decisions Made

Price Level Identification: Using unique IDs format TICKER_ID_L001 instead of simple numbering
Historical Tracking: All calculations linked to analysis runs for complete audit trail
Decimal Precision: Using Python's Decimal type for all price calculations
Data Validation: Built into model __post_init__ methods
Error Handling: Comprehensive try/except blocks in database operations

Next Implementation Steps
Immediate Next: Data Validation Layer (src/data/validators.py)
Create validation functions for:

Price level validation
Trading session data completeness
ATR calculations validation
Date/time consistency checks

Then: Begin UI Development (Phase 3)

Create src/ui/main_window.py
Build the overview widget
Implement weekly data entry form
Create M15 level input interface

Environment Setup Required
bash# Activate virtual environment
.\venv\Scripts\Activate.ps1  # PowerShell

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
Copy-Item -Path ".env.example" -Destination ".env"
# Edit .env with actual API keys

# Apply database schema in Supabase dashboard
# Copy and run the SQL schema in Supabase SQL editor
Notes for Next Developer/AI

All price calculations must use Decimal type
Maintain the analysis_run_id pattern for historical tracking
The UI should follow PyQt6 patterns with proper signal/slot connections
Keep confluence algorithm modular for easy updates
Test database operations thoroughly before UI integration