from pydantic import BaseModel, root_validator
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    location: str
    track: str
    subject: str
    force_refresh: bool = False

class SearchResult(BaseModel):
    educator_id: str
    name: str
    location: str
    track: str
    subjects: List[str] = []
    profiles: List[Dict[str, Any]] = []
    scores: Dict[str, Any] = {}
    evidence: List[Dict[str, Any]] = []

class SearchResponse(BaseModel):
    query: Dict[str, str]
    total_results: int
    target_reached: bool = False
    last_updated: str
    results: List[SearchResult]
