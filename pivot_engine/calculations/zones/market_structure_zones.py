"""
Market Structure Zones Calculator
Creates zones from overnight and prior day levels using 5-minute ATR
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketStructureZone:
    """Represents a market structure zone"""
    name: str  # e.g., "Overnight_High", "Prior_Day_Low"
    level: float
    zone_low: float
    zone_high: float
    zone_size: float
    source_type: str  # "overnight" or "prior_day"


class MarketStructureZoneCalculator:
    """
    Calculates zones from overnight and prior day market structure levels
    using 5-minute ATR for zone creation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_market_metrics(self, data_5min: pd.DataFrame, 
                                analysis_datetime: datetime) -> Dict[str, float]:
        """
        Calculate overnight and prior day metrics from 5-minute data
        
        Args:
            data_5min: 5-minute OHLCV data with UTC timezone
            analysis_datetime: The datetime of analysis (UTC)
            
        Returns:
            Dictionary with market structure metrics
        """
        metrics = {}
        
        try:
            # Ensure timezone awareness
            if analysis_datetime.tzinfo is None:
                analysis_datetime = pd.Timestamp(analysis_datetime).tz_localize('UTC')
            else:
                analysis_datetime = pd.Timestamp(analysis_datetime).tz_convert('UTC')
            
            # Calculate prior day boundaries (13:30 - 20:00 UTC)
            prior_day = analysis_datetime - timedelta(days=1)
            prior_day_start = prior_day.replace(hour=13, minute=30, second=0, microsecond=0)
            prior_day_end = prior_day.replace(hour=20, minute=0, second=0, microsecond=0)
            
            # Skip weekends
            while prior_day_start.weekday() >= 5:  # Saturday = 5, Sunday = 6
                prior_day_start -= timedelta(days=1)
                prior_day_end -= timedelta(days=1)
            
            # Get prior day regular session data
            prior_day_data = data_5min[
                (data_5min.index >= prior_day_start) & 
                (data_5min.index <= prior_day_end)
            ]
            
            if not prior_day_data.empty:
                metrics['prior_day_high'] = float(prior_day_data['high'].max())
                metrics['prior_day_low'] = float(prior_day_data['low'].min())
                metrics['prior_day_open'] = float(prior_day_data.iloc[0]['open'])
                metrics['prior_day_close'] = float(prior_day_data.iloc[-1]['close'])
                
                self.logger.info(f"Prior day metrics calculated: H:{metrics['prior_day_high']:.2f}, "
                               f"L:{metrics['prior_day_low']:.2f}")
            else:
                self.logger.warning("No prior day data found")
            
            # Calculate overnight boundaries (20:00 prior day to analysis time)
            overnight_start = prior_day.replace(hour=20, minute=0, second=0, microsecond=0)
            
            # Handle weekend wraparound for overnight session
            if overnight_start.weekday() == 4:  # Friday
                # Skip to Sunday night for Monday's overnight session
                if analysis_datetime.weekday() == 0:  # Monday
                    overnight_start = analysis_datetime - timedelta(days=1)
                    overnight_start = overnight_start.replace(hour=20, minute=0, second=0, microsecond=0)
            
            overnight_end = analysis_datetime
            
            # Get overnight session data
            overnight_data = data_5min[
                (data_5min.index > overnight_start) & 
                (data_5min.index <= overnight_end)
            ]
            
            if not overnight_data.empty:
                metrics['overnight_high'] = float(overnight_data['high'].max())
                metrics['overnight_low'] = float(overnight_data['low'].min())
                
                self.logger.info(f"Overnight metrics calculated: H:{metrics['overnight_high']:.2f}, "
                               f"L:{metrics['overnight_low']:.2f}")
            else:
                self.logger.warning("No overnight data found")
            
        except Exception as e:
            self.logger.error(f"Error calculating market metrics: {e}")
            
        return metrics
    
    def create_zones_from_metrics(self, metrics: Dict[str, float], 
                                 atr_5min: float) -> List[MarketStructureZone]:
        """
        Create zones from market structure metrics using 5-minute ATR
        
        Args:
            metrics: Dictionary containing market structure metrics
            atr_5min: 5-minute ATR value for zone creation
            
        Returns:
            List of MarketStructureZone objects
        """
        zones = []
        
        # Define which metrics to create zones from
        zone_configs = [
            ('overnight_high', 'Overnight High', 'overnight'),
            ('overnight_low', 'Overnight Low', 'overnight'),
            ('prior_day_high', 'Prior Day High', 'prior_day'),
            ('prior_day_low', 'Prior Day Low', 'prior_day'),
            ('prior_day_open', 'Prior Day Open', 'prior_day'),
            ('prior_day_close', 'Prior Day Close', 'prior_day'),
        ]
        
        for metric_key, zone_name, source_type in zone_configs:
            if metric_key in metrics and metrics[metric_key] > 0:
                level = metrics[metric_key]
                zone_low = level - atr_5min
                zone_high = level + atr_5min
                
                zone = MarketStructureZone(
                    name=zone_name,
                    level=level,
                    zone_low=zone_low,
                    zone_high=zone_high,
                    zone_size=atr_5min * 2,
                    source_type=source_type
                )
                zones.append(zone)
                
                self.logger.debug(f"Created zone: {zone_name} at ${level:.2f} "
                                f"(${zone_low:.2f}-${zone_high:.2f})")
        
        return zones
    
    def calculate_zones_from_data(self, data_5min: pd.DataFrame, 
                                 analysis_datetime: datetime,
                                 atr_5min: float) -> Dict[str, Any]:
        """
        Complete calculation: metrics extraction and zone creation
        
        Args:
            data_5min: 5-minute OHLCV data
            analysis_datetime: Analysis datetime
            atr_5min: 5-minute ATR for zone sizing
            
        Returns:
            Dictionary with zones and metrics
        """
        # Calculate metrics
        metrics = self.calculate_market_metrics(data_5min, analysis_datetime)
        
        # Create zones
        zones = self.create_zones_from_metrics(metrics, atr_5min)
        
        return {
            'metrics': metrics,
            'zones': zones,
            'zone_count': len(zones),
            'atr_5min': atr_5min
        }
    
    def get_zones_for_confluence(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format zones for confluence engine consumption
        
        Args:
            result: Result from calculate_zones_from_data
            
        Returns:
            List of zone dictionaries for confluence checking
        """
        if not result or 'zones' not in result:
            return []
        
        formatted_zones = []
        for zone in result['zones']:
            formatted_zones.append({
                'name': zone.name,
                'level': zone.level,
                'low': zone.zone_low,
                'high': zone.zone_high,
                'center': zone.level,
                'zone_size': zone.zone_size,
                'source_type': zone.source_type
            })
        
        return formatted_zones
    
    def format_zones_for_display(self, result: Dict[str, Any]) -> str:
        """Format zones for display in UI"""
        if not result or 'zones' not in result:
            return "No market structure zones calculated"
        
        output = []
        output.append("Market Structure Zones")
        output.append(f"5-Minute ATR: ${result.get('atr_5min', 0):.2f}")
        output.append("-" * 40)
        
        # Group by source type
        overnight_zones = [z for z in result['zones'] if z.source_type == 'overnight']
        prior_day_zones = [z for z in result['zones'] if z.source_type == 'prior_day']
        
        if overnight_zones:
            output.append("\nOvernight Session (20:00-Now UTC):")
            for zone in overnight_zones:
                output.append(f"  {zone.name}: ${zone.level:.2f}")
                output.append(f"    Zone: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}")
        
        if prior_day_zones:
            output.append("\nPrior Day Session (13:30-20:00 UTC):")
            for zone in prior_day_zones:
                output.append(f"  {zone.name}: ${zone.level:.2f}")
                output.append(f"    Zone: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}")
        
        return "\n".join(output)