from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import check_database_health

router = APIRouter()

@router.get("/health")
def get_health():
    """
    Lightweight health check endpoint.
    Checks application and Supabase database readiness without calling external APIs or consuming credits.
    """
    db_health = check_database_health()
    overall_status = "healthy" if db_health.get("connected") else "degraded"
    
    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_health,
        "providers_ready": {
            "anakin_configured": bool(settings.ANAKIN_API_KEY or settings.ANAKIN_SEARCH_API_KEY),
            "ddgs_ready": True
        }
    }
