import os
import json
import sys

# Ensure backend folder is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.anakin_scraper import AnakinScraperService
from app.core.config import settings

def test_scraper():
    print("Testing Anakin URL Scraper...")
    
    # We will test an instagram URL
    test_url = "https://www.instagram.com/physicswallah/"
    
    scraper = AnakinScraperService()
    
    print(f"Submitting URL for scraping: {test_url}")
    
    # Execute the scrape
    result = scraper.scrape_profile(test_url)
    
    # Ensure our directory exists
    os.makedirs("data/scraped_profiles", exist_ok=True)
    
    # Save the output
    out_path = os.path.join("data", "scraped_profiles", "test_profile_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
        
    print("\n--- Scraper Result ---")
    print(json.dumps(result, indent=4))
    print(f"\nSaved scraped profile to {out_path}")

if __name__ == "__main__":
    test_scraper()
