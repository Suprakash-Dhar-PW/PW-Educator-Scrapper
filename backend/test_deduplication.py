import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.deduplication import DeduplicationService

def test_deduplication():
    print("Testing Educator Identity Resolution (Deduplication)...")
    
    # Mock profiles that should merge (Same name, same username across IG and YT)
    # Mock profiles that should NOT merge (Same name, different username/bio)
    
    mock_enriched_profiles = [
        {
            "candidate_id": "cand-1",
            "name": "Amit Dixit",
            "profile_url": "https://instagram.com/amit_physics",
            "platform_profiles": [{
                "platform": "Instagram",
                "url": "https://instagram.com/amit_physics",
                "username": "amit_physics",
                "bio": "Physics educator at Physics Wallah. My YouTube: youtube.com/amit_physics_yt"
            }]
        },
        {
            "candidate_id": "cand-2",
            "name": "Amit Dixit",
            "profile_url": "https://youtube.com/amit_physics_yt",
            "platform_profiles": [{
                "platform": "YouTube",
                "url": "https://youtube.com/amit_physics_yt",
                "channel_name": "amit_physics", # Exact username match
                "description": "Welcome to my physics channel."
            }]
        },
        {
            "candidate_id": "cand-3",
            "name": "Amit Dixit",
            "profile_url": "https://linkedin.com/in/amit-dixit-123",
            "platform_profiles": [{
                "platform": "LinkedIn",
                "url": "https://linkedin.com/in/amit-dixit-123",
                "name": "Amit Dixit",
                "about": "Just a normal software engineer, completely unrelated."
            }]
        }
    ]
    
    dedup_service = DeduplicationService(confidence_threshold=0.65)
    result = dedup_service.resolve_identities(mock_enriched_profiles)
    
    # Print educators
    print("\n--- Educators ---")
    for ed in result["educators"]:
        print(f"ID: {ed['educator_id']} | Name: {ed['name']} | Match Confidence: {ed['match_confidence']:.2f}")
        
    print("\n--- Social Profiles Mapping ---")
    for sp in result["social_profiles"]:
        print(f"Educator ID: {sp['educator_id']} -> Platform: {sp['platform']} ({sp['url']})")

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "resolved_identities.json")
    
    # Optional: remove raw_profile_data for clean JSON output
    clean_profiles = []
    for sp in result["social_profiles"]:
        clean_p = sp.copy()
        if "raw_profile_data" in clean_p:
            del clean_p["raw_profile_data"]
        clean_profiles.append(clean_p)
        
    final_output = {
        "educators": result["educators"],
        "social_profiles": clean_profiles
    }
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
        
    print(f"\nResolved identities saved to {out_path}")

if __name__ == "__main__":
    test_deduplication()
