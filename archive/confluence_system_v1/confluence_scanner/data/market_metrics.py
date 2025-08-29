# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\data\market_metrics.py

"""
Market Metrics Calculator using Polygon API
Provides ATR, ADR, price metrics, and market structure levels for zone analysis
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .polygon_client import PolygonClient

logger = logging.getLogger(__name__)


@dataclass
class MarketMetrics:
    """Market metrics for zone analysis with optional market structure levels"""
    # Core metrics (required)
    symbol: str
    current_price: float
    atr_daily: float
    atr_m15: float
    adr_percent: float
    daily_high: float
    daily_low: float
    daily_open: float
    analysis_datetime: datetime
    
    # Market structure levels (optional)
    PDH: Optional[float] = None  # Previous Day High
    PDL: Optional[float] = None  # Previous Day Low
    PDC: Optional[float] = None  # Previous Day Close
    ONH: Optional[float] = None  # Overnight High
    ONL: Optional[float] = None  # Overnight Low
    
    def to_dict(self) -> Dict:
        """Convert to dictionary including market structure levels when available"""
        base_dict = {
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
        
        # Add market structure levels if available
        structure_levels = {}
        for level_name in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL']:
            level_value = getattr(self, level_name, None)
            if level_value is not None:
                structure_levels[level_name] = level_value
                base_dict[level_name] = level_value
        
        # Add summary if any structure levels exist
        if structure_levels:
            base_dict['market_structure_available'] = True
            base_dict['structure_level_count'] = len(structure_levels)
        else:
            base_dict['market_structure_available'] = False
            base_dict['structure_level_count'] = 0
        
        return base_dict
    
    def update_market_structure(self, structure_levels: Dict[str, float]):
        """
        Update market structure levels
        
        Args:
            structure_levels: Dictionary with PDH, PDL, PDC, ONH, ONL values
        """
        for level_name, level_value in structure_levels.items():
            if level_name in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL'] and level_value is not None:
                setattr(self, level_name, float(level_value))
                logger.debug(f"Updated {level_name} to ${level_value:.2f}")
    
    def get_structure_levels(self) -> Dict[str, float]:
        """
        Get available market structure levels
        
        Returns:
            Dictionary of available structure levels
        """
        structure_levels = {}
        for level_name in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL']:
            level_value = getattr(self, level_name, None)
            if level_value is not None:
                structure_levels[level_name] = level_value
        return structure_levels
    
    def has_structure_levels(self) -> bool:
        """Check if any market structure levels are available"""
        return any(getattr(self, level, None) is not None 
                  for level in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL'])


class MetricsCalculator:
    """Calculate market metrics using Polygon data"""
    
    def __init__(self, polygon_client: Optional[PolygonClient] = None):
        # IMPORTANT: Initialize with correct base URL
        self.client = polygon_client or PolygonClient(base_url="http://localhost:8200/api/v1")
        
    def calculate_metrics(self, 
                         symbol: str,
                         analysis_datetime: Optional[datetime] = None,
                         include_market_structure: bool = False) -> Optional[MarketMetrics]:
        """
        Calculate all required metrics for a symbol
        
        Args:
            symbol: Stock ticker
            analysis_datetime: DateTime for analysis (default: now)
            include_market_structure: Whether to calculate market structure levels
            
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
            
            # Create base metrics object
            metrics = MarketMetrics(
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
            
            # Add market structure levels if requested
            if include_market_structure:
                structure_levels = self._calculate_market_structure(
                    daily_df, m5_df, analysis_datetime, symbol
                )
                if structure_levels:
                    metrics.update_market_structure(structure_levels)
                    logger.info(f"Added market structure levels: {list(structure_levels.keys())}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_market_structure(self, 
                                  daily_df, 
                                  intraday_df, 
                                  analysis_datetime: datetime,
                                  symbol: str) -> Dict[str, float]:
        """
        Calculate market structure levels (PDH, PDL, PDC, ONH, ONL)
        
        Args:
            daily_df: Daily OHLC data
            intraday_df: Intraday data for overnight calculations
            analysis_datetime: Analysis time
            symbol: Stock symbol
            
        Returns:
            Dictionary with structure levels
        """
        try:
            from ..calculations.market_structure.pd_market_structure import MarketStructureCalculator
            
            calculator = MarketStructureCalculator()
            structure_levels = calculator.calculate_all_levels(
                daily_df, intraday_df, analysis_datetime
            )
            
            logger.info(f"Market structure calculation for {symbol}: {structure_levels}")
            return structure_levels
            
        except Exception as e:
            logger.error(f"Error calculating market structure for {symbol}: {e}")
            return {}