# mappings/h1_zones_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'H1Z1L': 'h1z1l',
        'H1Z1H': 'h1z1h',
        'H1Z2L': 'h1z2l',
        'H1Z2H': 'h1z2h',
        'H1Z3L': 'h1z3l',
        'H1Z3H': 'h1z3h',
        'H1Z4L': 'h1z4l',
        'H1Z4H': 'h1z4h',
        'H1Z5L': 'h1z5l',
        'H1Z5H': 'h1z5h',
        'H1Z6L': 'h1z6l',
        'H1Z6H': 'h1z6h',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'h1z1l': 'H1Z1L',
        'h1z1h': 'H1Z1H',
        'h1z2l': 'H1Z2L',
        'h1z2h': 'H1Z2H',
        'h1z3l': 'H1Z3L',
        'h1z3h': 'H1Z3H',
        'h1z4l': 'H1Z4L',
        'h1z4h': 'H1Z4H',
        'h1z5l': 'H1Z5L',
        'h1z5h': 'H1Z5H',
        'h1z6l': 'H1Z6L',
        'h1z6h': 'H1Z6H',
        'id': 'Supabase ID'  # Maps the Supabase ID to your tracking field
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',  # This ensures Ticker is treated as the title field
        'Date': 'date',
        'Ticker ID': 'rich_text',  # Formula field in Notion, but stored as text
        'H1Z1L': 'number',
        'H1Z1H': 'number',
        'H1Z2L': 'number',
        'H1Z2H': 'number',
        'H1Z3L': 'number',
        'H1Z3H': 'number',
        'H1Z4L': 'number',
        'H1Z4H': 'number',
        'H1Z5L': 'number',
        'H1Z5H': 'number',
        'H1Z6L': 'number',
        'H1Z6H': 'number',
        'Supabase ID': 'number'
    }
}