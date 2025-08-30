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
    zone_number: int
    high: float
    low: float
    center: float
    level: str
    confluence_level: str
    confluence_score: float
    sources: List[str]
    source_count: int
    color_intensity: float  # 0-1 based on confluence
    has_fractal: bool
    has_hvn: bool
    has_market_structure: bool
    has_atr: bool
    session_date: Optional[str] = None
    current_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ticker': self.ticker,
            'ticker_id': self.ticker_id,
            'zone_number': self.zone_number,
            'high': self.high,
            'low': self.low,
            'center': self.center,
            'level': self.level,
            'confluence_level': self.confluence_level,
            'confluence_score': self.confluence_score,
            'sources': self.sources,
            'source_count': self.source_count,
            'color_intensity': self.color_intensity,
            'confluence_flags': {
                'has_fractal': self.has_fractal,
                'has_hvn': self.has_hvn,
                'has_market_structure': self.has_market_structure,
                'has_atr': self.has_atr
            },
            'session_date': self.session_date,
            'current_price': self.current_price
        }

class ZoneFetcher:
    """Fetch and process zones for Sierra Chart"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def fetch_and_process_zones(self, trade_date: date, 
                               tickers: Optional[List[str]] = None,
                               min_confluence_score: float = 0.0) -> Dict[str, List[ProcessedZone]]:
        """
        Fetch zones from Supabase and process for Sierra Chart
        
        Args:
            trade_date: Date to fetch zones for
            tickers: Optional list of tickers to filter (None = all)
            min_confluence_score: Minimum confluence score to include
            
        Returns:
            Dictionary mapping ticker -> list of processed zones
        """
        logger.info(f"Fetching zones for date: {trade_date}")
        
        # Fetch raw zones from Supabase
        raw_zones = self.supabase.fetch_zones_for_date(trade_date)
        
        if not raw_zones:
            logger.warning(f"No zones found for {trade_date}")
            return {}
        
        # Group zones by ticker
        zones_by_ticker = {}
        
        for zone_data in raw_zones:
            ticker_id = zone_data['ticker_id']
            ticker = zone_data['ticker']
            
            # Filter by ticker list if provided
            if tickers and ticker not in tickers:
                continue
            
            # Filter by minimum confluence score
            confluence_score = zone_data.get('confluence_score', 0)
            if confluence_score < min_confluence_score:
                continue
            
            # Process zone
            try:
                processed_zone = self._process_zone(zone_data)
                
                if ticker not in zones_by_ticker:
                    zones_by_ticker[ticker] = []
                zones_by_ticker[ticker].append(processed_zone)
                
            except Exception as e:
                logger.warning(f"Error processing zone {zone_data.get('zone_number')} for {ticker}: {e}")
                continue
        
        # Sort zones by price level for each ticker
        for ticker in zones_by_ticker:
            zones_by_ticker[ticker].sort(key=lambda z: z.low)
            logger.info(f"Processed {len(zones_by_ticker[ticker])} zones for {ticker}")
        
        logger.info(f"Successfully processed zones for {len(zones_by_ticker)} tickers")
        return zones_by_ticker
    
    def _process_zone(self, zone_data: Dict[str, Any]) -> ProcessedZone:
        """Process raw zone data into ProcessedZone"""
        
        ticker_id = zone_data['ticker_id']
        ticker = zone_data['ticker']
        
        # Extract confluence data
        confluence_data = zone_data.get('confluence_data', {})
        confluence_score = confluence_data.get('confluence_score', zone_data.get('confluence_score', 0))
        sources = confluence_data.get('sources', [])
        
        # Get confluence flags
        has_fractal = confluence_data.get('has_fractal', False)
        has_hvn = confluence_data.get('has_hvn', False)
        has_market_structure = confluence_data.get('has_market_structure', False)
        has_atr = confluence_data.get('has_atr', False)
        
        # Calculate color intensity based on confluence score
        # Higher confluence = stronger color
        if confluence_score >= 9.0:
            color_intensity = 1.0      # Maximum intensity
        elif confluence_score >= 7.0:
            color_intensity = 0.8      # High intensity
        elif confluence_score >= 5.0:
            color_intensity = 0.6      # Medium intensity
        elif confluence_score >= 3.0:
            color_intensity = 0.4      # Low intensity
        else:
            color_intensity = 0.2      # Minimum intensity
        
        # Calculate center point
        high = float(zone_data['high'])
        low = float(zone_data['low'])
        center = (high + low) / 2.0
        
        return ProcessedZone(
            ticker=ticker,
            ticker_id=ticker_id,
            zone_number=zone_data.get('zone_number', 0),
            high=high,
            low=low,
            center=center,
            level=zone_data.get('level', zone_data.get('confluence_level', 'L3')),
            confluence_level=zone_data.get('confluence_level', 'L3'),
            confluence_score=float(confluence_score),
            sources=sources if isinstance(sources, list) else [],
            source_count=len(sources) if isinstance(sources, list) else confluence_data.get('source_count', 0),
            color_intensity=color_intensity,
            has_fractal=has_fractal,
            has_hvn=has_hvn,
            has_market_structure=has_market_structure,
            has_atr=has_atr,
            session_date=zone_data.get('session_date'),
            current_price=zone_data.get('current_price')
        )
    
    def get_zone_statistics(self, zones_by_ticker: Dict[str, List[ProcessedZone]]) -> Dict[str, Any]:
        """Get statistics about the processed zones"""
        
        total_zones = sum(len(zones) for zones in zones_by_ticker.values())
        level_counts = {}
        confluence_stats = {'min': float('inf'), 'max': 0, 'avg': 0}
        
        all_scores = []
        
        for ticker, zones in zones_by_ticker.items():
            for zone in zones:
                # Count levels
                level = zone.confluence_level
                level_counts[level] = level_counts.get(level, 0) + 1
                
                # Collect scores
                all_scores.append(zone.confluence_score)
        
        if all_scores:
            confluence_stats['min'] = min(all_scores)
            confluence_stats['max'] = max(all_scores)
            confluence_stats['avg'] = sum(all_scores) / len(all_scores)
        
        return {
            'total_tickers': len(zones_by_ticker),
            'total_zones': total_zones,
            'level_distribution': level_counts,
            'confluence_stats': confluence_stats,
            'zones_per_ticker': {ticker: len(zones) for ticker, zones in zones_by_ticker.items()}
        }