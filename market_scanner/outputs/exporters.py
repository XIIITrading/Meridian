"""
Export functionality for scan results.
"""
import os
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

from ..config import config

logger = logging.getLogger(__name__)

class CSVExporter:
    """Export scan results to CSV."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, filename: Optional[str] = None) -> str:
        """Export to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_results_{timestamp}.csv"
        
        output_path = config.OUTPUT_DIR / filename
        scan_results.to_csv(output_path, index=False)
        logger.info(f"Results exported to {output_path}")
        return str(output_path)

class SupabaseExporter:
    """Export scan results to Supabase."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, scan_date: datetime) -> bool:
        """Push scan results to Supabase."""
        try:
            from supabase import create_client, Client
        except ImportError:
            logger.error("Supabase client not installed. Install with: pip install supabase")
            return False
        
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            logger.error("Supabase credentials not found in environment variables.")
            return False
        
        try:
            # Initialize Supabase client
            supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            
            # Format scan date for database
            scan_date_str = scan_date.strftime('%Y-%m-%d')
            
            # Check for existing records
            existing = supabase.table('premarket_scans').select('ticker').eq('scan_date', scan_date_str).execute()
            
            if existing.data:
                logger.info(f"Deleting {len(existing.data)} existing records for {scan_date_str}")
                supabase.table('premarket_scans').delete().eq('scan_date', scan_date_str).execute()
            
            # Prepare records
            records = []
            for _, row in scan_results.iterrows():
                record = {
                    'ticker': row['ticker'],
                    'ticker_list': row.get('ticker_list', 'sp500'),
                    'price': float(row['price']),
                    'rank': int(row['rank']),
                    'premarket_volume': int(row['premarket_volume']),
                    'avg_daily_volume': int(row['avg_daily_volume']),
                    'dollar_volume': float(row['dollar_volume']),
                    'atr': float(row['atr']),
                    'atr_percent': float(row['atr_percent']),
                    'interest_score': float(row['interest_score']),
                    'pm_vol_ratio_score': float(row['pm_vol_ratio_score']),
                    'atr_percent_score': float(row['atr_percent_score']),
                    'dollar_vol_score': float(row['dollar_vol_score']),
                    'pm_vol_abs_score': float(row['pm_vol_abs_score']),
                    'price_atr_bonus': float(row['price_atr_bonus']),
                    'scan_date': scan_date_str,
                    'scan_time': row['scan_time'].isoformat() if pd.notna(row.get('scan_time')) else None,
                    'passed_filters': True,
                    'market_session': 'pre-market'
                }
                records.append(record)
            
            # Insert in batches
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                supabase.table('premarket_scans').insert(batch).execute()
            
            logger.info(f"Successfully pushed {len(records)} records to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing to Supabase: {e}")
            return False

class MarkdownExporter:
    """Export scan results to Markdown report."""
    
    @staticmethod
    def export(scan_results: pd.DataFrame, 
              summary: dict,
              criteria: dict,
              filename: Optional[str] = None) -> str:
        """Export to Markdown file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_report_{timestamp}.md"
        
        output_path = config.OUTPUT_DIR / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Market Scanner Report - {summary.get('ticker_list', 'Unknown').upper()}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Scanner Type:** Pre-market Scanner\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Ticker List | {summary.get('ticker_list', 'Unknown').upper()} |\n")
            f.write(f"| Total Scanned | {summary.get('total_scanned', 0)} |\n")
            f.write(f"| Passed Filters | {summary.get('passed_filters', 0)} |\n")
            f.write(f"| Pass Rate | {summary.get('pass_rate', '0.0%')} |\n")
            if summary.get('avg_interest_score'):
                f.write(f"| Avg Interest Score | {summary.get('avg_interest_score'):.2f} |\n")
            f.write("\n")
            
            # Filter Criteria
            f.write("## Filter Criteria\n\n")
            f.write("| Criterion | Value |\n")
            f.write("|-----------|-------|\n")
            for key, value in criteria.items():
                f.write(f"| {key} | {value} |\n")
            f.write("\n")
            
            # Results
            if scan_results.empty:
                f.write("## Results\n\n")
                f.write("❌ **No stocks passed all filters**\n")
            else:
                f.write(f"## Top {min(50, len(scan_results))} Stocks by Interest Score\n\n")
                
                # Results table
                f.write("| Rank | Ticker | Price | Score | PM Volume | PM % | ATR % |\n")
                f.write("|:----:|:------:|------:|------:|----------:|-----:|------:|\n")
                
                for _, row in scan_results.head(50).iterrows():
                    pm_vol_pct = (row['premarket_volume'] / row['avg_daily_volume'] * 100)
                    
                    # Highlight top 3
                    ticker = row['ticker']
                    if row['rank'] == 1:
                        ticker = f"🥇 **{ticker}**"
                    elif row['rank'] == 2:
                        ticker = f"🥈 **{ticker}**"
                    elif row['rank'] == 3:
                        ticker = f"🥉 **{ticker}**"
                    
                    f.write(f"| {row['rank']} | {ticker} | ${row['price']:.2f} | ")
                    f.write(f"{row['interest_score']:.1f} | {row['premarket_volume']:,.0f} | ")
                    f.write(f"{pm_vol_pct:.2f}% | {row['atr_percent']:.2f}% |\n")
        
        logger.info(f"Report exported to {output_path}")
        return str(output_path)