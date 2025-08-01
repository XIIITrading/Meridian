# mappings/pivot_candles_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'Pivot Time': 'pivot_time',
        'Time Frame': 'time_frame',
        'Pivot Type': 'pivot_type',
        'Candle High': 'candle_high',
        'Candle Low': 'candle_low',
        'Volume': 'volume',  
        'Candle Type': 'candle_type',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'pivot_time': 'Pivot Time',
        'time_frame': 'Time Frame',
        'pivot_type': 'Pivot Type',
        'candle_high': 'Candle High',
        'candle_low': 'Candle Low',
        'volume': 'Volume',  
        'candle_type': 'Candle Type',
        'id': 'Supabase ID'
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',
        'Date': 'date',
        'Ticker ID': 'rich_text',
        'Pivot Time': 'date',
        'Time Frame': 'select',
        'Pivot Type': 'select',
        'Candle High': 'number',
        'Candle Low': 'number',
        'Volume': 'checkbox', 
        'Candle Type': 'select',
        'Supabase ID': 'number'
    }
}