import logging
import urllib.parse
from datetime import datetime, timezone
from ddgs import DDGS
from typing import List, Dict, Any
import time

logger = logging.getLogger("anakin_search")

class AnakinSearchService:
    def __init__(self):
        pass

    def get_queries(self, location: str, track: str, subject: str) -> List[Tuple[str, str]]:
        loc_term = location.split(',')[0] if ',' in location else location
        
        # Varied queries covering name, location, track, coaching institutes
        return [
            ("LinkedIn", f'linkedin {track} {subject} {loc_term}'),
            ("YouTube", f'youtube {track} {subject} {loc_term}'),
            ("Instagram", f'instagram {track} {subject} {loc_term}'),
            ("Reddit", f'reddit {track} {subject} {loc_term}'),
            
            ("LinkedIn", f'linkedin faculty {subject} {loc_term}'),
            ("YouTube", f'youtube teacher {track} {loc_term}'),
            
            ("Other", f'"{loc_term}" "{track}" "{subject}" faculty profile'),
            ("Other", f'"{loc_term}" coaching institute "{subject}" faculty'),
            
            ("LinkedIn", f'linkedin {track} coaching {loc_term}'),
            ("YouTube", f'youtube {track} classes {loc_term}'),
            
            ("Other", f'top {subject} teachers in {loc_term} for {track}'),
            ("LinkedIn", f'linkedin {subject} educator {loc_term}'),
        ]

    def execute_query(self, platform: str, prompt: str, location: str, track: str, subject: str) -> List[Dict[str, Any]]:
        exclude_words = ["jobs", "job", "hiring", "vacancy", "vacancies", "urgent", "top 10", "top 5", "best teachers", "salary", "syllabus", "exam", "questions", "paper", "quora", "result", "results", "admissions", "admission"]
        
        ddgs = DDGS()
        normalized_results = []
        
        logger.info(f"[PLATFORM SEARCH] Executing query on {platform}: {prompt}")
        
        try:
            results = []
            for attempt in range(3):
                try:
                    results = list(ddgs.text(prompt, max_results=5))
                    break
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"[PLATFORM SEARCH] Failed for {platform} after 3 attempts: {e}")
                    else:
                        time.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"[PLATFORM SEARCH] Critical failure for {platform}: {e}")
            results = []
            
        if not results:
            return []
            
        for result in results:
            title = result.get("title", "")
            title_lower = title.lower()
            
            if any(bad_word in title_lower for bad_word in exclude_words):
                continue
                
            result_url = result.get("href", "")
            if not result_url:
                continue
            
            domain = urllib.parse.urlparse(result_url).netloc.lower()
            actual_platform = platform
            if "linkedin.com" in domain: actual_platform = "LinkedIn"
            elif "youtube.com" in domain or "youtu.be" in domain: actual_platform = "YouTube"
            elif "instagram.com" in domain: actual_platform = "Instagram"
            elif "reddit.com" in domain: actual_platform = "Reddit"
            else:
                if platform != "Other":
                    continue
                
            name = title.split(" - ")[0].split(" | ")[0].split("...")[0].strip()
            if not name or len(name) > 50:
                continue
                
            normalized_result = {
                "name": name,
                "platform": actual_platform,
                "profile_url": result_url,
                "snippet": result.get("body", ""),
                "date": "",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "requested_location": location,
                "requested_track": track,
                "requested_subject": subject,
                "discovery_query": prompt,
                "discovery_source": "ddgs"
            }
            
            try:
                logger.info(f"[CANDIDATE FOUND] {name.encode('ascii', 'ignore').decode()} on {actual_platform}")
            except:
                logger.info(f"[CANDIDATE FOUND] (Unicode Name) on {actual_platform}")
                
            normalized_results.append(normalized_result)
            
        return normalized_results
