import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get or initialize the Supabase client singleton.
    Falls back gracefully if initialization fails.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
        
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY
    
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not configured. Database operations will fail.")
        
    try:
        _supabase_client = create_client(url, key)
        logger.info(f"Connected to Supabase at {url}")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {type(e).__name__} - {e}")
        raise

def check_database_health() -> dict:
    """
    Lightweight health check against Supabase without exposing credentials.
    """
    try:
        client = get_supabase_client()
        # Query 1 row from educators with timeout
        res = client.table("educators").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "provider": "supabase_postgresql",
            "connected": True
        }
    except Exception as e:
        logger.error(f"Supabase health check failed: {type(e).__name__} - {e}")
        return {
            "status": "unhealthy",
            "provider": "supabase_postgresql",
            "connected": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }
