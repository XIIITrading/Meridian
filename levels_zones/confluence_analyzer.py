import pandas as pd
import numpy as np
from collections import defaultdict
import os

class ConfluenceZoneAnalyzer:
    def __init__(self, weight_config=None, zone_margin=0.005):
        """
        Initialize with weight configuration for different level types
        zone_margin: percentage to expand HVN zones (0.005 = 0.5%)
        """
        self.weights = weight_config or {
            'weekly_cam': 4,      # Weekly Cam Pivots
            'daily_structure': 3, # Daily Structure (AD/BD levels)
            'h4_ob': 2.5,        # H4 Order Blocks
            'daily_cam': 1,      # Daily Camarilla Pivots
        }
        self.zone_margin = zone_margin
        
    def get_hvn_zones(self, row):
        """
        Extract HVN zones - these are our PRIMARY zones now
        """
        hvn_zones = []
        
        # HVN Zone definitions
        zone_definitions = [
            ('BHVN1', 'BHVN1 Low', 'BHVN1 High', 'below'),
            ('BHVN2', 'BHVN2 Low', 'BHVN2 High', 'below'),
            ('AHVN1', 'AHVN1 Low', 'AHVN1 High', 'above'),
            ('AHVN2', 'AHVN2 Low', 'AHVN2 High', 'above')
        ]
        
        for zone_name, low_col, high_col, zone_position in zone_definitions:
            if pd.notna(row[low_col]) and pd.notna(row[high_col]):
                zone_low = row[low_col]
                zone_high = row[high_col]
                
                # Calculate the expansion margin (0.5% of the zone midpoint)
                zone_center = (zone_low + zone_high) / 2
                margin = zone_center * self.zone_margin
                
                hvn_zones.append({
                    'name': zone_name,
                    'position': zone_position,  # 'above' or 'below' HVN
                    'original_low': zone_low,
                    'original_high': zone_high,
                    'test_low': zone_low - margin,    # Expanded zone for confluence testing
                    'test_high': zone_high + margin,
                    'center': zone_center,
                    'zone_size': zone_high - zone_low,
                    'confluent_levels': [],
                    'confluence_score': 0
                })
        
        return hvn_zones
    
    def get_confluence_levels(self, row):
        """
        Extract all levels that could provide confluence to HVN zones
        Including Order Blocks as confluence levels now
        """
        levels = []
        
        # H4 Order Block Zones (now treated as confluence)
        ob_zones = [
            ('H4S2', 'H4S2 Low', 'H4S2 High', 'support'),
            ('H4S1', 'H4S1 Low', 'H4S1 High', 'support'),
            ('H4R1', 'H4R1 Low', 'H4R1 High', 'resistance'),
            ('H4R2', 'H4R2 Low', 'H4R2 High', 'resistance')
        ]
        
        for zone_name, low_col, high_col, zone_type in ob_zones:
            if pd.notna(row[low_col]) and pd.notna(row[high_col]):
                # Add OB zone edges as levels
                levels.append({
                    'type': 'h4_ob',
                    'name': f'{zone_name}_Low',
                    'price': row[low_col],
                    'weight': self.weights['h4_ob'],
                    'ob_type': zone_type
                })
                levels.append({
                    'type': 'h4_ob',
                    'name': f'{zone_name}_High',
                    'price': row[high_col],
                    'weight': self.weights['h4_ob'],
                    'ob_type': zone_type
                })
                
                # Also add OB zone center as a level
                center = (row[low_col] + row[high_col]) / 2
                levels.append({
                    'type': 'h4_ob',
                    'name': f'{zone_name}_Center',
                    'price': center,
                    'weight': self.weights['h4_ob'] * 0.75,  # Slightly less weight for center
                    'ob_type': zone_type
                })
        
        # Daily Structure Levels
        for level in ['AD3', 'AD2', 'AD1', 'BD1', 'BD2', 'BD3']:
            if pd.notna(row[level]):
                levels.append({
                    'type': 'daily_structure',
                    'name': level,
                    'price': row[level],
                    'weight': self.weights['daily_structure']
                })
        
        # Daily Camarilla Pivots
        for level in ['S6', 'S4', 'S3', 'R3', 'R4', 'R6']:
            if pd.notna(row[level]):
                levels.append({
                    'type': 'daily_cam',
                    'name': f'Daily_{level}',
                    'price': row[level],
                    'weight': self.weights['daily_cam']
                })
        
        # Weekly Camarilla Pivots
        for level in ['WS6', 'WS4', 'WS3', 'WR3', 'WR4', 'WR6']:
            if pd.notna(row[level]):
                levels.append({
                    'type': 'weekly_cam',
                    'name': f'Weekly_{level}',
                    'price': row[level],
                    'weight': self.weights['weekly_cam']
                })
        
        return levels
    
    def calculate_hvn_confluence(self, hvn_zones, confluence_levels):
        """
        For each HVN zone, calculate confluence based on levels within/near it
        """
        for hvn_zone in hvn_zones:
            # Reset confluence data
            hvn_zone['confluent_levels'] = []
            hvn_zone['confluence_details'] = {
                'weekly_cam': [],
                'daily_structure': [],
                'h4_ob': [],
                'daily_cam': []
            }
            
            # Check each level for confluence with this HVN zone
            for level in confluence_levels:
                # Check if level falls within the expanded HVN zone
                if hvn_zone['test_low'] <= level['price'] <= hvn_zone['test_high']:
                    hvn_zone['confluent_levels'].append(level)
                    hvn_zone['confluence_details'][level['type']].append(level)
            
            # Calculate confluence score for this HVN zone
            total_weight = sum(level['weight'] for level in hvn_zone['confluent_levels'])
            
            # Type diversity bonus
            types_present = sum(1 for level_type, levels in hvn_zone['confluence_details'].items() 
                              if len(levels) > 0)
            type_multiplier = 1 + (types_present - 1) * 0.25
            
            # Calculate final score
            hvn_zone['confluence_score'] = total_weight * type_multiplier
            hvn_zone['confluence_count'] = len(hvn_zone['confluent_levels'])
            hvn_zone['confluence_types'] = types_present
            
            # Categorize strength
            if hvn_zone['confluence_score'] < 3:
                hvn_zone['strength'] = 'Weak'
            elif hvn_zone['confluence_score'] < 8:
                hvn_zone['strength'] = 'Moderate'
            elif hvn_zone['confluence_score'] < 15:
                hvn_zone['strength'] = 'Strong'
            else:
                hvn_zone['strength'] = 'Exceptional'
            
            # Check if any Order Block overlaps significantly
            ob_overlap = any(level['type'] == 'h4_ob' for level in hvn_zone['confluent_levels'])
            hvn_zone['has_ob_confluence'] = ob_overlap
        
        return hvn_zones
    
    def analyze_row(self, row):
        """
        Analyze a single row of data
        """
        current_price = row['Pre-Market Price']
        
        # Step 1: Get HVN zones (our primary zones now)
        hvn_zones = self.get_hvn_zones(row)
        
        # Step 2: Get all other levels for confluence checking (including OB zones)
        confluence_levels = self.get_confluence_levels(row)
        
        # Step 3: Calculate confluence for each HVN zone
        hvn_zones = self.calculate_hvn_confluence(hvn_zones, confluence_levels)
        
        # Step 4: Separate and rank zones
        above_zones = [z for z in hvn_zones if z['center'] > current_price]
        below_zones = [z for z in hvn_zones if z['center'] < current_price]
        
        # Sort by confluence score (primary) and distance (secondary)
        above_zones.sort(key=lambda x: (-x['confluence_score'], abs(x['center'] - current_price)))
        below_zones.sort(key=lambda x: (-x['confluence_score'], abs(x['center'] - current_price)))
        
        return {
            'ticker': row['Ticker'],
            'date': row['Date'],
            'current_price': current_price,
            'resistance_zones': above_zones,
            'support_zones': below_zones,
            'all_hvn_zones': hvn_zones
        }

def analyze_levels_and_zones(csv_path='levels_zones.csv'):
    """
    Main analysis function
    """
    try:
        # Load data
        if not os.path.exists(csv_path):
            print(f"Error: Could not find {csv_path}")
            return None
            
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded {csv_path}")
        print(f"Found {len(df)} rows of data\n")
        
        # Initialize analyzer
        analyzer = ConfluenceZoneAnalyzer()
        
        # Analyze each row
        results = []
        for idx, row in df.iterrows():
            result = analyzer.analyze_row(row)
            results.append(result)
            
            # Display results
            print(f"\n{'='*80}")
            print(f"HVN ZONE CONFLUENCE ANALYSIS")
            print(f"Ticker: {result['ticker']} | Date: {result['date']} | Price: {result['current_price']}")
            print(f"{'='*80}")
            
            # Resistance Zones
            print(f"\n📈 RESISTANCE ZONES (HVN zones above price):")
            if result['resistance_zones']:
                for zone in result['resistance_zones']:
                    print(f"\n  🔴 {zone['name']} Zone: {zone['original_low']:.2f} - {zone['original_high']:.2f}")
                    print(f"     Strength: {zone['strength']} (Score: {zone['confluence_score']:.1f})")
                    print(f"     Size: {zone['zone_size']:.2f} points")
                    if zone['has_ob_confluence']:
                        print(f"     ⚡ Has Order Block confluence!")
                    
                    if zone['confluence_count'] > 0:
                        print(f"     Confluence ({zone['confluence_count']} levels):")
                        for level_type, levels in zone['confluence_details'].items():
                            if levels:
                                level_str = ', '.join([f"{l['name']}@{l['price']:.2f}" for l in levels])
                                print(f"       • {level_type}: {level_str}")
                    else:
                        print(f"     No additional confluence")
            else:
                print("  No HVN resistance zones found above current price")
            
            # Support Zones
            print(f"\n📉 SUPPORT ZONES (HVN zones below price):")
            if result['support_zones']:
                for zone in result['support_zones']:
                    print(f"\n  🟢 {zone['name']} Zone: {zone['original_low']:.2f} - {zone['original_high']:.2f}")
                    print(f"     Strength: {zone['strength']} (Score: {zone['confluence_score']:.1f})")
                    print(f"     Size: {zone['zone_size']:.2f} points")
                    if zone['has_ob_confluence']:
                        print(f"     ⚡ Has Order Block confluence!")
                    
                    if zone['confluence_count'] > 0:
                        print(f"     Confluence ({zone['confluence_count']} levels):")
                        for level_type, levels in zone['confluence_details'].items():
                            if levels:
                                level_str = ', '.join([f"{l['name']}@{l['price']:.2f}" for l in levels])
                                print(f"       • {level_type}: {level_str}")
                    else:
                        print(f"     No additional confluence")
            else:
                print("  No HVN support zones found below current price")
        
        # Summary
        print(f"\n\n{'='*80}")
        print("TRADING SUMMARY - HVN ZONES WITH CONFLUENCE")
        print(f"{'='*80}")
        
        for result in results:
            print(f"\n{result['ticker']} - {result['date']} (Price: {result['current_price']:.2f})")
            
            # Best resistance
            if result['resistance_zones']:
                best_r = result['resistance_zones'][0]
                ob_mark = "⚡" if best_r['has_ob_confluence'] else ""
                print(f"  Primary Resistance: {best_r['name']} ({best_r['original_low']:.2f}-{best_r['original_high']:.2f}) - {best_r['strength']} {ob_mark}")
            
            # Best support
            if result['support_zones']:
                best_s = result['support_zones'][0]
                ob_mark = "⚡" if best_s['has_ob_confluence'] else ""
                print(f"  Primary Support: {best_s['name']} ({best_s['original_low']:.2f}-{best_s['original_high']:.2f}) - {best_s['strength']} {ob_mark}")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run the analysis
if __name__ == "__main__":
    print("HVN Zone Confluence Analyzer")
    print("Analyzing High Volume Node zones with confluence from Order Blocks and other levels...")
    print("-" * 80)
    
    results = analyze_levels_and_zones()
    
    if results:
        print(f"\n\nAnalysis complete! Processed {len(results)} days of HVN zone data.")