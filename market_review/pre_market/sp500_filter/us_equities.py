# market_review/pre_market/sp500_filter/us_equities.py
"""
US Equities Universe - Fetches all tradeable US stocks
Uses Polygon API to get complete list of active US equities
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import json
import os
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class USEquitiesUniverse:
    """
    Manages the universe of all US equities.
    Fetches and caches the complete list of active US stocks.
    """
    
    def __init__(self, 
                 cache_dir: Optional[str] = None,
                 min_market_cap: Optional[float] = None,
                 min_avg_volume: Optional[float] = None,
                 exchanges: Optional[List[str]] = None,
                 exclude_otc: bool = True):
        """
        Initialize US Equities Universe.
        
        Args:
            cache_dir: Directory for caching ticker lists
            min_market_cap: Minimum market cap filter (for future use)
            min_avg_volume: Minimum average daily volume filter
            exchanges: List of exchanges to include (default: major US exchanges)
            exclude_otc: Exclude OTC stocks
        """
        # Cache configuration
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Filters
        self.min_market_cap = min_market_cap
        self.min_avg_volume = min_avg_volume
        self.exchanges = exchanges or ['XNYS', 'XNAS', 'XASE', 'ARCX', 'BATS']  # NYSE, NASDAQ, AMEX, ARCA, BATS
        self.exclude_otc = exclude_otc
        
        # Cache settings
        self.cache_file = self.cache_dir / 'us_equities_universe.json'
        self.cache_duration_hours = 24  # Refresh daily
        
    def get_all_tickers(self, 
                       force_refresh: bool = False,
                       ticker_types: Optional[List[str]] = None) -> List[str]:
        """
        Get all US equity tickers with optional filtering.
        
        Args:
            force_refresh: Force refresh from API instead of using cache
            ticker_types: Types to include (default: ['CS'] for common stock)
            
        Returns:
            List of ticker symbols
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            tickers = self._load_from_cache()
            if tickers:
                logger.info(f"Loaded {len(tickers)} tickers from cache")
                return tickers
        
        # Fetch from Polygon API
        logger.info("Fetching complete US equities list from Polygon...")
        tickers = self._fetch_from_polygon(ticker_types)
        
        # Save to cache
        self._save_to_cache(tickers)
        
        logger.info(f"Retrieved {len(tickers)} US equity tickers")
        return tickers
    
    def _fetch_from_polygon(self, ticker_types: Optional[List[str]] = None) -> List[str]:
        """
        Fetch all tickers from Polygon API.
        """
        # Get API key from environment
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")
        
        ticker_types = ticker_types or ['CS']  # Common Stock
        all_tickers = []
        
        # Polygon reference tickers endpoint
        url = "https://api.polygon.io/v3/reference/tickers"
        
        # Parameters for the request
        params = {
            'apiKey': api_key,
            'market': 'stocks',
            'active': 'true',
            'limit': 1000  # Max per request
        }
        
        next_url = url
        page_count = 0
        
        while next_url and page_count < 100:  # Safety limit
            try:
                if page_count == 0:
                    response = requests.get(next_url, params=params)
                else:
                    # For pagination, next_url already contains parameters
                    response = requests.get(next_url)
                
                response.raise_for_status()
                data = response.json()
                
                # Extract tickers
                for ticker_info in data.get('results', []):
                    # Apply filters
                    if not self._should_include_ticker(ticker_info, ticker_types):
                        continue
                    
                    ticker = ticker_info.get('ticker')
                    if ticker and self._is_valid_ticker(ticker):
                        all_tickers.append(ticker)
                
                # Check for next page
                next_url = data.get('next_url')
                if next_url:
                    # Append API key if not present
                    if 'apiKey' not in next_url:
                        next_url = f"{next_url}&apiKey={api_key}"
                
                page_count += 1
                
                if page_count % 5 == 0:
                    logger.info(f"Fetched {page_count} pages, total tickers: {len(all_tickers)}")
                
            except Exception as e:
                logger.error(f"Error fetching tickers (page {page_count}): {e}")
                break
        
        logger.info(f"Fetched total of {len(all_tickers)} tickers from {page_count} pages")
        return sorted(list(set(all_tickers)))  # Remove duplicates and sort
    
    def _should_include_ticker(self, ticker_info: Dict, ticker_types: List[str]) -> bool:
        """Check if ticker should be included based on filters."""
        # Check type
        if ticker_info.get('type') not in ticker_types:
            return False
        
        # Check exchange
        primary_exchange = ticker_info.get('primary_exchange', '')
        if self.exchanges and primary_exchange not in self.exchanges:
            # Also check if it's OTC
            if self.exclude_otc and 'OTC' in primary_exchange:
                return False
            elif primary_exchange and primary_exchange not in self.exchanges:
                return False
        
        # Check if delisted
        if ticker_info.get('delisted_utc'):
            return False
        
        return True
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """
        Validate ticker symbol.
        """
        # Basic validation rules
        if not ticker or len(ticker) > 5:
            return False
        
        # Exclude certain patterns for pre-market scanner
        exclude_patterns = [
            '-WS',   # Warrants
            '-UN',   # Units
            '-RT',   # Rights
            '.W',    # Warrants (alternative format)
            '.U',    # Units (alternative format)
            '.R',    # Rights (alternative format)
        ]
        
        for pattern in exclude_patterns:
            if pattern in ticker.upper():
                return False
        
        return True
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.cache_file.exists():
            return False
        
        # Check age
        cache_age = datetime.now() - datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        return cache_age < timedelta(hours=self.cache_duration_hours)
    
    def _load_from_cache(self) -> Optional[List[str]]:
        """Load tickers from cache."""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return data.get('tickers', [])
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None
    
    def _save_to_cache(self, tickers: List[str]):
        """Save tickers to cache."""
        try:
            data = {
                'tickers': tickers,
                'timestamp': datetime.now().isoformat(),
                'count': len(tickers),
                'exchanges': self.exchanges
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(tickers)} tickers to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def get_ticker_batches(self, 
                          batch_size: int = 100,
                          force_refresh: bool = False) -> List[List[str]]:
        """
        Get tickers in batches for processing.
        
        Args:
            batch_size: Number of tickers per batch
            force_refresh: Force refresh ticker list
            
        Returns:
            List of ticker batches
        """
        all_tickers = self.get_all_tickers(force_refresh)
        
        # Split into batches
        batches = []
        for i in range(0, len(all_tickers), batch_size):
            batches.append(all_tickers[i:i + batch_size])
        
        return batches


def get_us_equities(
    min_market_cap: Optional[float] = None,
    min_avg_volume: Optional[float] = None,
    exchanges: Optional[List[str]] = None,
    exclude_otc: bool = True,
    force_refresh: bool = False
) -> List[str]:
    """
    Convenience function to get US equities list.
    
    Args:
        min_market_cap: Minimum market cap filter
        min_avg_volume: Minimum average volume filter
        exchanges: List of exchanges to include
        exclude_otc: Exclude OTC stocks
        force_refresh: Force refresh from API
        
    Returns:
        List of ticker symbols
    """
    universe = USEquitiesUniverse(
        min_market_cap=min_market_cap,
        min_avg_volume=min_avg_volume,
        exchanges=exchanges,
        exclude_otc=exclude_otc
    )
    return universe.get_all_tickers(force_refresh)