# mappings/daily_pivots_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'S6': 's6',
        'S4': 's4',
        'S3': 's3',
        'R3': 'r3', 
        'R4': 'r4',
        'R6': 'r6',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        's6': 'S6',
        's4': 'S4',
        's3': 'S3',
        'r3': 'R3',
        'r4': 'R4',
        'r6': 'R6',
        'id': 'Supabase ID'
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',
        'Date': 'date',
        'Ticker ID': 'rich_text',
        'S6': 'number',
        'S4': 'number',
        'S3': 'number',
        'R3': 'number',
        'R4': 'number',
        'R6': 'number',
        'Supabase ID': 'number'
    }
}