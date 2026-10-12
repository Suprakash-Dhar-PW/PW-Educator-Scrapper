import pytest
from app.repositories.educator_repository import EducatorRepository
from app.repositories.saved_educator_repository import SavedEducatorRepository
from app.repositories.search_repository import SearchRepository
from app.core.database import check_database_health

def test_supabase_database_health():
    """Verify that Supabase PostgreSQL is reachable and healthy."""
    health = check_database_health()
    assert health["status"] == "healthy"
    assert health["connected"] is True
    assert health["provider"] == "supabase_postgresql"

def test_educator_repository_list():
    """Verify listing educators from Supabase."""
    repo = EducatorRepository()
    eds = repo.list_educators(limit=5)
    assert isinstance(eds, list)
    assert len(eds) > 0
    # Check shape of canonical educator record
    first = eds[0]
    assert "id" in first
    assert "name" in first
    assert "profiles" in first

def test_saved_educator_repository_flow():
    """Verify save and unsave flow in Supabase."""
    ed_repo = EducatorRepository()
    saved_repo = SavedEducatorRepository()
    
    # Pick first educator from Supabase
    eds = ed_repo.list_educators(limit=1)
    assert len(eds) > 0
    ed_id = eds[0]["id"]
    
    # Initially unsave if already present to establish baseline
    saved_repo.unsave(ed_id)
    assert saved_repo.is_saved(ed_id) is False
    
    # Save educator
    saved_repo.save(ed_id, notes="Automated test note")
    assert saved_repo.is_saved(ed_id) is True
    
    # Verify in all saved list
    all_saved = saved_repo.get_all()
    matching = [s for s in all_saved if s["id"] == ed_id]
    assert len(matching) == 1
    assert matching[0]["notes"] == "Automated test note"
    
    # Unsave
    saved_repo.unsave(ed_id)
    assert saved_repo.is_saved(ed_id) is False

def test_search_repository_exposure_tracking():
    """Verify search run creation and exposure tracking."""
    search_repo = SearchRepository()
    ed_repo = EducatorRepository()
    
    eds = ed_repo.list_educators(limit=2)
    assert len(eds) >= 2
    ed_ids = [e["id"] for e in eds]
    
    # Create search run
    run_id = search_repo.create_search_run(
        requested_location="Lucknow",
        requested_track="IIT-JEE",
        requested_subject="Physics",
        target_count=50
    )
    assert run_id is not None
    
    # Record exposure
    count = search_repo.record_exposure(ed_ids, search_run_id=run_id)
    assert count == len(ed_ids)
    
    # Verify educator IDs are now in exposure history
    exposed_ids = search_repo.get_exposed_educator_ids()
    for eid in ed_ids:
        assert eid in exposed_ids
