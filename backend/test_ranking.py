import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ranking import RankingService

def test_ranking():
    print("Testing Transparent Educator Ranking System...")
    
    educator = {
        "educator_id": "mock-ed-1",
        "name": "Amit Dixit"
    }
    
    social_profiles = [
        {
            "platform": "Instagram",
            "raw_profile_data": {
                "platform_profiles": [{
                    "bio": "IIT-JEE Physics Faculty. 10 years of experience teaching students.",
                    "followers": 15000,
                    "name": "Amit Dixit",
                    "url": "https://instagram.com/amit_physics"
                }]
            }
        },
        {
            "platform": "LinkedIn",
            "raw_profile_data": {
                "platform_profiles": [{
                    "about": "Professor of Physics. Educator at top coaching institutes.",
                    "connections": 500,
                    "name": "Amit Dixit",
                    "url": "https://linkedin.com/in/amit_dixit"
                }]
            }
        }
    ]
    
    # Mocking the output from ValidatorService
    verification_results = {
        "location_verification": {
            "value": "Lucknow",
            "confidence": 0.4,
            "status": "uncertain",
            "evidence": [{"platform": "LinkedIn", "text": "Location: Lucknow"}]
        },
        "track_verification": {
            "value": "IIT-JEE",
            "confidence": 1.0,
            "status": "verified",
            "evidence": [{"platform": "Instagram", "text": "IIT-JEE Physics Faculty"}]
        },
        "subject_verification": {
            "value": "Physics",
            "confidence": 1.0,
            "status": "verified",
            "evidence": [{"platform": "Instagram", "text": "Physics Faculty"}, {"platform": "LinkedIn", "text": "Professor of Physics"}]
        }
    }
    
    ranking_service = RankingService()
    ranking_results = ranking_service.rank_educator(educator, social_profiles, verification_results)
    
    output = {
        "educator": educator,
        "ranking": ranking_results
    }
    
    print("\n--- Ranking Results ---")
    print(json.dumps(output, indent=4))
    
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "ranking_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)
        
    print(f"\nSaved ranking results to {out_path}")

if __name__ == "__main__":
    test_ranking()
