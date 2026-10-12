import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from app.repositories.educator_repository import EducatorRepository
from app.core.exceptions import EntityNotFoundException

logger = logging.getLogger(__name__)
router = APIRouter()
educator_repo = EducatorRepository()

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_educators(
    track: Optional[str] = Query(None, description="Filter by exam track (IIT-JEE, NEET)"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset")
):
    """
    List verified educators persisted in Supabase PostgreSQL with filtering and pagination.
    """
    return educator_repo.list_educators(
        track=track,
        subject=subject,
        location=location,
        limit=limit,
        offset=offset
    )

@router.get("/{educator_id}")
def get_educator_detail(educator_id: str = Path(..., description="UUID of the educator")):
    """
    Retrieve comprehensive details, verified evidence, and social profiles for an educator.
    """
    educator = educator_repo.get_by_id(educator_id)
    if not educator:
        raise EntityNotFoundException(f"Educator with ID {educator_id} not found")
    return {"educator": educator}
