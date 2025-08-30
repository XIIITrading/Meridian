"""Configuration for Sierra Chart Integration"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Configuration settings for the Sierra Chart integration"""
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    
    # Sierra Chart settings
    SIERRA_CHART_PATH: str = "C:/SierraChart/Data/Zones"
    OUTPUT_FILENAME: str = "confluence_zones.json"
    
    # Zone level settings
    LEVEL_COLORS = {
        'L5': {'r': 255, 'g': 0, 'b': 0},      # Red
        'L4': {'r': 255, 'g': 128, 'b': 0},    # Orange  
        'L3': {'r': 0, 'g': 200, 'b': 0},      # Green
        'L2': {'r': 0, 'g': 128, 'b': 255},    # Blue
        'L1': {'r': 128, 'g': 128, 'b': 128}   # Gray
    }
    
    # Confluence thresholds
    HIGH_CONFLUENCE_THRESHOLD: float = 7.0
    MEDIUM_CONFLUENCE_THRESHOLD: float = 5.0
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("Supabase credentials not found in environment variables")
        
        if not os.path.exists(self.SIERRA_CHART_PATH):
            os.makedirs(self.SIERRA_CHART_PATH)
            print(f"Created Sierra Chart zones directory: {self.SIERRA_CHART_PATH}")
        
        return True

config = Config()