import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import urllib.parse

class Candidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    username: Optional[str] = None
    platform: str = ""
    profile_url: str = ""
    location: Optional[str] = None
    track: str = ""
    subject: str = ""
    bio: Optional[str] = None
    description: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    website: Optional[str] = None
    discovery_source: str = "anakin_search"
    discovery_query: str = ""
    discovery_snippet: str = ""
    verified: bool = False
    verification_status: str = "unverified"
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class CandidateNormalizer:
    
    @staticmethod
    def detect_platform(url: str) -> str:
        if not url:
            return "Other"
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            if "instagram.com" in domain:
                return "Instagram"
            elif "youtube.com" in domain or "youtu.be" in domain:
                return "YouTube"
            elif "linkedin.com" in domain:
                return "LinkedIn"
            elif "reddit.com" in domain:
                return "Reddit"
            elif "facebook.com" in domain:
                return "Facebook"
            else:
                return "Other"
        except Exception:
            return "Other"
            
    @staticmethod
    def extract_name(title: str) -> str:
        # Simple extraction: usually titles are "Name - Something" or "Name | Something"
        if not title:
            return ""
        
        # We try to split by common separators
        for sep in [" - ", " | ", " \u2013 ", " \u2014 "]:
            if sep in title:
                return title.split(sep)[0].strip()
        
        return title.strip()

    def normalize(
        self, 
        raw_result: Dict[str, Any], 
        track: str, 
        subject: str, 
        discovery_query: str
    ) -> Candidate:
        url = raw_result.get("url", "")
        platform = self.detect_platform(url)
        title = raw_result.get("title", "")
        name = self.extract_name(title)
        
        # Do not infer location or subject/track beyond what is explicitly provided.
        # Ensure we only map fields that exist or are given.
        
        return Candidate(
            name=name,
            platform=platform,
            profile_url=url,
            track=track,
            subject=subject,
            discovery_query=discovery_query,
            discovery_snippet=raw_result.get("snippet", ""),
            raw_data=raw_result
        )
