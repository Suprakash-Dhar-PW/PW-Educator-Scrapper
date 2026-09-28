import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.enrichment import EnrichmentService

def test_enrichment_pipeline():
    print("Testing Batch Enrichment Pipeline...")
    
    # Simulate a list of normalized candidates (some with duplicate URLs)
    mock_normalized_candidates = [
        {
            "candidate_id": "1111-2222-3333-4444",
            "name": "Alakh Pandey",
            "platform": "LinkedIn",
            "profile_url": "https://www.linkedin.com/in/alakh-pandey",
            "location": "Lucknow, Uttar Pradesh",
            "track": "IIT-JEE",
            "subject": "Physics",
            "discovery_source": "anakin_search",
            "discovery_snippet": "Prominent educator...",
            "raw_data": {
                "title": "Alakh Pandey - Physics Wallah | LinkedIn",
                "url": "https://www.linkedin.com/in/alakh-pandey"
            }
        },
        {
            "candidate_id": "duplicate-5555",
            "name": "Alakh Duplicate",
            "platform": "LinkedIn",
            "profile_url": "https://www.linkedin.com/in/alakh-pandey", # Duplicate URL
            "location": "Lucknow, Uttar Pradesh",
            "track": "IIT-JEE",
            "subject": "Physics",
            "discovery_source": "anakin_search",
            "discovery_snippet": "Duplicate entry...",
            "raw_data": {
                "title": "Alakh Pandey duplicate",
                "url": "https://www.linkedin.com/in/alakh-pandey"
            }
        },
        {
            "candidate_id": "5555-6666-7777-8888",
            "name": "Physics Wallah",
            "platform": "Instagram",
            "profile_url": "https://www.instagram.com/physicswallah/",
            "location": "Lucknow, Uttar Pradesh",
            "track": "IIT-JEE",
            "subject": "Physics",
            "discovery_source": "anakin_search",
            "discovery_snippet": "Instagram official profile",
            "raw_data": {
                "title": "Physics Wallah Official",
                "url": "https://www.instagram.com/physicswallah/"
            }
        }
    ]
    
    service = EnrichmentService()
    enriched = service.enrich_candidates(mock_normalized_candidates)
    
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "enriched_candidates.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=4)
        
    print(f"\nPipeline finished. Output saved to {out_path}")

if __name__ == "__main__":
    test_enrichment_pipeline()
