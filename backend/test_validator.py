import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.validator import ValidatorService

def test_validator():
    print("Testing Evidence-Based Verification Layer...")
    
    # Mock data representing an educator and their profiles
    educator = {
        "educator_id": "mock-ed-1",
        "name": "Amit Dixit"
    }
    
    social_profiles = [
        {
            "platform": "Instagram",
            "raw_profile_data": {
                "platform_profiles": [{
                    "bio": "IIT-JEE Physics Faculty at XYZ Coaching."
                }]
            }
        },
        {
            "platform": "YouTube",
            "raw_profile_data": {
                "platform_profiles": [{
                    "description": "Welcome to my channel. We cover Physics for JEE and NEET."
                }]
            }
        },
        {
            "platform": "LinkedIn",
            "raw_profile_data": {
                "discovery_snippet": "Amit Dixit | Professor of Physics | Location: Lucknow, Uttar Pradesh",
                "platform_profiles": [{
                    "about": "Passionate about teaching."
                }]
            }
        }
    ]
    
    validator = ValidatorService()
    
    verification_results = validator.verify_educator(
        educator=educator,
        social_profiles=social_profiles,
        target_location="Lucknow",
        target_track="IIT-JEE",
        target_subject="Physics"
    )
    
    print("\n--- Validation Results ---")
    print(json.dumps(verification_results, indent=4))
    
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "verification_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(verification_results, f, indent=4)
        
    print(f"\nSaved verification results to {out_path}")

if __name__ == "__main__":
    test_validator()
