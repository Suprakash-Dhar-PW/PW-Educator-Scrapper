import os
import time
import logging
from datetime import datetime, timezone
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

router = APIRouter()

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
    "Ahmedabad", "Belagavi", "Bengaluru", "Bhopal", "Bhubaneswar", "Chandigarh", "Chennai", 
    "Coimbatore", "Dehradun", "Delhi", "Faridabad", "Ghaziabad", "Guntur", "Gurugram", 
    "Guwahati", "Gwalior", "Hubballi", "Hyderabad", "Indore", "Jabalpur", 
    "Jaipur", "Jodhpur", "Kanpur", "Karimnagar", "Kochi", "Kolkata", "Kollam", 
    "Kota", "Kozhikode", "Lucknow", "Madurai", "Mangaluru", "Meerut", "Mumbai", 
    "Mysuru", "Nagpur", "Nashik", "Nellore", "Noida", "Online", "Patna", "Pune", 
    "Raipur", "Ranchi", "Salem", "Surat", "Thiruvananthapuram", "Thrissur", 
    "Tiruchirappalli", "Tirupati", "Vadodara", "Varanasi", "Vijayawada", 
    "Visakhapatnam", "Warangal"
]

PIPELINE_VERSION = "v4"

@router.get("/locations", response_model=List[str])
def get_locations():
    return sorted(SUPPORTED_LOCATIONS)

@router.get("/tracks", response_model=List[str])
def get_tracks():
    return list(VALID_TRACKS.keys())

@router.get("/subjects", response_model=List[str])
def get_subjects(track: str = Query(..., description="Track name like IIT-JEE or NEET")):
    if track not in VALID_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid track. Allowed: {list(VALID_TRACKS.keys())}")
    return VALID_TRACKS[track]

@router.post("/cache/clear")
def clear_cache():
    cache_service.clear()
    return {"status": "success", "message": "Cache successfully cleared"}

@router.get("/diagnostics")
def get_diagnostics():
    has_anakin_key = bool(settings.ANAKIN_API_KEY)
    has_search_key = bool(settings.ANAKIN_SEARCH_API_KEY)
    has_scraper_key = bool(settings.ANAKIN_SCRAPER_API_KEY)
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": PIPELINE_VERSION,
        "providers": {
            "anakin_scraper": {
                "configured": has_scraper_key or has_anakin_key,
                "endpoint": "https://api.anakin.io/v1/url-scraper"
            },
            "anakin_search": {
                "configured": has_search_key or has_anakin_key,
                "endpoint": "https://api.anakin.io/v1/search"
            },
            "ddgs": {
                "configured": True,
                "endpoint": "DuckDuckGo Text API"
            }
        },
        "supported_tracks": VALID_TRACKS,
        "supported_locations_count": len(SUPPORTED_LOCATIONS)
    }

@router.post("/search", response_model=SearchResponse)
def search_educators(request: SearchRequest):
    import traceback
    try:
        return _search_educators_impl(request)
    except Exception as e:
        print("EXCEPTION IN SEARCH_EDUCATORS:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}")

def _search_educators_impl(request: SearchRequest):
    start_time = time.time()
    search_service.search_credits_used = 0.0
    target_count = request.target_count or 50
    if request.track not in VALID_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid track: {request.track}")
        
    if request.subject not in VALID_TRACKS[request.track]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid subject '{request.subject}' for track '{request.track}'. Allowed: {VALID_TRACKS[request.track]}"
        )
        
    cache_key = f"{PIPELINE_VERSION}|{request.location.lower()}|{request.track.lower()}|{request.subject.lower()}|b{request.budget_max_candidates}|e{request.budget_max_enrichments}|t{target_count}"
    
    if not request.force_refresh:
        cached = cache_service.get(cache_key, settings.SEARCH_CACHE_TTL_SECONDS)
        if cached:
            return SearchResponse(
                query={"location": request.location, "track": request.track, "subject": request.subject},
                total_results=len(cached["results"]),
                target_count=cached.get("target_count", 50),
                target_reached=cached.get("target_reached", False),
                target_shortfall=cached.get("target_shortfall", 0),
                unique_candidates_discovered=cached.get("unique_candidates_discovered", 0),
                profiles_enriched=cached.get("profiles_enriched", 0),
                search_duration_seconds=cached.get("search_duration_seconds", 0.0),
                rejected_counts=cached.get("rejected_counts", {}),
                review_queue_count=cached.get("review_queue_count", 0),
                sources_searched=cached.get("sources_searched", 0),
                provider_errors=cached.get("provider_errors", []),
                last_updated=cached["timestamp"],
                cache_status="HIT",
                results=cached["results"],
                review_results=cached.get("review_results", []),
                credits_used=0.0,
                credits_estimated=0.0
            )
        
    logger = logging.getLogger("discovery")
    logger.info(f"[DISCOVERY] Initiating discovery for {request.track} {request.subject} in {request.location}")
    
    queries = search_service.get_queries(request.location, request.track, request.subject)
    
    # 1. Discover unique URLs (Broad discovery via DDGS)
    unique_urls_collected = set()
    raw_candidates = []
    sources_searched = 0
    provider_errors = []
    
    for platform, prompt in queries:
        if sources_searched >= request.budget_max_anakin_searches:
            break
        if len(unique_urls_collected) >= request.budget_max_candidates:
            break
            
        try:
            sources_searched += 1
            results = search_service.execute_query(platform, prompt, request.location, request.track, request.subject)
            for r in results:
                url = r.get("profile_url")
                if url and url not in unique_urls_collected:
                    unique_urls_collected.add(url)
                    raw_candidates.append(r)
                    if len(unique_urls_collected) >= request.budget_max_candidates:
                        break
        except Exception as e:
            provider_errors.append(f"{platform} error: {str(e)}")

    # 2. Deduplicate Candidates BEFORE Enrichment
    # Actually, deduplication.resolve_identities requires platform_profiles. 
    # But since we just collected raw unique URLs, we can enrich them directly, 
    # since we already deduplicated by exact URL above.
    
    # 3. Check Enrichment Cache for the unique URLs to avoid re-scraping
    candidates_to_enrich = []
    cached_enriched_candidates = []
    
    for cand in raw_candidates:
        url = cand.get("profile_url")
        cand_cache_key = f"enrich_v1_{url}"
        cached_enrich = cache_service.get(cand_cache_key, settings.SEARCH_CACHE_TTL_SECONDS * 10)
        
        if cached_enrich and not request.force_refresh:
            # Reconstruct enriched candidate from cache
            cached_enriched_candidates.append({
                "candidate_id": cand.get("candidate_id"),
                "name": cand.get("name"),
                "requested_location": cand.get("requested_location"),
                "requested_track": cand.get("requested_track"),
                "requested_subject": cand.get("requested_subject"),
                "discovery": {
                    "source": cand.get("discovery_source"),
                    "title": cand.get("name"),
                    "snippet": cand.get("snippet"),
                    "url": url
                },
                "platform_profiles": [cached_enrich]
            })
        else:
            candidates_to_enrich.append(cand)
            
    # Apply budget to new enrichments
    candidates_to_enrich = candidates_to_enrich[:request.budget_max_enrichments]
    
    # 4. Batch Enrich New Candidates
    enrichment_result = enrichment.enrich_candidates_batch(candidates_to_enrich)
    new_enriched = enrichment_result.get("enriched_candidates", [])
    credits_used = enrichment_result.get("credits_used", 0.0)
    credits_estimated = enrichment_result.get("credits_estimated", 0.0)
    
    # Save new enrichments to cache
    for encand in new_enriched:
        url = encand["discovery"]["url"]
        if encand.get("platform_profiles"):
            cache_service.set(f"enrich_v1_{url}", encand["platform_profiles"][0], settings.SEARCH_CACHE_TTL_SECONDS * 10)
            
    all_enriched = cached_enriched_candidates + new_enriched
    
    # 5. Resolve Identities & Deduplicate
    dedup_results = deduplication.resolve_identities(all_enriched)
    educators_list = dedup_results.get("educators", [])
    social_profiles_list = dedup_results.get("social_profiles", [])
    
    current_final_results = []
    current_review_results = []
    
    rejected_counts = {
        "EXCLUDED_CURRENT_PW": 0,
        "EXCLUDED_FORMER_PW": 0,
        "UNVERIFIED_IDENTITY": 0,
        "NOT_RELEVANT": 0
    }
    review_queue_count = 0

    for ed in educators_list:
        ed_profiles = [p for p in social_profiles_list if p["educator_id"] == ed["educator_id"]]
        
        verification = validator.verify_educator(
            educator=ed,
            social_profiles=ed_profiles,
            target_location=request.location,
            target_track=request.track,
            target_subject=request.subject
        )
        
        identity = verification.get("identity_verification", {})
        employment = verification.get("employment_verification", {})
        
        # 1. Subject & Track relevance: Both MUST be relevant for competitive exams (IIT-JEE / NEET)
        subj_status = verification.get("subject_verification", {}).get("status")
        track_status = verification.get("track_verification", {}).get("status")
        
        if subj_status == "not_relevant" or track_status == "not_relevant":
            rejected_counts["NOT_RELEVANT"] += 1
            continue

        # 2. Role verification: Exclude students, aspirants, and non-mentors (e.g. Pg Haritha)
        role_ver = verification.get("role_verification", {})
        if role_ver.get("is_student") or not role_ver.get("is_educator"):
            rejected_counts["NOT_RELEVANT"] += 1
            continue

        # 3. Institutional / Official account exclusion (e.g. IIT Hyderabad_Official)
        if identity.get("is_institution") or identity.get("entity_type") in ["institution", "channel"]:
            rejected_counts["UNVERIFIED_IDENTITY"] += 1
            continue

        if not identity.get("value"):
            rejected_counts["UNVERIFIED_IDENTITY"] += 1
            continue

        # 4. Strict PW / Vidyapeeth Exclusion (both current and former) (e.g. Tushar Kumar)
        emp_val = employment.get("value")
        if emp_val in ["EXCLUDED_CURRENT_PW", "EXCLUDED_FORMER_PW"]:
            rejected_counts[emp_val] += 1
            continue

        # Identity & employment review routing
        needs_review = False
        
        if emp_val == "ELIGIBILITY_UNCONFIRMED":
            needs_review = True
            
        if identity.get("confidence", 0) < 0.5 or identity.get("status") == "unconfirmed":
            needs_review = True

        rank_data = ranking.rank_educator(ed, ed_profiles, verification)
        
        evidence_list = []
        for dim, res in verification.items():
            for ev in res.get("evidence", []):
                evidence_list.append({
                    "dimension": dim.replace("_verification", ""),
                    "platform": ev.get("platform"),
                    "text": ev.get("text")
                })
                
        primary_profile = ed_profiles[0] if ed_profiles else {}
        
        profiles_for_result = []
        for p in ed_profiles:
            raw_p = p.get("raw_profile_data", {})
            plat_profs = raw_p.get("platform_profiles", [])
            if plat_profs:
                profiles_for_result.append(plat_profs[0])
            else:
                profiles_for_result.append({
                    "platform": p.get("platform", "Unknown"),
                    "url": p.get("url", "")
                })

        result = SearchResult(
            educator_id=ed["educator_id"],
            full_name=identity.get("value") or ed.get("name", "Unknown"),
            professional_headline=identity.get("headline"),
            current_employer=identity.get("employer"),
            location=verification.get("location_verification", {}).get("value") or request.location,
            track=verification.get("track_verification", {}).get("value") or request.track,
            subjects=[verification.get("subject_verification", {}).get("value")] if verification.get("subject_verification", {}).get("value") else [request.subject],
            profiles=profiles_for_result,
            scores={
                "components": {f["key"]: f["earned_points"] for f in rank_data.get("score_explanation", {}).get("factors", [])},
                "overall": rank_data.get("relevance_score", 0),
                "reasons": [f["explanation"] for f in rank_data.get("score_explanation", {}).get("factors", []) if f.get("status") != "unknown"]
            },
            evidence=evidence_list,
            pw_exclusion_status=emp_val,
            identity_confidence=identity.get("confidence", 0),
            employment_verification_status=employment.get("status", "unconfirmed"),
            source_platform=primary_profile.get("platform", "Unknown"),
            profile_url=primary_profile.get("url", "")
        )
        
        if needs_review:
            current_review_results.append(result)
            review_queue_count += 1
        else:
            current_final_results.append(result)

    current_final_results.sort(key=lambda x: x.scores.get("overall", 0), reverse=True)
    current_review_results.sort(key=lambda x: x.scores.get("overall", 0), reverse=True)
    
    final_results = current_final_results[:target_count]
    review_results = current_review_results
    target_shortfall = max(0, target_count - len(final_results))
    search_duration_seconds = round(time.time() - start_time, 2)
    total_credits_used = round(float(credits_used) + float(search_service.search_credits_used), 2)
    
    now_iso = datetime.now(timezone.utc).isoformat()
    cache_entry = {
        "timestamp": now_iso,
        "target_count": target_count,
        "target_reached": len(final_results) >= target_count,
        "target_shortfall": target_shortfall,
        "unique_candidates_discovered": len(unique_urls_collected),
        "profiles_enriched": len(new_enriched),
        "search_duration_seconds": search_duration_seconds,
        "rejected_counts": rejected_counts,
        "review_queue_count": review_queue_count,
        "sources_searched": sources_searched,
        "provider_errors": provider_errors,
        "results": [r.model_dump() for r in final_results],
        "review_results": [r.model_dump() for r in review_results]
    }
    
    cache_service.set(cache_key, cache_entry, settings.SEARCH_CACHE_TTL_SECONDS)
    
    response = SearchResponse(
        query={"location": request.location, "track": request.track, "subject": request.subject},
        total_results=len(final_results),
        target_count=target_count,
        target_reached=len(final_results) >= target_count,
        target_shortfall=target_shortfall,
        unique_candidates_discovered=len(unique_urls_collected),
        profiles_enriched=len(new_enriched),
        search_duration_seconds=search_duration_seconds,
        rejected_counts=rejected_counts,
        review_queue_count=review_queue_count,
        sources_searched=sources_searched,
        provider_errors=provider_errors,
        last_updated=now_iso,
        cache_status="MISS",
        results=final_results,
        review_results=review_results,
        credits_used=total_credits_used,
        credits_estimated=credits_estimated
    )
    
    return response
