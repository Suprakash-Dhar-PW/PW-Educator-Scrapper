import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.core.database import get_supabase_client
from app.core.exceptions import DatabaseException, EntityNotFoundException

logger = logging.getLogger(__name__)

class EducatorRepository:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    def get_by_id(self, educator_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a canonical educator by ID including social profiles, subjects, locations, and evidence.
        """
        try:
            res = self.client.table("educators").select("*").eq("id", educator_id).execute()
            if not res.data:
                return None
            educator = res.data[0]
            
            # Fetch relations
            profiles = self.client.table("social_profiles").select("*").eq("educator_id", educator_id).execute()
            subjects = self.client.table("educator_subjects").select("*").eq("educator_id", educator_id).execute()
            locations = self.client.table("educator_locations").select("*").eq("educator_id", educator_id).execute()
            evidence = self.client.table("educator_evidence").select("*").eq("educator_id", educator_id).execute()
            
            educator["profiles"] = profiles.data or []
            educator["subjects"] = [s["subject"] for s in (subjects.data or [])]
            educator["locations"] = [l["location_name"] for l in (locations.data or [])]
            educator["evidence"] = evidence.data or []
            
            return educator
        except Exception as e:
            logger.error(f"Error fetching educator by ID {educator_id}: {e}")
            raise DatabaseException(f"Failed to fetch educator {educator_id}")

    def list_educators(
        self,
        track: Optional[str] = None,
        subject: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List educators with optional track, subject, and location filters.
        """
        try:
            query = self.client.table("educators").select("*")
            if track:
                query = query.eq("primary_track", track)
            if location and location.lower() != "all" and location.lower() != "online":
                query = query.ilike("primary_location", f"%{location}%")
                
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            res = query.execute()
            educators = res.data or []
            
            if not educators:
                return []
                
            # Populate profiles for educators
            ed_ids = [e["id"] for e in educators]
            profiles_res = self.client.table("social_profiles").select("*").in_("educator_id", ed_ids).execute()
            profiles_map: Dict[str, list] = {}
            for p in (profiles_res.data or []):
                profiles_map.setdefault(p["educator_id"], []).append(p)
                
            for e in educators:
                e["profiles"] = profiles_map.get(e["id"], [])
                if e["profiles"]:
                    e["profile_url"] = e["profiles"][0]["url"]
                    e["source_platform"] = e["profiles"][0]["platform"]
                else:
                    e["profile_url"] = ""
                    e["source_platform"] = "Web"
            return educators
        except Exception as e:
            logger.error(f"Error listing educators: {e}")
            raise DatabaseException("Failed to query educators from database")

    def find_or_create(self, educator_data: Dict[str, Any]) -> str:
        """
        Find existing educator by primary URL or name, or create a new record.
        Returns the canonical educator UUID string.
        """
        name = educator_data.get("full_name") or educator_data.get("name")
        primary_url = educator_data.get("profile_url") or ""
        
        # 1. Check by profile URL if present
        if primary_url:
            p_res = self.client.table("social_profiles").select("educator_id").eq("url", primary_url).execute()
            if p_res.data:
                return p_res.data[0]["educator_id"]
                
        # 2. Check by name
        if name:
            n_res = self.client.table("educators").select("id").eq("name", name.strip()).execute()
            if n_res.data:
                return n_res.data[0]["id"]
                
        # 3. Create new educator
        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "id": new_id,
            "name": name.strip() if name else "Unknown Educator",
            "primary_track": educator_data.get("track") or "IIT-JEE",
            "primary_location": educator_data.get("location") or "India",
            "professional_headline": educator_data.get("professional_headline"),
            "current_job_title": educator_data.get("current_job_title"),
            "current_employer": educator_data.get("current_employer"),
            "pw_exclusion_status": educator_data.get("pw_exclusion_status", "ELIGIBLE"),
            "identity_confidence": float(educator_data.get("identity_confidence", 1.0) or 1.0),
            "employment_verification_status": educator_data.get("employment_verification_status", "verified"),
            "verification_status": "verified",
            "created_at": now,
            "updated_at": now
        }
        self.client.table("educators").insert(payload).execute()
        
        # Insert social profile
        if primary_url:
            self.client.table("social_profiles").insert({
                "educator_id": new_id,
                "platform": educator_data.get("source_platform", "Web"),
                "url": primary_url,
                "scrape_status": "success",
                "scraped_at": now
            }).execute()
            
        return new_id

    def save_candidates_batch(self, candidates: List[Dict[str, Any]], req_track: str, req_loc: str, req_subj: str) -> int:
        """
        Batch save verified candidates from a discovery pipeline run.
        """
        saved_count = 0
        for cand in candidates:
            try:
                ed_id = self.find_or_create(cand)
                # Ensure subject is associated
                self.client.table("educator_subjects").upsert({
                    "educator_id": ed_id,
                    "track": req_track,
                    "subject": req_subj
                }, on_conflict="educator_id,track,subject").execute()
                
                # Ensure location is associated
                if req_loc:
                    self.client.table("educator_locations").upsert({
                        "educator_id": ed_id,
                        "location_name": req_loc
                    }, on_conflict="educator_id,location_name").execute()
                    
                saved_count += 1
            except Exception as e:
                logger.warning(f"Error persisting candidate {cand.get('name')}: {e}")
                
        return saved_count
