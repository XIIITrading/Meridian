# mappings/monthly_pivots_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'MS6': 'ms6',
        'MS4': 'ms4',
        'MS3': 'ms3',
        'MR3': 'mr3',
        'MR4': 'mr4',
        'MR6': 'mr6',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'ms6': 'MS6',
        'ms4': 'MS4',
        'ms3': 'MS3',
        'mr3': 'MR3',
        'mr4': 'MR4',
        'mr6': 'MR6',
        'id': 'Supabase ID'  # Maps the Supabase ID to your tracking field
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',  # This ensures Ticker is treated as the title field
        'Date': 'date',
        'Ticker ID': 'rich_text',  # Formula field in Notion, but stored as text
        'MS6': 'number',
        'MS4': 'number',
        'MS3': 'number',
        'MR3': 'number',
        'MR4': 'number',
        'MR6': 'number',
        'Supabase ID': 'number'
    }
}