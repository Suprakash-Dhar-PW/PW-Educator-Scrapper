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

MOCK_LOCATIONS = [
    "Lucknow", "Delhi", "Kota", "Pune", "Patna", 
    "Mumbai", "Bangalore", "Hyderabad", "Online"
]

@router.get("/locations", response_model=List[str])
async def get_locations():
    return MOCK_LOCATIONS

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
                last_updated=cached["timestamp"],
                results=cached["results"]
            )
        
    # 2. Search Anakin
    try:
        raw_results = search_service.search_educators(request.location, request.track, request.subject)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search service failed: {str(e)}")
        
    # 3. Normalize candidates (Already normalized in search_service)
    import logging
    logger = logging.getLogger("discovery")
    logger.info(f"[DISCOVERY] Initiating multi-platform discovery for {request.track} {request.subject} in {request.location}")
    normalized = raw_results
    
    # 4. Enrich profiles (Synchronously blocking for now as requested)
    enriched = enrichment.enrich_candidates(normalized)
    
    # 5. Deduplicate educators
    dedup_results = deduplication.resolve_identities(enriched)
    educators_list = dedup_results.get("educators", [])
    social_profiles_list = dedup_results.get("social_profiles", [])
    
    final_results = []
    
    # 6 & 7. Verify evidence and calculate ranking
    for ed in educators_list:
        ed_profiles = [p for p in social_profiles_list if p["educator_id"] == ed["educator_id"]]
        
        # Verify
        verification = validator.verify_educator(
            educator=ed,
            social_profiles=ed_profiles,
            target_location=request.location,
            target_track=request.track,
            target_subject=request.subject
        )
        
        # Rank
        rank_data = ranking.rank_educator(ed, ed_profiles, verification)
        
        # Extract evidence array from verification dict
        evidence = []
        for dim, res in verification.items():
            for ev in res.get("evidence", []):
                evidence.append({
                    "dimension": dim.replace("_verification", ""),
                    "platform": ev.get("platform"),
                    "text": ev.get("text")
                })
                
        # Format the result
        result = SearchResult(
            educator_id=ed["educator_id"],
            name=ed["name"],
            location=verification.get("location_verification", {}).get("value") or "Unknown",
            track=verification.get("track_verification", {}).get("value") or "Unknown",
            subjects=[verification.get("subject_verification", {}).get("value")] if verification.get("subject_verification", {}).get("value") else [],
            profiles=[p.get("raw_profile_data", {}).get("platform_profiles", [{}])[0] for p in ed_profiles],
            scores={
                "components": rank_data["scores"],
                "overall": rank_data["overall_relevance_score"],
                "reasons": rank_data["reasons"]
            },
            evidence=evidence
        )
        
        final_results.append(result)
        
    # Sort by overall score descending
    final_results.sort(key=lambda x: x.scores.get("overall", 0), reverse=True)
    
    now_iso = datetime.now(timezone.utc).isoformat()
    cache_service.set(cache_key, [r.dict() for r in final_results])

    return SearchResponse(
        query={
            "location": request.location,
            "track": request.track,
            "subject": request.subject
        },
        total_results=len(final_results),
        last_updated=now_iso,
        results=final_results
    )
