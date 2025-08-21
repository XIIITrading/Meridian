Meridian Pre-Market Trading System
Overview
The Meridian pre-market system builds confluence around M15 Market Structure analysis to identify high-probability trading opportunities. This systematic approach combines multiple timeframe analysis with precise entry and exit models for intraday trading.
Core Purpose

Build confluence around M15 Market Structure system
Identify areas of interest within price action and structure on the 15-minute timeframe
Utilize Order Blocks to outline zones where significant price movements occur
Achieve favorable risk-to-reward ratios through structured zone analysis

Key Concepts
Order Blocks: Price zones where large institutional traders have placed significant buy or sell orders, typically preceding notable price movements. These zones represent high liquidity areas that can act as support or resistance levels.
M15 Timeframe Benefits:

Clean Analysis: Provides clear areas of interest while reducing noise from tick-by-tick price action
Natural Price Movement: Offers broad enough zones for natural price action while maintaining effective stop-loss levels (M15 ATR proxy)
Reduced False Signals: Enables tighter correlation to M2/M5 movements for more reliable entry confirmation


Step 1: Broader Picture Price Location
Weekly Price Analysis
Analyze the weekly timeframe to understand overall market context and identify potential obstacles to current directional movement.
Protocol - Weekly Analysis
Document the following data points:

Trend Direction: Bull, Bear, or Range
Internal Trend Direction: Bull, Bear, or Range
Position in Structure: % location within current structure
End of Week Bias: Expected directional bias
Notes: Additional observations and context

Daily Price Analysis
Protocol - Daily Analysis
Document the following data points:

Trend Direction: Bull, Bear, or Range
Internal Trend Direction: Bull, Bear, or Range
Position in Structure: % location within current structure
End of Day Bias: Expected directional bias
Six Significant Price Levels: Three above and three below current price
Notes: Additional observations and context

M15 Market Structure Levels
Six Significant Price Levels (3 Above, 3 Below)

Break of Structure (BOS)
Change of Character (CHoCH)
Order Blocks
Volume Accumulation Points
Liquidity Grabs


Step 2: Confluence Algorithm
The confluence algorithm analyzes M15 levels and zones against other technical indicators to rank probability of significance. This maintains visual simplicity while providing clarity on high-probability levels.

Note: Price action and tape reading remain the final decision factors, as historical locations provide guidance but are not foolproof.

1. High Volume Node (HVN) Zones
Analyze Volume by Price (VBP) across multiple timeframes:
Timeframes Analyzed

7-day VBP
15-day VBP
30-day VBP

Technical Process
Volume Profile Construction:

Divides price range into equal levels (default: 100)
Aggregates volume at each price level across specified timeframe
Creates histogram of volume by price

Percentile Ranking:

Assigns each price level a rank from 1-100 based on volume percentage
100 = highest volume, 1 = lowest volume

Threshold Filtering:

Identifies significant levels above 80th percentile threshold
Focuses on top 20% highest volume levels as HVN candidates

Cluster Formation:

Groups adjacent HVN levels above threshold into contiguous clusters
Calculates aggregate statistics: total volume, price range, weighted center price

2. Camarilla Pivots
Calculate and analyze Camarilla pivots across multiple timeframes:
Timeframes

Daily Camarilla Pivots
Weekly Camarilla Pivots
Monthly Camarilla Pivots

Confluence Factors
Multi-Timeframe Validation:

M15 zones aligning with pivots from multiple timeframes indicate stronger support/resistance
Different trader groups watching same levels increases significance

Institutional Significance:

Monthly and weekly levels represent longer-term institutional reference points
Higher probability of reaction due to larger position sizing

Proximity Scoring:

Calculate distance between M15 zones and pivot levels
Zones within 0.1-0.2% of multiple pivots receive higher confluence scores

Pivot Clustering:

"Super confluence" occurs when daily H3, weekly L4, and monthly pivot converge near M15 zone
Multiple mathematical models agreeing within ATR range

Dynamic Strength Assessment:

Use pivot hierarchy for weighting (H5/L5 strongest, H1/L1 weakest)
Monthly H4 alignment scores higher than daily H1 alignment

3. Prior Day Levels
Key Levels Analyzed

ON High (Overnight High)
ON Low (Overnight Low)
PD High (Previous Day High)
PD Low (Previous Day Low)
PD Open (Previous Day Open)
PD Close (Previous Day Close)


Step 3: Entry and Exit Models
Entry Models
Continuation Trades
Price continues through a level in the direction of the dominant M5 trend.
Setup Process:

Price enters M15 zone → triggers alert → trade moves to "Analyze" state
Price continues through zone and closes on opposite side in direction of M5 trend

Entry Options:

Model #1 (Required): Enter on open of next M2 candle after close outside zone
Model #2 (Optional): Enter on open of next M2 candle after Model #1 + liquidity grab confirmation

Reversal Trades
Price enters M15 zone, stalls, and reverses direction.
Setup Process:

Price enters M15 zone → triggers alert → trade moves to "Analyze" state
Price holds within zone, develops CHoCH, exits zone in same direction as entry

Entry Options:

Model #1 (Required): Enter on open of next M2 candle after closed CHoCH opposite to trend
Model #2 (Optional): Enter on open of next M2 candle after liquidity grab + PBL (Price Before Liquidity) break

Exit Models
Position Management

75% of position: Exit at 2R (2x risk)
25% of position: Exit at CHoCH on M1 timeframe


Implementation Notes

All alerts should be configured to trigger when price enters identified M15 zones
Risk management remains paramount - respect stop losses based on M15 ATR
Confluence ranking should be updated regularly as market conditions change
Document all trades for system refinement and performance analysis

This systematic approach combines multiple timeframe analysis with precise entry/exit criteria to identify high-probability trading opportunities while maintaining disciplined risk management.