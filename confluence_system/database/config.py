"""
Database configuration for Confluence System
Compatible with existing levels_zones infrastructure
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
else:
    # Try current directory
    load_dotenv()
    logger.warning("Loading .env from current directory")

# Supabase configuration (same as Monte Carlo)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

def validate_config() -> bool:
    """Validate required configuration"""
    if not SUPABASE_URL:
        logger.error("Missing SUPABASE_URL in environment")
        return False
    
    if not SUPABASE_KEY:
        logger.error("Missing SUPABASE_KEY or SUPABASE_ANON_KEY in environment")
        return False
    
    if not SUPABASE_URL.startswith('https://'):
        logger.error("SUPABASE_URL must be a valid HTTPS URL")
        return False
    
    logger.info("Database configuration validated successfully")
    return True

def get_connection_info() -> dict:
    """Get connection information for debugging"""
    return {
        'url_configured': bool(SUPABASE_URL),
        'key_configured': bool(SUPABASE_KEY),
        'url_preview': f"{SUPABASE_URL[:30]}..." if SUPABASE_URL else None,
        'key_preview': f"{SUPABASE_KEY[:20]}..." if SUPABASE_KEY else None,
    }