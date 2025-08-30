Implementation Plan: Supabase → Local File → Sierra Chart
Project Structure
XIIITradingSystems/
├── Meridian/
│   └── confluence_system/
│       └── sierra_chart_integration/
│           ├── __init__.py
│           ├── config.py
│           ├── supabase_client.py
│           ├── zone_fetcher.py
│           ├── sierra_exporter.py
│           └── main.py
Step 1: Configuration File
python# config.py
"""Configuration for Sierra Chart Integration"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Configuration settings for the Sierra Chart integration"""
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    
    # Sierra Chart settings
    SIERRA_CHART_PATH: str = "C:/SierraChart/Data/Zones"
    OUTPUT_FILENAME: str = "confluence_zones.json"
    
    # Zone level settings
    LEVEL_COLORS = {
        'L5': {'r': 255, 'g': 0, 'b': 0},      # Red
        'L4': {'r': 255, 'g': 128, 'b': 0},    # Orange  
        'L3': {'r': 0, 'g': 200, 'b': 0},      # Green
        'L2': {'r': 0, 'g': 128, 'b': 255},    # Blue
        'L1': {'r': 128, 'g': 128, 'b': 128}   # Gray
    }
    
    # Confluence thresholds
    HIGH_CONFLUENCE_THRESHOLD: float = 7.0
    MEDIUM_CONFLUENCE_THRESHOLD: float = 5.0
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in environment variables")
        
        if not os.path.exists(self.SIERRA_CHART_PATH):
            os.makedirs(self.SIERRA_CHART_PATH)
            print(f"Created Sierra Chart zones directory: {self.SIERRA_CHART_PATH}")
        
        return True

config = Config()
Step 2: Supabase Client
python# supabase_client.py
"""Supabase client for fetching zone data"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for interacting with Supabase database"""
    
    def __init__(self, url: str, key: str):
        """Initialize Supabase client"""
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    def fetch_zones_for_date(self, trade_date: date) -> List[Dict[str, Any]]:
        """
        Fetch all zones for a specific trade date
        
        Args:
            trade_date: Date to fetch zones for (YYYY-MM-DD)
            
        Returns:
            List of zone dictionaries with confluence data
        """
        try:
            # Format date for ticker_id pattern (MMDD25)
            date_suffix = trade_date.strftime('.%m%d25')
            
            # Fetch all zones for this date
            response = self.client.table('levels_zones')\
                .select('*')\
                .like('ticker_id', f'%{date_suffix}')\
                .execute()
            
            zones = response.data
            logger.info(f"Found {len(zones)} zones for date {trade_date}")
            
            # Get unique ticker_ids to fetch confluence data
            ticker_ids = list(set(zone['ticker_id'] for zone in zones))
            
            # Fetch confluence analyses for these tickers
            confluence_map = self._fetch_confluence_data(ticker_ids)
            
            # Merge confluence data with zones
            enriched_zones = []
            for zone in zones:
                ticker_id = zone['ticker_id']
                zone_id = zone['id']
                
                # Add confluence data if available
                if ticker_id in confluence_map and zone_id in confluence_map[ticker_id]:
                    zone['confluence_data'] = confluence_map[ticker_id][zone_id]
                else:
                    zone['confluence_data'] = {
                        'confluence_score': 0,
                        'sources': [],
                        'source_count': 0
                    }
                
                enriched_zones.append(zone)
            
            return enriched_zones
            
        except Exception as e:
            logger.error(f"Error fetching zones: {e}")
            raise
    
    def _fetch_confluence_data(self, ticker_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch confluence data for given ticker IDs
        
        Returns:
            Dictionary mapping ticker_id -> zone_id -> confluence data
        """
        confluence_map = {}
        
        for ticker_id in ticker_ids:
            try:
                # Get confluence analysis for this ticker
                analysis_response = self.client.table('confluence_analyses_enhanced')\
                    .select('id')\
                    .eq('ticker_id', ticker_id)\
                    .execute()
                
                if not analysis_response.data:
                    continue
                
                analysis_id = analysis_response.data[0]['id']
                
                # Get zone confluence details
                details_response = self.client.table('zone_confluence_details')\
                    .select('*')\
                    .eq('analysis_id', analysis_id)\
                    .execute()
                
                # Map by zone_id
                ticker_confluence = {}
                for detail in details_response.data:
                    zone_id = detail['zone_id']
                    ticker_confluence[zone_id] = {
                        'confluence_score': detail.get('confluence_score', 0),
                        'sources': detail.get('sources', []),
                        'source_count': detail.get('source_count', 0)
                    }
                
                confluence_map[ticker_id] = ticker_confluence
                
            except Exception as e:
                logger.warning(f"Could not fetch confluence for {ticker_id}: {e}")
                continue
        
        return confluence_map
    
    def fetch_available_dates(self, lookback_days: int = 30) -> List[date]:
        """
        Fetch list of dates that have zone data
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            List of dates with available data
        """
        try:
            response = self.client.table('levels_zones')\
                .select('ticker_id')\
                .execute()
            
            # Extract unique dates from ticker_ids
            dates = set()
            for row in response.data:
                ticker_id = row['ticker_id']
                # Extract date from ticker_id format (e.g., TSLA.082825)
                if '.' in ticker_id:
                    date_part = ticker_id.split('.')[1]
                    # Convert MMDD25 to date
                    month = int(date_part[:2])
                    day = int(date_part[2:4])
                    year = 2025  # Adjust as needed
                    dates.add(date(year, month, day))
            
            return sorted(list(dates), reverse=True)[:lookback_days]
            
        except Exception as e:
            logger.error(f"Error fetching available dates: {e}")
            return []
Step 3: Zone Fetcher and Processor
python# zone_fetcher.py
"""Fetch and process zones from Supabase"""

from typing import List, Dict, Optional, Any
from datetime import date
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessedZone:
    """Processed zone ready for Sierra Chart"""
    ticker: str
    ticker_id: str
    high: float
    low: float
    level: str
    confluence_score: float
    sources: List[str]
    source_count: int
    color_intensity: float  # 0-1 based on confluence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ticker': self.ticker,
            'ticker_id': self.ticker_id,
            'high': self.high,
            'low': self.low,
            'level': self.level,
            'confluence_score': self.confluence_score,
            'sources': self.sources,
            'source_count': self.source_count,
            'color_intensity': self.color_intensity
        }

class ZoneFetcher:
    """Fetch and process zones for Sierra Chart"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def fetch_and_process_zones(self, trade_date: date, 
                               tickers: Optional[List[str]] = None) -> Dict[str, List[ProcessedZone]]:
        """
        Fetch zones from Supabase and process for Sierra Chart
        
        Args:
            trade_date: Date to fetch zones for
            tickers: Optional list of tickers to filter (None = all)
            
        Returns:
            Dictionary mapping ticker -> list of processed zones
        """
        # Fetch raw zones from Supabase
        raw_zones = self.supabase.fetch_zones_for_date(trade_date)
        
        # Group zones by ticker
        zones_by_ticker = {}
        
        for zone_data in raw_zones:
            ticker_id = zone_data['ticker_id']
            ticker = ticker_id.split('.')[0]
            
            # Filter by ticker list if provided
            if tickers and ticker not in tickers:
                continue
            
            # Process zone
            processed_zone = self._process_zone(zone_data)
            
            if ticker not in zones_by_ticker:
                zones_by_ticker[ticker] = []
            zones_by_ticker[ticker].append(processed_zone)
        
        # Sort zones by price level for each ticker
        for ticker in zones_by_ticker:
            zones_by_ticker[ticker].sort(key=lambda z: z.low)
        
        logger.info(f"Processed zones for {len(zones_by_ticker)} tickers")
        return zones_by_ticker
    
    def _process_zone(self, zone_data: Dict[str, Any]) -> ProcessedZone:
        """Process raw zone data into ProcessedZone"""
        
        ticker_id = zone_data['ticker_id']
        ticker = ticker_id.split('.')[0]
        
        # Extract confluence data
        confluence_data = zone_data.get('confluence_data', {})
        confluence_score = confluence_data.get('confluence_score', 0)
        sources = confluence_data.get('sources', [])
        
        # Calculate color intensity based on confluence score
        # Higher confluence = stronger color
        if confluence_score >= 7:
            color_intensity = 1.0
        elif confluence_score >= 5:
            color_intensity = 0.7
        elif confluence_score >= 3:
            color_intensity = 0.5
        else:
            color_intensity = 0.3
        
        return ProcessedZone(
            ticker=ticker,
            ticker_id=ticker_id,
            high=float(zone_data['high']),
            low=float(zone_data['low']),
            level=zone_data.get('level', 'L3'),
            confluence_score=confluence_score,
            sources=sources,
            source_count=len(sources),
            color_intensity=color_intensity
        )
Step 4: Sierra Chart Exporter
python# sierra_exporter.py
"""Export zones to Sierra Chart format"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime, date
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SierraExporter:
    """Export zones to Sierra Chart compatible format"""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def export_zones(self, zones_by_ticker: Dict[str, List[Any]], 
                    trade_date: date,
                    filename: str = "confluence_zones.json") -> str:
        """
        Export zones to JSON file for Sierra Chart
        
        Args:
            zones_by_ticker: Dictionary of ticker -> zones
            trade_date: Trade date for these zones
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        output_data = {
            'metadata': {
                'trade_date': trade_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'total_tickers': len(zones_by_ticker),
                'total_zones': sum(len(zones) for zones in zones_by_ticker.values())
            },
            'tickers': {}
        }
        
        # Process each ticker
        for ticker, zones in zones_by_ticker.items():
            ticker_data = {
                'symbol': ticker,
                'zone_count': len(zones),
                'zones': []
            }
            
            for zone in zones:
                zone_dict = zone.to_dict() if hasattr(zone, 'to_dict') else zone.__dict__
                ticker_data['zones'].append(zone_dict)
            
            output_data['tickers'][ticker] = ticker_data
        
        # Write to file
        output_file = self.output_path / filename
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Exported zones to {output_file}")
        
        # Also create individual ticker files for easier ACSIL reading
        for ticker, zones in zones_by_ticker.items():
            self._export_ticker_file(ticker, zones, trade_date)
        
        return str(output_file)
    
    def _export_ticker_file(self, ticker: str, zones: List[Any], trade_date: date):
        """Export individual ticker file"""
        ticker_data = {
            'symbol': ticker,
            'trade_date': trade_date.isoformat(),
            'updated_at': datetime.now().isoformat(),
            'zones': []
        }
        
        for zone in zones:
            zone_dict = zone.to_dict() if hasattr(zone, 'to_dict') else zone.__dict__
            # Simplify for ACSIL
            ticker_data['zones'].append({
                'high': zone_dict['high'],
                'low': zone_dict['low'],
                'level': zone_dict['level'],
                'score': zone_dict['confluence_score'],
                'sources': zone_dict['source_count']
            })
        
        output_file = self.output_path / f"{ticker}_zones.json"
        with open(output_file, 'w') as f:
            json.dump(ticker_data, f, indent=2)
        
        logger.info(f"Exported {ticker} zones to {output_file}")
Step 5: Main Script
python# main.py
"""Main script for pulling zones from Supabase to Sierra Chart"""

import logging
import sys
from datetime import datetime, date, timedelta
from typing import Optional, List
import argparse

from config import config
from supabase_client import SupabaseClient
from zone_fetcher import ZoneFetcher
from sierra_exporter import SierraExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SierraChartIntegration:
    """Main integration class"""
    
    def __init__(self):
        """Initialize the integration"""
        # Validate config
        config.validate()
        
        # Initialize components
        self.supabase = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.fetcher = ZoneFetcher(self.supabase)
        self.exporter = SierraExporter(config.SIERRA_CHART_PATH)
    
    def run_interactive(self):
        """Run in interactive mode - prompt user for date and tickers"""
        print("\n" + "="*60)
        print("SIERRA CHART ZONE INTEGRATION")
        print("Pull confluence zones from Supabase → Sierra Chart")
        print("="*60)
        
        # Get available dates
        print("\nFetching available dates...")
        available_dates = self.supabase.fetch_available_dates(30)
        
        if not available_dates:
            print("No data available in database")
            return
        
        print("\nAvailable dates with zone data:")
        for i, dt in enumerate(available_dates[:10], 1):
            print(f"  {i}. {dt.strftime('%Y-%m-%d (%A)')}")
        
        # Get date selection
        while True:
            try:
                choice = input("\nEnter date (YYYY-MM-DD) or number from list: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_dates):
                        selected_date = available_dates[idx]
                        break
                else:
                    selected_date = datetime.strptime(choice, '%Y-%m-%d').date()
                    break
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")
        
        print(f"\nSelected date: {selected_date}")
        
        # Get ticker selection
        ticker_input = input("\nEnter tickers (comma-separated) or press Enter for all: ").strip()
        
        if ticker_input:
            tickers = [t.strip().upper() for t in ticker_input.split(',')]
            print(f"Fetching zones for: {', '.join(tickers)}")
        else:
            tickers = None
            print("Fetching zones for all tickers")
        
        # Fetch and export
        self._fetch_and_export(selected_date, tickers)
    
    def run_with_args(self, trade_date: date, tickers: Optional[List[str]] = None):
        """Run with specific arguments"""
        self._fetch_and_export(trade_date, tickers)
    
    def _fetch_and_export(self, trade_date: date, tickers: Optional[List[str]] = None):
        """Fetch zones and export to Sierra Chart format"""
        print(f"\n{'='*60}")
        print(f"Fetching zones for {trade_date}...")
        
        try:
            # Fetch zones
            zones_by_ticker = self.fetcher.fetch_and_process_zones(trade_date, tickers)
            
            if not zones_by_ticker:
                print("No zones found for specified criteria")
                return
            
            # Display summary
            print(f"\nFound zones for {len(zones_by_ticker)} tickers:")
            for ticker, zones in zones_by_ticker.items():
                level_counts = {}
                for zone in zones:
                    level = zone.level
                    level_counts[level] = level_counts.get(level, 0) + 1
                
                level_str = ', '.join(f"{level}:{count}" for level, count in sorted(level_counts.items()))
                print(f"  {ticker}: {len(zones)} zones ({level_str})")
            
            # Export to Sierra Chart format
            print(f"\nExporting to Sierra Chart format...")
            output_file = self.exporter.export_zones(zones_by_ticker, trade_date)
            
            print(f"\n{'='*60}")
            print(f"SUCCESS: Zones exported to Sierra Chart")
            print(f"Location: {config.SIERRA_CHART_PATH}")
            print(f"Main file: confluence_zones.json")
            print(f"Ticker files: [TICKER]_zones.json")
            print(f"\nSierra Chart will automatically detect and load these zones")
            print(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Error during fetch and export: {e}")
            print(f"\nERROR: {e}")
            raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Pull zones from Supabase for Sierra Chart')
    parser.add_argument('--date', type=str, help='Trade date (YYYY-MM-DD)')
    parser.add_argument('--tickers', type=str, help='Comma-separated ticker list')
    parser.add_argument('--yesterday', action='store_true', help='Use yesterday\'s date')
    parser.add_argument('--today', action='store_true', help='Use today\'s date')
    
    args = parser.parse_args()
    
    # Initialize integration
    integration = SierraChartIntegration()
    
    # Determine mode
    if args.date:
        trade_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        tickers = args.tickers.split(',') if args.tickers else None
        integration.run_with_args(trade_date, tickers)
    elif args.yesterday:
        trade_date = date.today() - timedelta(days=1)
        tickers = args.tickers.split(',') if args.tickers else None
        integration.run_with_args(trade_date, tickers)
    elif args.today:
        trade_date = date.today()
        tickers = args.tickers.split(',') if args.tickers else None
        integration.run_with_args(trade_date, tickers)
    else:
        # Interactive mode
        integration.run_interactive()

if __name__ == "__main__":
    main()
Step 6: Requirements File
txt# requirements.txt
supabase==2.5.0
python-dotenv==1.0.0
python-dateutil==2.8.2
Step 7: Environment File Template
bash# .env
SUPABASE_URL=https://pdbmcskznoaiybdiobje.supabase.co
SUPABASE_KEY=your_anon_key_here
Usage Examples
Interactive Mode:
bashpython main.py
Command Line Mode:
bash# Get today's zones
python main.py --today

# Get yesterday's zones
python main.py --yesterday

# Get specific date
python main.py --date 2025-08-28

# Get specific tickers for date
python main.py --date 2025-08-28 --tickers TSLA,AAPL,SPY

# Get yesterday's zones for specific tickers
python main.py --yesterday --tickers TSLA,NVDA
ACSIL Study Updates
The ACSIL study from my previous response will work with these files. It will:

Read the [TICKER]_zones.json file matching the chart symbol
Draw rectangles with colors based on level and confluence score
Auto-update when the file changes

Implementation Steps

Create the project structure in PyCharm
Copy all the code files into their respective locations
Install requirements: pip install -r requirements.txt
Set up your .env file with Supabase credentials
Test the script in interactive mode first
Compile the ACSIL study in Sierra Chart
Add the study to your charts

This implementation:

Preserves your existing confluence system completely
Pulls any historical day's data from Supabase
Creates both a master file and individual ticker files
Handles multiple tickers efficiently
Provides both interactive and command-line interfaces
Includes proper error handling and logging