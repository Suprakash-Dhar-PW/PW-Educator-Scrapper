from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data

def test_api_v1_locations():
    res = client.get("/api/v1/locations")
    assert res.status_code == 200
    locations = res.json()
    assert isinstance(locations, list)
    assert "Lucknow" in locations
    assert "Kota" in locations

def test_api_v1_tracks_and_subjects():
    res_tracks = client.get("/api/v1/tracks")
    assert res_tracks.status_code == 200
    assert "IIT-JEE" in res_tracks.json()
    assert "NEET" in res_tracks.json()

    res_subjs = client.get("/api/v1/subjects?track=IIT-JEE")
    assert res_subjs.status_code == 200
    assert "Physics" in res_subjs.json()

def test_api_v1_educators_listing():
    res = client.get("/api/v1/educators?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_api_v1_saved_educators_crud():
    # 1. Fetch educators
    ed_res = client.get("/api/v1/educators?limit=1")
    assert ed_res.status_code == 200
    eds = ed_res.json()
    assert len(eds) > 0
    ed_id = eds[0]["id"]

    # 2. Save educator
    save_res = client.post(f"/api/v1/saved-educators/{ed_id}", json={"notes": "API test note"})
    assert save_res.status_code == 200

    # 3. List saved
    list_res = client.get("/api/v1/saved-educators")
    assert list_res.status_code == 200
    saved_items = list_res.json()["items"]
    assert any(item["id"] == ed_id for item in saved_items)

    # 4. Unsave
    del_res = client.delete(f"/api/v1/saved-educators/{ed_id}")
    assert del_res.status_code == 200
