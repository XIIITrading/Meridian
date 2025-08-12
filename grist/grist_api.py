import os
from dotenv import load_dotenv

load_dotenv()

# Grist Configuration
GRIST_API_KEY = os.getenv('GRIST_API_KEY')
GRIST_SERVER = os.getenv('GRIST_SERVER', 'http://localhost:8484')
GRIST_DOC_ID = os.getenv('GRIST_DOC_ID')

# Polygon Configuration  
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

# Supabase Configuration (optional for direct sync)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')