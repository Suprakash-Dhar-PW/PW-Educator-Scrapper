from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    locations,
    educators,
    saved_educators,
    searches
)

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(locations.router, prefix="/locations", tags=["locations"])
v1_router.include_router(locations.filters_router, tags=["filters"])
v1_router.include_router(educators.router, prefix="/educators", tags=["educators"])
v1_router.include_router(saved_educators.router, prefix="/saved-educators", tags=["saved-educators"])
v1_router.include_router(searches.router, prefix="/searches", tags=["searches"])
