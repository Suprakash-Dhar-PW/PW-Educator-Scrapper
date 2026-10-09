from fastapi import APIRouter, HTTPException, Query
from app.schemas.educator import SearchRequest, SearchResponse, SearchResult
from app.services.anakin_search import AnakinSearchService
from app.services.normalizer import CandidateNormalizer
from app.services.enrichment import EnrichmentService
from app.services.deduplication import DeduplicationService
from app.services.validator import ValidatorService
from app.services.ranking import RankingService
from app.services.cache import CacheService
from app.core.config import settings
from typing import List
from datetime import datetime, timezone

router = APIRouter()

# Instantiate services
search_service = AnakinSearchService()
normalizer = CandidateNormalizer()
enrichment = EnrichmentService()
deduplication = DeduplicationService(confidence_threshold=0.65)
validator = ValidatorService()
ranking = RankingService()
cache_service = CacheService()

VALID_TRACKS = {
    "IIT-JEE": ["Physics", "Chemistry", "Mathematics"],
    "NEET": ["Physics", "Chemistry", "Biology"]
}

SUPPORTED_LOCATIONS = [
    # Karnataka
    "Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi",
    # Tamil Nadu
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    # Telangana
    "Hyderabad", "Warangal", "Karimnagar",
    # Andhra Pradesh
    "Vijayawada", "Visakhapatnam", "Guntur", "Tirupati", "Nellore",
    # Kerala
    "Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Kollam",
    # Existing
    "Lucknow", "Delhi", "Kota", "Pune", "Patna", "Mumbai", "Online"
]

@router.get("/locations", response_model=List[str])
async def get_locations():
    return sorted(SUPPORTED_LOCATIONS)

@router.get("/tracks", response_model=List[str])
async def get_tracks():
    return list(VALID_TRACKS.keys())

@router.get("/subjects", response_model=List[str])
async def get_subjects(track: str = Query(..., description="Track name like IIT-JEE or NEET")):
    if track not in VALID_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid track. Allowed: {list(VALID_TRACKS.keys())}")
    return VALID_TRACKS[track]

@router.post("/search", response_model=SearchResponse)
async def search_educators(request: SearchRequest):
    # 1. Validate filters
    if request.track not in VALID_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid track: {request.track}")
        
    if request.subject not in VALID_TRACKS[request.track]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid subject '{request.subject}' for track '{request.track}'. Allowed: {VALID_TRACKS[request.track]}"
        )
        
    cache_key = f"{request.location.lower()}|{request.track.lower()}|{request.subject.lower()}"
    
    if not request.force_refresh:
        cached = cache_service.get(cache_key, settings.SEARCH_CACHE_TTL_SECONDS)
        if cached:
            return SearchResponse(
                query={
                    "location": request.location,
                    "track": request.track,
                    "subject": request.subject
                },
                total_results=len(cached["results"]),
                target_reached=cached.get("target_reached", False),
                last_updated=cached["timestamp"],
                results=cached["results"]
            )
        
    import logging
    import time
    logger = logging.getLogger("discovery")
    logger.info(f"[DISCOVERY] Initiating multi-platform discovery for {request.track} {request.subject} in {request.location}")
    
    target_count = 15
    queries = search_service.get_queries(request.location, request.track, request.subject)
    
    all_enriched = []
    seen_urls = set()
    final_results = []
    target_reached = False
    
    start_time = time.time()
    max_duration_seconds = 45 # Prevent API timeout
    
    # Process queries in batches to avoid overwhelming the scraper and hit target efficiently
    batch_size = 4
    for i in range(0, len(queries), batch_size):
        if time.time() - start_time > max_duration_seconds:
            logger.info("[DISCOVERY] Reached max execution time, stopping discovery loop.")
            break
            
        current_batch_queries = queries[i:i+batch_size]
        new_raw_results = []
        
        for platform, prompt in current_batch_queries:
            try:
                results = search_service.execute_query(platform, prompt, request.location, request.track, request.subject)
                for r in results:
                    url = r.get("profile_url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        new_raw_results.append(r)
            except Exception as e:
                logger.error(f"[DISCOVERY] Query execution failed: {e}")
                
        if not new_raw_results:
            continue
            
        # Enrich the newly found raw results
        logger.info(f"[DISCOVERY] Enriching {len(new_raw_results)} new candidates from batch...")
        batch_enriched = enrichment.enrich_candidates(new_raw_results)
        all_enriched.extend(batch_enriched)
        
        # Deduplicate all accumulated enriched results so far
        dedup_results = deduplication.resolve_identities(all_enriched)
        educators_list = dedup_results.get("educators", [])
        social_profiles_list = dedup_results.get("social_profiles", [])
        
        # Verify and rank
        current_final_results = []
        for ed in educators_list:
            ed_profiles = [p for p in social_profiles_list if p["educator_id"] == ed["educator_id"]]
            
            verification = validator.verify_educator(
                educator=ed,
                social_profiles=ed_profiles,
                target_location=request.location,
                target_track=request.track,
                target_subject=request.subject
            )
            
            # We count candidates that have some relevance to the track/subject
            subj_status = verification.get("subject_verification", {}).get("status")
            track_status = verification.get("track_verification", {}).get("status")
            
            # If they are at least discovered for the subject/track, we consider them eligible
            if subj_status != "not_relevant" or track_status != "not_relevant":
                rank_data = ranking.rank_educator(ed, ed_profiles, verification)
                
                evidence = []
                for dim, res in verification.items():
                    for ev in res.get("evidence", []):
                        evidence.append({
                            "dimension": dim.replace("_verification", ""),
                            "platform": ev.get("platform"),
                            "text": ev.get("text")
                        })
                        
                result = SearchResult(
                    educator_id=ed["educator_id"],
                    name=ed["name"],
                    location=verification.get("location_verification", {}).get("value") or "Unknown",
                    track=verification.get("track_verification", {}).get("value") or "Unknown",
                    subjects=[verification.get("subject_verification", {}).get("value")] if verification.get("subject_verification", {}).get("value") else [],
                    profiles=[p.get("raw_profile_data", {}).get("platform_profiles", [{}])[0] for p in ed_profiles if p.get("raw_profile_data")],
                    scores={
                        "components": rank_data["scores"],
                        "overall": rank_data["overall_relevance_score"],
                        "reasons": rank_data["reasons"]
                    },
                    evidence=evidence
                )
                current_final_results.append(result)
                
        # Sort current results by score
        current_final_results.sort(key=lambda x: x.scores.get("overall", 0), reverse=True)
        final_results = current_final_results
        
        if len(final_results) >= target_count:
            logger.info(f"[DISCOVERY] Target of {target_count} reached ({len(final_results)} found). Stopping.")
            target_reached = True
            break

    logger.info(f"[DISCOVERY] Final candidates: {len(final_results)}. Unique sources queried: {len(seen_urls)}")
    
    # Store with target_reached in cache to retrieve later
    now_iso = datetime.now(timezone.utc).isoformat()
    cache_data = {
        "timestamp": now_iso,
        "target_reached": target_reached,
        "results": [r.model_dump() for r in final_results]
    }
    
    if not final_results:
        # Cache briefly on empty
        cache_service.set(cache_key, cache_data, 300)
    else:
        cache_service.set(cache_key, cache_data)
        
    return SearchResponse(
        query={
            "location": request.location,
            "track": request.track,
            "subject": request.subject
        },
        total_results=len(final_results),
        target_reached=target_reached,
        last_updated=now_iso,
        results=final_results
    )
