# scanner/zone_scanner.py - Complete with M15 candle details

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from data.polygon_client import PolygonClient
from data.market_metrics import MetricsCalculator
from discovery.zone_discovery import ZoneDiscoveryEngine

# Import calculation modules
from calculations.volume.hvn_engine import HVNEngine
from calculations.pivots.camarilla_engine import CamarillaEngine
from calculations.zones.weekly_zone_calc import WeeklyZoneCalculator
from calculations.zones.daily_zone_calc import DailyZoneCalculator
from calculations.zones.atr_zone_calc import ATRZoneCalculator

logger = logging.getLogger(__name__)


class ZoneScanner:
    """Main scanner using complete calculation engine"""
    
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
        
        logger.info("Zone Scanner initialized with complete calculation engine")
    
    def initialize(self):
        """Test connection"""
        return self.polygon_client.test_connection()
    
    def _format_hvn_peaks(self, hvn_results: Dict, atr_m15: float, scan_low: float, scan_high: float) -> List[Dict]:
        """Format HVN peaks for zone discovery"""
        formatted = []
        
        for days, result in hvn_results.items():
            if not result or not result.peaks:
                continue
            
            for peak in result.peaks[:5]:  # Top 5 per timeframe
                if scan_low <= peak.price <= scan_high:
                    zone_width = atr_m15 * 0.3
                    
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
            
            if timeframe == 'monthly':
                zone_width = atr_m15 * 2
            elif timeframe == 'weekly':
                zone_width = atr_m15 * 1.5
            else:  # daily
                zone_width = atr_m15 * 0.5
            
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
             **kwargs):
        """Run scan with full confluence engine"""
        
        if analysis_datetime is None:
            analysis_datetime = datetime.now()
        
        logger.info(f"Starting full confluence scan for {ticker}")
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_metrics(ticker, analysis_datetime)
        if not metrics:
            return {"error": "Failed to calculate metrics"}
        
        scan_low = metrics.current_price - (2 * metrics.atr_daily)
        scan_high = metrics.current_price + (2 * metrics.atr_daily)
        
        # Collect ALL confluence items in a single list
        all_confluence_items = []
        source_counts = {}
        
        # 1. HVN PEAKS
        try:
            logger.info("Calculating HVN peaks...")
            end_date = analysis_datetime.strftime('%Y-%m-%d')
            start_date = (analysis_datetime - timedelta(days=120)).strftime('%Y-%m-%d')
            
            df = self.polygon_client.fetch_bars(ticker, start_date, end_date, '5min')
            if df is not None and not df.empty:
                df['timestamp'] = df.index
                
                hvn_results = self.hvn_engine.analyze_multi_timeframe(
                    df, 
                    timeframes=[30, 14, 7],
                    include_pre=True, 
                    include_post=True
                )
                
                if hvn_results:
                    hvn_formatted = self._format_hvn_peaks(hvn_results, metrics.atr_m15, scan_low, scan_high)
                    all_confluence_items.extend(hvn_formatted)
                    source_counts['hvn_peaks'] = len(hvn_formatted)
                    logger.info(f"Added {len(hvn_formatted)} formatted HVN peaks")
        except Exception as e:
            logger.error(f"HVN calculation failed: {e}")
        
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
        except Exception as e:
            logger.error(f"Camarilla calculation failed: {e}")
        
        # 3. WEEKLY ZONES
        if weekly_levels:
            weekly_count = 0
            zone_width = metrics.atr_m15 * 2
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
        
        # 4. DAILY LEVELS
        if daily_levels:
            daily_level_count = 0
            for i, level in enumerate(daily_levels):
                if level and scan_low <= level <= scan_high:
                    all_confluence_items.append({
                        'name': f'DL{i+1}',
                        'level': level,
                        'low': level - 0.1,
                        'high': level + 0.1,
                        'type': 'daily-level'
                    })
                    daily_level_count += 1
            source_counts['daily_levels'] = daily_level_count
            logger.info(f"Added {daily_level_count} daily levels")
        
        # 5. DAILY ZONES
        if daily_levels:
            daily_zone_count = 0
            zone_width = metrics.atr_m15
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
        
        # 6. ATR ZONES
        try:
            atr_high = metrics.current_price + metrics.atr_daily
            atr_low = metrics.current_price - metrics.atr_daily
            
            atr_count = 0
            if scan_low <= atr_high <= scan_high:
                all_confluence_items.append({
                    'name': 'ATR_High',
                    'level': atr_high,
                    'low': atr_high - metrics.atr_m15,
                    'high': atr_high + metrics.atr_m15,
                    'type': 'atr'
                })
                atr_count += 1
            
            if scan_low <= atr_low <= scan_high:
                all_confluence_items.append({
                    'name': 'ATR_Low',
                    'level': atr_low,
                    'low': atr_low - metrics.atr_m15,
                    'high': atr_low + metrics.atr_m15,
                    'type': 'atr'
                })
                atr_count += 1
            
            source_counts['atr_zones'] = atr_count
            logger.info(f"Added {atr_count} ATR zones")
        except Exception as e:
            logger.error(f"ATR zones failed: {e}")
        
        logger.info(f"Total confluence items: {len(all_confluence_items)}")
        
        # Group items by type for discovery engine
        confluence_sources = {}
        for item in all_confluence_items:
            item_type = item.get('type', 'unknown')
            if item_type not in confluence_sources:
                confluence_sources[item_type] = []
            confluence_sources[item_type].append(item)
        
        # Run zone discovery
        zones = self.discovery_engine.discover_zones(
            scan_low=scan_low,
            scan_high=scan_high,
            current_price=metrics.current_price,
            atr_15min=metrics.atr_m15,
            confluence_sources=confluence_sources
        )
        
        # Find best M15 candles
        if zones:
            self.discovery_engine.find_best_candles_for_zones(
                zones, ticker, self.polygon_client, lookback_days
            )
        
        logger.info(f"Discovered {len(zones)} zones with full confluence")
        
        return {
            "symbol": ticker,
            "metrics": metrics.to_dict(),
            "zones": zones,
            "confluence_sources": list(source_counts.keys()),
            "confluence_counts": source_counts,
            "total_confluence_items": len(all_confluence_items),
            "analysis_datetime": analysis_datetime
        }
    
    def format_result(self, result: Dict) -> str:
        """Format scan results for display with detailed M15 candle info"""
        if 'error' in result:
            return f"Error: {result['error']}"
        
        import pytz
        current_time_utc = datetime.now(pytz.UTC)
        
        output = []
        output.append("\n" + "="*60)
        output.append("SCAN RESULTS - FULL CONFLUENCE ENGINE")
        output.append("="*60)
        
        # Metrics
        if 'metrics' in result:
            m = result['metrics']
            output.append(f"\nMarket Metrics:")
            output.append(f"  Current Price: ${m['current_price']:.2f}")
            output.append(f"  Daily ATR: ${m['atr_daily']:.2f}")
            output.append(f"  M15 ATR: ${m['atr_m15']:.2f}")
        
        # Confluence sources with counts
        if 'confluence_counts' in result:
            output.append(f"\nConfluence Sources ({result.get('total_confluence_items', 0)} total items):")
            for source, count in result['confluence_counts'].items():
                if count > 0:
                    output.append(f"  ✓ {source}: {count} items")
        
        # Zones with enhanced M15 candle details
        if 'zones' in result:
            zones = result['zones']
            output.append(f"\nZones Discovered: {len(zones)}")
            
            if zones:
                output.append("\n" + "="*60)
                output.append("DETAILED ZONE ANALYSIS")
                output.append("="*60)
                
                for i, zone in enumerate(zones[:10], 1):
                    output.append(f"\n{'─'*50}")
                    output.append(f"ZONE #{i}: {zone.zone_type.upper()}")
                    output.append(f"{'─'*50}")
                    output.append(f"Price Range: ${zone.zone_low:.2f} - ${zone.zone_high:.2f}")
                    output.append(f"Center: ${zone.center_price:.2f}")
                    output.append(f"Width: ${zone.zone_width:.2f}")
                    output.append(f"Distance: {zone.distance_percentage:.1f}% {'above' if zone.zone_type == 'resistance' else 'below'}")
                    output.append(f"Confluence: {zone.confluence_level} (Score: {zone.confluence_score:.1f})")
                    
                    # Contributing sources
                    source_types = []
                    for source in zone.confluent_sources:
                        src_type = source.get('type', source.get('name', 'unknown'))
                        if src_type not in source_types:
                            source_types.append(src_type)
                    output.append(f"Sources: {', '.join(source_types)}")
                    
                    # Detailed M15 candle information with proper timezone handling
                    if zone.best_candle:
                        candle = zone.best_candle
                        candle_datetime = candle['datetime']
                        
                        # Handle timezone properly
                        if hasattr(candle_datetime, 'tzinfo'):
                            if candle_datetime.tzinfo is None:
                                candle_dt = pytz.UTC.localize(candle_datetime)
                            else:
                                candle_dt = candle_datetime
                        else:
                            # If it's a string, parse it first
                            if isinstance(candle_datetime, str):
                                candle_dt = datetime.strptime(candle_datetime, '%Y-%m-%d %H:%M:%S')
                                candle_dt = pytz.UTC.localize(candle_dt)
                            else:
                                candle_dt = pytz.UTC.localize(candle_datetime)
                        
                        days_ago = (current_time_utc - candle_dt).days
                        time_str = candle_dt.strftime('%Y-%m-%d %H:%M')
                        
                        output.append(f"\n📊 M15 CANDLE VALIDATION:")
                        output.append(f"  Overlap: {candle['overlap_pct']:.1f}%")
                        output.append(f"  Date/Time: {time_str} UTC")
                        output.append(f"  Days Ago: {days_ago}")
                        output.append(f"  Candle Range: ${candle['low']:.2f} - ${candle['high']:.2f}")
                        output.append(f"  Open: ${candle['open']:.2f} | Close: ${candle['close']:.2f}")
                        
                        # Candle type
                        if candle['close'] > candle['open']:
                            candle_type = "Bullish"
                            candle_body = candle['close'] - candle['open']
                        elif candle['close'] < candle['open']:
                            candle_type = "Bearish"
                            candle_body = candle['open'] - candle['close']
                        else:
                            candle_type = "Doji"
                            candle_body = 0
                        
                        output.append(f"  Type: {candle_type}")
                        
                        if candle_body > 0:
                            candle_range = candle['high'] - candle['low']
                            if candle_range > 0:
                                body_ratio = (candle_body / candle_range) * 100
                                output.append(f"  Body/Range: {body_ratio:.1f}%")
                        
                        if candle.get('volume', 0) > 0:
                            output.append(f"  Volume: {candle['volume']:,.0f}")
                        
                        # Recency indicator with zone scoring impact
                        if days_ago <= 5:
                            if hasattr(zone, 'recency_score') and zone.recency_score > 1:
                                output.append(f"  ⚡ RECENT INTERACTION (Score boost: {(zone.recency_score-1)*100:.0f}%)")
                            else:
                                output.append(f"  ⚡ RECENT INTERACTION")
                        elif days_ago <= 10:
                            if hasattr(zone, 'recency_score') and zone.recency_score > 1:
                                output.append(f"  ✓ Recent (Score boost: {(zone.recency_score-1)*100:.0f}%)")
                            else:
                                output.append(f"  ✓ Recent (within 10 days)")
                        elif days_ago <= 20:
                            output.append(f"  · Moderate recency")
                        else:
                            output.append(f"  · Historical")
                    else:
                        output.append(f"\n⚠️  No M15 candle overlap found in last 30 days")
        
        output.append("\n" + "="*60)
        output.append("LEGEND")
        output.append("="*60)
        output.append("Confluence Levels: L1 (Low) → L5 (High)")
        output.append("Zone Types: Support = Below current price | Resistance = Above current price")
        output.append("M15 Overlap: % of candle body that overlapped with zone")
        output.append("Recency Boost: Recent M15 interactions increase zone score")
        
        return "\n".join(output)