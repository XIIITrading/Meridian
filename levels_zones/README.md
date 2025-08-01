# Meridian Pre-Market Trading System

A PyQt6 desktop application for pre-market trading analysis that combines manual data entry with automated confluence calculations using Polygon.io market data and Supabase for storage.

## Features

- Manual Data Entry: Weekly/Daily trend analysis, M15 market structure levels
- Automated Calculations: HVN zones, Camarilla pivots, ATR calculations
- Confluence Algorithm: Ranks trading levels by probability of significance
- Data Persistence: Supabase integration for storing and retrieving analysis
- Market Data Integration: Polygon.io Max tier for real-time and historical data

## Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and add your API credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Project Status

Currently in Phase 1: Project Foundation