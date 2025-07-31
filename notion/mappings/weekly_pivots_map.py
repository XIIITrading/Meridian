# mappings/weekly_pivots_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'WS6': 'ws6',
        'WS4': 'ws4',
        'WS3': 'ws3',
        'WR3': 'wr3',
        'WR4': 'wr4',
        'WR6': 'wr6',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'ws6': 'WS6',
        'ws4': 'WS4',
        'ws3': 'WS3',
        'wr3': 'WR3',
        'wr4': 'WR4',
        'wr6': 'WR6',
        'id': 'Supabase ID'  # Maps the Supabase ID to your tracking field
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',  # This ensures Ticker is treated as the title field
        'Date': 'date',
        'Ticker ID': 'rich_text',  # Formula field in Notion, but stored as text
        'WS6': 'number',
        'WS4': 'number',
        'WS3': 'number',
        'WR3': 'number',
        'WR4': 'number',
        'WR6': 'number',
        'Supabase ID': 'number'
    }
}