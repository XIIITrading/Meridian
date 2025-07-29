"""
Data fetching abstraction layer.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

from polygon import DataFetcher
from polygon.config import PolygonConfig

from ..config import config

logger = logging.getLogger(__name__)

class DataFetcherInterface(ABC):
    """Abstract interface for data fetchers."""
    
    @abstractmethod
    def fetch_historical(self, 
                        symbol: str,
                        start_date: datetime,
                        end_date: datetime) -> pd.DataFrame:
        """Fetch historical daily data."""
        pass
    
    @abstractmethod
    def fetch_intraday(self,
                      symbol: str,
                      start_time: datetime,
                      end_time: datetime,
                      timeframe: str = '1min') -> pd.DataFrame:
        """Fetch intraday data."""
        pass

class PolygonDataFetcher(DataFetcherInterface):
    """Polygon.io data fetcher implementation."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize Polygon fetcher."""
        self.fetcher = DataFetcher(
            config=PolygonConfig({'cache_enabled': cache_enabled})
        )
    
    def fetch_historical(self, 
                        symbol: str,
                        start_date: datetime,
                        end_date: datetime) -> pd.DataFrame:
        """Fetch historical daily data from Polygon."""
        try:
            df = self.fetcher.fetch_data(
                symbol=symbol,
                timeframe='1d',
                start_date=start_date,
                end_date=end_date,
                use_cache=True,
                validate=True,
                fill_gaps=True
            )
            return df
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_intraday(self,
                      symbol: str,
                      start_time: datetime,
                      end_time: datetime,
                      timeframe: str = '1min') -> pd.DataFrame:
        """Fetch intraday data from Polygon."""
        try:
            df = self.fetcher.fetch_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_time,
                end_date=end_time,
                use_cache=True,
                validate=True
            )
            return df
        except Exception as e:
            logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
            return pd.DataFrame()