# formatter/camarilla_formatter.py
from typing import Dict, List
from calculations.pivots.camarilla_engine import CamarillaResult

class CamarillaFormatter:
    """Format Camarilla results for zone discovery"""
    
    @staticmethod
    def format_for_discovery(camarilla_results: Dict[str, CamarillaResult], atr_m15: float) -> List[Dict]:
        """Convert Camarilla pivots to zone discovery format"""
        formatted = []
        
        # Key levels to use (skip minor ones)
        key_levels = {'R6', 'R5', 'R4', 'R3', 'S3', 'S4', 'S5', 'S6'}
        
        for timeframe, result in camarilla_results.items():
            if not result or not result.pivots:
                continue
            
            # Different zone widths based on timeframe
            if timeframe == 'monthly':
                zone_width = atr_m15 * 3
            elif timeframe == 'weekly':
                zone_width = atr_m15 * 2
            else:  # daily
                zone_width = atr_m15
            
            for pivot in result.pivots:
                if pivot.level_name in key_levels:
                    formatted.append({
                        'type': f'camarilla-{timeframe}',
                        'name': f'CAM_{timeframe[0].upper()}_{pivot.level_name}',
                        'level': pivot.price,
                        'low': pivot.price - zone_width/2,
                        'high': pivot.price + zone_width/2,
                        'strength': pivot.strength
                    })
        
        return formatted