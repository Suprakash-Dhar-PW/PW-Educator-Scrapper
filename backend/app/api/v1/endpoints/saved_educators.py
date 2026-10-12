import logging
from fastapi import APIRouter, HTTPException, Path
from typing import Optional
from app.schemas.educator import SaveEducatorRequest, SavedEducatorsResponse, SavedEducatorItem
from app.repositories.saved_educator_repository import SavedEducatorRepository

logger = logging.getLogger(__name__)
router = APIRouter()
saved_repo = SavedEducatorRepository()

@router.get("", response_model=SavedEducatorsResponse)
@router.get("/", response_model=SavedEducatorsResponse)
def get_saved_educators():
    """
    Retrieve all shortlisted/saved educators persisted in Supabase PostgreSQL.
    """
    items = saved_repo.get_all()
    return SavedEducatorsResponse(total=len(items), items=items)

@router.post("/{educator_id}", response_model=SavedEducatorItem)
def save_educator(
    educator_id: str = Path(..., description="UUID of the educator to save"),
    body: Optional[SaveEducatorRequest] = None
):
    """
    Save an educator to the shortlist in Supabase.
    """
    notes = body.notes if body else ""
    saved_record = saved_repo.save(educator_id, notes=notes)
    # Return formatted educator
    all_saved = saved_repo.get_all()
    for item in all_saved:
        if item["id"] == educator_id:
            return SavedEducatorItem(**item)
            
    return SavedEducatorItem(
        id=educator_id,
        name="Saved Educator",
        track="IIT-JEE",
        location="India",
        notes=notes,
        saved_id=saved_record.get("id")
    )

@router.delete("/{educator_id}")
def unsave_educator(educator_id: str = Path(..., description="UUID of the educator to unsave")):
    """
    Remove an educator from the shortlist in Supabase.
    """
    saved_repo.unsave(educator_id)
    return {"status": "success", "message": f"Educator {educator_id} removed from saved list"}
