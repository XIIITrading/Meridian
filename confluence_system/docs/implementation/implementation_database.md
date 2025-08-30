Complete Implementation Plan: Confluence CLI → Database → Monte Carlo Integration
After reviewing your Monte Carlo engine, I can see it's already well-integrated with levels_zones table. Here's a comprehensive plan that maintains backward compatibility while adding enhanced tracking capabilities.
Architecture Overview
Confluence CLI → Database (Enhanced + levels_zones) → Monte Carlo Engine
                     ↓                                      ↓
              Enhanced Tracking                    Confluence Analysis
Phase 1: Database Schema Enhancement
1.1 Keep Existing Tables
Your Monte Carlo engine already uses:

levels_zones (source for zones)
monte_carlo_batches (batch metadata)
monte_carlo_trades (individual trades)

1.2 Add Enhanced Tables for Granular Tracking
sql-- Enhanced confluence tracking (supplements levels_zones)
CREATE TABLE public.confluence_analyses_enhanced (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    ticker_id VARCHAR(20) NOT NULL,  -- Matches levels_zones.ticker_id
    ticker VARCHAR(10) NOT NULL,
    session_date DATE NOT NULL,
    analysis_datetime TIMESTAMPTZ NOT NULL,
    
    -- Link to levels_zones
    levels_zones_id UUID REFERENCES public.levels_zones(id),
    
    -- Detailed parameters
    params JSONB NOT NULL DEFAULT '{}',
    cli_version VARCHAR(10) DEFAULT '2.0',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT confluence_analyses_enhanced_pkey PRIMARY KEY (id),
    CONSTRAINT unique_enhanced_analysis UNIQUE (ticker_id, analysis_datetime)
);

-- Granular zone confluence tracking
CREATE TABLE public.zone_confluence_details (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES public.confluence_analyses_enhanced(id) ON DELETE CASCADE,
    zone_number INTEGER NOT NULL,  -- Maps to m15_zone1-6 in levels_zones
    
    -- Granular boolean tracking for Monte Carlo analysis
    has_hvn_7d BOOLEAN DEFAULT FALSE,
    has_hvn_14d BOOLEAN DEFAULT FALSE,
    has_hvn_30d BOOLEAN DEFAULT FALSE,
    has_hvn_60d BOOLEAN DEFAULT FALSE,
    
    has_cam_daily BOOLEAN DEFAULT FALSE,
    has_cam_weekly BOOLEAN DEFAULT FALSE,
    has_cam_monthly BOOLEAN DEFAULT FALSE,
    has_cam_h5 BOOLEAN DEFAULT FALSE,
    has_cam_h4 BOOLEAN DEFAULT FALSE,
    has_cam_h3 BOOLEAN DEFAULT FALSE,
    has_cam_l3 BOOLEAN DEFAULT FALSE,
    has_cam_l4 BOOLEAN DEFAULT FALSE,
    has_cam_l5 BOOLEAN DEFAULT FALSE,
    
    has_pivot_daily BOOLEAN DEFAULT FALSE,
    has_pivot_weekly BOOLEAN DEFAULT FALSE,
    
    has_pdh BOOLEAN DEFAULT FALSE,
    has_pdl BOOLEAN DEFAULT FALSE,
    has_pdc BOOLEAN DEFAULT FALSE,
    has_onh BOOLEAN DEFAULT FALSE,
    has_onl BOOLEAN DEFAULT FALSE,
    has_pwh BOOLEAN DEFAULT FALSE,
    has_pwl BOOLEAN DEFAULT FALSE,
    
    has_vwap BOOLEAN DEFAULT FALSE,
    has_ema_9 BOOLEAN DEFAULT FALSE,
    has_ema_21 BOOLEAN DEFAULT FALSE,
    has_sma_50 BOOLEAN DEFAULT FALSE,
    has_sma_200 BOOLEAN DEFAULT FALSE,
    
    -- Source details
    confluence_sources TEXT[] NOT NULL,
    source_details JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT zone_confluence_details_pkey PRIMARY KEY (id),
    CONSTRAINT unique_zone_detail UNIQUE (analysis_id, zone_number)
);

-- Add indexes
CREATE INDEX idx_zone_confluence_analysis ON zone_confluence_details(analysis_id);
CREATE INDEX idx_zone_confluence_sources ON zone_confluence_details USING GIN(confluence_sources);
CREATE INDEX idx_zone_confluence_hvn ON zone_confluence_details(has_hvn_7d, has_hvn_14d, has_hvn_30d);
Phase 2: Create Database Module for Confluence CLI
2.1 Directory Structure
confluence_system/
├── database/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── supabase_client.py
│   └── service.py
├── confluence_cli.py  (modified)
└── requirements.txt   (updated)
2.2 Create database/config.py
python"""
Database configuration for Confluence System
Compatible with existing levels_zones infrastructure
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
else:
    # Try current directory
    load_dotenv()

# Supabase configuration (same as Monte Carlo)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

def validate_config():
    """Validate required configuration"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY in environment")
        return False
    return True
2.3 Create database/models.py
python"""
Data models matching levels_zones structure
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal

@dataclass
class ZoneConfluenceDetail:
    """Detailed confluence for a single zone"""
    zone_number: int
    confluence_sources: List[str]
    
    # Granular tracking
    has_hvn_7d: bool = False
    has_hvn_14d: bool = False
    has_hvn_30d: bool = False
    has_hvn_60d: bool = False
    
    has_cam_daily: bool = False
    has_cam_weekly: bool = False
    has_cam_monthly: bool = False
    has_cam_h3: bool = False
    has_cam_l3: bool = False
    
    has_pdh: bool = False
    has_pdl: bool = False
    has_pdc: bool = False
    has_onh: bool = False
    has_onl: bool = False
    
    has_vwap: bool = False
    
    source_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LevelsZonesRecord:
    """Record matching levels_zones table structure"""
    ticker_id: str
    ticker: str
    session_date: date
    
    # Weekly levels
    weekly_wl1: Optional[float] = None
    weekly_wl2: Optional[float] = None
    weekly_wl3: Optional[float] = None
    weekly_wl4: Optional[float] = None
    
    # Daily levels
    daily_dl1: Optional[float] = None
    daily_dl2: Optional[float] = None
    daily_dl3: Optional[float] = None
    daily_dl4: Optional[float] = None
    
    # M15 zones (up to 6)
    zones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metrics
    current_price: Optional[float] = None
    atr_daily: Optional[float] = None
    atr_15min: Optional[float] = None
    
    # Analysis results
    zones_ranked_text: Optional[str] = None
2.4 Create database/supabase_client.py
python"""
Supabase client for Confluence System
Maintains compatibility with levels_zones for Monte Carlo
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
from decimal import Decimal

from .models import LevelsZonesRecord, ZoneConfluenceDetail

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client with levels_zones compatibility"""
    
    def __init__(self, url: str, key: str):
        """Initialize client"""
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    def save_to_levels_zones(self, cli_output: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save CLI output to levels_zones table for Monte Carlo compatibility
        
        Args:
            cli_output: Output from confluence_cli.py
            
        Returns:
            Tuple of (success, ticker_id)
        """
        try:
            # Parse analysis time to get date
            analysis_dt = datetime.fromisoformat(cli_output['analysis_time'])
            session_date = analysis_dt.date()
            
            # Create ticker_id in expected format (TICKER.MMDDYY)
            ticker = cli_output['symbol']
            date_str = session_date.strftime('%m%d%y')
            ticker_id = f"{ticker}.{date_str}"
            
            # Build levels_zones record
            record = {
                'ticker_id': ticker_id,
                'ticker': ticker,
                'session_date': session_date.isoformat(),
                'is_live': True,
                'analysis_datetime': datetime.now().isoformat(),
                'analysis_status': 'completed',
                
                # Price and ATR
                'current_price': cli_output['current_price'],
                'pre_market_price': cli_output['current_price'],  # Use current as pre-market
                'atr_daily': cli_output['metrics']['atr_daily'],
                'atr_15min': cli_output['metrics']['atr_15min'],
                
                # Weekly levels
                'weekly_wl1': cli_output['parameters']['weekly_levels'][0],
                'weekly_wl2': cli_output['parameters']['weekly_levels'][1],
                'weekly_wl3': cli_output['parameters']['weekly_levels'][2],
                'weekly_wl4': cli_output['parameters']['weekly_levels'][3],
                
                # Daily levels
                'daily_dl1': cli_output['parameters']['daily_levels'][0],
                'daily_dl2': cli_output['parameters']['daily_levels'][1],
                'daily_dl3': cli_output['parameters']['daily_levels'][2],
                'daily_dl4': cli_output['parameters']['daily_levels'][3],
                
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add M15 zones (up to 6)
            for i, level in enumerate(cli_output['levels'][:6], 1):
                record[f'm15_zone{i}_level'] = (level['low'] + level['high']) / 2
                record[f'm15_zone{i}_high'] = level['high']
                record[f'm15_zone{i}_low'] = level['low']
                record[f'm15_zone{i}_date'] = session_date.isoformat()
                record[f'm15_zone{i}_time'] = analysis_dt.time().isoformat()
                record[f'm15_zone{i}_confluence_score'] = level['score']
                record[f'm15_zone{i}_confluence_level'] = level['confluence']
                record[f'm15_zone{i}_confluence_count'] = level.get('source_count', 0)
            
            # Fill remaining zones with None
            for i in range(len(cli_output['levels']) + 1, 7):
                record[f'm15_zone{i}_level'] = None
                record[f'm15_zone{i}_high'] = None
                record[f'm15_zone{i}_low'] = None
                record[f'm15_zone{i}_date'] = None
                record[f'm15_zone{i}_time'] = None
                record[f'm15_zone{i}_confluence_score'] = None
                record[f'm15_zone{i}_confluence_level'] = None
                record[f'm15_zone{i}_confluence_count'] = None
            
            # Upsert to handle re-runs
            result = self.client.table('levels_zones')\
                .upsert(record, on_conflict='ticker_id')\
                .execute()
            
            if result.data:
                logger.info(f"Saved to levels_zones: {ticker_id}")
                return True, ticker_id
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error saving to levels_zones: {e}")
            return False, None
    
    def save_enhanced_confluence(self, cli_output: Dict[str, Any], 
                                ticker_id: str) -> bool:
        """
        Save enhanced confluence details for advanced analysis
        
        Args:
            cli_output: CLI output dictionary
            ticker_id: Ticker ID from levels_zones
            
        Returns:
            Success boolean
        """
        try:
            # Create enhanced analysis record
            analysis_data = {
                'ticker_id': ticker_id,
                'ticker': cli_output['symbol'],
                'session_date': cli_output['analysis_time'].split('T')[0],
                'analysis_datetime': cli_output['analysis_time'],
                'params': cli_output['parameters'],
                'cli_version': '2.0'
            }
            
            result = self.client.table('confluence_analyses_enhanced')\
                .insert(analysis_data)\
                .execute()
            
            if not result.data:
                return False
            
            analysis_id = result.data[0]['id']
            
            # Save zone confluence details
            zone_details = []
            for i, level in enumerate(cli_output['levels'][:6], 1):
                sources = level.get('confluence_sources', [])
                
                detail = {
                    'analysis_id': analysis_id,
                    'zone_number': i,
                    'confluence_sources': sources,
                    **self._parse_confluence_flags(sources)
                }
                zone_details.append(detail)
            
            if zone_details:
                self.client.table('zone_confluence_details')\
                    .insert(zone_details)\
                    .execute()
            
            logger.info(f"Saved enhanced confluence for {ticker_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving enhanced confluence: {e}")
            return False
    
    def _parse_confluence_flags(self, sources: List[str]) -> Dict[str, bool]:
        """Parse sources into boolean flags"""
        flags = {}
        
        # Initialize all flags to False
        flag_names = [
            'has_hvn_7d', 'has_hvn_14d', 'has_hvn_30d', 'has_hvn_60d',
            'has_cam_daily', 'has_cam_weekly', 'has_cam_monthly',
            'has_cam_h3', 'has_cam_l3',
            'has_pdh', 'has_pdl', 'has_pdc', 'has_onh', 'has_onl',
            'has_vwap'
        ]
        
        for flag in flag_names:
            flags[flag] = False
        
        # Parse sources
        for source in sources:
            source_upper = source.upper()
            
            if 'HVN_7D' in source_upper:
                flags['has_hvn_7d'] = True
            elif 'HVN_14D' in source_upper:
                flags['has_hvn_14d'] = True
            elif 'HVN_30D' in source_upper:
                flags['has_hvn_30d'] = True
            
            if 'CAM' in source_upper:
                if 'DAILY' in source_upper:
                    flags['has_cam_daily'] = True
                elif 'WEEKLY' in source_upper:
                    flags['has_cam_weekly'] = True
                
                if 'H3' in source_upper or 'R3' in source_upper:
                    flags['has_cam_h3'] = True
                elif 'L3' in source_upper or 'S3' in source_upper:
                    flags['has_cam_l3'] = True
            
            if 'PDH' in source_upper:
                flags['has_pdh'] = True
            elif 'PDL' in source_upper:
                flags['has_pdl'] = True
            elif 'PDC' in source_upper:
                flags['has_pdc'] = True
            
            if 'VWAP' in source_upper:
                flags['has_vwap'] = True
        
        return flags
    
    def check_existing(self, ticker_id: str) -> bool:
        """Check if ticker_id already exists in levels_zones"""
        try:
            result = self.client.table('levels_zones')\
                .select('ticker_id')\
                .eq('ticker_id', ticker_id)\
                .execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error checking existing: {e}")
            return False
2.5 Create database/service.py
python"""
Database service layer - orchestrates all database operations
"""
import logging
from typing import Dict, Any, Optional, Tuple
from .supabase_client import SupabaseClient
from .config import SUPABASE_URL, SUPABASE_KEY, validate_config

logger = logging.getLogger(__name__)

class DatabaseService:
    """High-level database service"""
    
    def __init__(self):
        """Initialize service"""
        self.client = None
        self.enabled = False
        
        try:
            if validate_config():
                self.client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
                self.enabled = True
                logger.info("Database service initialized")
        except Exception as e:
            logger.warning(f"Database disabled: {e}")
    
    def save_cli_output(self, cli_output: Dict[str, Any], 
                       skip_existing: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Save CLI output to both levels_zones and enhanced tables
        
        Args:
            cli_output: Output from confluence_cli
            skip_existing: Skip if already exists
            
        Returns:
            Tuple of (success, ticker_id)
        """
        if not self.enabled:
            logger.warning("Database service is disabled")
            return False, None
        
        try:
            # Generate ticker_id
            ticker = cli_output['symbol']
            date = datetime.fromisoformat(cli_output['analysis_time']).date()
            ticker_id = f"{ticker}.{date.strftime('%m%d%y')}"
            
            # Check existing if requested
            if skip_existing and self.client.check_existing(ticker_id):
                logger.info(f"Skipping existing {ticker_id}")
                return False, ticker_id
            
            # Save to levels_zones (for Monte Carlo compatibility)
            success, ticker_id = self.client.save_to_levels_zones(cli_output)
            
            if success:
                # Also save enhanced confluence details
                self.client.save_enhanced_confluence(cli_output, ticker_id)
                
                logger.info(f"Successfully saved {ticker_id}")
                return True, ticker_id
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error saving CLI output: {e}")
            return False, None
Phase 3: Modify confluence_cli.py
3.1 Update CLI with Database Support
python# Add to imports at top of confluence_cli.py
try:
    from database.service import DatabaseService
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Note: Database module not available. Install dependencies for database support.")

# Add to parse_arguments()
parser.add_argument(
    '--save-db',
    action='store_true',
    help='Save results to Supabase database (levels_zones table)'
)

parser.add_argument(
    '--skip-existing',
    action='store_true',
    help='Skip if analysis already exists in database'
)

# Modify main() function - add after results generation
def main():
    """Main execution"""
    args = parse_arguments()
    
    # Initialize database if requested
    db_service = None
    if args.save_db:
        if not DB_AVAILABLE:
            print("Error: Database module not available. Install requirements:")
            print("  pip install supabase python-dotenv")
            sys.exit(1)
        
        db_service = DatabaseService()
        if not db_service.enabled:
            print("Error: Database service could not initialize. Check .env file.")
            sys.exit(1)
    
    try:
        # Run analysis
        results = run_analysis(args)
        
        # Display results (existing code)
        if args.output in ['terminal', 'both']:
            display_terminal_output(results)
        
        # Save to database if requested
        if args.save_db and db_service:
            print("\n" + "="*60)
            print("SAVING TO DATABASE")
            print("="*60)
            
            success, ticker_id = db_service.save_cli_output(
                results, 
                skip_existing=args.skip_existing
            )
            
            if success:
                print(f"✓ Saved to database")
                print(f"  Ticker ID: {ticker_id}")
                print(f"  Zones: {len(results['levels'][:6])}")
                print(f"\nReady for Monte Carlo analysis:")
                print(f"  python main.py {ticker_id}")
            elif args.skip_existing:
                print(f"✓ Already exists: {ticker_id}")
            else:
                print("✗ Failed to save to database")
        
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
Phase 4: Testing Plan
4.1 Test Database Connection
bash# Create test script: test_db_connection.py
python -c "
from database.config import validate_config
from database.service import DatabaseService

service = DatabaseService()
if service.enabled:
    print('✓ Database connection successful')
else:
    print('✗ Database connection failed')
"
4.2 Test CLI Without Database
bash# Test basic CLI functionality
python confluence_cli.py AAPL 2025-01-15 14:30 \
    -w 450 445 440 435 \
    -d 448 446 443 441 \
    --output terminal
4.3 Test CLI With Database Save
bash# Test database save
python confluence_cli.py AAPL 2025-01-15 14:30 \
    -w 450 445 440 435 \
    -d 448 446 443 441 \
    --save-db \
    --verbose
4.4 Test Monte Carlo Integration
bash# After saving to database, test Monte Carlo
cd ../backtest_engine/monte-carlo
python main.py AAPL.011525
4.5 Create Integration Test Script
python# integration_test.py
"""
Full integration test: Confluence CLI → Database → Monte Carlo
"""
import subprocess
import time
from datetime import datetime

def run_integration_test():
    # Test parameters
    ticker = "TEST"
    date = datetime.now().strftime("%Y-%m-%d")
    time_str = "14:30"
    
    print("="*60)
    print("INTEGRATION TEST")
    print("="*60)
    
    # Step 1: Run confluence CLI with database save
    print("\n[1] Running Confluence Analysis...")
    cmd = [
        "python", "confluence_system/confluence_cli.py",
        ticker, date, time_str,
        "-w", "100", "98", "96", "94",
        "-d", "99", "97", "95", "93",
        "--save-db"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"✗ CLI failed: {result.stderr}")
        return False
    
    print("✓ Confluence analysis complete")
    
    # Extract ticker_id
    ticker_id = f"{ticker}.{datetime.strptime(date, '%Y-%m-%d').strftime('%m%d%y')}"
    print(f"  Ticker ID: {ticker_id}")
    
    # Step 2: Verify in database
    print("\n[2] Verifying Database...")
    from database.service import DatabaseService
    service = DatabaseService()
    exists = service.client.check_existing(ticker_id)
    
    if not exists:
        print("✗ Data not found in database")
        return False
    
    print("✓ Data saved to levels_zones")
    
    # Step 3: Run Monte Carlo
    print("\n[3] Running Monte Carlo...")
    cmd = ["python", "backtest_engine/monte-carlo/main.py", ticker_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Monte Carlo failed: {result.stderr}")
        return False
    
    print("✓ Monte Carlo analysis complete")
    
    print("\n" + "="*60)
    print("✓ INTEGRATION TEST PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    run_integration_test()
Phase 5: Enhanced Monte Carlo Analysis
5.1 Update Monte Carlo to Use Enhanced Confluence
python# Add to monte-carlo/analysis.py
def analyze_by_detailed_confluence(self, df: pd.DataFrame) -> Dict:
    """
    Analyze using granular confluence data from zone_confluence_details
    """
    # Query enhanced confluence data
    from config import SUPABASE_URL, SUPABASE_KEY
    from supabase import create_client
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get zone confluence details
    confluence_stats = {}
    
    # Analyze specific confluence combinations
    combinations = [
        ('HVN_30D + CAM_S3', ['has_hvn_30d', 'has_cam_l3']),
        ('PDL + VWAP', ['has_pdl', 'has_vwap']),
        ('CAM_Daily + Weekly', ['has_cam_daily', 'has_cam_weekly']),
    ]
    
    for name, flags in combinations:
        # Filter trades matching this confluence
        # Implementation depends on joining with zone_confluence_details
        pass
    
    return confluence_stats
Implementation Order for Claude Code

Phase 1: Database Setup (30 min)

Create SQL tables in Supabase
Test table creation


Phase 2: Database Module (45 min)

Create database/ directory structure
Implement config.py
Implement models.py
Implement supabase_client.py
Implement service.py
Test database connection


Phase 3: CLI Integration (30 min)

Modify confluence_cli.py
Add database arguments
Test CLI with database save
Verify data in levels_zones table


Phase 4: Monte Carlo Test (15 min)

Test existing Monte Carlo with new data
Verify zones are loaded correctly
Run single day analysis


Phase 5: Integration Testing (30 min)

Create integration test script
Test full pipeline
Debug any issues


Phase 6: Enhanced Analysis (Optional, 45 min)

Add queries for granular confluence
Create confluence effectiveness reports
Generate recommendations



Quick Start Commands
bash# 1. Install dependencies
pip install supabase python-dotenv

# 2. Set up .env file
echo "SUPABASE_URL=your-url" >> .env
echo "SUPABASE_KEY=your-key" >> .env

# 3. Test database connection
python -c "from database.service import DatabaseService; s = DatabaseService(); print('DB enabled:', s.enabled)"

# 4. Run confluence analysis with save
python confluence_cli.py AAPL 2025-01-15 14:30 -w 450 445 440 435 -d 448 446 443 441 --save-db

# 5. Run Monte Carlo
cd ../backtest_engine/monte-carlo
python main.py AAPL.011525

# 6. View results in database
# Check Supabase dashboard for levels_zones and monte_carlo_trades tables
This implementation maintains full backward compatibility with your existing Monte Carlo engine while adding enhanced tracking capabilities for future analysis improvements.