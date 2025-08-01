Purpose:
The purpose of this document is to outline the framework of the required PyQT6 tool that will need to be developed for efficient data entry and storage in the Supabase database systen which will be queried during confluence calculattions. Sections 1, 2, 3, and 4 will be manual entry.

Required Field:
1. Overview: (Manual)
    - Ticker (Text)
    - Date (Date)
    - Ticker ID (prop("Ticker") + "." + formatDate(prop("Date"), "MMDDYY"))
    - Live (Boolean)
    - Historical Date (Date)
    - Historical Time (Time)
    - Run Analysis (Button)
2. Weekly Data (Manual)
    a. Trend Direction (Bull, Bear, Range)
    b. Internal Trend Direction (Bull, Bear, Range)
    c. Position in Structure (% Location in Current Structure)
    d. End of Week Bias (Bull, Bear, Range)
    e. Notes (Text)
3. Daily Data (Manual)
    a. Trend Direction (Bull, Bear, Range)
    b. Internal Trend Direction (Bull, Bear, Range)
    c. Position in Structure (% Location in Current Structure)
    d. End of Day Bias (Bull, Bear, Range)
    e. Six (6) Siginficant Price Levels (Three (3) Above and Three (3) Below)
    e. Notes (Text)
4. M15 Market Structure Levels (Manual)
    a. Six (6) Significant Price Levels (Three (3) Above and Three (3) Below)
        -  For Each Price Level
            - Line Price (Decimal - 2)
            - Candle Datetime #Datetime for the M15 candle that created the zone. This will be used by the calculation later on to build zones from the candle high / low 
            - Candle High (Decimal - 2) # Manual Entry - will be deprecated later on once calculation is built
            - Candle Low (Decimal - 2) # Manual Entry - will be deprecated later on oncer calculation is built
5. Daily Metrics
    Pre-Market Price (Decimal -2)
    5-Minute ATR (Previous RTH from 13:30 to 20:00 UTC)
    10 Minute ATR (Previous RTH from 13:30 to 20:00 UTC)
    15-Minute ATR (Previous RTH from 13:30 to 20:00 UTC)
    Daily ATR (Triling 14 Days Period)
    ATR High - Pre-Market Price + Daily ATR
    ATR Low - Pre-Market Price - Daily ATR
5. HVN Zones (Calculated)
    a. 7-Day Analysis
        - Top 10 levels calculated and ranked via total volume within the cluster
        - Price Centroid (Decimal - 2)
        - Zone High (Decimal -2)
        - Zone Low (Decimal -2)
        - Within Daily ATR High and Daily ATR Low (Boolean)
    b.   14-Day Analysis
        - Top 10 levels calculated and ranked via total volume within the cluster
        - Price Centroid (Decimal - 2)
        - Zone High (Decimal -2)
        - Zone Low (Decimal -2)
        - Within Daily ATR High and Daily ATR Low (Boolean)
    c.   30-Day Analysis
        - Top 10 levels calculated and ranked via total volume within the cluster
        - Price Centroid (Decimal - 2)
        - Zone High (Decimal -2)
        - Zone Low (Decimal -2)
        - Within Daily ATR High and Daily ATR Low (Boolean)
6. Monthly Camariilla Pivots (Calculated)
    - MR6 (Decimal - 2)
    - MR4 (Decimal - 2)
    - MR3 (Decimal - 2)
    - MS3 (Decimal - 2)
    - MS4 (Decimal - 2)
    - MS6 (Decimal - 2)
    - Within Daily ATR High and Daily ATR Low (Boolean)
7. Weekly Camariilla Pivots (Calculated)
    - WR6 (Decimal - 2)
    - WR4 (Decimal - 2)
    - WR3 (Decimal - 2)
    - WS3 (Decimal - 2)
    - WS4 (Decimal - 2)
    - WS6 (Decimal - 2)
    - Within Daily ATR High and Daily ATR Low (Boolean)
8. Weekly Camariilla Pivots (Calculated)
    - R6 (Decimal - 2)
    - R4 (Decimal - 2)
    - R3 (Decimal - 2)
    - S3 (Decimal - 2)
    - S4 (Decimal - 2)
    - S6 (Decimal - 2)
    - Within Daily ATR High and Daily ATR Low (Boolean)
9. Previous Period Levels (Calculated)
    - ON High (Decimal - 2)
    - ON Low (Decimal - 2)
    - PD High (Decimal - 2)
    - PD Low (Decimal - 2)



