"""
Ticker list management for various markets and indices.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import warnings
import json
from pathlib import Path

from ..config import config

class TickerList(Enum):
    """Available ticker lists."""
    SP500 = "sp500"
    NASDAQ100 = "nasdaq100"
    RUSSELL2000 = "russell2000"
    DOW30 = "dow30"

class TickerManager:
    """Manages ticker lists for various indices."""
    
    def __init__(self):
        self.data_dir = config.BASE_DIR / "data" / "ticker_lists"
        self.data_dir.mkdir(exist_ok=True)
        self._ticker_data = self._load_ticker_data()
    
    def _load_ticker_data(self) -> Dict:
        """Load ticker data from file."""
        data_file = self.data_dir / "tickers.json"
        
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        else:
            # Initialize with default S&P 500 list
            return {
                "sp500": {
                    "last_updated": "2025-01-26",
                    "tickers": self._get_default_sp500_tickers()
                }
            }
    
    def get_tickers(self, ticker_list: TickerList, check_staleness: bool = True) -> List[str]:
        """Get tickers for specified list."""
        list_name = ticker_list.value
        
        if list_name not in self._ticker_data:
            raise ValueError(f"Ticker list '{list_name}' not found")
        
        data = self._ticker_data[list_name]
        
        if check_staleness:
            self._check_staleness(list_name, data['last_updated'])
        
        return data['tickers'].copy()
    
    def update_tickers(self, ticker_list: TickerList, tickers: List[str]):
        """Update ticker list."""
        list_name = ticker_list.value
        
        self._ticker_data[list_name] = {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "tickers": sorted(tickers)
        }
        
        # Save to file
        self._save_ticker_data()
    
    def _save_ticker_data(self):
        """Save ticker data to file."""
        data_file = self.data_dir / "tickers.json"
        with open(data_file, 'w') as f:
            json.dump(self._ticker_data, f, indent=2)
    
    def _check_staleness(self, list_name: str, last_updated: str):
        """Check if ticker list needs updating."""
        last_update = datetime.strptime(last_updated, "%Y-%m-%d")
        days_since_update = (datetime.now() - last_update).days
        
        if days_since_update > config.UPDATE_FREQUENCY_DAYS:
            warnings.warn(
                f"\n{'='*60}\n"
                f"WARNING: {list_name.upper()} list is {days_since_update} days old!\n"
                f"Last updated: {last_updated}\n"
                f"Please run: python scripts/update_tickers.py --list {list_name}\n"
                f"{'='*60}\n",
                UserWarning,
                stacklevel=3
            )
    
    def verify_ticker(self, ticker: str, ticker_list: TickerList) -> bool:
        """Check if a ticker is in the specified list."""
        tickers = self.get_tickers(ticker_list, check_staleness=False)
        return ticker.upper() in tickers
    
    def _get_default_sp500_tickers(self) -> List[str]:
        """Get default S&P 500 tickers."""
        # Your existing S&P 500 list
        return [
            'A', 'AAL', 'AAP', 'AAPL', 'ABBV', 'ABC', 'ABMD', 'ABT', 'ACGL', 'ACN',
            'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AEE', 'AEP', 'AES', 'AFL', 'AIG',
            'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK', 'ALL', 'ALLE', 'AMAT', 'AMCR',
            'AMD', 'AME', 'AMGN', 'AMP', 'AMT', 'AMTM', 'AMZN', 'ANET', 'ANSS', 'AON',
            'AOS', 'APA', 'APD', 'APH', 'APO', 'APTV', 'ARE', 'ATO', 'AVB', 'AVGO',
            'AVY', 'AWK', 'AXON', 'AXP', 'AZO', 'BA', 'BAC', 'BALL', 'BAX', 'BBWI',
            'BBY', 'BDX', 'BEN', 'BF-B', 'BG', 'BIIB', 'BIO', 'BK', 'BKNG', 'BKR',
            'BLDR', 'BLK', 'BMY', 'BR', 'BRK-B', 'BRO', 'BSX', 'BWA', 'BX', 'BXP',
            'C', 'CAG', 'CAH', 'CARR', 'CAT', 'CB', 'CBOE', 'CBRE', 'CCI', 'CCL',
            'CDAY', 'CDNS', 'CDW', 'CE', 'CEG', 'CF', 'CFG', 'CHD', 'CHRW', 'CHTR',
            'CI', 'CINF', 'CL', 'CLX', 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS',
            'CNC', 'CNP', 'COF', 'COO', 'COP', 'COR', 'COST', 'CPAY', 'CPB', 'CPRT',
            'CPT', 'CRL', 'CRM', 'CRWD', 'CSCO', 'CSGP', 'CSX', 'CTAS', 'CTLT', 'CTRA',
            'CTSH', 'CTVA', 'CVS', 'CVX', 'CZR', 'D', 'DAL', 'DD', 'DE', 'DECK',
            'DFS', 'DG', 'DGX', 'DHI', 'DHR', 'DIS', 'DISH', 'DLR', 'DLTR', 'DOC',
            'DOV', 'DOW', 'DPZ', 'DRI', 'DTE', 'DUK', 'DVA', 'DVN', 'DXCM', 'EA',
            'EBAY', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL', 'ELV', 'EMN', 'EMR',
            'ENPH', 'EOG', 'EPAM', 'EQIX', 'EQR', 'EQT', 'ERIE', 'ES', 'ESS', 'ETN',
            'ETR', 'ETSY', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'F', 'FANG',
            'FAST', 'FCX', 'FDS', 'FDX', 'FE', 'FFIV', 'FI', 'FICO', 'FIS', 'FITB',
            'FLT', 'FMC', 'FOX', 'FOXA', 'FRT', 'FSLR', 'FTNT', 'FTV', 'GD', 'GDDY',
            'GE', 'GEHC', 'GEN', 'GEV', 'GILD', 'GIS', 'GL', 'GLW', 'GM', 'GNRC',
            'GOOG', 'GOOGL', 'GPC', 'GPN', 'GRMN', 'GS', 'GWW', 'HAL', 'HAS', 'HBAN',
            'HCA', 'HD', 'HES', 'HIG', 'HII', 'HLT', 'HOLX', 'HON', 'HPE', 'HPQ',
            'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HUM', 'HWM', 'IBM', 'ICE', 'IDXX',
            'IEX', 'IFF', 'ILMN', 'INCY', 'INTC', 'INTU', 'INVH', 'IP', 'IPG', 'IQV',
            'IR', 'IRM', 'ISRG', 'IT', 'ITW', 'IVZ', 'J', 'JBHT', 'JBL', 'JCI',
            'JKHY', 'JNJ', 'JNPR', 'JPM', 'K', 'KDP', 'KEY', 'KEYS', 'KHC', 'KIM',
            'KKR', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 'KR', 'KVUE', 'L', 'LDOS',
            'LEN', 'LH', 'LHX', 'LII', 'LIN', 'LKQ', 'LLY', 'LMT', 'LNT', 'LOW',
            'LRCX', 'LULU', 'LUV', 'LVS', 'LW', 'LYB', 'LYV', 'MA', 'MAA', 'MAR',
            'MAS', 'MBC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'MDT', 'MET', 'META',
            'MGM', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MMM', 'MNST', 'MO', 'MOH',
            'MOS', 'MPC', 'MPWR', 'MRK', 'MRNA', 'MRO', 'MS', 'MSCI', 'MSFT', 'MSI',
            'MTB', 'MTCH', 'MTD', 'MU', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NEM', 'NFLX',
            'NI', 'NKE', 'NOC', 'NOW', 'NRG', 'NSC', 'NTAP', 'NTRS', 'NUE', 'NVDA',
            'NVR', 'NWS', 'NWSA', 'NXPI', 'O', 'ODFL', 'OKE', 'OMC', 'ON', 'ORCL',
            'ORLY', 'OTIS', 'OXY', 'PANW', 'PARA', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEAK',
            'PEG', 'PEP', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKG', 'PLD',
            'PLTR', 'PM', 'PNC', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU',
            'PSA', 'PSX', 'PTC', 'PWR', 'PXD', 'PYPL', 'QCOM', 'QRVO', 'RCL', 'REG',
            'REGN', 'RF', 'RHI', 'RJF', 'RL', 'RMD', 'ROK', 'ROL', 'ROP', 'ROST',
            'RSG', 'RTX', 'RVTY', 'SBAC', 'SBUX', 'SCHW', 'SHW', 'SJM', 'SLB', 'SMCI',
            'SNA', 'SNPS', 'SO', 'SOLV', 'SPG', 'SPGI', 'SRE', 'STE', 'STLD', 'STT',
            'STX', 'STZ', 'SWK', 'SWKS', 'SYF', 'SYK', 'SYY', 'T', 'TAP', 'TDG',
            'TDY', 'TECH', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 'TJX', 'TMO', 'TMUS',
            'TPL', 'TPR', 'TRGP', 'TRMB', 'TROW', 'TRV', 'TSCO', 'TSLA', 'TSN', 'TT',
            'TTWO', 'TXN', 'TXT', 'TYL', 'UAL', 'UBER', 'UDR', 'UHS', 'ULTA', 'UNH',
            'UNP', 'UPS', 'URI', 'USB', 'V', 'VICI', 'VLO', 'VLTO', 'VMC', 'VRSK',
            'VRSN', 'VRTX', 'VST', 'VTR', 'VTRS', 'VZ', 'WAB', 'WAT', 'WBA', 'WBD',
            'WDC', 'WDAY', 'WEC', 'WELL', 'WFC', 'WM', 'WMB', 'WMT', 'WRB', 'WRK',
            'WST', 'WTW', 'WY', 'WYNN', 'XEL', 'XOM', 'XRAY', 'XYL', 'YUM', 'ZBH',
            'ZBRA', 'ZION', 'ZTS'
        ]

# Global instance
ticker_manager = TickerManager()