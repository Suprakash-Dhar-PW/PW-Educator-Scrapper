import os
import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Query, HTTPException

router = APIRouter()
filters_router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "locations.db")

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

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=503, detail="Location database not available")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Core helper functions
def list_supported_locations():
    return sorted(SUPPORTED_LOCATIONS)

def list_tracks():
    return list(VALID_TRACKS.keys())

def list_subjects_for_track(track: str):
    if track not in VALID_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid track. Allowed: {list(VALID_TRACKS.keys())}")
    return VALID_TRACKS[track]

# Location database routes (prefixed under /locations)
@router.get("/", response_model=List[str])
@router.get("", response_model=List[str])
def get_locations_list():
    return list_supported_locations()

@router.get("/states", response_model=List[Dict[str, str]])
async def get_states():
    """Get all Indian states from the GeoNames locations database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, name FROM states ORDER BY name ASC")
    states = [{"code": row["code"], "name": row["name"]} for row in cursor.fetchall()]
    conn.close()
    return states

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_locations(
    query: str = Query("", description="Search term for city/town"),
    state_code: str = Query(None, description="Optional state code to filter by")
):
    """Fast typeahead city/town autocompletion from GeoNames database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT geonameid, name, admin1_code, population FROM locations WHERE name LIKE ? "
    params = [f"{query}%"]
    if state_code:
        sql += " AND admin1_code = ? "
        params.append(state_code)
    sql += " ORDER BY population DESC LIMIT 50"
    cursor.execute(sql, params)
    results = [
        {
            "id": row["geonameid"],
            "name": row["name"],
            "state_code": row["admin1_code"],
            "population": row["population"]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return results

# Filter routes (mounted at /tracks, /subjects, /locations)
@filters_router.get("/locations", response_model=List[str])
def filter_locations():
    return list_supported_locations()

@filters_router.get("/tracks", response_model=List[str])
def filter_tracks():
    return list_tracks()

@filters_router.get("/subjects", response_model=List[str])
def filter_subjects(track: str = Query(..., description="Track name like IIT-JEE or NEET")):
    return list_subjects_for_track(track)
