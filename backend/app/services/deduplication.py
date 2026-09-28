import uuid
import re
from typing import List, Dict, Any, Tuple

class DeduplicationService:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def resolve_identities(self, enriched_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        educators = []  # List of unique educators
        social_profiles = []  # List of profiles linked to educators
        
        import logging
        logger = logging.getLogger("deduplication")
        
        for profile in enriched_profiles:
            best_match_id = None
            highest_confidence = 0.0
            
            # Compare current profile with existing educators to find a match
            for educator in educators:
                confidence = self._calculate_similarity(profile, educator, social_profiles)
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match_id = educator["educator_id"]
            
            # Extract basic profile info
            profile_name = profile.get("name") or "Unknown"
            platform_data_list = profile.get("platform_profiles", [])
            platform_data = platform_data_list[0] if platform_data_list else {}
            
            if highest_confidence >= self.confidence_threshold and best_match_id:
                logger.info(f"[IDENTITY MATCH] Merging profile '{profile_name}' into {best_match_id} (confidence: {highest_confidence:.2f})")
                # Merge into existing educator
                educator_id = best_match_id
                
                # Update educator's confidence (average or max, let's keep max for simplicity)
                for ed in educators:
                    if ed["educator_id"] == educator_id:
                        # Keep the longest name as primary name
                        if len(profile_name) > len(ed["name"]) and profile_name != "Unknown":
                            ed["name"] = profile_name
                        
                        ed["match_confidence"] = max(ed.get("match_confidence", 0.0), highest_confidence)
                        break
            else:
                if best_match_id:
                    logger.info(f"[IDENTITY UNCERTAIN] Creating new identity for '{profile_name}' (highest match confidence: {highest_confidence:.2f})")
                else:
                    logger.info(f"[IDENTITY UNCERTAIN] Creating first identity for '{profile_name}'")
                    
                # Create a new educator
                educator_id = str(uuid.uuid4())
                educators.append({
                    "educator_id": educator_id,
                    "name": profile_name,
                    "match_confidence": 1.0 # 1.0 for the self/first profile
                })
            
            # Create the social profile link
            social_profiles.append({
                "educator_id": educator_id,
                "candidate_id": profile.get("candidate_id"),
                "platform": platform_data.get("platform", "Unknown"),
                "url": platform_data.get("url", profile.get("profile_url")),
                "raw_profile_data": profile  # Optional, keeping for reference
            })
            
        return {
            "educators": educators,
            "social_profiles": social_profiles
        }
        
    def _calculate_similarity(self, new_profile: Dict[str, Any], educator: Dict[str, Any], social_profiles: List[Dict[str, Any]]) -> float:
        # Find all existing social profiles belonging to this educator
        existing_profiles = [p for p in social_profiles if p["educator_id"] == educator["educator_id"]]
        
        max_score = 0.0
        
        new_platform_data = new_profile.get("platform_profiles", [{}])[0]
        new_name = (new_profile.get("name") or "").lower().strip()
        new_username = self._get_username(new_platform_data).lower()
        new_bio = self._get_bio(new_platform_data).lower()
        new_website = self._get_website(new_platform_data).lower()
        
        for existing_p in existing_profiles:
            score = 0.0
            ex_data = existing_p.get("raw_profile_data", {}).get("platform_profiles", [{}])[0]
            
            ex_name = (existing_p.get("raw_profile_data", {}).get("name") or "").lower().strip()
            ex_username = self._get_username(ex_data).lower()
            ex_bio = self._get_bio(ex_data).lower()
            ex_website = self._get_website(ex_data).lower()
            
            # 1. Exact URL match (Rare since enrichment deduplicates, but good fallback)
            if new_platform_data.get("url") and new_platform_data.get("url") == ex_data.get("url"):
                return 1.0
                
            # 2. Cross-platform link using structured social profiles
            new_socials = new_platform_data.get("social_profiles", [])
            ex_socials = ex_data.get("social_profiles", [])
            
            new_urls = [s.get("url", "").lower() for s in new_socials if s.get("url")]
            ex_urls = [s.get("url", "").lower() for s in ex_socials if s.get("url")]
            
            new_url = (new_platform_data.get("url") or "").lower()
            ex_url = (ex_data.get("url") or "").lower()
            
            if (new_url and new_url in ex_urls) or (ex_url and ex_url in new_urls) or (set(new_urls) & set(ex_urls)):
                score += 0.85
            elif (new_url and new_url in ex_bio) or (ex_url and ex_url in new_bio):
                score += 0.85
                
            # 3. Exact Username Match (across different platforms)
            if new_username and ex_username and new_username == ex_username:
                score += 0.6
                
            # 4. Website Match
            if new_website and ex_website and new_website == ex_website:
                score += 0.6
                
            # 5. Name Similarity
            if new_name and ex_name and new_name == ex_name:
                score += 0.35 # Not enough to merge alone (0.35 < 0.65 threshold)
            
            # 6. Institution/Employer Reference
            # Simple heuristic: check common coaching institutes if both bios mention it
            institutions = ["physics wallah", "pw", "allen", "unacademy", "vedantu", "byjus", "aakash", "fiitjee"]
            for inst in institutions:
                if inst in new_bio and inst in ex_bio:
                    score += 0.3
                    break
                    
            if score > max_score:
                max_score = score
                
        # Cap score at 1.0
        return min(max_score, 1.0)
        
    def _get_username(self, platform_data: Dict[str, Any]) -> str:
        return str(platform_data.get("username") or platform_data.get("channel_name") or "")
        
    def _get_bio(self, platform_data: Dict[str, Any]) -> str:
        return str(platform_data.get("bio") or platform_data.get("description") or platform_data.get("about") or "")
        
    def _get_website(self, platform_data: Dict[str, Any]) -> str:
        # In our generic extraction, we might not always have website scraped, but we handle it if present
        return str(platform_data.get("website") or "")
