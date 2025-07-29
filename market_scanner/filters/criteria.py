"""
Filter criteria definitions and management.
"""
from dataclasses import dataclass
from typing import Dict

@dataclass
class FilterCriteria:
    """Configurable filter criteria with defaults."""
    min_price: float = 5.0
    max_price: float = 500.0
    min_avg_volume: float = 500_000
    min_premarket_volume: float = 300_000       
    min_premarket_volume_ratio: float = 0.002
    min_dollar_volume: float = 1_000_000          
    min_atr: float = 2.0                    
    min_atr_percent: float = 0.5 
    
    def to_dict(self) -> Dict:
        """Convert criteria to dictionary for logging/display."""
        return {
            'Price Range': f'${self.min_price} - ${self.max_price}',
            'Min Avg Volume': f'{self.min_avg_volume:,.0f} shares',
            'Min PM Volume': f'{self.min_premarket_volume:,.0f} shares',
            'Min PM Volume Ratio': f'{self.min_premarket_volume_ratio:.1%}',
            'Min Dollar Volume': f'${self.min_dollar_volume:,.0f}',
            'Min ATR': f'${self.min_atr}',
            'Min ATR %': f'{self.min_atr_percent}%'
        }
    
    @classmethod
    def from_profile(cls, profile_name: str):
        """Create FilterCriteria from a pre-defined profile."""
        from ..config.filter_profiles import get_filter_profile
        
        profile = get_filter_profile(profile_name)
        return cls(
            min_price=profile.min_price,
            max_price=profile.max_price,
            min_avg_volume=profile.min_avg_volume,
            min_premarket_volume=profile.min_premarket_volume,
            min_premarket_volume_ratio=profile.min_premarket_volume_ratio,
            min_dollar_volume=profile.min_dollar_volume,
            min_atr=profile.min_atr,
            min_atr_percent=profile.min_atr_percent
        )