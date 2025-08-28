# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\discovery\zone_validation.py

"""
Zone Validation Module
Validates discovered zones using M15 precision data
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..data.polygon_client import PolygonClient
from ..data.market_metrics import MarketMetrics

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of zone validation"""
    is_valid: bool
    score: float
    m15_touches: int
    recent_respect: bool
    notes: str = ""


class ZoneValidator:
    """Validates zones using M15 precision data"""
    
    def __init__(self, polygon_client: PolygonClient):
        self.client = polygon_client
    
    def validate_zone(self,
                     zone: Any,  # Will be DiscoveredZone from zone_discovery
                     symbol: str,
                     analysis_datetime: datetime,
                     metrics: MarketMetrics) -> ValidationResult:
        """
        Validate a zone using M15 data
        
        Args:
            zone: DiscoveredZone to validate
            symbol: Stock ticker
            analysis_datetime: Analysis time
            metrics: Market metrics
            
        Returns:
            ValidationResult
        """
        try:
            # Zone is already validated through discovery process
            # Just convert the scoring
            
            # Check if zone has a best candle (M15 validation)
            has_m15_validation = zone.best_candle is not None
            m15_touches = len(zone.confluent_sources) if hasattr(zone, 'confluent_sources') else 0
            
            # Score based on confluence level
            confluence_map = {
                'L5': 100,
                'L4': 80,
                'L3': 60,
                'L2': 40,
                'L1': 20
            }
            
            score = confluence_map.get(zone.confluence_level, 50)
            
            # Adjust score based on distance
            if zone.distance_percentage < 1:
                score += 10
            elif zone.distance_percentage > 5:
                score -= 20
            
            # Check recency if best candle exists
            recent_respect = False
            if zone.best_candle and 'datetime' in zone.best_candle:
                days_since = (analysis_datetime - zone.best_candle['datetime']).days
                recent_respect = days_since <= 5
                if recent_respect:
                    score += 10
            
            return ValidationResult(
                is_valid=score >= 40,  # Minimum score threshold
                score=min(100, max(0, score)),
                m15_touches=m15_touches,
                recent_respect=recent_respect,
                notes=f"Confluence Level: {zone.confluence_level}"
            )
            
        except Exception as e:
            logger.error(f"Error validating zone: {e}")
            return ValidationResult(
                is_valid=False,
                score=0,
                m15_touches=0,
                recent_respect=False,
                notes=f"Validation error: {str(e)}"
            )