# Monte Carlo Backtesting Engine - Confluence System Integration

Enhanced Monte Carlo backtesting engine integrated with the Confluence System database and analysis tools.

## Features

### Core Capabilities
- **Single Day Analysis**: Run Monte Carlo simulation for individual trading sessions
- **Batch Processing**: Analyze multiple trading sessions in sequence
- **Real-time Data**: Fetches minute-by-minute market data via Polygon API
- **Database Integration**: Seamlessly works with confluence_system database

### Enhanced Confluence Integration
- **Confluence-Aware Zones**: Uses zones with confluence scores, levels, and source data
- **Weighted Analysis**: Applies confluence multipliers to optimize trade selection
- **Advanced Metrics**: Tracks confluence performance across all analysis dimensions
- **Smart Filtering**: Prioritizes high-confluence zones for better edge

### Advanced Analytics
- **R-Multiple Analysis**: Complete optimal R distribution analysis
- **Confluence Performance**: Detailed breakdown by confluence levels and sources
- **Zone Performance**: Enhanced zone analysis with confluence context
- **Time Pattern Analysis**: Intraday performance patterns with confluence data
- **Exit Reason Analysis**: Why trades exit and how confluence affects outcomes

## Quick Start

### 1. Test Your Setup
```bash
cd confluence_system/backtest_engine/monte-carlo
python test_monte_carlo.py
```

### 2. List Available Sessions
```bash
python main.py --list
python main.py --list AAPL  # Filter by ticker
```

### 3. Run Single Day Analysis
```bash
python main.py AAPL.082524
```

### 4. Run Batch Analysis
```bash
python main.py --batch AAPL 2024-08-01 2024-08-31
```

### 5. Analyze Existing Results
```bash
python main.py --analyze BATCH_ID
```

## CLI Usage

### Single Day Analysis
```bash
python main.py TICKER.MMDDYY [options]

Options:
  --no-save         Skip saving to database
  --no-analyze      Skip detailed analysis
  --export-csv      Export results to CSV
```

### Batch Analysis
```bash
python main.py --batch TICKER START_DATE END_DATE

Example:
python main.py --batch TSLA 2024-08-01 2024-08-31
```

### List Sessions
```bash
python main.py --list [TICKER] [--limit N]

Examples:
python main.py --list                    # List all sessions
python main.py --list NVDA               # List NVDA sessions
python main.py --list --limit 50         # List 50 most recent
```

### Analyze Existing Batch
```bash
python main.py --analyze BATCH_ID [--export-csv]

Example:
python main.py --analyze abc123def456 --export-csv
```

### Show Configuration
```bash
python main.py --config
```

## Integration with Confluence System

### Prerequisites
1. **Database Setup**: Run confluence_system database setup
2. **Confluence Data**: Run confluence CLI with `--save-db` to populate data
3. **API Keys**: Ensure POLYGON_API_KEY and Supabase credentials are configured

### Data Flow
```
Confluence CLI → Supabase (levels_zones) → Monte Carlo Engine → Enhanced Results
```

### Enhanced Zone Data
Each zone includes:
- **Basic Data**: High, low, center prices
- **Confluence Score**: Numerical confluence rating
- **Confluence Level**: L1-L5 classification  
- **Confluence Sources**: List of contributing factors
- **Expected Edge**: Calculated trading edge
- **Risk Adjustment**: Risk-adjusted scoring

## Output and Results

### Database Storage
- **monte_carlo_batches**: Batch metadata with confluence info
- **monte_carlo_trades**: Individual trade results with enhanced confluence data

### Enhanced Trade Records Include
- Traditional metrics (entry, exit, R-multiples)
- Confluence data (level, score, sources)
- Weighted optimal R calculations
- Confluence flags and detailed source breakdown

### Analysis Reports
- **Basic Statistics**: Win rates, R-multiples with confluence context
- **Confluence Analysis**: Performance by confluence levels and sources
- **Zone Performance**: Zone-by-zone breakdown with confluence metrics
- **Time Patterns**: Intraday performance with confluence correlation
- **Recommendations**: Data-driven insights for improvement

## Examples

### Example 1: Quick Analysis
```bash
# List available data
python main.py --list

# Run analysis on most recent session
python main.py NVDA.082524

# Results show:
# - Total trades generated
# - Win rates and R-multiples
# - Confluence level breakdown
# - Zone performance with confluence scores
# - Recommendations based on confluence data
```

### Example 2: Batch Processing
```bash
# Process all August TSLA sessions
python main.py --batch TSLA 2024-08-01 2024-08-31

# Results in:
# - Multiple batch IDs created
# - Aggregate performance metrics
# - Cross-session confluence patterns
# - Optimal confluence combinations identified
```

### Example 3: Deep Analysis
```bash
# Run with all options
python main.py AAPL.082524 --export-csv

# Then analyze the batch
python main.py --analyze abc123def456 --export-csv

# Outputs:
# - Enhanced trade CSV with all confluence data
# - Analysis summary CSV with metrics breakdown
# - Confluence performance insights
# - Actionable recommendations
```

## Configuration

### Environment Variables Required
```env
POLYGON_API_KEY=your_polygon_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### Trading Parameters (config.py)
- **Trading Hours**: 13:30-19:30 UTC (9:30 AM - 3:30 PM ET)
- **Position Close**: 19:50 UTC (3:50 PM ET)
- **Stop Offset**: 0.05 (beyond zone boundary)
- **Zone Size Limits**: 0.10 - 5.00 price range

### Confluence Weights
- **L1 (Minimal)**: 1.0x multiplier
- **L2 (Low)**: 1.2x multiplier
- **L3 (Medium)**: 1.5x multiplier  
- **L4 (High)**: 2.0x multiplier
- **L5 (Highest)**: 2.5x multiplier

## Troubleshooting

### Common Issues

**"No zones found for TICKER.MMDDYY"**
- Run confluence CLI with `--save-db` first
- Verify ticker ID format (TICKER.MMDDYY)
- Check that confluence analysis generated valid zones

**"Database service not enabled"**
- Check .env file has correct Supabase credentials
- Run `python test_monte_carlo.py` to verify setup
- Ensure confluence_system database module is working

**"No minute data available"**
- Verify Polygon API key is valid and has minute data access
- Check that trading date is a valid market day
- Ensure Polygon Max tier subscription for minute data

**Performance Issues**
- Large datasets may take time to process
- Use `--no-analyze` for faster batch processing
- Consider date range limits for batch analysis

### Getting Help

1. **Test Setup**: Run `python test_monte_carlo.py`
2. **Check Config**: Run `python main.py --config` 
3. **Verify Data**: Run `python main.py --list`
4. **Check Logs**: Monitor console output for detailed error messages

## Advanced Usage

### Custom Analysis
```python
from main import MonteCarloAPI

api = MonteCarloAPI()
batch_id = api.run_single_day_analysis('AAPL.082524')

# Custom analysis
from analyzer import MonteCarloAnalyzer
analyzer = MonteCarloAnalyzer()
results = analyzer.analyze_batch(batch_id)

# Access confluence-specific results
confluence_performance = results['confluence_analysis']
source_analysis = results['confluence_source_analysis']
```

### Integration with Other Tools
The Monte Carlo engine is designed to integrate with:
- Confluence CLI for data preparation
- Database interactive tools for result exploration
- Custom analysis scripts using the same database
- Export capabilities for external analysis tools

---

**Ready to run Monte Carlo analysis with confluence-enhanced edge detection!** 🎯