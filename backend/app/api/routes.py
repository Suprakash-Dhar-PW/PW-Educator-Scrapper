from fastapi import APIRouter
from app.api.v1.router import v1_router
from app.api.v1.endpoints import (
    health,
    locations,
    educators,
    saved_educators,
    searches
)

api_router = APIRouter()

# 1. Mount Versioned API (/api/v1/*)
api_router.include_router(v1_router, prefix="/v1")

# 2. Backward Compatibility Aliases (/api/*)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(locations.filters_router, tags=["filters"])
api_router.include_router(educators.router, prefix="/educators", tags=["educators"])
api_router.include_router(saved_educators.router, prefix="/saved-educators", tags=["saved-educators"])
api_router.include_router(searches.router, tags=["searches"])
