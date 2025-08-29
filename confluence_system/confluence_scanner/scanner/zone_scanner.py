# scanner/zone_scanner.py - Complete with M15 candle details, fractal integration, and market structure levels

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from ..data.polygon_client import PolygonClient
from ..data.market_metrics import MetricsCalculator
from ..discovery.zone_discovery import ZoneDiscoveryEngine

# Import calculation modules
from ..calculations.volume.hvn_engine import HVNEngine
from ..calculations.pivots.camarilla_engine import CamarillaEngine
from ..calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
from ..calculations.zones.daily_zone_calc import DailyZoneCalculator
from ..calculations.zones.atr_zone_calc import ATRZoneCalculator
from ..calculations.market_structure.pd_market_structure import MarketStructureCalculator
from ..config import (
    HVN_POC_MODE_ENABLED,
    HVN_POC_ZONE_WIDTH_MULTIPLIER,
    HVN_POC_MIN_ZONES,
    HVN_POC_OVERLAP_THRESHOLD
)

logger = logging.getLogger(__name__)


class ZoneScanner:
    """Main scanner using complete calculation engine with market structure integration"""
    
    def __init__(self, polygon_client: Optional[PolygonClient] = None):
        self.polygon_client = polygon_client or PolygonClient(
            base_url="http://localhost:8200/api/v1"
        )
        self.metrics_calculator = MetricsCalculator(self.polygon_client)
        self.discovery_engine = ZoneDiscoveryEngine()
        
        # Initialize calculation engines
        self.hvn_engine = HVNEngine(levels=100)
        self.camarilla_engine = CamarillaEngine()
        self.weekly_calc = WeeklyZoneCalculator()
        self.daily_calc = DailyZoneCalculator()
        self.atr_calc = ATRZoneCalculator()
        self.market_structure_calc = MarketStructureCalculator()
        
        # ================================================================
        # ZONE WIDTH CONFIGURATION - All multipliers in one place
        # ================================================================
        # These multipliers control how wide zones are around each level
        # All are multiplied by the 15-minute ATR (atr_m15)
        
        # HVN Peak Zone Widths
        self.hvn_zone_multiplier = 0.15  # Narrow zones for volume peaks
        
        # Camarilla Pivot Zone Widths (full width, will be halved for +/-)
        self.camarilla_monthly_multiplier = 0.5  
        self.camarilla_weekly_multiplier = 0.4   
        self.camarilla_daily_multiplier = 0.15    
        
        # Weekly Level Zone Width
        self.weekly_zone_multiplier = 0.5  
        
        # Daily Zone Width (for DZ items, not DL)
        self.daily_zone_multiplier = 0.3   
        
        # ATR Zone Width
        self.atr_zone_multiplier = 1.0
        
        # Market Structure Zone Width (uses 5-min ATR equivalent)
        self.market_structure_multiplier = 0.15  # 5-min ATR approximation as % of 15-min ATR
        
        # Daily Level Width (for DL items - essentially points)
        self.daily_level_width = 0.1  
        
        # Scan Range Configuration
        self.scan_range_atr_multiplier = 2.0  # Scan within 2x Daily ATR
        
        # HVN Configuration
        self.hvn_timeframes = [30, 14, 7]  # Days to analyze
        self.hvn_peaks_per_timeframe = 5   # Top N peaks per timeframe
        self.hvn_lookback_days = 120       # Days of data for HVN
        
        # Merge Configuration (default values)
        self.default_merge_overlapping = True
        self.default_merge_identical = False

        # HVN POC Zone Configuration (from config)
        self.hvn_poc_mode = HVN_POC_MODE_ENABLED
        self.hvn_poc_zone_width_multiplier = HVN_POC_ZONE_WIDTH_MULTIPLIER
        self.hvn_poc_min_zones = HVN_POC_MIN_ZONES
        self.hvn_poc_overlap_threshold = HVN_POC_OVERLAP_THRESHOLD
        self.hvn_poc_timeframe = 7  # Days for HVN analysis
        
        # ================================================================
        
        logger.info("Zone Scanner initialized with complete calculation engine including market structure")
    
    def initialize(self):
        """Test connection"""
        return self.polygon_client.test_connection()
    
    def _format_hvn_peaks(self, hvn_results: Dict, atr_m15: float, scan_low: float, scan_high: float) -> List[Dict]:
        """Format HVN peaks for zone discovery"""
        formatted = []
        
        for days, result in hvn_results.items():
            if not result or not result.peaks:
                continue
            
            for peak in result.peaks[:self.hvn_peaks_per_timeframe]:
                if scan_low <= peak.price <= scan_high:
                    zone_width = atr_m15 * self.hvn_zone_multiplier
                    
                    formatted.append({
                        'name': f'HVN{days}d_R{peak.rank}',
                        'level': peak.price,
                        'low': peak.price - zone_width,
                        'high': peak.price + zone_width,
                        'type': f'hvn-{days}d',
                        'strength': peak.volume_percent
                    })
        
        return formatted
    
    def _format_camarilla_pivots(self, camarilla_results: Dict, atr_m15: float, scan_low: float, scan_high: float) -> List[Dict]:
        """Format Camarilla pivots for zone discovery"""
        formatted = []
        key_levels = {'R6', 'R5', 'R4', 'R3', 'S3', 'S4', 'S5', 'S6'}
        
        for timeframe, result in camarilla_results.items():
            if not result or not result.pivots:
                continue
            
            # Use configured multipliers
            if timeframe == 'monthly':
                zone_width = atr_m15 * self.camarilla_monthly_multiplier
            elif timeframe == 'weekly':
                zone_width = atr_m15 * self.camarilla_weekly_multiplier
            else:  # daily
                zone_width = atr_m15 * self.camarilla_daily_multiplier
            
            for pivot in result.pivots:
                if pivot.level_name in key_levels:
                    if scan_low <= pivot.price <= scan_high:
                        formatted.append({
                            'name': f'{timeframe[0].upper()}{pivot.level_name}',
                            'level': pivot.price,
                            'low': pivot.price - zone_width/2,
                            'high': pivot.price + zone_width/2,
                            'type': f'cam-{timeframe}',
                            'strength': pivot.strength
                        })
        
        return formatted
    
    def scan(self, 
             ticker: str,
             analysis_datetime: Optional[datetime] = None,
             weekly_levels: Optional[List[float]] = None,
             daily_levels: Optional[List[float]] = None,
             lookback_days: int = 30,
             additional_confluence: Optional[Dict[str, List[Dict]]] = None,
             merge_overlapping: bool = None,
             merge_identical: bool = None,
             **kwargs):
        """
        Run scan with full confluence engine including market structure
        
        Args:
            ticker: Stock symbol
            analysis_datetime: Analysis time
            weekly_levels: Weekly price levels
            daily_levels: Daily price levels
            lookback_days: Days to look back
            additional_confluence: Additional confluence items (e.g., fractals)
            merge_overlapping: Whether to merge overlapping zones
            merge_identical: Whether to merge identical price levels
            **kwargs: Additional parameters
        """
        
        # Use defaults if not specified
        if merge_overlapping is None:
            merge_overlapping = self.default_merge_overlapping
        if merge_identical is None:
            merge_identical = self.default_merge_identical
            
        if analysis_datetime is None:
            analysis_datetime = datetime.now()
        
        logger.info(f"Starting full confluence scan for {ticker}")
        
        # Calculate basic metrics first
        metrics = self.metrics_calculator.calculate_metrics(ticker, analysis_datetime)
        if not metrics:
            return {"error": "Failed to calculate metrics"}
        
        # Use configured scan range
        scan_low = metrics.current_price - (self.scan_range_atr_multiplier * metrics.atr_daily)
        scan_high = metrics.current_price + (self.scan_range_atr_multiplier * metrics.atr_daily)
        
        logger.info(f"Scan range: ${scan_low:.2f} - ${scan_high:.2f}")
        
        # Collect ALL confluence items in a single list
        all_confluence_items = []
        source_counts = {}

        # 0. CREATE HVN POC ANCHOR ZONES (if in POC mode)
        poc_zones = []
        if self.hvn_poc_mode:
            try:
                logger.info("Creating multi-timeframe HVN POC anchor zones...")
                
                # Calculate 5-minute ATR approximation
                atr_5min = metrics.atr_m15 * self.hvn_poc_zone_width_multiplier
                
                # Collect POCs from multiple timeframes
                timeframe_configs = [
                    (7, 1.0),   # 7-day: highest priority
                    (14, 0.7),  # 14-day: medium priority  
                    (30, 0.5)   # 30-day: lowest priority
                ]
                
                all_poc_zones = []
                
                for timeframe_days, weight in timeframe_configs:
                    end_date = analysis_datetime.strftime('%Y-%m-%d')
                    start_date = (analysis_datetime - timedelta(days=timeframe_days)).strftime('%Y-%m-%d')
                    
                    df = self.polygon_client.fetch_bars(ticker, start_date, end_date, '5min')
                    if df is not None and not df.empty:
                        df['timestamp'] = df.index
                        
                        poc_result = self.hvn_engine.create_poc_anchor_zones(
                            df,
                            timeframe_days=timeframe_days,
                            zone_width_atr=atr_5min,
                            min_zones=6
                        )
                        
                        timeframe_pocs = poc_result.get('poc_zones', [])
                        for poc in timeframe_pocs:
                            poc['timeframe_weight'] = weight
                            poc['distance_to_price'] = abs(poc['poc_price'] - metrics.current_price)
                        
                        all_poc_zones.extend(timeframe_pocs)
                        logger.info(f"Found {len(timeframe_pocs)} POCs from {timeframe_days}-day timeframe")
                
                # Filter overlapping POCs - keep higher weighted
                poc_zones = self._filter_overlapping_pocs(all_poc_zones, overlap_threshold=0.005)
                
                source_counts['hvn_poc_anchors'] = len(poc_zones)
                logger.info(f"Using {len(poc_zones)} POC anchor zones after overlap filtering")
                
            except Exception as e:
                logger.error(f"POC zone creation failed: {e}")
                poc_zones = []
        
        # 1. HVN PEAKS
        try:
            logger.info("Calculating HVN peaks...")
            end_date = analysis_datetime.strftime('%Y-%m-%d')
            start_date = (analysis_datetime - timedelta(days=self.hvn_lookback_days)).strftime('%Y-%m-%d')
            
            df = self.polygon_client.fetch_bars(ticker, start_date, end_date, '5min')
            if df is not None and not df.empty:
                df['timestamp'] = df.index
                
                hvn_results = self.hvn_engine.analyze_multi_timeframe(
                    df, 
                    timeframes=self.hvn_timeframes,
                    include_pre=True, 
                    include_post=True
                )
                
                if hvn_results:
                    hvn_formatted = self._format_hvn_peaks(hvn_results, metrics.atr_m15, scan_low, scan_high)
                    all_confluence_items.extend(hvn_formatted)
                    source_counts['hvn_peaks'] = len(hvn_formatted)
                    logger.info(f"Added {len(hvn_formatted)} formatted HVN peaks")
                else:
                    source_counts['hvn_peaks'] = 0
            else:
                source_counts['hvn_peaks'] = 0
        except Exception as e:
            logger.error(f"HVN calculation failed: {e}")
            source_counts['hvn_peaks'] = 0
        
        # 2. CAMARILLA PIVOTS
        try:
            logger.info("Calculating Camarilla pivots...")
            self.camarilla_engine.set_analysis_date(analysis_datetime)
            
            camarilla_data = self.polygon_client.fetch_bars(
                ticker,
                (analysis_datetime - timedelta(days=30)).strftime('%Y-%m-%d'),
                analysis_datetime.strftime('%Y-%m-%d'),
                '1day'
            )
            
            if camarilla_data is not None and not camarilla_data.empty:
                camarilla_results = {}
                
                for timeframe in ['daily', 'weekly', 'monthly']:
                    result = self.camarilla_engine.calculate_from_data(
                        camarilla_data, 
                        timeframe
                    )
                    if result:
                        camarilla_results[timeframe] = result
                
                if camarilla_results:
                    cam_formatted = self._format_camarilla_pivots(camarilla_results, metrics.atr_m15, scan_low, scan_high)
                    all_confluence_items.extend(cam_formatted)
                    source_counts['camarilla_pivots'] = len(cam_formatted)
                    logger.info(f"Added {len(cam_formatted)} formatted Camarilla pivots")
                else:
                    source_counts['camarilla_pivots'] = 0
            else:
                source_counts['camarilla_pivots'] = 0
        except Exception as e:
            logger.error(f"Camarilla calculation failed: {e}")
            source_counts['camarilla_pivots'] = 0
        
        # 3. WEEKLY ZONES
        if weekly_levels:
            weekly_count = 0
            zone_width = metrics.atr_m15 * self.weekly_zone_multiplier
            for i, level in enumerate(weekly_levels):
                if level and scan_low <= level <= scan_high:
                    all_confluence_items.append({
                        'name': f'WL{i+1}',
                        'level': level,
                        'low': level - zone_width,
                        'high': level + zone_width,
                        'type': 'weekly'
                    })
                    weekly_count += 1
            source_counts['weekly_zones'] = weekly_count
            logger.info(f"Added {weekly_count} weekly zones")
        else:
            source_counts['weekly_zones'] = 0
        
        # 4. DAILY LEVELS
        if daily_levels:
            daily_level_count = 0
            for i, level in enumerate(daily_levels):
                if level and scan_low <= level <= scan_high:
                    all_confluence_items.append({
                        'name': f'DL{i+1}',
                        'level': level,
                        'low': level - self.daily_level_width,
                        'high': level + self.daily_level_width,
                        'type': 'daily-level'
                    })
                    daily_level_count += 1
            source_counts['daily_levels'] = daily_level_count
            logger.info(f"Added {daily_level_count} daily levels")
        else:
            source_counts['daily_levels'] = 0
        
        # 5. DAILY ZONES
        if daily_levels:
            daily_zone_count = 0
            zone_width = metrics.atr_m15 * self.daily_zone_multiplier
            for i, level in enumerate(daily_levels):
                if level and scan_low <= level <= scan_high:
                    all_confluence_items.append({
                        'name': f'DZ{i+1}',
                        'level': level,
                        'low': level - zone_width/2,
                        'high': level + zone_width/2,
                        'type': 'daily-zone'
                    })
                    daily_zone_count += 1
            source_counts['daily_zones'] = daily_zone_count
            logger.info(f"Added {daily_zone_count} daily zones")
        else:
            source_counts['daily_zones'] = 0
        
        # 6. ATR ZONES
        try:
            atr_high = metrics.current_price + metrics.atr_daily
            atr_low = metrics.current_price - metrics.atr_daily
            zone_width = metrics.atr_m15 * self.atr_zone_multiplier
            
            atr_count = 0
            if scan_low <= atr_high <= scan_high:
                all_confluence_items.append({
                    'name': 'ATR_High',
                    'level': atr_high,
                    'low': atr_high - zone_width,
                    'high': atr_high + zone_width,
                    'type': 'atr'
                })
                atr_count += 1
            
            if scan_low <= atr_low <= scan_high:
                all_confluence_items.append({
                    'name': 'ATR_Low',
                    'level': atr_low,
                    'low': atr_low - zone_width,
                    'high': atr_low + zone_width,
                    'type': 'atr'
                })
                atr_count += 1
            
            source_counts['atr_zones'] = atr_count
            logger.info(f"Added {atr_count} ATR zones")
        except Exception as e:
            logger.error(f"ATR zones failed: {e}")
            source_counts['atr_zones'] = 0
        
        # 7. MARKET STRUCTURE LEVELS (PDH, PDL, PDC, ONH, ONL) - ENHANCED INTEGRATION
        try:
            logger.info("Calculating market structure levels...")
            
            # Calculate enhanced metrics with market structure
            enhanced_metrics = self.metrics_calculator.calculate_metrics(
                ticker, analysis_datetime, include_market_structure=True
            )
            
            if enhanced_metrics and enhanced_metrics.has_structure_levels():
                # Update our main metrics object with structure levels
                structure_levels = enhanced_metrics.get_structure_levels()
                metrics.update_market_structure(structure_levels)
                
                logger.info(f"Market structure levels calculated: {list(structure_levels.keys())}")
                
                # Format for confluence using 5-minute ATR zones
                atr_5min = metrics.atr_m15 * self.market_structure_multiplier
                
                structure_formatted = self.market_structure_calc.format_for_confluence(
                    structure_levels, atr_5min
                )
                
                # Filter to scan range and add to confluence items
                structure_count = 0
                for item in structure_formatted:
                    if scan_low <= item['level'] <= scan_high:
                        all_confluence_items.append(item)
                        structure_count += 1
                        logger.info(f"Added {item['name']} at ${item['level']:.2f} to confluence")
                
                source_counts['market_structure'] = structure_count
                logger.info(f"Added {structure_count} market structure levels to confluence")
                
                # Log all calculated levels for debugging
                for name, value in structure_levels.items():
                    in_range = "in range" if scan_low <= value <= scan_high else "out of range"
                    logger.info(f"  {name}: ${value:.2f} ({in_range})")
                    
            else:
                logger.warning("No market structure levels calculated - check data availability")
                source_counts['market_structure'] = 0
                
        except Exception as e:
            logger.error(f"Market structure calculation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            source_counts['market_structure'] = 0
        
        # 8. ADDITIONAL CONFLUENCE (e.g., FRACTALS)
        if additional_confluence:
            for source_type, items in additional_confluence.items():
                if items and isinstance(items, list):
                    # Filter items within scan range
                    filtered_items = []
                    for item in items:
                        if 'level' in item and scan_low <= item['level'] <= scan_high:
                            filtered_items.append(item)
                    
                    if filtered_items:
                        all_confluence_items.extend(filtered_items)
                        source_counts[source_type] = len(filtered_items)
                        logger.info(f"Added {len(filtered_items)} {source_type} items from additional confluence")
                    else:
                        source_counts[source_type] = 0
        
        logger.info(f"Total confluence items: {len(all_confluence_items)}")
        
        # Group items by type for discovery engine
        confluence_sources = {}
        for item in all_confluence_items:
            item_type = item.get('type', 'unknown')
            if item_type not in confluence_sources:
                confluence_sources[item_type] = []
            confluence_sources[item_type].append(item)
        
        # Set merge mode on discovery engine
        self.discovery_engine.set_merge_mode(merge_overlapping, merge_identical)

        # Set discovery mode based on configuration
        if self.hvn_poc_mode and poc_zones:
            self.discovery_engine.discovery_mode = 'hvn_anchor'
            logger.info(f"Using HVN POC anchor mode with {len(poc_zones)} anchor zones")
        else:
            self.discovery_engine.discovery_mode = 'cluster'
            logger.info("Using traditional clustering mode")

        # Run zone discovery
        zones = self.discovery_engine.discover_zones(
            scan_low=scan_low,
            scan_high=scan_high,
            current_price=metrics.current_price,
            atr_15min=metrics.atr_m15,
            confluence_sources=confluence_sources,
            poc_zones=poc_zones  # ADD THIS PARAMETER
        )
        
        logger.info(f"Discovered {len(zones)} zones with full confluence including market structure")
        
        return {
            "symbol": ticker,
            "metrics": metrics.to_dict(),
            "zones": zones,
            "confluence_sources": list(source_counts.keys()),
            "confluence_counts": source_counts,
            "total_confluence_items": len(all_confluence_items),
            "analysis_datetime": analysis_datetime
        }
    
    def _filter_overlapping_pocs(self, poc_zones: List[Dict], overlap_threshold: float = 0.005) -> List[Dict]:
        """
        Filter overlapping POCs, keeping only the highest weighted one
        """
        if not poc_zones:
            return []
        
        # Sort by weight (highest first), then by distance (closest first)
        sorted_pocs = sorted(poc_zones, 
                            key=lambda x: (-x.get('timeframe_weight', 1.0), x.get('distance_to_price', 0)))
        
        filtered = []
        
        for poc in sorted_pocs:
            # Check if this POC overlaps with any already selected
            is_overlap = False
            for selected_poc in filtered:
                price_diff = abs(poc['poc_price'] - selected_poc['poc_price']) / selected_poc['poc_price']
                if price_diff <= overlap_threshold:
                    is_overlap = True
                    break
            
            if not is_overlap:
                filtered.append(poc)
        
        return filtered

    def format_result(self, result: Dict) -> str:
        """Format scan results for display with market structure"""
        if 'error' in result:
            return f"Error: {result['error']}"
        
        output = []
        output.append("\n" + "="*60)
        output.append("CONFLUENCE SCAN RESULTS")
        output.append("="*60)
        
        # Metrics
        if 'metrics' in result:
            m = result['metrics']
            output.append(f"\nMarket Metrics:")
            output.append(f"  Current Price: ${m['current_price']:.2f}")
            output.append(f"  Daily ATR: ${m['atr_daily']:.2f}")
            output.append(f"  M15 ATR: ${m['atr_m15']:.2f}")
            
            # Add market structure levels if present
            structure_levels = {}
            for level_name in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL']:
                if level_name in m and m[level_name] is not None:
                    structure_levels[level_name] = m[level_name]
            
            if structure_levels:
                output.append(f"\nMarket Structure Levels:")
                for level_name in ['PDH', 'PDL', 'PDC', 'ONH', 'ONL']:
                    if level_name in structure_levels:
                        output.append(f"  {level_name}: ${structure_levels[level_name]:.2f}")
            
            if m.get('market_structure_available', False):
                output.append(f"  Structure levels available: {m.get('structure_level_count', 0)}")
        
        # Confluence sources
        if 'confluence_counts' in result:
            output.append(f"\nConfluence Sources ({result.get('total_confluence_items', 0)} total items):")
            for source, count in result['confluence_counts'].items():
                if count > 0:
                    # Add special indicator for market structure
                    indicator = "📊" if source == 'market_structure' else "✓"
                    output.append(f"  {indicator} {source}: {count} items")
        
        # Show POC anchor information if available
        if 'hvn_poc_anchors' in result.get('confluence_counts', {}):
            poc_count = result['confluence_counts']['hvn_poc_anchors']
            if poc_count > 0:
                output.append(f"\n HVN POC Anchors: {poc_count} zones")
        
        # Zones
        if 'zones' in result:
            zones = result['zones']
            output.append(f"\nZones Discovered: {len(zones)}")
            
            if zones:
                output.append("\nZone Details:")
                for i, zone in enumerate(zones[:10], 1):
                    output.append(f"\n  Zone #{i}:")
                    output.append(f"    Range: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}")
                    output.append(f"    Type: {zone.zone_type}")
                    output.append(f"    Level: {zone.confluence_level} (Score: {zone.confluence_score:.1f})")
                    output.append(f"    Sources: {len(zone.confluent_sources)}")
                    output.append(f"    Distance: {zone.distance_percentage:.1f}%")
                    
                    # Show if zone contains market structure
                    has_ms = any('market-structure' in str(s.get('type', '')) 
                               for s in zone.confluent_sources)
                    if has_ms:
                        ms_names = [s.get('name', '') for s in zone.confluent_sources 
                                   if s.get('type') == 'market-structure']
                        output.append(f"    📊 Market Structure: {', '.join(ms_names)}")
        
        return "\n".join(output)