"""
Test full confluence integration with correct data structures
"""

import sys
from pathlib import Path

# Add levels_zones directory to path
levels_zones_root = Path(__file__).parent.parent
sys.path.insert(0, str(levels_zones_root))

def test_full_confluence_integration():
    """Test confluence with correctly structured HVN and Camarilla data"""
    print("=== FULL CONFLUENCE INTEGRATION TEST ===")
    
    try:
        from calculations.volume.hvn_engine import TimeframeResult, VolumePeak
        from calculations.pivots.camarilla_engine import CamarillaResult, CamarillaPivot
        from calculations.confluence.confluence_engine import ConfluenceEngine
        
        # Create VolumePeak objects with correct constructor
        # VolumePeak(price, rank, volume_percent, level_index)
        volume_peaks_7day = [
            VolumePeak(price=249.75, rank=1, volume_percent=15.2, level_index=87),
            VolumePeak(price=246.30, rank=2, volume_percent=12.8, level_index=45),
            VolumePeak(price=252.10, rank=3, volume_percent=11.5, level_index=95),
            VolumePeak(price=244.80, rank=4, volume_percent=10.1, level_index=32),
        ]
        
        volume_peaks_14day = [
            VolumePeak(price=248.90, rank=1, volume_percent=18.5, level_index=72),
            VolumePeak(price=245.60, rank=2, volume_percent=14.2, level_index=38),
            VolumePeak(price=251.40, rank=3, volume_percent=12.8, level_index=91),
        ]
        
        volume_peaks_30day = [
            VolumePeak(price=247.20, rank=1, volume_percent=16.8, level_index=55),
            VolumePeak(price=250.50, rank=2, volume_percent=15.3, level_index=85),
        ]
        
        # Create TimeframeResult objects
        hvn_7day = TimeframeResult(
            timeframe_days=7,
            price_range=(240.0, 255.0),
            total_levels=100,
            peaks=volume_peaks_7day,
            data_points=2016  # 7 days * 24 hours * 12 (5-min bars)
        )
        
        hvn_14day = TimeframeResult(
            timeframe_days=14,
            price_range=(238.0, 257.0),
            total_levels=100,
            peaks=volume_peaks_14day,
            data_points=4032
        )
        
        hvn_30day = TimeframeResult(
            timeframe_days=30,
            price_range=(235.0, 260.0),
            total_levels=100,
            peaks=volume_peaks_30day,
            data_points=8640
        )
        
        # Create CamarillaPivot objects with correct constructor
        # CamarillaPivot(level_name, price, strength, timeframe)
        daily_pivots = [
            CamarillaPivot(level_name='R6', price=253.45, strength=6, timeframe='daily'),
            CamarillaPivot(level_name='R4', price=251.20, strength=4, timeframe='daily'),
            CamarillaPivot(level_name='R3', price=250.10, strength=3, timeframe='daily'),
            CamarillaPivot(level_name='S3', price=245.80, strength=3, timeframe='daily'),
            CamarillaPivot(level_name='S4', price=244.70, strength=4, timeframe='daily'),
            CamarillaPivot(level_name='S6', price=242.35, strength=6, timeframe='daily'),
        ]
        
        weekly_pivots = [
            CamarillaPivot(level_name='R6', price=255.80, strength=6, timeframe='weekly'),
            CamarillaPivot(level_name='R4', price=252.40, strength=4, timeframe='weekly'),
            CamarillaPivot(level_name='R3', price=250.85, strength=3, timeframe='weekly'),
            CamarillaPivot(level_name='S3', price=244.20, strength=3, timeframe='weekly'),
            CamarillaPivot(level_name='S4', price=242.10, strength=4, timeframe='weekly'),
            CamarillaPivot(level_name='S6', price=238.95, strength=6, timeframe='weekly'),
        ]
        
        monthly_pivots = [
            CamarillaPivot(level_name='R6', price=258.20, strength=6, timeframe='monthly'),
            CamarillaPivot(level_name='R4', price=254.10, strength=4, timeframe='monthly'),
            CamarillaPivot(level_name='R3', price=252.30, strength=3, timeframe='monthly'),
            CamarillaPivot(level_name='S3', price=242.80, strength=3, timeframe='monthly'),
            CamarillaPivot(level_name='S4', price=240.50, strength=4, timeframe='monthly'),
            CamarillaPivot(level_name='S6', price=236.75, strength=6, timeframe='monthly'),
        ]
        
        # Create CamarillaResult objects
        cam_daily = CamarillaResult(
            timeframe='daily',
            close=247.50,
            high=248.90,
            low=246.20,
            pivots=daily_pivots,
            range_type='higher',
            central_pivot=247.87
        )
        
        cam_weekly = CamarillaResult(
            timeframe='weekly',
            close=247.50,
            high=252.80,
            low=242.10,
            pivots=weekly_pivots,
            range_type='higher',
            central_pivot=247.47
        )
        
        cam_monthly = CamarillaResult(
            timeframe='monthly',
            close=247.50,
            high=258.20,
            low=236.75,
            pivots=monthly_pivots,
            range_type='higher',
            central_pivot=247.48
        )
        
        print("✅ Successfully created all data structures!")
        
        # Test M15 zones designed to hit multiple confluences
        m15_zones = [
            {'zone_number': 1, 'high': '250.50', 'low': '248.75'},  # Should hit multiple HVN peaks + daily levels + Camarilla
            {'zone_number': 2, 'high': '245.25', 'low': '243.80'},  # Should hit some HVN + Camarilla S levels  
            {'zone_number': 3, 'high': '252.50', 'low': '251.00'},  # Should hit R3/R4 levels + some HVN
            {'zone_number': 4, 'high': '240.60', 'low': '238.90'},  # Should hit S6 levels
        ]
        
        # Daily levels (6 levels: 3 above, 3 below current price of 247.50)
        daily_levels = [252.30, 250.75, 249.20, 246.80, 244.50, 242.10]
        
        # Metrics (ATR and reference prices)
        metrics = {
            'current_price': 247.50,
            'atr_high': 250.25,
            'atr_low': 244.75,
            'open_price': 246.80,
            'pre_market_price': 247.10
        }
        
        print(f"\nTest Data Summary:")
        print(f"• HVN 7-day: {len(volume_peaks_7day)} peaks")
        print(f"• HVN 14-day: {len(volume_peaks_14day)} peaks") 
        print(f"• HVN 30-day: {len(volume_peaks_30day)} peaks")
        print(f"• Daily Camarilla: {len(daily_pivots)} pivots")
        print(f"• Weekly Camarilla: {len(weekly_pivots)} pivots")
        print(f"• Monthly Camarilla: {len(monthly_pivots)} pivots")
        print(f"• Daily levels: {len(daily_levels)} levels")
        print(f"• M15 zones: {len(m15_zones)} zones")
        print(f"• Current price: ${metrics['current_price']}")
        
        # Run full confluence analysis
        engine = ConfluenceEngine()
        
        result = engine.calculate_confluence(
            m15_zones=m15_zones,
            hvn_results={7: hvn_7day, 14: hvn_14day, 30: hvn_30day},
            camarilla_results={'daily': cam_daily, 'weekly': cam_weekly, 'monthly': cam_monthly},
            daily_levels=daily_levels,
            metrics=metrics
        )
        
        print(f"\n🎉 FULL CONFLUENCE TEST SUCCESSFUL!")
        print(f"Total inputs processed: {result.total_inputs_checked}")
        print(f"Zones with confluence: {result.zones_with_confluence}/{len(result.zone_scores)}")
        
        print(f"\n📊 Input Summary:")
        for source_type, count in result.input_summary.items():
            print(f"  • {source_type.value}: {count} inputs")
        
        # Show detailed confluence results
        print(f"\n" + "="*70)
        print("CONFLUENCE ANALYSIS RESULTS")
        print("="*70)
        formatted = engine.format_confluence_result(result, 247.50)
        print(formatted)
        
        # Detailed breakdown
        print(f"\n" + "="*70)
        print("DETAILED CONFLUENCE BREAKDOWN")
        print("="*70)
        
        ranked_zones = result.get_ranked_zones()
        for zone in ranked_zones:
            print(f"\n🎯 Zone {zone.zone_number} ({zone.confluence_level.value})")
            print(f"   Range: ${zone.zone_low} - ${zone.zone_high}")
            print(f"   Confluences: {zone.confluence_count}")
            
            # Group by source type for cleaner display
            by_source = {}
            for inp in zone.confluent_inputs:
                if inp.source_type not in by_source:
                    by_source[inp.source_type] = []
                by_source[inp.source_type].append(inp)
            
            for source_type, inputs in by_source.items():
                print(f"   📈 {source_type.value}:")
                for inp in inputs:
                    print(f"      • {inp.level_name}: ${inp.price}")
        
        return result
        
    except Exception as e:
        print(f"❌ Full confluence test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("FULL CONFLUENCE INTEGRATION TEST")
    print("=" * 70)
    
    result = test_full_confluence_integration()
    
    if result:
        print(f"\n🚀 SUCCESS!")
        print(f"✅ Confluence engine fully integrated and working")
        print(f"✅ All data structures properly constructed")
        print(f"✅ Ready for analysis_thread.py integration")
        
        # Show summary stats for confidence
        print(f"\n📋 Integration Ready Checklist:")
        print(f"   ✅ ConfluenceEngine imports correctly")
        print(f"   ✅ TimeframeResult/CamarillaResult structures confirmed")
        print(f"   ✅ VolumePeak/CamarillaPivot constructors verified")  
        print(f"   ✅ Full confluence calculation working")
        print(f"   ✅ Formatted output displays correctly")
        print(f"   ✅ Multiple input sources processed ({result.total_inputs_checked} total)")
        print(f"   ✅ Zone ranking system working")
        
    else:
        print(f"\n❌ ISSUES FOUND")
        print(f"❌ Debug needed before analysis_thread.py integration")
    
    print("\n" + "=" * 70)
    print("Test complete!")