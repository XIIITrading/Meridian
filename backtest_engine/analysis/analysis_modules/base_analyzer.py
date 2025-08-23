"""
Base class for all analysis modules
Defines the interface that all analyzers must implement
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """
    Abstract base class for all analysis modules
    """
    
    def __init__(self, storage_manager, min_sample_size: int = 5):
        """
        Initialize base analyzer
        
        Args:
            storage_manager: BacktestStorageManager instance
            min_sample_size: Minimum trades for statistical significance
        """
        self.storage = storage_manager
        self.min_sample_size = min_sample_size
        self.confidence_level = 0.95
        
    @abstractmethod
    def analyze(self, trades_df: pd.DataFrame) -> Any:
        """
        Perform analysis on trades DataFrame
        
        Args:
            trades_df: DataFrame containing trade data
            
        Returns:
            Analysis results (format depends on specific analyzer)
        """
        pass
    
    @abstractmethod
    def get_analysis_name(self) -> str:
        """
        Get the name of this analysis type
        
        Returns:
            String identifier for this analysis
        """
        pass
    
    def validate_data(self, trades_df: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate that DataFrame has required columns
        
        Args:
            trades_df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if valid, False otherwise
        """
        if trades_df.empty:
            logger.warning(f"{self.get_analysis_name()}: Empty DataFrame provided")
            return False
            
        missing_columns = [col for col in required_columns if col not in trades_df.columns]
        
        if missing_columns:
            logger.warning(f"{self.get_analysis_name()}: Missing columns: {missing_columns}")
            return False
            
        return True
    
    def has_sufficient_data(self, count: int) -> bool:
        """
        Check if sample size is sufficient for analysis
        
        Args:
            count: Number of samples
            
        Returns:
            True if sufficient, False otherwise
        """
        return count >= self.min_sample_size