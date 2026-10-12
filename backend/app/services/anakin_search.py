import logging
import urllib.parse
import re
import time
import requests
from datetime import datetime, timezone
from ddgs import DDGS
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger("anakin_search")

class AnakinSearchService:
    def __init__(self):
        self.api_key = settings.ANAKIN_SEARCH_API_KEY or settings.ANAKIN_API_KEY
        self.search_credits_used = 0.0

    def get_queries(self, location: str, track: str, subject: str) -> List[Tuple[str, str]]:
        loc_clean = location.split(',')[0].strip() if location and ',' in location else (location or "").strip()
        is_online = not loc_clean or loc_clean.lower() in ["online", "remote", "all india", "india", "pan-india"]
        loc_term = "India" if is_online else loc_clean

        # Track-specific terminology
        track_terms = f'"{track}"'
        if track.upper() == "IIT-JEE":
            track_terms = '("IIT-JEE" OR "JEE Advanced" OR "JEE Main")'
        elif track.upper() == "NEET":
            track_terms = '("NEET" OR "AIPMT" OR "Medical Entrance")'

        # Multi-query discovery across platforms, coaching directories, and public teaching videos
        queries = [
            ("LinkedIn", f'site:linkedin.com/in/ {track_terms} "{subject}" faculty "{loc_term}"'),
            ("LinkedIn", f'site:linkedin.com/in/ "{subject} educator" "{loc_term}" {track_terms}'),
            ("YouTube", f'site:youtube.com {track_terms} "{subject}" teacher "{loc_term}"'),
            ("LinkedIn", f'site:linkedin.com/in/ "{subject} teacher" {track_terms} "{loc_term}"'),
            ("YouTube", f'site:youtube.com "{subject} sir" {track_terms} "{loc_term}"'),
            ("Other", f'"{loc_term}" coaching institute "{subject}" faculty {track_terms}'),
            ("Other", f'"{loc_term}" {track_terms} "{subject}" teacher profile -jobs -vacancy'),
            ("LinkedIn", f'site:linkedin.com/in/ "{subject} lecturer" "{loc_term}" {track_terms}'),
            ("Other", f'top "{subject}" teachers in "{loc_term}" for {track}'),
            ("Instagram", f'site:instagram.com "{subject} faculty" {track_terms} "{loc_term}"'),
            ("LinkedIn", f'site:linkedin.com/in/ "{subject} mentor" {track_terms} "{loc_term}"'),
            ("Other", f'"{loc_term}" coaching centres "{subject}" faculty directory'),
            ("LinkedIn", f'site:linkedin.com/in/ HOD "{subject}" {track_terms} "{loc_term}"'),
            ("YouTube", f'site:youtube.com {track_terms} "{subject} classes" "{loc_term}"'),
            ("Other", f'"{loc_term}" Senior Faculty "{subject}" {track_terms}'),
            ("LinkedIn", f'site:linkedin.com/in/ "{subject}" {track_terms} "{loc_term}"'),
            ("Instagram", f'site:instagram.com {track_terms} "{subject}" tutor "{loc_term}"'),
            ("Other", f'"{loc_term}" coaching "{subject}" teacher biography OR interview {track}'),
            ("YouTube", f'site:youtube.com/c/ OR site:youtube.com/@ "{subject}" {track_terms} "{loc_term}"'),
            ("Other", f'"{loc_term}" "{subject}" tutorial faculty {track_terms}')
        ]
        return queries

    def _extract_clean_person_name(self, title: str) -> str:
        if not title:
            return ""
            
        # Remove site suffixes
        clean = re.sub(r'\s*[\-–|•]\s*(LinkedIn|YouTube|Instagram|Facebook|Reddit|Twitter|X).*$', '', title, flags=re.I).strip()
        
        platform_names = {"youtube", "instagram", "linkedin", "facebook", "reddit", "twitter", "google", "quora", "telegram", "github", "wikipedia"}
        if clean.lower() in platform_names:
            return ""
            
        generic_words = {
            "classes", "tutors", "tutor", "coaching", "jee", "neet", "11", "12", "best", "top",
            "academy", "institute", "physics", "chemistry", "mathematics", "biology", "maths",
            "teacher", "sir", "faculty", "lectures", "tutorials", "prep", "learning", "study",
            "education", "online", "official", "channel", "solutions", "foundation", "batch",
            "centre", "center", "expert", "master", "lecture", "video", "videos", "shorts",
            "playlist", "allen", "fiitjee", "aakash", "unacademy", "pw", "wallah", "vidyapeeth",
            "group", "school", "college", "university", "department", "admin", "team", "notes",
            "youtube", "instagram", "linkedin", "facebook", "reddit", "twitter", "profile", "lecturer"
        }
        
        # Split on separators like - | • :
        parts = re.split(r'\s*[\-–|•:]\s*', clean)
        
        for p in parts:
            p = p.strip()
            # Remove academic honorifics
            p_clean = re.sub(r'^(Dr\.|Prof\.|Er\.|Mr\.|Mrs\.|Shri|Er|Dr|Prof)\s+', '', p, flags=re.I).strip()
            words = p_clean.split()
            if 2 <= len(words) <= 4:
                non_generic = [w for w in words if w.lower().strip(",.-_'\"") not in generic_words]
                if len(non_generic) >= 2 and all(re.match(r"^[A-Za-z.\'-]+$", w) for w in non_generic):
                    name = " ".join(words)
                    if len(name) <= 40:
                        return name
                        
        return ""

    def execute_query(self, platform: str, prompt: str, location: str, track: str, subject: str) -> List[Dict[str, Any]]:
        exclude_words = ["jobs", "job", "hiring", "vacancy", "vacancies", "urgent", "top 10", "top 5", "salary", "syllabus", "exam", "questions", "paper", "quora", "result", "results", "admissions", "admission"]
        
        raw_items = []
        source_type = "ddgs"
        
        logger.info(f"[PLATFORM SEARCH] Executing query on {platform}: {prompt}")
        
        # 1. Primary discovery: DDGS
        try:
            ddgs = DDGS()
            for attempt in range(2):
                try:
                    res = list(ddgs.text(prompt, max_results=25))
                    if res:
                        for item in res:
                            raw_items.append({
                                "title": item.get("title", ""),
                                "url": item.get("href", ""),
                                "snippet": item.get("body", "")
                            })
                        break
                except Exception as e:
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"[PLATFORM SEARCH] DDGS error for {platform}: {e}")

        # 2. Secondary discovery: Anakin Search API (if DDGS yielded few results and API key available)
        if len(raw_items) < 3 and self.api_key:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key
                }
                # Clean search prompt for search API
                api_prompt = prompt.replace("site:linkedin.com/in/ ", "linkedin ").replace("site:youtube.com ", "youtube ").replace("site:instagram.com ", "instagram ")
                resp = requests.post("https://api.anakin.io/v1/search", headers=headers, json={"prompt": api_prompt}, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    search_results = data.get("results", [])
                    self.search_credits_used += 1.0
                    source_type = "anakin_search"
                    logger.info(f"[ANAKIN SEARCH SUCCESS] Retrieved {len(search_results)} results for query: {api_prompt}")
                    for item in search_results:
                        raw_items.append({
                            "title": item.get("title", ""),
                            "url": item.get("url") or item.get("link", ""),
                            "snippet": item.get("snippet", "")
                        })
                elif resp.status_code == 402:
                    logger.warning("[ANAKIN SEARCH] 402 Payment Required - stopping further Anakin search calls.")
                    self.api_key = None
            except Exception as e:
                logger.warning(f"[ANAKIN SEARCH ERROR] Query failed: {e}")

        if not raw_items:
            return []
            
        normalized_results = []
        
        for item in raw_items:
            title = item.get("title", "")
            title_lower = title.lower()
            
            if any(bad_word in title_lower for bad_word in exclude_words):
                continue
                
            result_url = item.get("url", "")
            if not result_url:
                continue
                
            domain = urllib.parse.urlparse(result_url).netloc.lower()
            actual_platform = platform
            if "linkedin.com" in domain:
                actual_platform = "LinkedIn"
            elif "youtube.com" in domain or "youtu.be" in domain:
                actual_platform = "YouTube"
            elif "instagram.com" in domain:
                actual_platform = "Instagram"
            elif "reddit.com" in domain:
                actual_platform = "Reddit"
            elif "facebook.com" in domain:
                actual_platform = "Facebook"
            else:
                actual_platform = "Web"
                
            # Extract clean candidate name
            name = self._extract_clean_person_name(title)
            if not name:
                continue
                
            normalized_result = {
                "name": name,
                "platform": actual_platform,
                "profile_url": result_url,
                "snippet": item.get("snippet", ""),
                "date": "",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "requested_location": location,
                "requested_track": track,
                "requested_subject": subject,
                "discovery_query": prompt,
                "discovery_source": source_type
            }
            
            try:
                logger.info(f"[CANDIDATE FOUND] {name.encode('ascii', 'ignore').decode()} on {actual_platform} ({result_url})")
            except:
                logger.info(f"[CANDIDATE FOUND] {name} on {actual_platform}")
                
            normalized_results.append(normalized_result)
            
        return normalized_results
