Main UI Structure (OverviewWidget)
The interface is organized into distinct sections within a scrollable area:
1. Session Information Frame (Top Section)
Components:

Ticker Entry: Text input for stock symbol (max 10 characters)
Live Toggle: Checkbox to indicate if session is live
Date: Date picker with calendar popup (format: yyyy-MM-dd)
Time: Time input (format: HH:mm:ss)
Action Buttons:

"Fetch Market Data" - Retrieves data from Polygon API for Metrics Frame
"Run Analysis" - Executes all calculations
"Clear All" - Resets all fields (Ctrl+Shift+C)
"Save to Supabase" - Saves session to database



2. Metrics Frame
Displays calculated ATR values and prices (all read-only):
    - Metrics should be four (4) in a row
    - Set space for 5 rows

ATR Metrics:

5-Minute ATR
15-Minute ATR
2-Hour ATR
Daily ATR

Market Structure Metrics:
Previous Day High (PDH)
Previous Day Low (PDL)
Previous Day Close (PDC)
Overnight High (ONH)
Overnight Low (ONL)


Price Metrics:

Current Price at DateTime
Open Price (if after market open)
ATR High (Current + Daily ATR)
ATR Low (Current - Daily ATR)
2x ATR High (Current + (2 * ATR))
2x ATR Low (Current - (2 * ATR))



3. Weekly Analysis Section
Data Entry Fields:

Trend Direction: Dropdown (Bull/Bear/Range) with color coding
Internal Trend: Dropdown (Bull/Bear/Range)
Position in Structure: Percentage spinner (0-100%)
EOW (End of Week) Bias: Dropdown (Bull/Bear/Range)
Weekly Levels: 4 price inputs (WL1-WL4)

4. Daily Analysis Section
Data Entry Fields:

Trend Direction: Dropdown (Bull/Bear/Range)
Internal Trend: Dropdown (Bull/Bear/Range)
Position in Structure: Percentage spinner (0-100%)
EOD (End of Day) Bias: Dropdown (Bull/Bear/Range)
Six Price Levels: 4 inputs (DL1-DL4)

5. M15 Zone Data Results Table
6-row table with columns:

Zone: Numbers 1-6 with color coding
Date: MM-DD-YY format
Time (UTC): HH:MM format
Level: Mid-price of candle
Zone High: Candle high
Zone Low: Candle low

6. M15 Zones Confluence Ranking Table
Visual table showing confluence analysis:

Columns:

Zone number and price range
Direction relative to current price (↑/↓/←→)
Confluence indicators (checkmarks) for:

HVN 7D, 14D, 30D
Camarilla Monthly, Weekly, Daily
Weekly ATR Zones
Daily ATR Zones
1x ATR Zone
2x ATR Zone
PDH
PDL
PDC
ONH
ONL


Score and Level designation (L1-L5)



7. Calculations Display Section
Three rows of calculation results:
Row 1 - HVN (High Volume Nodes):

7-Day HVN: Volume profile analysis
14-Day HVN: Volume profile analysis
30-Day HVN: Volume profile analysis

Row 2 - Camarilla Pivots:

Monthly Cam Pivots: Support/resistance levels
Weekly Cam Pivots: Support/resistance levels
Daily Cam Pivots: Support/resistance levels

Row 3 - Zone Calculations:

Weekly Zones (2Hr ATR): Zones from WL1-WL4 ± 2-hour ATR
Daily Zones (15min ATR): Zones from DL1-DL6 ± 15-min ATR
ATR Zones (5min ATR): Dynamic zones based on ATR calculations

Data Flow

Manual Entry: User inputs ticker, date/time, weekly/daily analysis data
Market Data Fetch: Fetches real-time/historical data from Polygon API
Analysis Execution: Calculates Fractal Engine, HVN, Camarilla Pivots, Zones, and Confluence Scores
Results Display: Populates calculation text areas and confluence table
Database Save: Stores complete session data to Supabase

Key Features

Dark Theme: Professional grey-scale interface with color accents
Real-time Validation: Date/time format checking
Keyboard Shortcuts: Ctrl+Q (Query Data), Ctrl+Shift+C (Clear All)
Color Coding: Zones use distinct colors, trends show Bull (teal), Bear (red), Range (orange)
Confluence Visualization: Checkmarks show which analysis methods support each zone
Placeholder Text: Guides users on expected formats and pending calculations

The interface is designed for pre-market trading analysis, combining manual technical analysis inputs with automated calculations to identify high-probability trading zones through confluence of multiple indicators.