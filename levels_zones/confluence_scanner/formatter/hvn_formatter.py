# formatter/hvn_formatter.py
from typing import Dict, List
from calculations.volume.hvn_engine import TimeframeResult

class HVNFormatter:
    """Format HVN results for zone discovery"""
    
    @staticmethod
    def format_for_discovery(hvn_results: Dict[int, TimeframeResult], atr_m15: float) -> List[Dict]:
        """Convert HVN peaks to zone discovery format"""
        formatted = []
        
        for days, result in hvn_results.items():
            if not result or not result.peaks:
                continue
            
            # Take top 5 peaks per timeframe
            for peak in result.peaks[:5]:
                # Create a zone around each peak using M15 ATR
                zone_width = atr_m15 * 0.5  # Half ATR for HVN zones
                
                formatted.append({
                    'type': f'hvn-{days}d',
                    'name': f'HVN_{days}d_R{peak.rank}',
                    'level': peak.price,
                    'low': peak.price - zone_width,
                    'high': peak.price + zone_width,
                    'strength': peak.volume_percent
                })
        
        return formatted