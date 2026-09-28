import logging
from typing import List, Dict, Any
from app.services.anakin_scraper import AnakinScraperService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("enrichment")

class EnrichmentService:
    def __init__(self):
        self.scraper = AnakinScraperService()
        
    def enrich_candidates(self, normalized_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched_candidates = []
        seen_urls = set()
        
        logger.info(f"[SEARCH] Processing {len(normalized_candidates)} normalized candidates.")
        
        import concurrent.futures
        
        def process_candidate(candidate):
            url = candidate.get("profile_url")
            
            if not url or url in seen_urls:
                logger.info(f"[DEDUPLICATED] Skipping duplicate or invalid URL: {url}")
                return None
            
            seen_urls.add(url)
            logger.info(f"[PROFILE SCRAPE START] Enqueueing scrape for URL: {url}")
            
            scrape_result = self.scraper.scrape_profile(url)
            status = scrape_result.get("scrape_status", "failed")
            
            if status == "success":
                logger.info(f"[PROFILE SCRAPE SUCCESS] Completed scrape for URL: {url}")
            else:
                logger.info(f"[PROFILE SCRAPE FAILED] Failed scrape for URL: {url} | Status: {status}")
                
            enriched_candidate = {
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "requested_location": candidate.get("requested_location"),
                "requested_track": candidate.get("requested_track"),
                "requested_subject": candidate.get("requested_subject"),
                
                "discovery": {
                    "source": candidate.get("discovery_source"),
                    "title": candidate.get("name"),
                    "snippet": candidate.get("snippet"),
                    "url": candidate.get("profile_url")
                },
                
                "platform_profiles": [
                    scrape_result
                ]
            }
            return enriched_candidate

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(process_candidate, normalized_candidates)
            for res in results:
                if res:
                    enriched_candidates.append(res)
                    
        return enriched_candidates
