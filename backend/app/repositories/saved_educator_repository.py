import logging
from typing import List, Optional, Dict, Any
from app.core.database import get_supabase_client
from app.core.exceptions import DatabaseException, EntityNotFoundException

logger = logging.getLogger(__name__)

class SavedEducatorRepository:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all saved educators with joined educator profile details.
        """
        try:
            # Query saved_educators joined with educators and profiles
            res = self.client.table("saved_educators").select(
                "id, educator_id, notes, created_at, educators(*)"
            ).order("created_at", desc=True).execute()
            
            saved_list = []
            for item in (res.data or []):
                ed_data = item.get("educators") or {}
                ed_id = item.get("educator_id")
                
                # Fetch social profiles for this educator
                profs_res = self.client.table("social_profiles").select("*").eq("educator_id", ed_id).execute()
                profiles = profs_res.data or []
                primary_url = profiles[0]["url"] if profiles else ""
                platform = profiles[0]["platform"] if profiles else "Web"
                
                # Fetch subjects
                subjs_res = self.client.table("educator_subjects").select("subject").eq("educator_id", ed_id).execute()
                subjects = [s["subject"] for s in (subjs_res.data or [])]
                
                saved_list.append({
                    "saved_id": item.get("id"),
                    "id": ed_id,
                    "name": ed_data.get("name") or "Unknown Educator",
                    "track": ed_data.get("primary_track") or "IIT-JEE",
                    "location": ed_data.get("primary_location") or "India",
                    "professional_headline": ed_data.get("professional_headline") or "",
                    "current_job_title": ed_data.get("current_job_title") or "",
                    "current_employer": ed_data.get("current_employer") or "",
                    "profile_url": primary_url,
                    "source_platform": platform,
                    "profiles": profiles,
                    "subjects": subjects,
                    "pw_exclusion_status": ed_data.get("pw_exclusion_status", "ELIGIBLE"),
                    "verification_status": ed_data.get("verification_status", "verified"),
                    "notes": item.get("notes") or "",
                    "saved_at": item.get("created_at")
                })
            return saved_list
        except Exception as e:
            logger.error(f"Error fetching saved educators: {e}")
            raise DatabaseException("Failed to retrieve saved educators from database")

    def save(self, educator_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Save an educator to the shortlist. Idempotent upsert on conflict.
        """
        try:
            # Verify educator exists
            ed_check = self.client.table("educators").select("id").eq("id", educator_id).execute()
            if not ed_check.data:
                raise EntityNotFoundException(f"Educator with ID {educator_id} does not exist")
                
            payload = {
                "educator_id": educator_id,
                "notes": notes or ""
            }
            res = self.client.table("saved_educators").upsert(
                payload, on_conflict="educator_id"
            ).execute()
            return res.data[0] if res.data else payload
        except EntityNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error saving educator {educator_id}: {e}")
            raise DatabaseException(f"Failed to save educator {educator_id}")

    def unsave(self, educator_id: str) -> bool:
        """
        Remove an educator from the saved list.
        """
        try:
            self.client.table("saved_educators").delete().eq("educator_id", educator_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error unsaving educator {educator_id}: {e}")
            raise DatabaseException(f"Failed to remove educator {educator_id} from saved list")

    def is_saved(self, educator_id: str) -> bool:
        """
        Check if an educator is currently saved.
        """
        try:
            res = self.client.table("saved_educators").select("id").eq("educator_id", educator_id).execute()
            return bool(res.data and len(res.data) > 0)
        except Exception as e:
            logger.warning(f"Error checking is_saved for {educator_id}: {e}")
            return False
