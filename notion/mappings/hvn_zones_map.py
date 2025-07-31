# mappings/hvn_zones_map.py

FIELD_MAPPING = {
    'notion_to_supabase': {
        'Ticker': 'ticker',
        'Date': 'date',
        'Ticker ID': 'ticker_id',
        'HVN1L': 'hvn1l',
        'HVN1H': 'hvn1h',
        'HVN2L': 'hvn2l',
        'HVN2H': 'hvn2h',
        'HVN3L': 'hvn3l',
        'HVN3H': 'hvn3h',
        'HVN4L': 'hvn4l',
        'HVN4H': 'hvn4h',
        'HVN5L': 'hvn5l',
        'HVN5H': 'hvn5h',
        'HVN6L': 'hvn6l',
        'HVN6H': 'hvn6h',
        'Supabase ID': 'supabase_id'
    },
    'supabase_to_notion': {
        'ticker': 'Ticker',
        'date': 'Date',
        'ticker_id': 'Ticker ID',
        'hvn1l': 'HVN1L',
        'hvn1h': 'HVN1H',
        'hvn2l': 'HVN2L',
        'hvn2h': 'HVN2H',
        'hvn3l': 'HVN3L',
        'hvn3h': 'HVN3H',
        'hvn4l': 'HVN4L',
        'hvn4h': 'HVN4H',
        'hvn5l': 'HVN5L',
        'hvn5h': 'HVN5H',
        'hvn6l': 'HVN6L',
        'hvn6h': 'HVN6H',
        'id': 'Supabase ID'  # Maps the Supabase ID to your tracking field
    },
    'id_field': 'Supabase ID',
    'field_types': {
        'Ticker': 'title',  # This ensures Ticker is treated as the title field
        'Date': 'date',
        'Ticker ID': 'rich_text',  # Formula field in Notion, but stored as text
        'HVN1L': 'number',
        'HVN1H': 'number',
        'HVN2L': 'number',
        'HVN2H': 'number',
        'HVN3L': 'number',
        'HVN3H': 'number',
        'HVN4L': 'number',
        'HVN4H': 'number',
        'HVN5L': 'number',
        'HVN5H': 'number',
        'HVN6L': 'number',
        'HVN6H': 'number',
        'Supabase ID': 'number'
    }
}