import os
import json
import sys

# Ensure backend folder is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.anakin_search import AnakinSearchService
from app.core.config import settings

def run_test():
    # Setup mock API key if none exists just to run the test and show the dummy output
    # or rely on the try-except in the service.
    
    print("Testing Anakin Search API...")
    
    location = "Lucknow, Uttar Pradesh"
    track = "IIT-JEE"
    subject = "Physics"
    
    search_service = AnakinSearchService()
    
    print(f"Location: {location}")
    print(f"Track: {track}")
    print(f"Subject: {subject}\n")
    
    try:
        results = search_service.search_educators(location, track, subject)
    except ValueError as e:
        print(f"Setup Issue: {e}")
        print("Temporarily setting a dummy ANAKIN_API_KEY for the test...")
        search_service.api_key = "dummy_key_for_test"
        results = search_service.search_educators(location, track, subject)

    raw_response = results.get("raw_response", {})
    normalized_candidates = results.get("normalized_candidates", [])
    
    # Save raw response
    raw_path = os.path.join("data", "raw_search_results.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_response, f, indent=4)
        
    print(f"Saved raw results to: {raw_path}")
    
    # Save normalized response
    norm_path = os.path.join("data", "discovered_candidates.json")
    with open(norm_path, "w", encoding="utf-8") as f:
        json.dump(normalized_candidates, f, indent=4)
        
    print(f"Saved normalized candidates to: {norm_path}")
    
if __name__ == "__main__":
    run_test()
