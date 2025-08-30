# Sierra Chart ACSIL Setup Guide

Complete setup instructions for the Confluence Zones ACSIL study in Sierra Chart.

## Files Created

Your Sierra Chart integration includes:

### Python Integration
- `main.py` - CLI tool for zone export
- `supabase_client.py` - Database connectivity
- `zone_fetcher.py` - Data processing
- `sierra_exporter.py` - JSON file generation
- `config.py` - Configuration settings

### ACSIL Study Files
- `ConfluenceZones.cpp` - Main ACSIL study
- `ConfluenceZones.h` - Header file with declarations
- `SIERRA_CHART_SETUP.md` - This setup guide

### Generated Data Files (Created when you run the Python tool)
- `TICKER_zones.json` - Individual ticker zone data (e.g., `TSLA_zones.json`)
- `confluence_zones.json` - Master file with all zones
- `zones_summary.json` - Statistics summary
- `confluence_zones.h` - Auto-generated C++ header

## Step-by-Step Setup

### Step 1: Compile the ACSIL Study

1. **Copy ACSIL files to Sierra Chart**:
   ```
   Copy ConfluenceZones.cpp → C:\SierraChart\ACS_Source\
   Copy ConfluenceZones.h → C:\SierraChart\ACS_Source\
   ```

2. **Open Sierra Chart**
3. **Go to Analysis → Build Custom Studies DLL**
4. **Click "Build" - this compiles all studies including yours**
5. **Wait for "Build succeeded" message**

### Step 2: Add Study to Your Chart

1. **Right-click on any chart**
2. **Select "Studies" → "Add Study"**
3. **Find "Confluence Zones" in the list**
4. **Click "Add"**
5. **Configure the study settings (see Configuration section below)**

### Step 3: Configure the Study

The study has several configurable options:

#### Display Options
- **Show Zones**: Enable/disable all zone display
- **Show Zone Labels**: Show level and score labels on zones
- **Zone Transparency**: 0-100% transparency level
- **Minimum Confluence Score**: Only show zones above this score

#### Level Filters
- **Show L1 (Gray) Zones**: Low confluence zones
- **Show L2 (Blue) Zones**: Low-medium confluence
- **Show L3 (Green) Zones**: Medium confluence  
- **Show L4 (Orange) Zones**: High confluence
- **Show L5 (Red) Zones**: Highest confluence zones

#### Advanced Options
- **Zone File Path**: Leave empty for auto-detection
- **Refresh Interval**: How often to check for file updates (5-300 seconds)

### Step 4: Generate Zone Data

Use the Python integration to export zones:

```bash
# Navigate to confluence system
cd C:\XIIITradingSystems\Meridian\confluence_system

# Interactive mode (recommended)
python -m sierra_chart.main

# Command line examples
python -m sierra_chart.main --date 2025-08-28 --tickers TSLA
python -m sierra_chart.main --yesterday --tickers TSLA,AAPL,NVDA
python -m sierra_chart.main --today --min-score 5.0
```

## How It Works

### Data Flow
1. **Confluence Analysis** → Creates zones with confluence scores
2. **Database Storage** → Saves to Supabase with detailed confluence data  
3. **Python Export** → Generates JSON files in `C:\SierraChart\Data\Zones\`
4. **ACSIL Study** → Reads JSON files and draws zones on charts

### File Structure
The ACSIL study automatically looks for files named:
```
C:\SierraChart\Data\Zones\SYMBOL_zones.json
```

For example:
- `TSLA_zones.json` for Tesla charts
- `AAPL_zones.json` for Apple charts
- `SPY_zones.json` for SPY charts

### Zone Display
- **Rectangles**: Colored zones based on confluence level
- **Colors**: L5=Red, L4=Orange, L3=Green, L2=Blue, L1=Gray
- **Labels**: Show level and confluence score
- **Transparency**: Adjustable for better chart visibility

## Typical Workflow

### Daily Trading Setup

1. **Morning**: Run confluence analysis for your watchlist
   ```bash
   python confluence_cli.py TSLA 2025-08-29 09:00 -w WL1 WL2 WL3 WL4 -d DL1 DL2 DL3 DL4 --save-db
   ```

2. **Export zones to Sierra Chart**:
   ```bash
   python -m sierra_chart.main --today --tickers TSLA,AAPL,NVDA --min-score 3.0
   ```

3. **Open Sierra Chart** - zones appear automatically on your charts

4. **Trade** using the confluence zones as support/resistance levels

### Updating During the Day

The ACSIL study automatically refreshes based on your refresh interval setting. If you run new confluence analysis:

1. Run the Python export tool again
2. The study will detect file changes and update zones automatically
3. No need to restart Sierra Chart or reload the study

## Troubleshooting

### Study Not Appearing
- **Check compilation**: Look for errors in the Build Custom Studies dialog
- **Restart Sierra Chart**: Sometimes required after first compilation
- **Verify file placement**: Ensure .cpp and .h files are in ACS_Source folder

### No Zones Displayed
- **Check file path**: Verify `C:\SierraChart\Data\Zones\SYMBOL_zones.json` exists
- **Symbol matching**: File name must match chart symbol exactly
- **Filter settings**: Check minimum confluence score and level filters
- **File permissions**: Ensure Sierra Chart can read the zone files

### Zones Not Updating
- **Check refresh interval**: Increase if zones seem stale
- **Manual refresh**: Remove and re-add the study to force reload
- **File timestamps**: Ensure JSON files have recent modification times

### Common Error Messages

**"Cannot open zone file"**
- Run the Python export tool for this symbol/date
- Check that the file path is correct
- Verify file permissions

**"No zones array found in JSON"**
- JSON file may be corrupted
- Re-run the Python export tool
- Check that the export completed successfully

## Advanced Configuration

### Custom File Paths
If you want to store zone files elsewhere:

1. Set the **Zone File Path** input to your custom location
2. Ensure the Python tool exports to the same location
3. Update the `SIERRA_CHART_PATH` in `config.py`

### Performance Tuning
- **Refresh Interval**: Higher values (60+ seconds) for better performance
- **Level Filters**: Disable unused levels to reduce drawing load
- **Minimum Score**: Higher values show only the best zones

### Integration with Other Studies
The zones work well with:
- Volume Profile studies
- Support/Resistance indicators  
- Trend analysis tools
- Custom alert systems

## API Reference

### ACSIL Study Functions

```cpp
// Main study entry point
scsf_ConfluenceZones(SCStudyInterfaceRef sc)

// Load zones from JSON file
LoadZonesFromFile(sc, filePath, zones)

// Draw zones on chart
DrawConfluenceZones(sc, zones, showLabels, transparency, minScore, ...)

// Clear existing zone drawings
ClearZoneDrawings(sc)
```

### Zone Data Structure
```cpp
struct ConfluenceZone {
    float High, Low, Center;    // Zone price levels
    float Score;                // Confluence score (0-10)
    int SourceCount;           // Number of confluence sources
    COLORREF Color;            // RGB color for display
    SCString Level;            // L1, L2, L3, L4, or L5
    bool IsValid;              // Zone validity flag
}
```

## Support and Updates

### Version History
- **v1.0.0**: Initial release with full confluence integration

### Known Issues
- Very large zone files (1000+ zones) may impact performance
- File system latency can delay zone updates

### Feature Requests
Consider adding:
- Zone expiration times
- Dynamic color intensity based on time
- Integration with Sierra Chart alerts
- Multi-timeframe zone display

---

**Your complete confluence zone integration is now ready for production trading!** 🎯