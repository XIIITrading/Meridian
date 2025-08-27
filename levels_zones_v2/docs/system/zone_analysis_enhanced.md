What Currently Exists:

M15 Zone Entry & Confluence Analysis:

Manual M15 zone entry through M15ZoneTable (zones 1-6)
Confluence scoring via ConfluenceEngine
Display of confluence results in M15ConfluenceWidget
Zones get confluence levels (L1-L5) based on score thresholds


Zone-based Confluence:

Zones are compared against HVN, Camarilla, Weekly/Daily zones, etc.
Final ranking shows which zones have highest confluence scores



What Step 5 Requires (NOT Implemented):

Fractal Detection Algorithm:

No fractal_high/fractal_low detection exists
No active_candle identification logic


Overlap Calculation:

No algorithm to calculate percentage overlap between fractals and zones
No 25% overlap threshold checking


Confluence Inheritance:

No logic for fractals to "inherit" confluence levels from overlapping zones
Current system only scores manually entered zones



Missing Components for Step 5:
python# These algorithms need to be created:

class FractalDetector:
    def detect_fractals(self, price_data) -> List[Fractal]:
        # Identify fractal_high and fractal_low points
        pass
    
    def identify_active_candles(self, fractals) -> List[ActiveCandle]:
        # Determine which fractals are "active"
        pass

class ZoneFractalAnalyzer:
    def calculate_overlap(self, fractal, zone) -> float:
        # Calculate percentage overlap between fractal and zone
        pass
    
    def inherit_confluence(self, fractals, high_confluence_zones):
        # Apply 25% overlap rule and inheritance logic
        pass
Recommendation: Step 5 would be a significant new feature requiring fractal detection, overlap mathematics, and inheritance logic - none of which currently exist in your tooling.