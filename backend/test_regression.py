import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import json
from datetime import datetime, timezone

client = TestClient(app)

@pytest.fixture
def mock_cache(monkeypatch):
    cache_store = {}
    class DummyCache:
        def get(self, key, ttl=None):
            return cache_store.get(key)
        def set(self, key, value, ttl=None):
            if isinstance(value, list):
                cache_store[key] = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "results": value
                }
            else:
                cache_store[key] = value
    
    mock_service = DummyCache()
    monkeypatch.setattr("app.api.endpoints.discovery.cache_service", mock_service)
    return cache_store

def test_invalid_track_or_subject():
    # Invalid track
    res = client.post("/api/search", json={
        "location": "Lucknow", "track": "INVALID", "subject": "Physics", "force_refresh": True
    })
    assert res.status_code == 400
    assert "Invalid track" in res.json()["detail"]

    # Invalid subject for valid track
    res = client.post("/api/search", json={
        "location": "Lucknow", "track": "IIT-JEE", "subject": "Biology", "force_refresh": True
    })
    assert res.status_code == 400
    assert "Invalid subject" in res.json()["detail"]

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
@patch("app.api.endpoints.discovery.enrichment.enrich_candidates")
def test_successful_search_multiple(mock_enrich, mock_exec, mock_get):
    mock_get.return_value = [("LinkedIn", "q1")]
    mock_exec.return_value = [
        {"name": "Edu 1", "platform": "LinkedIn", "profile_url": "http://1", "snippet": "A", "discovery_source": "test"},
        {"name": "Edu 2", "platform": "YouTube", "profile_url": "http://2", "snippet": "B", "discovery_source": "test"}
    ]
    
    mock_enrich.return_value = [
        {
            "candidate_id": "1", "name": "Edu 1", "requested_location": "Lucknow", "requested_track": "IIT-JEE", "requested_subject": "Physics",
            "discovery": {"source": "test", "url": "http://1", "snippet": "A"},
            "platform_profiles": [{"platform": "LinkedIn", "url": "http://1", "scrape_status": "success", "followers": 100}]
        },
        {
            "candidate_id": "2", "name": "Edu 2", "requested_location": "Lucknow", "requested_track": "IIT-JEE", "requested_subject": "Physics",
            "discovery": {"source": "test", "url": "http://2", "snippet": "B"},
            "platform_profiles": [{"platform": "YouTube", "url": "http://2", "scrape_status": "success", "subscribers": 500}]
        }
    ]
    
    res = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
def test_all_providers_failing(mock_exec, mock_get):
    mock_get.return_value = [("LinkedIn", "q1")]
    mock_exec.side_effect = Exception("All providers blocked")
    
    # Since we catch execution errors and log them, it doesn't 500, it just continues and returns 0 results
    res = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    assert res.json()["total_results"] == 0

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
def test_search_zero_candidates_cache_logic(mock_exec, mock_get, mock_cache):
    mock_get.return_value = [("LinkedIn", "q1")]
    mock_exec.return_value = []
    
    res = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    assert res.json()["total_results"] == 0
    
    cache_key = "lucknow|iit-jee|physics"
    assert cache_key in mock_cache
    assert mock_cache[cache_key]["results"] == []

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
@patch("app.api.endpoints.discovery.enrichment.enrich_candidates")
def test_enrichment_failing_keeps_candidates(mock_enrich, mock_exec, mock_get):
    mock_get.return_value = [("LinkedIn", "q1")]
    mock_exec.return_value = [
        {"name": "Edu 1", "platform": "LinkedIn", "profile_url": "http://1", "snippet": "A", "discovery_source": "test"}
    ]
    
    mock_enrich.return_value = [
        {
            "candidate_id": "1", "name": "Edu 1", "requested_location": "Lucknow", "requested_track": "IIT-JEE", "requested_subject": "Physics",
            "discovery": {"source": "test", "url": "http://1", "snippet": "A"},
            "platform_profiles": [{"platform": "LinkedIn", "url": "http://1", "scrape_status": "failed"}]
        }
    ]
    
    res = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    assert res.json()["total_results"] == 1
    assert res.json()["results"][0]["name"] == "Edu 1"

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
@patch("app.api.endpoints.discovery.enrichment.enrich_candidates")
def test_cache_hit_miss_and_force_refresh(mock_enrich, mock_exec, mock_get, mock_cache):
    mock_get.return_value = [("LinkedIn", "q1")]
    mock_exec.return_value = [{"name": "Edu Cache", "platform": "LinkedIn", "profile_url": "http://c", "snippet": "C", "discovery_source": "test"}]
    mock_enrich.return_value = [{
        "candidate_id": "1", "name": "Edu Cache", "requested_location": "Lucknow", "requested_track": "IIT-JEE", "requested_subject": "Physics",
        "discovery": {"source": "test", "url": "http://c", "snippet": "C"},
        "platform_profiles": [{"platform": "LinkedIn", "url": "http://c", "scrape_status": "success"}]
    }]
    
    res1 = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res1.json()["total_results"] == 1
    assert mock_exec.call_count == 1
    
    res2 = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": False})
    assert res2.json()["total_results"] == 1
    assert mock_exec.call_count == 1
    
    res3 = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res3.json()["total_results"] == 1
    assert mock_exec.call_count == 2

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
@patch("app.api.endpoints.discovery.enrichment.enrich_candidates")
def test_one_platform_fails_others_succeed(mock_enrich, mock_exec, mock_get):
    mock_get.return_value = [("LinkedIn", "linkedin q"), ("YouTube", "youtube q")]
    
    def side_effect(platform, prompt, loc, track, sub):
        if platform == "LinkedIn":
            raise Exception("LinkedIn blocked")
        return [{"name": "Edu YouTube", "platform": "YouTube", "profile_url": "http://youtube.com/user1", "snippet": "Snippet", "discovery_source": "test"}]
        
    mock_exec.side_effect = side_effect
    
    mock_enrich.return_value = [
        {
            "candidate_id": "1", "name": "Edu YouTube", "requested_location": "Lucknow", "requested_track": "IIT-JEE", "requested_subject": "Physics",
            "discovery": {"source": "test", "url": "http://youtube.com/user1", "snippet": "Snippet"},
            "platform_profiles": [{"platform": "YouTube", "url": "http://youtube.com/user1", "scrape_status": "success"}]
        }
    ]
    
    res = client.post("/api/search", json={"location": "Lucknow", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    assert res.json()["total_results"] > 0
    assert any(r["platform"] == "YouTube" for r in res.json()["results"][0]["profiles"])

@patch("app.api.endpoints.discovery.search_service.get_queries")
@patch("app.api.endpoints.discovery.search_service.execute_query")
@patch("app.api.endpoints.discovery.enrichment.enrich_candidates")
def test_target_15_educators(mock_enrich, mock_exec, mock_get):
    # Setup 16 queries
    mock_get.return_value = [(f"Plat{i}", f"q{i}") for i in range(16)]
    
    # Each query returns 1 valid candidate
    def mock_exec_side_effect(platform, prompt, loc, track, sub):
        idx = prompt.replace("q", "")
        return [{"name": f"Edu {idx}", "platform": platform, "profile_url": f"http://{idx}", "snippet": "A", "discovery_source": "test"}]
        
    mock_exec.side_effect = mock_exec_side_effect
    
    # Enrichment passes candidate directly
    def mock_enrich_side_effect(candidates):
        res = []
        for c in candidates:
            idx = c["profile_url"].replace("http://", "")
            res.append({
                "candidate_id": idx, "name": c["name"], "requested_location": "Bengaluru", "requested_track": "IIT-JEE", "requested_subject": "Physics",
                "discovery": {"source": "test", "url": c["profile_url"], "snippet": "A"},
                "platform_profiles": [{"platform": c["platform"], "url": c["profile_url"], "scrape_status": "success", "followers": 100}]
            })
        return res
        
    mock_enrich.side_effect = mock_enrich_side_effect
    
    res = client.post("/api/search", json={"location": "Bengaluru", "track": "IIT-JEE", "subject": "Physics", "force_refresh": True})
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] >= 15 # Because batch size is 4, it may hit 16 before stopping
    assert data["target_reached"] == True

