"""
Grist Integration Script
Updates Grist tables with calculated ATR values
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal
import logging
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import PolygonBridge, TradingSession
from scripts.atr_calculations import ATRCalculator
import requests

logger = logging.getLogger(__name__)

class GristUpdater:
    """Updates Grist tables with market data"""
    
    def __init__(self, grist_api_key: str, grist_server: str, grist_doc_id: str):
        self.api_key = grist_api_key
        self.server = grist_server
        self.doc_id = grist_doc_id
        self.headers = {'Authorization': f'Bearer {api_key}'}
        self.base_url = f"{server}/api/docs/{doc_id}"
        self.calculator = ATRCalculator()
    
    def update_market_metrics(self, ticker_id: str, ticker: str, analysis_date: date):
        """
        Fetch ATR values and update Grist market_metrics table
        """
        # Calculate all ATRs
        logger.info(f"Calculating ATRs for {ticker}...")
        results = self.calculator.get_all_atrs(ticker, analysis_date)
        
        if 'error' in results:
            logger.error(f"Failed to calculate ATRs: {results['error']}")
            return False
        
        # Prepare update for Grist
        metrics_update = {
            'ticker_id': ticker_id,
            'atr_5min': float(results['atr_5min']) if results['atr_5min'] else None,
            'atr_15min': float(results['atr_15min']) if results['atr_15min'] else None,
            'atr_2hr': float(results['atr_2hr']) if results['atr_2hr'] else None,
            'daily_atr': float(results['daily_atr']) if results['daily_atr'] else None,
            'fetched_at': datetime.now().isoformat()
        }
        
        # Update Grist
        return self._update_grist_record('market_metrics', ticker_id, metrics_update)
    
    def _update_grist_record(self, table: str, ticker_id: str, data: Dict[str, Any]):
        """Update or create a record in Grist"""
        try:
            # First, try to find existing record
            url = f"{self.base_url}/tables/{table}/records"
            params = {'filter': {'ticker_id': ticker_id}}
            
            response = requests.get(url, headers=self.headers, params=params)
            existing = response.json().get('records', [])
            
            if existing:
                # Update existing record
                record_id = existing[0]['id']
                update_url = f"{self.base_url}/tables/{table}/records"
                update_data = {'records': [{'id': record_id, 'fields': data}]}
                response = requests.patch(update_url, headers=self.headers, json=update_data)
                logger.info(f"Updated {table} for {ticker_id}")
            else:
                # Create new record
                create_data = {'records': [{'fields': data}]}
                response = requests.post(url, headers=self.headers, json=create_data)
                logger.info(f"Created new {table} record for {ticker_id}")
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating Grist: {e}")
            return False