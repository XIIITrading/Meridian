"""Export zones to Sierra Chart format"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime, date
from pathlib import Path
import logging

from .config import config

logger = logging.getLogger(__name__)

class SierraExporter:
    """Export zones to Sierra Chart compatible format"""
    
    def __init__(self, output_path: str = None):
        """Initialize exporter with output path"""
        self.output_path = Path(output_path or config.SIERRA_CHART_PATH)
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Sierra Chart output path: {self.output_path}")
    
    def export_zones(self, zones_by_ticker: Dict[str, List[Any]], 
                    trade_date: date,
                    filename: str = None) -> str:
        """
        Export zones to JSON file for Sierra Chart
        
        Args:
            zones_by_ticker: Dictionary of ticker -> zones
            trade_date: Trade date for these zones
            filename: Output filename (defaults to config.OUTPUT_FILENAME)
            
        Returns:
            Path to exported main file
        """
        filename = filename or config.OUTPUT_FILENAME
        
        # Create comprehensive output data
        output_data = {
            'metadata': {
                'trade_date': trade_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'total_tickers': len(zones_by_ticker),
                'total_zones': sum(len(zones) for zones in zones_by_ticker.values()),
                'confluence_levels': list(config.LEVEL_COLORS.keys()),
                'color_mapping': config.LEVEL_COLORS,
                'version': '1.0.0'
            },
            'tickers': {}
        }
        
        # Process each ticker
        for ticker, zones in zones_by_ticker.items():
            ticker_data = {
                'symbol': ticker,
                'trade_date': trade_date.isoformat(),
                'zone_count': len(zones),
                'zones': [],
                'statistics': self._calculate_ticker_stats(zones)
            }
            
            # Add zone data
            for zone in zones:
                zone_dict = zone.to_dict() if hasattr(zone, 'to_dict') else zone.__dict__
                
                # Add Sierra Chart specific formatting
                sierra_zone = {
                    'id': f"{ticker}_zone_{zone_dict.get('zone_number', 0)}",
                    'high': zone_dict['high'],
                    'low': zone_dict['low'],
                    'center': zone_dict.get('center', (zone_dict['high'] + zone_dict['low']) / 2),
                    'level': zone_dict.get('confluence_level', zone_dict.get('level', 'L3')),
                    'score': zone_dict.get('confluence_score', 0),
                    'source_count': zone_dict.get('source_count', 0),
                    'sources': zone_dict.get('sources', []),
                    'color': self._get_zone_color(zone_dict),
                    'intensity': zone_dict.get('color_intensity', 0.5),
                    'confluence_flags': zone_dict.get('confluence_flags', {}),
                    'zone_number': zone_dict.get('zone_number', 0)
                }
                
                ticker_data['zones'].append(sierra_zone)
            
            # Sort zones by price for consistent ordering
            ticker_data['zones'].sort(key=lambda z: z['low'])
            output_data['tickers'][ticker] = ticker_data
        
        # Write main consolidated file
        main_file = self.output_path / filename
        with open(main_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Exported consolidated zones to {main_file}")
        
        # Create individual ticker files for ACSIL
        for ticker, zones in zones_by_ticker.items():
            self._export_ticker_file(ticker, zones, trade_date)
        
        # Create summary file
        self._export_summary_file(output_data, trade_date)
        
        return str(main_file)
    
    def _export_ticker_file(self, ticker: str, zones: List[Any], trade_date: date):
        """Export individual ticker file optimized for ACSIL reading"""
        
        ticker_data = {
            'metadata': {
                'symbol': ticker,
                'trade_date': trade_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'zone_count': len(zones)
            },
            'zones': []
        }
        
        for zone in zones:
            zone_dict = zone.to_dict() if hasattr(zone, 'to_dict') else zone.__dict__
            
            # Simplified format for ACSIL consumption
            acsil_zone = {
                'high': float(zone_dict['high']),
                'low': float(zone_dict['low']),
                'center': float(zone_dict.get('center', (zone_dict['high'] + zone_dict['low']) / 2)),
                'level': zone_dict.get('confluence_level', zone_dict.get('level', 'L3')),
                'score': float(zone_dict.get('confluence_score', 0)),
                'source_count': int(zone_dict.get('source_count', 0)),
                'color_intensity': float(zone_dict.get('color_intensity', 0.5)),
                'zone_id': zone_dict.get('zone_number', 0),
                # RGB color values for direct ACSIL use
                'color_rgb': self._get_zone_color(zone_dict, as_rgb=True)
            }
            
            ticker_data['zones'].append(acsil_zone)
        
        # Sort by price
        ticker_data['zones'].sort(key=lambda z: z['low'])
        
        # Write ticker-specific file
        ticker_file = self.output_path / f"{ticker}_zones.json"
        with open(ticker_file, 'w') as f:
            json.dump(ticker_data, f, indent=2)
        
        logger.info(f"Exported {ticker} zones to {ticker_file}")
    
    def _export_summary_file(self, output_data: Dict[str, Any], trade_date: date):
        """Export summary statistics file"""
        
        summary = {
            'date': trade_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'overview': output_data['metadata'],
            'ticker_summary': {}
        }
        
        for ticker, data in output_data['tickers'].items():
            summary['ticker_summary'][ticker] = {
                'zones': data['zone_count'],
                'levels': data.get('statistics', {}).get('level_counts', {}),
                'avg_score': data.get('statistics', {}).get('avg_confluence_score', 0),
                'max_score': data.get('statistics', {}).get('max_confluence_score', 0)
            }
        
        summary_file = self.output_path / "zones_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Exported summary to {summary_file}")
    
    def _get_zone_color(self, zone_dict: Dict[str, Any], as_rgb: bool = False) -> Dict[str, Any]:
        """Get color information for a zone based on confluence level"""
        
        level = zone_dict.get('confluence_level', zone_dict.get('level', 'L3'))
        base_color = config.LEVEL_COLORS.get(level, config.LEVEL_COLORS['L3'])
        intensity = zone_dict.get('color_intensity', 0.5)
        
        # Apply intensity scaling
        scaled_color = {
            'r': int(base_color['r'] * intensity),
            'g': int(base_color['g'] * intensity), 
            'b': int(base_color['b'] * intensity)
        }
        
        if as_rgb:
            return scaled_color
        else:
            return {
                'level': level,
                'rgb': scaled_color,
                'hex': f"#{scaled_color['r']:02x}{scaled_color['g']:02x}{scaled_color['b']:02x}",
                'intensity': intensity
            }
    
    def _calculate_ticker_stats(self, zones: List[Any]) -> Dict[str, Any]:
        """Calculate statistics for a ticker's zones"""
        
        if not zones:
            return {}
        
        scores = []
        level_counts = {}
        source_counts = []
        
        for zone in zones:
            zone_dict = zone.to_dict() if hasattr(zone, 'to_dict') else zone.__dict__
            
            score = zone_dict.get('confluence_score', 0)
            level = zone_dict.get('confluence_level', zone_dict.get('level', 'L3'))
            source_count = zone_dict.get('source_count', 0)
            
            scores.append(float(score))
            source_counts.append(int(source_count))
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'zone_count': len(zones),
            'level_counts': level_counts,
            'confluence_stats': {
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'total_sources': sum(source_counts),
                'avg_sources': sum(source_counts) / len(source_counts) if source_counts else 0
            }
        }
    
    def create_acsil_header_file(self):
        """Create C++ header file with zone data structures for ACSIL"""
        
        header_content = '''// Auto-generated Sierra Chart ACSIL header for Confluence Zones
// Generated at: {timestamp}

#ifndef CONFLUENCE_ZONES_H
#define CONFLUENCE_ZONES_H

struct ConfluenceZone {{
    float High;
    float Low;
    float Center;
    float ConfluenceScore;
    int SourceCount;
    float ColorIntensity;
    int ZoneId;
    COLORREF Color;
}};

// Zone level definitions
#define ZONE_L1 1
#define ZONE_L2 2  
#define ZONE_L3 3
#define ZONE_L4 4
#define ZONE_L5 5

// Color definitions
#define COLOR_L1 RGB(128, 128, 128)  // Gray
#define COLOR_L2 RGB(0, 128, 255)    // Blue
#define COLOR_L3 RGB(0, 200, 0)      // Green
#define COLOR_L4 RGB(255, 128, 0)    // Orange
#define COLOR_L5 RGB(255, 0, 0)      // Red

#endif // CONFLUENCE_ZONES_H
'''.format(timestamp=datetime.now().isoformat())
        
        header_file = self.output_path / "confluence_zones.h"
        with open(header_file, 'w') as f:
            f.write(header_content)
        
        logger.info(f"Created ACSIL header file: {header_file}")
        return str(header_file)