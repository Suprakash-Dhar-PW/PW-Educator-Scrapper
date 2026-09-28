import requests
import json
import time

def test_search():
    print("Testing Educator Discovery Pipeline...")
    url = "http://127.0.0.1:8000/api/search"
    payload = {
        "location": "Lucknow, Uttar Pradesh",
        "track": "IIT-JEE",
        "subject": "Physics",
        "force_refresh": True
    }
    
    start = time.time()
    response = requests.post(url, json=payload)
    end = time.time()
    
    print(f"Request completed in {end - start:.2f} seconds")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
        
    data = response.json()
    results = data.get("results", [])
    
    print(f"\nFound {len(results)} educators\n")
    print("="*60)
    
    for ed in results:
        print(f"Name: {ed.get('name')}")
        print(f"Location: {ed.get('location')}")
        print(f"Track: {ed.get('track')}")
        print(f"Subject: {', '.join(ed.get('subjects', []))}")
        
        profiles = ed.get("profiles", [])
        print("\nPlatforms:")
        for p in profiles:
            platform = p.get("platform")
            p_url = p.get("url")
            followers = p.get("followers") or p.get("subscribers") or p.get("connections")
            f_text = f" ({followers} audience)" if followers else ""
            print(f"- {platform}: {p_url}{f_text}")
            
        print(f"\nRelevance score: {ed.get('scores', {}).get('overall')}")
        
        print("\nVerification status:")
        for ev in ed.get("evidence", []):
            print(f"- [{ev.get('dimension')}] ({ev.get('platform')}): {ev.get('text')}")
            
        print("="*60)

if __name__ == "__main__":
    test_search()
