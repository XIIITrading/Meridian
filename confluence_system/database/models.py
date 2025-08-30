"""
Data models matching levels_zones structure
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from decimal import Decimal

@dataclass
class ZoneConfluenceDetail:
    """Detailed confluence for a single zone"""
    zone_number: int
    confluence_sources: List[str] = field(default_factory=list)
    
    # HVN confluence flags
    has_hvn_7d: bool = False
    has_hvn_14d: bool = False
    has_hvn_30d: bool = False
    has_hvn_60d: bool = False
    
    # Camarilla confluence flags
    has_cam_daily: bool = False
    has_cam_weekly: bool = False
    has_cam_monthly: bool = False
    has_cam_h5: bool = False
    has_cam_h4: bool = False
    has_cam_h3: bool = False
    has_cam_l3: bool = False
    has_cam_l4: bool = False
    has_cam_l5: bool = False
    
    # Traditional pivot flags
    has_pivot_daily: bool = False
    has_pivot_weekly: bool = False
    
    # Key level flags
    has_pdh: bool = False  # Previous Day High
    has_pdl: bool = False  # Previous Day Low
    has_pdc: bool = False  # Previous Day Close
    has_onh: bool = False  # Overnight High
    has_onl: bool = False  # Overnight Low
    has_pwh: bool = False  # Previous Week High
    has_pwl: bool = False  # Previous Week Low
    
    # Moving average flags
    has_vwap: bool = False
    has_ema_9: bool = False
    has_ema_21: bool = False
    has_sma_50: bool = False
    has_sma_200: bool = False
    
    source_details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate zone number"""
        if not 1 <= self.zone_number <= 6:
            raise ValueError(f"Zone number must be 1-6, got {self.zone_number}")

@dataclass
class LevelsZonesRecord:
    """Record matching levels_zones table structure"""
    ticker_id: str
    ticker: str
    session_date: date
    
    # Weekly levels
    weekly_wl1: Optional[float] = None
    weekly_wl2: Optional[float] = None
    weekly_wl3: Optional[float] = None
    weekly_wl4: Optional[float] = None
    
    # Daily levels
    daily_dl1: Optional[float] = None
    daily_dl2: Optional[float] = None
    daily_dl3: Optional[float] = None
    daily_dl4: Optional[float] = None
    
    # M15 zones (up to 6)
    zones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metrics
    current_price: Optional[float] = None
    atr_daily: Optional[float] = None
    atr_15min: Optional[float] = None
    
    # Analysis results
    zones_ranked_text: Optional[str] = None
    analysis_datetime: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.ticker_id or not self.ticker:
            raise ValueError("ticker_id and ticker are required")
        
        if len(self.zones) > 6:
            raise ValueError("Maximum 6 zones allowed")

@dataclass
class ConfluenceAnalysis:
    """Enhanced confluence analysis record"""
    ticker_id: str
    ticker: str
    session_date: date
    analysis_datetime: datetime
    params: Dict[str, Any] = field(default_factory=dict)
    cli_version: str = "2.0"
    
    # Zone details
    zone_details: List[ZoneConfluenceDetail] = field(default_factory=list)
    
    def add_zone_detail(self, detail: ZoneConfluenceDetail):
        """Add a zone confluence detail"""
        # Remove existing detail for same zone if present
        self.zone_details = [zd for zd in self.zone_details if zd.zone_number != detail.zone_number]
        self.zone_details.append(detail)
        
        # Keep sorted by zone number
        self.zone_details.sort(key=lambda x: x.zone_number)
    
    def get_zone_detail(self, zone_number: int) -> Optional[ZoneConfluenceDetail]:
        """Get detail for a specific zone"""
        return next((zd for zd in self.zone_details if zd.zone_number == zone_number), None)

# Helper functions for data conversion
def cli_output_to_levels_zones_record(cli_output: Dict[str, Any]) -> LevelsZonesRecord:
    """Convert CLI output to LevelsZonesRecord"""
    analysis_dt = datetime.fromisoformat(cli_output['analysis_time'])
    session_date = analysis_dt.date()
    ticker = cli_output['symbol']
    date_str = session_date.strftime('%m%d%y')
    ticker_id = f"{ticker}.{date_str}"
    
    # Extract zones
    zones = []
    for level in cli_output['levels'][:6]:
        zones.append({
            'zone_number': level.get('zone', 0),
            'high': level['high'],
            'low': level['low'],
            'center': (level['high'] + level['low']) / 2,
            'score': level['score'],
            'confluence': level['confluence'],
            'source_count': level.get('source_count', 0)
        })
    
    return LevelsZonesRecord(
        ticker_id=ticker_id,
        ticker=ticker,
        session_date=session_date,
        weekly_wl1=cli_output['parameters']['weekly_levels'][0],
        weekly_wl2=cli_output['parameters']['weekly_levels'][1],
        weekly_wl3=cli_output['parameters']['weekly_levels'][2],
        weekly_wl4=cli_output['parameters']['weekly_levels'][3],
        daily_dl1=cli_output['parameters']['daily_levels'][0],
        daily_dl2=cli_output['parameters']['daily_levels'][1],
        daily_dl3=cli_output['parameters']['daily_levels'][2],
        daily_dl4=cli_output['parameters']['daily_levels'][3],
        zones=zones,
        current_price=cli_output['current_price'],
        atr_daily=cli_output['metrics']['atr_daily'],
        atr_15min=cli_output['metrics']['atr_15min'],
        analysis_datetime=analysis_dt
    )