# mappings/daily_levels_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'D1': 'd1',
        'D2': 'd2',
        'D3': 'd3',
        'D4': 'd4',
        'D5': 'd5',
        'D6': 'd6',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'd1': 'D1',
        'd2': 'D2',
        'd3': 'D3',
        'd4': 'D4',
        'd5': 'D5',
        'd6': 'D6',
        'id': 'Supabase ID'  # Maps the Supabase ID to your tracking field
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',  # This ensures Ticker is treated as the title field
        'Date': 'date',
        'Ticker ID': 'rich_text',  # Formula field in Notion, but stored as text
        'D1': 'number',
        'D2': 'number',
        'D3': 'number',
        'D4': 'number',
        'D5': 'number',
        'D6': 'number',
        'Supabase ID': 'number'
    }
}