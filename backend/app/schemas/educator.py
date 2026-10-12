from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    location: str
    track: str
    subject: str
    force_refresh: bool = False
    budget_max_anakin_searches: int = 5
    budget_max_enrichments: int = 20
    budget_max_candidates: int = 60
    target_count: int = 50

class SearchResult(BaseModel):
    educator_id: str
    full_name: str
    professional_headline: Optional[str] = None
    current_job_title: Optional[str] = None
    current_employer: Optional[str] = None
    location: str
    track: str
    subjects: List[str] = []
    profiles: List[Dict[str, Any]] = []
    scores: Dict[str, Any] = {}
    evidence: List[Dict[str, Any]] = []
    pw_exclusion_status: Optional[str] = None
    identity_confidence: float = 0.0
    employment_verification_status: str = "unconfirmed"
    source_platform: str = "Unknown"
    profile_url: str = ""

class SearchResponse(BaseModel):
    query: Dict[str, str]
    total_results: int
    target_count: int = 0
    target_reached: bool = False
    target_shortfall: int = 0
    unique_candidates_discovered: int = 0
    profiles_enriched: int = 0
    rejected_counts: Dict[str, int] = {}
    review_queue_count: int = 0
    sources_searched: int = 0
    provider_errors: List[str] = []
    search_duration_seconds: float = 0.0
    last_updated: str
    cache_status: str = "MISS"
    results: List[SearchResult]
    review_results: List[SearchResult] = []
    credits_used: float = 0.0
    credits_estimated: float = 0.0

class SaveEducatorRequest(BaseModel):
    notes: Optional[str] = ""

class SavedEducatorItem(BaseModel):
    saved_id: Optional[str] = None
    id: str
    name: str
    track: Optional[str] = "IIT-JEE"
    location: Optional[str] = "India"
    professional_headline: Optional[str] = ""
    current_job_title: Optional[str] = ""
    current_employer: Optional[str] = ""
    profile_url: str = ""
    source_platform: str = "Web"
    profiles: List[Dict[str, Any]] = []
    subjects: List[str] = []
    pw_exclusion_status: Optional[str] = "ELIGIBLE"
    verification_status: str = "verified"
    notes: Optional[str] = ""
    saved_at: Optional[str] = None

class SavedEducatorsResponse(BaseModel):
    total: int
    items: List[SavedEducatorItem]

class EducatorDetailResponse(BaseModel):
    educator: Dict[str, Any]

class ExposureRecordRequest(BaseModel):
    educator_ids: List[str]
    search_run_id: Optional[str] = None
