# Sierra Chart Integration

Fetch confluence zone data from Supabase and export to Sierra Chart compatible JSON format for ACSIL consumption.

## Features

- ✅ **Date-based zone retrieval** from confluence system database
- ✅ **Multi-ticker support** with filtering capabilities  
- ✅ **Confluence-aware export** with proper level colors and scoring
- ✅ **Sierra Chart optimized format** for ACSIL integration
- ✅ **Interactive mode** for easy date/ticker selection
- ✅ **Command line interface** for automation
- ✅ **Individual ticker files** for optimized ACSIL reading
- ✅ **Statistics and summaries** for analysis

## Quick Start

### Prerequisites

1. **Environment**: Ensure `.env` file has valid `SUPABASE_URL` and `SUPABASE_KEY`
2. **Database**: Confluence system database with zone data
3. **Dependencies**: Install requirements

```bash
pip install -r requirements.txt
```

### Usage Examples

#### Interactive Mode (Recommended for first use)
```bash
python -m sierra_chart.main
```

#### Command Line Examples
```bash
# Get today's zones for all tickers
python -m sierra_chart.main --today

# Get yesterday's zones
python -m sierra_chart.main --yesterday

# Get specific date
python -m sierra_chart.main --date 2025-08-28

# Get specific tickers for date
python -m sierra_chart.main --date 2025-08-28 --tickers TSLA,AAPL,NVDA

# Filter by minimum confluence score
python -m sierra_chart.main --yesterday --min-score 5.0 --tickers TSLA
```

## Output Files

The system creates several files in `C:/SierraChart/Data/Zones/`:

### Main Files
- **`confluence_zones.json`** - Master file with all zone data
- **`zones_summary.json`** - Statistics and overview
- **`confluence_zones.h`** - C++ header for ACSIL development

### Individual Ticker Files
- **`TICKER_zones.json`** - Optimized data for each ticker (e.g., `TSLA_zones.json`)

## File Formats

### Individual Ticker File Format
```json
{
  "metadata": {
    "symbol": "TSLA",
    "trade_date": "2025-08-28",
    "zone_count": 6
  },
  "zones": [
    {
      "high": 350.22,
      "low": 349.86,
      "center": 350.04,
      "level": "L3",
      "score": 7.2,
      "source_count": 4,
      "color_intensity": 0.8,
      "zone_id": 1,
      "color_rgb": {"r": 0, "g": 160, "b": 0}
    }
  ]
}
```

## ACSIL Integration

The generated files are designed for easy ACSIL consumption:

```cpp
// Example ACSIL code to read zone data
#include "confluence_zones.h"

// In your study function:
SCString ZoneFile = SCString().Format("%s\\\\%s_zones.json", 
    sc.DataFilesFolder().GetChars(), sc.GetChartSymbol(sc.ChartNumber).GetChars());

// Parse JSON and draw zones
// (Full ACSIL implementation available in documentation)
```

## Configuration

Modify `config.py` to customize:

```python
# Sierra Chart settings
SIERRA_CHART_PATH: str = "C:/SierraChart/Data/Zones"
OUTPUT_FILENAME: str = "confluence_zones.json"

# Zone level colors
LEVEL_COLORS = {
    'L5': {'r': 255, 'g': 0, 'b': 0},      # Red
    'L4': {'r': 255, 'g': 128, 'b': 0},    # Orange  
    'L3': {'r': 0, 'g': 200, 'b': 0},      # Green
    'L2': {'r': 0, 'g': 128, 'b': 255},    # Blue
    'L1': {'r': 128, 'g': 128, 'b': 128}   # Gray
}
```

## Troubleshooting

### Common Issues

**"No zone data available in database"**
- Run confluence analysis first with `--save-db` flag
- Verify database connection in `.env` file

**"Failed to connect to Supabase database"**
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Verify internet connection

**"No zones found for specified criteria"**
- Try different date or lower minimum confluence score
- Check that confluence CLI was run with `--save-db` for that date

### Logging

Enable verbose logging:
```bash
python -m sierra_chart.main --verbose --date 2025-08-28
```

## Integration Workflow

1. **Run Confluence Analysis**:
   ```bash
   python confluence_cli.py TSLA 2025-08-28 12:30 -w 354.91 335.00 315.55 286.03 -d 365.36 340.45 334.34 319.51 --save-db
   ```

2. **Export to Sierra Chart**:
   ```bash
   python -m sierra_chart.main --date 2025-08-28 --tickers TSLA
   ```

3. **Use in Sierra Chart**:
   - Compile your ACSIL study
   - Add study to charts
   - Zones appear automatically

## Support

- Check logs for detailed error messages
- Verify database connectivity with test mode
- Ensure Sierra Chart directory is writable
- Validate date formats and ticker symbols