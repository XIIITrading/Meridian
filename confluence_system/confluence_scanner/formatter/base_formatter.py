# formatter/base_formatter.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseFormatter(ABC):
    """Base class for formatting calculation results for zone discovery"""
    
    @abstractmethod
    def format_for_discovery(self, data: Any, atr_m15: float) -> List[Dict]:
        """Format data for ZoneDiscoveryEngine"""
        pass