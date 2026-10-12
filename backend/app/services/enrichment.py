import logging
from typing import List, Dict, Any
from app.services.anakin_scraper import AnakinScraperService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("enrichment")

class EnrichmentService:
    def __init__(self):
        self.scraper = AnakinScraperService()
        
    def enrich_candidates_batch(self, deduplicated_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        enriched_candidates = []
        urls_to_scrape = []
        url_to_candidate = {}
        
        for cand in deduplicated_candidates:
            url = cand.get("profile_url")
            if url:
                if url not in url_to_candidate:
                    urls_to_scrape.append(url)
                    url_to_candidate[url] = cand
                    
        logger.info(f"[SEARCH] Batch enriching {len(urls_to_scrape)} unique candidates.")
        
        scrape_results = {"results": {}, "credits_used": 0.0, "credits_estimated": 0.0}
        if urls_to_scrape:
            # Check if scraper has batch support added
            if hasattr(self.scraper, "scrape_profiles_batch"):
                scrape_results = self.scraper.scrape_profiles_batch(urls_to_scrape)
            else:
                # Fallback to single scrapes (should not happen based on patch)
                import concurrent.futures
                results = {}
                def scrape_single(u):
                    return u, self.scraper.scrape_profile(u)
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    for u, res in executor.map(scrape_single, urls_to_scrape):
                        results[u] = res
                scrape_results = {"results": results, "credits_used": 0.0, "credits_estimated": len(urls_to_scrape) * 5.0}

        for url, scrape_result in scrape_results.get("results", {}).items():
            candidate = url_to_candidate[url]
            status = scrape_result.get("scrape_status", "failed")
            
            if status == "success":
                logger.info(f"[PROFILE SCRAPE SUCCESS] URL: {url}")
            elif "402" in status:
                logger.warning(f"[PROFILE SCRAPE FAILED 402] Out of credits: {url}")
            else:
                logger.info(f"[PROFILE SCRAPE FAILED] URL: {url} | Status: {status}")
                
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
            enriched_candidates.append(enriched_candidate)
            
        return {
            "enriched_candidates": enriched_candidates,
            "credits_used": scrape_results.get("credits_used", 0.0),
            "credits_estimated": scrape_results.get("credits_estimated", 0.0)
        }
