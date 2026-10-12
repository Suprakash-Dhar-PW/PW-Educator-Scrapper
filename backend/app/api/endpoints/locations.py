from fastapi import APIRouter, Query, HTTPException
import sqlite3
from typing import List, Dict, Any
import os

router = APIRouter()

DB_PATH = "data/locations.db"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=503, detail="Location database not ready")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/states", response_model=List[Dict[str, str]])
async def get_states():
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "SELECT geonameid, name, admin1_code, population FROM locations WHERE name LIKE ? "
    params = [f"{query}%"]
    
    if state_code:
        sql += " AND admin1_code = ? "
        params.append(state_code)
        
    sql += " ORDER BY population DESC LIMIT 50"
    
    cursor.execute(sql, params)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row["geonameid"],
            "name": row["name"],
            "state_code": row["admin1_code"],
            "population": row["population"]
        })
        
    conn.close()
    return results
