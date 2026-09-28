import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class CacheService:
    def __init__(self, cache_file: str = "data/search_cache.json"):
        self.cache_file = cache_file
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
    def _load_cache(self) -> Dict[str, Any]:
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self, data: Dict[str, Any]):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get(self, key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        cache_data = self._load_cache()
        entry = cache_data.get(key)
        
        if not entry:
            return None
            
        timestamp_str = entry.get("timestamp")
        if not timestamp_str:
            return None
            
        try:
            cached_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            delta = (now - cached_time).total_seconds()
            
            if delta <= ttl_seconds:
                return entry
        except Exception as e:
            print(f"Cache time parsing error: {e}")
            
        return None

    def set(self, key: str, results: list):
        cache_data = self._load_cache()
        
        cache_data[key] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results
        }
        
        self._save_cache(cache_data)
