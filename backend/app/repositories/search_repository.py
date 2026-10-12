import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set
from app.core.database import get_supabase_client
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)

class SearchRepository:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def create_search_run(
        self,
        requested_location: str,
        requested_track: str,
        requested_subject: str,
        target_count: int = 50
    ) -> str:
        """
        Record the start of a search run in Supabase. Returns the search_run_id.
        """
        run_id = str(uuid.uuid4())
        try:
            payload = {
                "id": run_id,
                "requested_location": requested_location,
                "requested_track": requested_track,
                "requested_subject": requested_subject,
                "status": "pending",
                "target_count": target_count,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.client.table("search_runs").insert(payload).execute()
            return run_id
        except Exception as e:
            logger.error(f"Error creating search run: {e}")
            return run_id

    def update_search_run(
        self,
        search_run_id: str,
        status: str,
        total_results: int = 0,
        target_shortfall: int = 0,
        unique_candidates: int = 0,
        profiles_enriched: int = 0,
        duration_seconds: float = 0.0,
        credits_used: float = 0.0,
        credits_estimated: float = 0.0,
        rejected_counts: Optional[Dict[str, int]] = None,
        provider_errors: Optional[List[str]] = None,
        cache_status: str = "MISS"
    ) -> None:
        """
        Update the search run record with completion metrics.
        """
        try:
            update_data = {
                "status": status,
                "total_results": total_results,
                "target_shortfall": target_shortfall,
                "unique_candidates_discovered": unique_candidates,
                "profiles_enriched": profiles_enriched,
                "search_duration_seconds": duration_seconds,
                "credits_used": credits_used,
                "credits_estimated": credits_estimated,
                "rejected_counts": rejected_counts or {},
                "provider_errors": provider_errors or [],
                "cache_status": cache_status
            }
            self.client.table("search_runs").update(update_data).eq("id", search_run_id).execute()
        except Exception as e:
            logger.error(f"Error updating search run {search_run_id}: {e}")

    def record_exposure(self, educator_ids: List[str], search_run_id: Optional[str] = None) -> int:
        """
        Mark educators as exposed to prevent showing duplicate educators across searches.
        """
        if not educator_ids:
            return 0
        try:
            now = datetime.now(timezone.utc).isoformat()
            records = [
                {
                    "educator_id": ed_id,
                    "search_run_id": search_run_id,
                    "interaction_type": "displayed",
                    "exposed_at": now
                }
                for ed_id in educator_ids
            ]
            self.client.table("exposure_history").insert(records).execute()
            return len(records)
        except Exception as e:
            logger.error(f"Error recording exposure: {e}")
            return 0

    def get_exposed_educator_ids(self) -> Set[str]:
        """
        Get all educator IDs that have been previously displayed to users.
        """
        try:
            res = self.client.table("exposure_history").select("educator_id").execute()
            return {row["educator_id"] for row in (res.data or []) if row.get("educator_id")}
        except Exception as e:
            logger.warning(f"Error reading exposure history: {e}")
            return set()

    def get_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent search runs for diagnostics and operational visibility.
        """
        try:
            res = self.client.table("search_runs").select("*").order("created_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching recent search runs: {e}")
            return []
