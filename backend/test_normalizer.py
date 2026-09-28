import os
import json
import sys

# Ensure backend folder is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.normalizer import CandidateNormalizer

def test_normalization():
    print("Testing Candidate Normalizer...")
    
    mock_raw_results = [
        {
            "title": "Alakh Pandey - Physics Wallah | LinkedIn",
            "url": "https://www.linkedin.com/in/alakh-pandey",
            "snippet": "Alakh Pandey is a prominent Physics educator...",
            "date": "2023-10-01",
            "last_updated": "2023-10-15"
        },
        {
            "title": "Rajwant Singh - Physics | YouTube",
            "url": "https://www.youtube.com/rajwant-physics",
            "snippet": "Top IIT-JEE Physics educator...",
            "date": "2023-10-05",
            "last_updated": "2023-10-16"
        },
        {
            "title": "Educators - IIT School",
            "url": "https://www.iitschool.in/pages/educators",
            "snippet": "Learn from India's Most Trusted IIT Educators",
            "date": "",
            "last_updated": ""
        }
    ]
    
    track = "IIT-JEE"
    subject = "Physics"
    query = "Find IIT-JEE Physics educators and teachers in Lucknow."
    
    normalizer = CandidateNormalizer()
    normalized_candidates = []
    
    for raw in mock_raw_results:
        candidate = normalizer.normalize(
            raw_result=raw,
            track=track,
            subject=subject,
            discovery_query=query
        )
        normalized_candidates.append(candidate.model_dump())
        
    # Output to verify
    for cand in normalized_candidates:
        print(f"\n--- Candidate: {cand['name']} ---")
        print(f"Platform: {cand['platform']}")
        print(f"URL: {cand['profile_url']}")
        print(f"Verified: {cand['verified']} ({cand['verification_status']})")
        
    # Save the output for inspection
    out_path = os.path.join("data", "normalized_test_output.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized_candidates, f, indent=4)
        
    print(f"\nSaved normalized test output to {out_path}")

if __name__ == "__main__":
    test_normalization()
