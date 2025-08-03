"""
Analysis coordinator that orchestrates all analysis operations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from analysis.hvn_analyzer import HVNAnalyzer
from analysis.camarilla_analyzer import CamarillaAnalyzer
from analysis.confluence_analyzer import ConfluenceAnalyzer
from analysis.metrics_analyzer import MetricsAnalyzer
from data.polygon_bridge import PolygonBridge

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Container for analysis request parameters"""
    ticker: str
    analysis_datetime: datetime
    session_data: Dict[str, Any]
    analysis_types: list = None  # ['hvn', 'camarilla', 'metrics', 'confluence']
    
    def __post_init__(self):
        if self.analysis_types is None:
            self.analysis_types = ['hvn', 'camarilla', 'metrics', 'confluence']


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    request: AnalysisRequest
    status: str  # 'completed', 'failed', 'partial'
    timestamp: datetime
    hvn_results: Optional[Dict] = None
    camarilla_results: Optional[Dict] = None
    metrics_results: Optional[Dict] = None
    confluence_results: Optional[Dict] = None
    formatted_results: Optional[Dict] = None
    errors: Optional[list] = None


class AnalysisCoordinator:
    """
    Coordinates all analysis operations across different analyzers
    """
    
    def __init__(self):
        self.polygon_bridge = PolygonBridge()
        self.hvn_analyzer = HVNAnalyzer()
        self.camarilla_analyzer = CamarillaAnalyzer()
        self.confluence_analyzer = ConfluenceAnalyzer()
        self.metrics_analyzer = MetricsAnalyzer()
        
        # Cache for data to avoid redundant fetches
        self._data_cache = {}
    
    def analyze(self, request: AnalysisRequest, progress_callback=None) -> AnalysisResult:
        """
        Perform complete analysis based on request
        
        Args:
            request: Analysis request parameters
            progress_callback: Optional callback(percentage, message)
            
        Returns:
            AnalysisResult with all calculated data
        """
        result = AnalysisResult(
            request=request,
            status='in_progress',
            timestamp=datetime.now(),
            errors=[]
        )
        
        try:
            # Step 1: Fetch required data
            self._emit_progress(progress_callback, 10, "Fetching market data...")
            market_data = self._fetch_market_data(request)
            
            if not market_data:
                raise ValueError("Failed to fetch market data")
            
            # Step 2: Calculate metrics if requested
            if 'metrics' in request.analysis_types:
                self._emit_progress(progress_callback, 25, "Calculating ATR metrics...")
                result.metrics_results = self.metrics_analyzer.calculate(
                    market_data['5min'],
                    market_data['daily'],
                    request.analysis_datetime
                )
            
            # Step 3: HVN analysis if requested
            if 'hvn' in request.analysis_types:
                self._emit_progress(progress_callback, 40, "Analyzing volume profiles...")
                result.hvn_results = self.hvn_analyzer.analyze_timeframes(
                    market_data['5min'],
                    timeframes=[7, 14, 30]  # UI timeframes
                )
            
            # Step 4: Camarilla analysis if requested
            if 'camarilla' in request.analysis_types:
                self._emit_progress(progress_callback, 60, "Calculating Camarilla pivots...")
                result.camarilla_results = self.camarilla_analyzer.analyze_timeframes(
                    market_data['daily'],
                    timeframes=['daily', 'weekly', 'monthly']
                )
            
            # Step 5: Confluence analysis if requested
            if 'confluence' in request.analysis_types and result.hvn_results:
                self._emit_progress(progress_callback, 80, "Calculating confluence zones...")
                
                # Determine current price
                current_price = self._get_current_price(request, result, market_data)
                
                result.confluence_results = self.confluence_analyzer.analyze(
                    result.hvn_results,
                    result.camarilla_results,
                    current_price
                )
            
            # Step 6: Format results for display
            self._emit_progress(progress_callback, 90, "Formatting results...")
            result.formatted_results = self._format_results(result)
            
            result.status = 'completed'
            self._emit_progress(progress_callback, 100, "Analysis complete!")
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            result.errors.append(str(e))
            result.status = 'failed'
        
        return result
    
    def _fetch_market_data(self, request: AnalysisRequest) -> Dict:
        """Fetch all required market data"""
        ticker = request.ticker
        end_date = request.analysis_datetime.date()
        
        # Check cache first
        cache_key = f"{ticker}_{end_date}"
        if cache_key in self._data_cache:
            logger.debug(f"Using cached data for {cache_key}")
            return self._data_cache[cache_key]
        
        data = {}
        
        try:
            # Fetch 5-minute data (120 days for HVN)
            start_date_5min = end_date - timedelta(days=120)
            data['5min'] = self.polygon_bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date_5min,
                end_date=end_date,
                timeframe='5min'
            )
            
            # Fetch daily data (60 days for Camarilla)
            start_date_daily = end_date - timedelta(days=60)
            data['daily'] = self.polygon_bridge.get_historical_bars(
                ticker=ticker,
                start_date=start_date_daily,
                end_date=end_date,
                timeframe='day'
            )
            
            # Cache the data
            self._data_cache[cache_key] = data
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {str(e)}")
            return {}
        
        return data
    
    def _get_current_price(self, request, result, market_data):
        """Determine current price from various sources"""
        # Try from session data first
        current_price = float(request.session_data.get('pre_market_price', 0))
        
        # If not available, try from metrics results
        if current_price == 0 and result.metrics_results:
            current_price = result.metrics_results.get('current_price', 0)
        
        # Finally, use latest market data
        if current_price == 0 and '5min' in market_data:
            current_price = float(market_data['5min']['close'].iloc[-1])
        
        return current_price
    
    def _format_results(self, result: AnalysisResult) -> Dict:
        """Format all results for UI display"""
        formatted = {}
        
        # Format HVN results
        if result.hvn_results:
            for timeframe, hvn_data in result.hvn_results.items():
                key = f'hvn_{timeframe}day'
                formatted[key] = self.hvn_analyzer.format_result(hvn_data)
        
        # Format Camarilla results
        if result.camarilla_results:
            for timeframe, cam_data in result.camarilla_results.items():
                key = f'cam_{timeframe}'
                formatted[key] = self.camarilla_analyzer.format_result(cam_data)
        
        # Format confluence results
        if result.confluence_results:
            formatted['zones_ranked'] = self.confluence_analyzer.format_result(
                result.confluence_results
            )
        
        # Include metrics directly
        if result.metrics_results:
            formatted['metrics'] = result.metrics_results
        
        return formatted
    
    def _emit_progress(self, callback, percentage, message):
        """Emit progress if callback provided"""
        if callback:
            callback(percentage, message)
    
    def clear_cache(self):
        """Clear data cache"""
        self._data_cache.clear()