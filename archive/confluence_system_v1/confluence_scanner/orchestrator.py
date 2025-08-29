"""
Orchestrator for confluence scanner module
Coordinates all confluence detection and zone discovery operations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    """Container for scan results"""
    symbol: str
    analysis_datetime: datetime
    metrics: Dict
    zones: List[Any]
    confluence_sources: List[str]
    confluence_counts: Dict[str, int]
    total_confluence_items: int
    zones_with_candles: List[Any] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'analysis_datetime': self.analysis_datetime.isoformat() if self.analysis_datetime else None,
            'metrics': self.metrics,
            'zones': self.zones,
            'confluence_sources': self.confluence_sources,
            'confluence_counts': self.confluence_counts,
            'total_confluence_items': self.total_confluence_items
        }


class ConfluenceOrchestrator:
    """
    Orchestrator for confluence scanner module
    Manages all sub-components and coordinates scanning workflow
    """
    
    def __init__(self):
        """Initialize the confluence orchestrator"""
        self.scanner = None
        self.is_initialized = False
        
    def initialize(self):
        """Lazy initialization of components"""
        if not self.is_initialized:
            try:
                # Import components
                from .scanner.zone_scanner import ZoneScanner
                from .data.polygon_client import PolygonClient
                from .data.market_metrics import MetricsCalculator
                from .discovery.zone_discovery import ZoneDiscoveryEngine
                
                # Initialize scanner with all components
                self.scanner = ZoneScanner()
                self.polygon_client = self.scanner.polygon_client
                self.metrics_calculator = self.scanner.metrics_calculator
                self.discovery_engine = self.scanner.discovery_engine
                
                # Test connection
                success, msg = self.polygon_client.test_connection()
                if not success:
                    logger.warning(f"Polygon connection failed: {msg}")
                    
                self.is_initialized = True
                logger.info("Confluence orchestrator initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize confluence orchestrator: {e}")
                raise
                
    def run_analysis(self, 
                symbol: str,
                analysis_datetime: Optional[datetime] = None,
                fractal_data: Optional[Dict] = None,
                weekly_levels: Optional[List[float]] = None,
                daily_levels: Optional[List[float]] = None,
                lookback_days: int = 30,
                merge_overlapping: bool = True,
                merge_identical: bool = False) -> ScanResult:
        """
        Main entry point for confluence analysis
        Properly integrates fractals as confluence source
        
        Args:
            symbol: Stock symbol
            analysis_datetime: Analysis time (defaults to now)
            fractal_data: Fractal data from fractal_engine
            weekly_levels: Weekly price levels
            daily_levels: Daily price levels
            lookback_days: Days to look back for data
            merge_overlapping: If True, merge zones with overlapping boundaries
            merge_identical: If True, merge items at same price (within $0.10)
        
        Returns:
            ScanResult with zones and confluence data
        """
        # Ensure initialization
        if not self.is_initialized:
            self.initialize()
            
        if analysis_datetime is None:
            analysis_datetime = datetime.now()
            
        logger.info(f"[Confluence] Starting analysis for {symbol} at {analysis_datetime}")
        logger.info(f"[Confluence] Merge mode - Overlapping: {merge_overlapping}, Identical: {merge_identical}")
        
        try:
            # Set merge mode on discovery engine
            self.discovery_engine.set_merge_mode(merge_overlapping, merge_identical)
            
            # Prepare additional confluence from fractals
            additional_confluence = {}
            
            if fractal_data and 'fractals' in fractal_data:
                # Import fractal integrator
                from .calculations.fractals.fractal_integration import FractalIntegrator
                integrator = FractalIntegrator()
                
                # Get metrics for ATR calculation (though not used after fix)
                metrics = self.metrics_calculator.calculate_metrics(symbol, analysis_datetime)
                
                if metrics:
                    # Convert fractals to confluence items (using actual candle boundaries)
                    additional_confluence = integrator.add_fractals_as_confluence(
                        additional_confluence,
                        fractal_data['fractals'],
                        metrics.atr_m15  # Can be removed after fractal_integration fix
                    )
                    logger.info(f"Prepared {len(additional_confluence.get('fractals', []))} fractal confluence items")
            
            # Run the scan with all confluence sources
            result = self.scanner.scan(
                ticker=symbol,
                analysis_datetime=analysis_datetime,
                weekly_levels=weekly_levels or [],
                daily_levels=daily_levels or [],
                lookback_days=lookback_days,
                additional_confluence=additional_confluence,
                merge_overlapping=merge_overlapping,  # Pass through to scanner
                merge_identical=merge_identical        # Pass through to scanner
            )
            
            # Log zone discovery results
            if result.get('zones'):
                zone_summary = {}
                for zone in result['zones']:
                    level = zone.confluence_level
                    zone_summary[level] = zone_summary.get(level, 0) + 1
                logger.info(f"[Confluence] Zone distribution: {zone_summary}")
            
            # Associate fractals with discovered zones for enhanced analysis
            if fractal_data and 'fractals' in fractal_data and result.get('zones'):
                from .calculations.fractals.fractal_integration import FractalIntegrator
                integrator = FractalIntegrator()
                
                zone_associations = integrator.associate_fractals_with_zones(
                    result['zones'],
                    fractal_data['fractals']
                )
                result['zone_fractal_associations'] = zone_associations
                logger.info(f"Associated {len(zone_associations)} zones with fractals")
            
            # Package results
            scan_result = ScanResult(
                symbol=result.get('symbol', symbol),
                analysis_datetime=result.get('analysis_datetime', analysis_datetime),
                metrics=result.get('metrics', {}),
                zones=result.get('zones', []),
                confluence_sources=result.get('confluence_sources', []),
                confluence_counts=result.get('confluence_counts', {}),
                total_confluence_items=result.get('total_confluence_items', 0),
                zones_with_candles=result.get('zones', [])
            )
            
            logger.info(f"[Confluence] Analysis complete: {len(scan_result.zones)} zones discovered")
            logger.info(f"[Confluence] Confluence sources: {', '.join(scan_result.confluence_sources)}")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Confluence analysis failed: {e}")
            raise
    
    # Other methods remain unchanged
    def get_calculation_engines(self) -> Dict:
        # [Previous code remains the same]
        pass
        
    def format_results(self, scan_result: ScanResult) -> str:
        # [Previous code remains the same]
        pass
        
    def run_quick_scan(self, symbol: str) -> ScanResult:
        # [Previous code remains the same]
        pass