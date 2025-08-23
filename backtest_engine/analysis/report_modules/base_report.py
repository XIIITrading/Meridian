"""
Base class for report generators
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BaseReportGenerator(ABC):
    """Abstract base class for all report generators"""
    
    def __init__(self, output_dir: str = "reports/output"):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], filename: str) -> str:
        """
        Generate report from data
        
        Args:
            data: Report data
            filename: Output filename
            
        Returns:
            Path to generated file
        """
        pass
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get the format name"""
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_keys = ['title', 'generated_at']
        for key in required_keys:
            if key not in data:
                logger.warning(f"Missing required key: {key}")
                return False
        return True