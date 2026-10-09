import requests
import time
import urllib.parse
from typing import Dict, Any, Optional
from app.core.config import settings

class AnakinScraperService:
    def __init__(self):
        self.api_base_url = "https://api.anakin.io/v1/scraper"
        self.api_key = settings.ANAKIN_API_KEY
        
    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
    @staticmethod
    def detect_platform(url: str) -> str:
        if not url:
            return "Other"
        try:
            domain = urllib.parse.urlparse(url).netloc.lower()
            if "instagram.com" in domain: return "Instagram"
            if "youtube.com" in domain or "youtu.be" in domain: return "YouTube"
            if "linkedin.com" in domain: return "LinkedIn"
            if "reddit.com" in domain: return "Reddit"
            if "facebook.com" in domain: return "Facebook"
            return "Other"
        except Exception:
            return "Other"

    def _create_fallback_response(self, url: str, platform: str, status: str = "failed") -> Dict[str, Any]:
        """Returns the conservative platform-specific fallback schema in case of failure."""
        base = {
            "platform": platform,
            "url": url,
            "scrape_status": status
        }
        
        if platform == "Instagram":
            base.update({"username": None, "followers": None, "bio": None})
        elif platform == "YouTube":
            base.update({"channel_name": None, "subscribers": None, "description": None})
        elif platform == "LinkedIn":
            base.update({"name": None, "followers": None, "connections": None, "about": None})
        elif platform == "Reddit":
            base.update({"username": None, "karma": None, "description": None})
        elif platform == "Facebook":
            base.update({"page_name": None, "likes": None, "followers": None, "about": None})
        else:
            base.update({"name": None, "description": None})
            
        return base

    def scrape_profile(self, url: str) -> Dict[str, Any]:
        platform = self.detect_platform(url)
        
        if not self.api_key:
            # Return empty fallback since API is not available
            return self._create_fallback_response(url, platform, status="failed")

        submit_endpoint = "https://api.anakin.io/v1/url-scraper"
        payload = {
            "url": url,
            "extraction_schema": {
                "name": "Full name of the person, if available",
                "username": "Username on the platform",
                "bio": "Biography or about section",
                "followers": "Number of followers (as integer)",
                "following": "Number of following (as integer)",
                "subscribers": "Number of subscribers (as integer)",
                "website": "Personal or business website URL",
                "location": "Geographical location, if explicitly stated",
                "headline": "Professional headline",
                "description": "Any additional description",
                "social_profiles": [
                    {
                        "platform": "Platform name (e.g. Instagram, YouTube, LinkedIn, Reddit, Facebook)",
                        "url": "URL of the social profile"
                    }
                ]
            }
        }
        
        try:
            response = requests.post(submit_endpoint, headers=self.get_headers(), json=payload, timeout=10)
            response.raise_for_status()
            job_data = response.json()
            import logging
            logging.getLogger("anakin_scraper").info(f"[SCRAPE INITIATED] URL: {url} | Job ID: {job_data.get('id') or job_data.get('job_id')}")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            error_msg = e.response.text if e.response else str(e)
            import logging
            logging.getLogger("anakin_scraper").error(f"[SCRAPE HTTP ERROR] Provider: Anakin API | Status: {status_code} | URL: {url} | Response: {error_msg}")
            return self._create_fallback_response(url, platform, status="failed")
        except requests.exceptions.RequestException as e:
            import logging
            logging.getLogger("anakin_scraper").error(f"[SCRAPE REQUEST ERROR] Provider: Anakin API | URL: {url} | Error: {str(e)}")
            return self._create_fallback_response(url, platform, status="failed")
            
        job_id = job_data.get("id") or job_data.get("job_id") or job_data.get("jobId")
        if not job_id:
            return self._create_fallback_response(url, platform, status="failed")

        poll_endpoint = f"https://api.anakin.io/v1/url-scraper/{job_id}"
        
        for attempt in range(12):
            try:
                time.sleep(5) 
                poll_response = requests.get(poll_endpoint, headers=self.get_headers(), timeout=10)
                poll_response.raise_for_status()
                status_data = poll_response.json()
                
                status = status_data.get("status", "").lower()
                
                if status in ["completed", "success"]:
                    return self._extract_structured_info(status_data, url, platform)
                elif status in ["failed", "error"]:
                    return self._create_fallback_response(url, platform, status="failed")
                
            except requests.exceptions.RequestException:
                continue

        return self._create_fallback_response(url, platform, status="timeout")

    def _extract_structured_info(self, result_data: Dict[str, Any], url: str, platform: str) -> Dict[str, Any]:
        content = result_data.get("result", result_data.get("data", result_data))
        
        import logging
        logger = logging.getLogger("anakin_scraper")
        
        try:
            base = {
                "platform": platform,
                "url": url,
                "scrape_status": "success",
                "name": content.get("name"),
                "username": content.get("username"),
                "bio": content.get("bio") or content.get("description"),
                "followers": content.get("followers") or content.get("subscribers"),
                "following": content.get("following"),
                "website": content.get("website"),
                "location": content.get("location"),
                "headline": content.get("headline"),
                "description": content.get("description")
            }
            
            # Extract social profiles
            social_profiles = content.get("social_profiles", [])
            valid_socials = []
            if isinstance(social_profiles, list):
                for sp in social_profiles:
                    sp_platform = sp.get("platform")
                    sp_url = sp.get("url")
                    if sp_platform and sp_url:
                        valid_socials.append({"platform": sp_platform, "url": sp_url})
                        logger.info(f"[PROFILE LINK FOUND] {sp_platform}: {sp_url}")
                        
            base["social_profiles"] = valid_socials
            return base
            
        except Exception as e:
            logger.error(f"Error extracting data from raw result for {url}: {e}")
            return self._create_fallback_response(url, platform, status="malformed_response")
