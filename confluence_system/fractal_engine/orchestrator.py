"""
Orchestrator for fractal engine module
Coordinates all fractal detection operations
Extracted from the original fractal_engine.py CLI tool
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from .detector import FractalDetector
from .data_fetcher import DataFetcher
from . import config

class FractalOrchestrator:
    def __init__(self):
        """Initialize the fractal orchestrator with default components"""
        self.detector = None  # Will be initialized with parameters
        self.data_fetcher = DataFetcher()
        
        # Default parameters from config
        self.fractal_length = config.FRACTAL_LENGTH
        self.min_atr_distance = config.MIN_FRACTAL_DISTANCE_ATR
        self.lookback_days = config.LOOKBACK_DAYS
        
    def run_detection(self, 
                     symbol: str, 
                     analysis_time: datetime = None,
                     lookback_days: int = None,
                     fractal_length: int = None,
                     min_atr_distance: float = None) -> Dict:
        """
        Main entry point for fractal detection
        
        Args:
            symbol: Stock ticker symbol
            analysis_time: Time point for analysis (defaults to now)
            lookback_days: Days of historical data (defaults to config)
            fractal_length: Number of bars for fractal pattern (defaults to config)
            min_atr_distance: Minimum ATR distance between fractals (defaults to config)
            
        Returns:
            Dictionary containing detected fractals with metadata
        """
        # Use provided parameters or defaults
        if analysis_time is None:
            analysis_time = datetime.utcnow()
        if lookback_days is None:
            lookback_days = self.lookback_days
        if fractal_length is None:
            fractal_length = self.fractal_length
        if min_atr_distance is None:
            min_atr_distance = self.min_atr_distance
            
        # Initialize detector with parameters
        self.detector = FractalDetector(
            fractal_length=fractal_length,
            min_atr_distance=min_atr_distance
        )
        
        try:
            # Step 1: Fetch data
            print(f"[Fractal Engine] Fetching {lookback_days} days of data for {symbol}...")
            df = self._fetch_data(symbol, analysis_time, lookback_days)
            
            # Step 2: Detect fractals
            print(f"[Fractal Engine] Detecting fractals...")
            fractals = self.detector.detect_fractals(df, analysis_time)
            
            # Step 3: Apply overlap filter if configured
            if config.CHECK_PRICE_OVERLAP:
                fractals = self._apply_overlap_filter(fractals, df)
            
            # Step 4: Prepare results with metadata
            results = self._prepare_results(fractals, symbol, analysis_time, df)
            
            return results
            
        except Exception as e:
            print(f"[Fractal Engine] Error during detection: {str(e)}")
            raise
            
    def _fetch_data(self, symbol: str, end_date: datetime, lookback_days: int) -> pd.DataFrame:
        """
        Fetch historical price data
        
        Args:
            symbol: Stock ticker
            end_date: End date for data retrieval
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with OHLCV data
        """
        # Test connection first
        if not self.data_fetcher.test_connection():
            raise ConnectionError(
                f"Cannot connect to Polygon server at {config.POLYGON_SERVER_URL}"
            )
        
        # Fetch bars
        df = self.data_fetcher.fetch_bars(
            ticker=symbol,
            end_date=end_date,
            lookback_days=lookback_days,
            timeframe="minute",
            multiplier=config.AGGREGATION_MULTIPLIER
        )
        
        print(f"[Fractal Engine] Successfully fetched {len(df)} bars")
        return df
        
    def _apply_overlap_filter(self, fractals: Dict, df: pd.DataFrame) -> Dict:
        """
        Filter swings to remove those with overlapping price ranges
        
        Args:
            fractals: Dictionary with 'highs' and 'lows' lists
            df: DataFrame with price data
            
        Returns:
            Filtered fractals dictionary
        """
        # Combine all swings for filtering
        all_swings = []
        
        for high in fractals['highs']:
            high['type'] = 'high'
            all_swings.append(high)
            
        for low in fractals['lows']:
            low['type'] = 'low'
            all_swings.append(low)
        
        # Sort by datetime
        all_swings.sort(key=lambda x: x['datetime'])
        
        # Apply filter
        filtered = []
        for i, current_swing in enumerate(all_swings):
            # Get bar data
            if current_swing.get('index') is not None and current_swing['index'] < len(df):
                current_bar = {
                    'high': df.loc[current_swing['index'], 'high'],
                    'low': df.loc[current_swing['index'], 'low']
                }
            else:
                current_bar = {
                    'high': current_swing['price'],
                    'low': current_swing['price']
                }
            
            # Check for overlap with last accepted swing
            has_overlap = False
            valid_alternation = True
            
            if filtered:
                last_valid = filtered[-1]
                
                # Check type alternation
                if current_swing['type'] == last_valid['type']:
                    valid_alternation = False
                
                # Get last bar data
                if last_valid.get('index') is not None and last_valid['index'] < len(df):
                    last_bar = {
                        'high': df.loc[last_valid['index'], 'high'],
                        'low': df.loc[last_valid['index'], 'low']
                    }
                else:
                    last_bar = {
                        'high': last_valid['price'],
                        'low': last_valid['price']
                    }
                
                # Check for price overlap
                if (current_bar['low'] <= last_bar['high'] and 
                    current_bar['high'] >= last_bar['low']):
                    has_overlap = True
            
            # Add swing if it passes filters
            if valid_alternation and not has_overlap:
                filtered.append(current_swing)
        
        # Separate back into highs and lows
        filtered_fractals = {
            'highs': [s for s in filtered if s['type'] == 'high'],
            'lows': [s for s in filtered if s['type'] == 'low']
        }
        
        print(f"[Fractal Engine] Overlap filter: {len(fractals['highs'])} highs → "
              f"{len(filtered_fractals['highs'])} highs, "
              f"{len(fractals['lows'])} lows → {len(filtered_fractals['lows'])} lows")
        
        return filtered_fractals
        
    def _prepare_results(self, fractals: Dict, symbol: str, 
                        analysis_time: datetime, df: pd.DataFrame) -> Dict:
        """
        Prepare comprehensive results dictionary
        
        Args:
            fractals: Detected fractals
            symbol: Stock symbol
            analysis_time: Analysis timestamp
            df: Price data DataFrame
            
        Returns:
            Complete results dictionary with metadata
        """
        # Add bar data to each fractal
        for high in fractals['highs']:
            if high.get('index') is not None and high['index'] < len(df):
                high['bar_high'] = df.loc[high['index'], 'high']
                high['bar_low'] = df.loc[high['index'], 'low']
                high['bar_open'] = df.loc[high['index'], 'open']
                high['bar_close'] = df.loc[high['index'], 'close']
                high['bar_volume'] = df.loc[high['index'], 'volume']
                
        for low in fractals['lows']:
            if low.get('index') is not None and low['index'] < len(df):
                low['bar_high'] = df.loc[low['index'], 'high']
                low['bar_low'] = df.loc[low['index'], 'low']
                low['bar_open'] = df.loc[low['index'], 'open']
                low['bar_close'] = df.loc[low['index'], 'close']
                low['bar_volume'] = df.loc[low['index'], 'volume']
        
        # Calculate structure metrics
        structure_analysis = self._analyze_structure(fractals)
        
        return {
            'symbol': symbol,
            'analysis_time': analysis_time,
            'fractals': fractals,
            'parameters': {
                'fractal_length': self.detector.fractal_length,
                'min_atr_distance': self.detector.min_atr_distance,
                'lookback_days': self.lookback_days,
                'overlap_filter': config.CHECK_PRICE_OVERLAP
            },
            'statistics': {
                'total_highs': len(fractals['highs']),
                'total_lows': len(fractals['lows']),
                'date_range': {
                    'start': df['datetime'].min(),
                    'end': df['datetime'].max()
                }
            },
            'structure': structure_analysis
        }
        
    def _analyze_structure(self, fractals: Dict) -> Dict:
        """
        Analyze market structure from fractals
        
        Args:
            fractals: Dictionary with highs and lows
            
        Returns:
            Structure analysis dictionary
        """
        # Combine and sort all fractals
        all_swings = []
        for high in fractals['highs']:
            high_copy = high.copy()
            high_copy['type'] = 'high'
            all_swings.append(high_copy)
        for low in fractals['lows']:
            low_copy = low.copy()
            low_copy['type'] = 'low'
            all_swings.append(low_copy)
            
        all_swings.sort(key=lambda x: x['datetime'], reverse=True)
        
        if len(all_swings) < 4:
            return {'trend': 'INSUFFICIENT_DATA'}
        
        # Get recent highs and lows for trend analysis
        recent_highs = [s for s in all_swings[:6] if s['type'] == 'high']
        recent_lows = [s for s in all_swings[:6] if s['type'] == 'low']
        
        structure_info = {}
        
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Check trend
            hh = recent_highs[0]['price'] > recent_highs[1]['price']
            hl = recent_lows[0]['price'] > recent_lows[1]['price']
            lh = recent_highs[0]['price'] < recent_highs[1]['price']
            ll = recent_lows[0]['price'] < recent_lows[1]['price']
            
            if hh and hl:
                structure_info['trend'] = 'UPTREND'
                structure_info['description'] = 'Higher Highs & Higher Lows'
            elif lh and ll:
                structure_info['trend'] = 'DOWNTREND'
                structure_info['description'] = 'Lower Highs & Lower Lows'
            elif hh and ll:
                structure_info['trend'] = 'EXPANDING'
                structure_info['description'] = 'Higher Highs & Lower Lows'
            elif lh and hl:
                structure_info['trend'] = 'CONTRACTING'
                structure_info['description'] = 'Lower Highs & Higher Lows'
            else:
                structure_info['trend'] = 'MIXED'
                structure_info['description'] = 'Mixed Structure'
                
            # Add recent levels
            structure_info['recent_high'] = recent_highs[0]['price'] if recent_highs else None
            structure_info['recent_low'] = recent_lows[0]['price'] if recent_lows else None
            
            if structure_info['recent_high'] and structure_info['recent_low']:
                structure_info['range'] = structure_info['recent_high'] - structure_info['recent_low']
                
        return structure_info
    
    def get_latest_fractals(self, symbol: str, count: int = 10) -> Dict:
        """
        Get the most recent fractals for a symbol
        
        Args:
            symbol: Stock ticker
            count: Number of recent fractals to return
            
        Returns:
            Dictionary with recent fractals
        """
        results = self.run_detection(symbol)
        
        # Combine all fractals and sort by date
        all_fractals = []
        for high in results['fractals']['highs']:
            high['type'] = 'high'
            all_fractals.append(high)
        for low in results['fractals']['lows']:
            low['type'] = 'low'
            all_fractals.append(low)
            
        all_fractals.sort(key=lambda x: x['datetime'], reverse=True)
        
        return {
            'symbol': symbol,
            'recent_fractals': all_fractals[:count],
            'structure': results['structure']
        }