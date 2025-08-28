# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\data\market_metrics.py

"""
Market Metrics Calculator using Polygon API
Provides ATR, ADR, and price metrics for zone analysis
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .polygon_client import PolygonClient

logger = logging.getLogger(__name__)


@dataclass
class MarketMetrics:
    """Market metrics for zone analysis"""
    symbol: str
    current_price: float
    atr_daily: float
    atr_m15: float
    adr_percent: float
    daily_high: float
    daily_low: float
    daily_open: float
    analysis_datetime: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'current_price': self.current_price,
            'atr_daily': self.atr_daily,
            'atr_m15': self.atr_m15,
            'adr_percent': self.adr_percent,
            'daily_high': self.daily_high,
            'daily_low': self.daily_low,
            'daily_open': self.daily_open,
            'analysis_datetime': self.analysis_datetime.isoformat()
        }


class MetricsCalculator:
    """Calculate market metrics using Polygon data"""
    
    def __init__(self, polygon_client: Optional[PolygonClient] = None):
        # IMPORTANT: Initialize with correct base URL
        self.client = polygon_client or PolygonClient(base_url="http://localhost:8200/api/v1")
        
    def calculate_metrics(self, 
                         symbol: str,
                         analysis_datetime: Optional[datetime] = None) -> Optional[MarketMetrics]:
        """
        Calculate all required metrics for a symbol
        
        Args:
            symbol: Stock ticker
            analysis_datetime: DateTime for analysis (default: now)
            
        Returns:
            MarketMetrics object or None if calculation fails
        """
        try:
            if analysis_datetime is None:
                analysis_datetime = datetime.now()
            
            # Calculate date ranges
            end_date = analysis_datetime.strftime('%Y-%m-%d')
            daily_start = (analysis_datetime - timedelta(days=30)).strftime('%Y-%m-%d')
            intraday_start = (analysis_datetime - timedelta(days=10)).strftime('%Y-%m-%d')
            
            # Fetch daily data for ATR and ADR
            logger.info(f"Fetching daily data for {symbol}")
            daily_df = self.client.fetch_bars(
                symbol, 
                daily_start,
                end_date,
                '1day'  # Use '1day' not 'day'
            )
            
            if daily_df is None or daily_df.empty:
                logger.error(f"No daily data available for {symbol}")
                return None
            
            # Calculate daily ATR
            atr_daily = self.client.calculate_atr(daily_df, period=14)
            if atr_daily is None:
                logger.error(f"Failed to calculate daily ATR for {symbol}")
                return None
            
            # Calculate ADR (Average Daily Range) as percentage
            daily_df['range'] = ((daily_df['high'] - daily_df['low']) / daily_df['close'] * 100)
            adr_percent = daily_df['range'].rolling(window=20).mean().iloc[-1]
            
            # Get latest daily values
            latest_daily = daily_df.iloc[-1]
            daily_high = float(latest_daily['high'])
            daily_low = float(latest_daily['low'])
            daily_open = float(latest_daily['open'])
            
            # Fetch 5-minute data for current price
            logger.info(f"Fetching 5-minute data for {symbol}")
            m5_df = self.client.fetch_bars(
                symbol,
                intraday_start,
                end_date,
                '5min'
            )
            
            if m5_df is not None and not m5_df.empty:
                current_price = float(m5_df.iloc[-1]['close'])
            else:
                # Fall back to daily close
                current_price = float(latest_daily['close'])
            
            # Fetch 15-minute data for M15 ATR
            logger.info(f"Fetching 15-minute data for {symbol}")
            m15_df = self.client.fetch_bars(
                symbol,
                intraday_start,
                end_date,
                '15min'
            )
            
            if m15_df is not None and not m15_df.empty:
                atr_m15 = self.client.calculate_atr(m15_df, period=14)
                if atr_m15 is None:
                    # Use a fraction of daily ATR as fallback
                    atr_m15 = atr_daily * 0.25
            else:
                # Use a fraction of daily ATR as fallback
                atr_m15 = atr_daily * 0.25
            
            # Try to get real-time price if available
            latest_price = self.client.get_latest_price(symbol)
            if latest_price is not None:
                current_price = latest_price
            
            logger.info(f"Metrics calculation complete for {symbol}")
            logger.info(f"  Current Price: ${current_price:.2f}")
            logger.info(f"  Daily ATR: ${atr_daily:.2f}")
            logger.info(f"  M15 ATR: ${atr_m15:.2f}")
            logger.info(f"  ADR%: {adr_percent:.2f}%")
            
            return MarketMetrics(
                symbol=symbol,
                current_price=current_price,
                atr_daily=atr_daily,
                atr_m15=atr_m15,
                adr_percent=adr_percent,
                daily_high=daily_high,
                daily_low=daily_low,
                daily_open=daily_open,
                analysis_datetime=analysis_datetime
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None