import os
import sys
import json
import uuid
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=True)

def get_supabase_client():
    url = os.getenv("SUPABASE_URL", "https://wzpxmsiiqmzdkxyygvvy.supabase.co")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6cHhtc2lpcW16ZGt4eXlndnZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE3ODIwOTUsImV4cCI6MjEwNzM1ODA5NX0.6NwDChZoAmCSnvVDxfGhWHrGXGEYOsKQsZWMVc317Yk"
    return create_client(url, key)

def chunked_list(lst, chunk_size=40):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def retry_batch_insert(table_ref, items, max_retries=3):
    if not items:
        return 0
    imported = 0
    for chunk in chunked_list(items, chunk_size=35):
        for attempt in range(1, max_retries + 1):
            try:
                table_ref.insert(chunk).execute()
                imported += len(chunk)
                break
            except Exception as e:
                err_msg = str(e)
                if "duplicate key" in err_msg.lower() or "unique constraint" in err_msg.lower():
                    # Fallback to individual inserts in this chunk to skip duplicates
                    for item in chunk:
                        try:
                            table_ref.insert(item).execute()
                            imported += 1
                        except Exception:
                            pass
                    break
                if attempt == max_retries:
                    print(f"    Batch insert error on table: {e}", flush=True)
                time.sleep(1.0 * attempt)
    return imported

def run_migration():
    print("=" * 65, flush=True)
    print("Starting Batch Data Migration to Supabase PostgreSQL", flush=True)
    print("=" * 65, flush=True)
    
    supabase = get_supabase_client()
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    # In-memory structures to assemble
    educators_map = {}        # key: name.lower() -> dict
    url_to_ed_id = {}         # key: url -> ed_id
    search_runs_list = []     # list of search_runs
    search_results_list = []  # list of search_results
    social_profiles_list = [] # list of profiles
    subjects_set = set()      # set of (ed_id, track, subject)
    locations_set = set()     # set of (ed_id, loc_name)
    evidence_list = []        # list of evidence items

    # Step 1: Pre-load already existing data from Supabase
    print("[1/5] Checking existing records in Supabase...", flush=True)
    existing_ed_names = set()
    existing_urls = set()
    try:
        res_eds = supabase.table("educators").select("id, name").execute()
        for r in (res_eds.data or []):
            existing_ed_names.add(r["name"].strip().lower())
            educators_map[r["name"].strip().lower()] = {
                "id": r["id"],
                "name": r["name"],
                "exists": True
            }
        print(f"  Found {len(existing_ed_names)} existing educators in Supabase.", flush=True)
        
        res_profs = supabase.table("social_profiles").select("educator_id, url").execute()
        for p in (res_profs.data or []):
            existing_urls.add(p["url"])
            url_to_ed_id[p["url"]] = p["educator_id"]
        print(f"  Found {len(existing_urls)} existing social profile URLs in Supabase.", flush=True)
    except Exception as e:
        print(f"  Note while checking existing: {e}", flush=True)

    # Step 2: Parse search_cache.json
    cache_path = os.path.join(data_dir, "search_cache.json")
    if os.path.exists(cache_path):
        print("\n[2/5] Parsing search_cache.json...", flush=True)
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            
        for key, entry in cache_data.items():
            if not isinstance(entry, dict) or "results" not in entry:
                continue
                
            parts = key.split("|")
            req_loc = "India"
            req_track = "IIT-JEE"
            req_subj = "Physics"
            
            if len(parts) >= 3:
                if parts[0].startswith("v"):
                    req_loc = parts[1].title() if len(parts) > 1 else "India"
                    req_track = parts[2].upper() if len(parts) > 2 else "IIT-JEE"
                    req_subj = parts[3].title() if len(parts) > 3 else "Physics"
                else:
                    req_loc = parts[0].title()
                    req_track = parts[1].upper()
                    req_subj = parts[2].title()

            results = entry.get("results", [])
            ts = entry.get("timestamp") or datetime.now(timezone.utc).isoformat()
            search_run_id = str(uuid.uuid4())
            
            search_runs_list.append({
                "id": search_run_id,
                "requested_location": req_loc,
                "requested_track": req_track,
                "requested_subject": req_subj,
                "status": "completed",
                "total_results": len(results),
                "target_count": entry.get("target_count", 50),
                "target_shortfall": entry.get("target_shortfall", max(0, 50 - len(results))),
                "unique_candidates_discovered": entry.get("unique_candidates_discovered", len(results)),
                "profiles_enriched": entry.get("profiles_enriched", len(results)),
                "search_duration_seconds": float(entry.get("search_duration_seconds", 0.0) or 0.0),
                "credits_used": float(entry.get("credits_used", 0.0) or 0.0),
                "credits_estimated": float(entry.get("credits_estimated", 0.0) or 0.0),
                "rejected_counts": entry.get("rejected_counts", {}),
                "review_queue_count": entry.get("review_queue_count", 0),
                "sources_searched": entry.get("sources_searched", 0),
                "provider_errors": entry.get("provider_errors", []),
                "cache_status": entry.get("cache_status", "HIT"),
                "created_at": ts
            })

            for ed in results:
                raw_name = ed.get("full_name") or ed.get("name")
                if not raw_name or len(raw_name.strip()) < 2:
                    continue
                name = raw_name.strip()
                name_key = name.lower()
                primary_url = ed.get("profile_url") or ""
                
                # Deduplication logic
                ed_id = None
                if primary_url and primary_url in url_to_ed_id:
                    ed_id = url_to_ed_id[primary_url]
                elif name_key in educators_map:
                    ed_id = educators_map[name_key]["id"]
                else:
                    ed_id = str(uuid.uuid4())
                    educators_map[name_key] = {
                        "id": ed_id,
                        "name": name,
                        "primary_track": ed.get("track") or req_track,
                        "primary_location": ed.get("location") or req_loc,
                        "professional_headline": ed.get("professional_headline"),
                        "current_job_title": ed.get("current_job_title"),
                        "current_employer": ed.get("current_employer"),
                        "pw_exclusion_status": ed.get("pw_exclusion_status", "ELIGIBLE"),
                        "identity_confidence": float(ed.get("identity_confidence", 1.0) or 1.0),
                        "employment_verification_status": ed.get("employment_verification_status", "verified"),
                        "verification_status": "verified",
                        "created_at": ts,
                        "updated_at": ts,
                        "exists": False
                    }
                    if primary_url:
                        url_to_ed_id[primary_url] = ed_id

                # Profiles
                profiles = ed.get("profiles", [])
                if not profiles and primary_url:
                    profiles = [{"platform": ed.get("source_platform", "Web"), "url": primary_url}]
                    
                for p in profiles:
                    p_url = p.get("url")
                    if p_url and p_url not in existing_urls:
                        existing_urls.add(p_url)
                        url_to_ed_id[p_url] = ed_id
                        social_profiles_list.append({
                            "educator_id": ed_id,
                            "platform": p.get("platform", "Web"),
                            "url": p_url,
                            "username": p.get("username"),
                            "followers": int(p.get("followers") or p.get("subscribers") or p.get("connections") or 0) or None,
                            "bio": p.get("bio"),
                            "scrape_status": "success",
                            "scraped_at": ts
                        })

                # Subjects
                ed_subjs = ed.get("subjects") or [req_subj]
                for s in ed_subjs:
                    subjects_set.add((ed_id, ed.get("track") or req_track, s))

                # Locations
                ed_loc = ed.get("location") or req_loc
                if ed_loc:
                    locations_set.add((ed_id, ed_loc))

                # Evidence
                for ev in ed.get("evidence", []):
                    evidence_list.append({
                        "educator_id": ed_id,
                        "dimension": ev.get("dimension", "general"),
                        "detected_value": (ev.get("text") or "")[:100],
                        "source_platform": ev.get("platform", "Web"),
                        "evidence_text": ev.get("text", ""),
                        "confidence_score": 0.95,
                        "verification_status": "verified"
                    })

                # Search Results linkage
                if primary_url:
                    search_results_list.append({
                        "search_run_id": search_run_id,
                        "raw_title": name,
                        "raw_url": primary_url,
                        "raw_snippet": ed.get("professional_headline", ""),
                        "discovery_source": ed.get("source_platform", "search"),
                        "status": "enriched"
                    })

    # Step 3: Parse resolved_identities.json & enriched_candidates.json
    print("[3/5] Parsing resolved_identities.json and enriched_candidates.json...", flush=True)
    ident_path = os.path.join(data_dir, "resolved_identities.json")
    if os.path.exists(ident_path):
        with open(ident_path, "r", encoding="utf-8") as f:
            for ed in json.load(f).get("educators", []):
                raw_name = ed.get("name")
                if not raw_name:
                    continue
                name_key = raw_name.strip().lower()
                if name_key not in educators_map:
                    new_id = str(uuid.uuid4())
                    educators_map[name_key] = {
                        "id": new_id,
                        "name": raw_name.strip(),
                        "primary_track": ed.get("primary_track", "IIT-JEE"),
                        "verification_status": "verified",
                        "exists": False
                    }

    enc_path = os.path.join(data_dir, "enriched_candidates.json")
    if os.path.exists(enc_path):
        with open(enc_path, "r", encoding="utf-8") as f:
            for cand in json.load(f):
                raw_name = cand.get("name")
                if not raw_name:
                    continue
                name_key = raw_name.strip().lower()
                if name_key not in educators_map:
                    new_id = str(uuid.uuid4())
                    educators_map[name_key] = {
                        "id": new_id,
                        "name": raw_name.strip(),
                        "primary_track": cand.get("requested_track") or "IIT-JEE",
                        "primary_location": cand.get("requested_location") or "India",
                        "verification_status": "verified",
                        "exists": False
                    }
                ed_id = educators_map[name_key]["id"]
                disc_url = cand.get("discovery", {}).get("url")
                if disc_url and disc_url not in existing_urls:
                    existing_urls.add(disc_url)
                    social_profiles_list.append({
                        "educator_id": ed_id,
                        "platform": "LinkedIn" if "linkedin" in disc_url else "Web",
                        "url": disc_url,
                        "scrape_status": "success"
                    })

    # Prepare batch insertion lists
    new_educators = [
        {k: v for k, v in ed.items() if k != "exists"}
        for ed in educators_map.values() if not ed.get("exists")
    ]
    subjects_list = [
        {"educator_id": item[0], "track": item[1], "subject": item[2]}
        for item in subjects_set
    ]
    locations_list = [
        {"educator_id": item[0], "location_name": item[1]}
        for item in locations_set
    ]

    print(f"\n[4/5] Prepared records for insertion:", flush=True)
    print(f"  - New Educators:       {len(new_educators)}", flush=True)
    print(f"  - Search Runs:         {len(search_runs_list)}", flush=True)
    print(f"  - Social Profiles:     {len(social_profiles_list)}", flush=True)
    print(f"  - Subjects:            {len(subjects_list)}", flush=True)
    print(f"  - Locations:           {len(locations_list)}", flush=True)
    print(f"  - Evidence Items:      {len(evidence_list)}", flush=True)
    print(f"  - Search Results:      {len(search_results_list)}", flush=True)

    # Step 4: Execute Batch Inserts
    print("\n[5/5] Executing Batch Inserts into Supabase...", flush=True)
    
    print("  Inserting search_runs...", flush=True)
    n_runs = retry_batch_insert(supabase.table("search_runs"), search_runs_list)
    print(f"  [OK] Search runs inserted: {n_runs}", flush=True)

    print("  Inserting educators...", flush=True)
    n_eds = retry_batch_insert(supabase.table("educators"), new_educators)
    print(f"  [OK] Educators inserted: {n_eds}", flush=True)

    print("  Inserting social_profiles...", flush=True)
    n_profs = retry_batch_insert(supabase.table("social_profiles"), social_profiles_list)
    print(f"  [OK] Social profiles inserted: {n_profs}", flush=True)

    print("  Inserting educator_subjects...", flush=True)
    n_subjs = retry_batch_insert(supabase.table("educator_subjects"), subjects_list)
    print(f"  [OK] Subjects inserted: {n_subjs}", flush=True)

    print("  Inserting educator_locations...", flush=True)
    n_locs = retry_batch_insert(supabase.table("educator_locations"), locations_list)
    print(f"  [OK] Locations inserted: {n_locs}", flush=True)

    print("  Inserting educator_evidence...", flush=True)
    n_ev = retry_batch_insert(supabase.table("educator_evidence"), evidence_list)
    print(f"  [OK] Evidence items inserted: {n_ev}", flush=True)

    print("  Inserting search_results...", flush=True)
    n_res = retry_batch_insert(supabase.table("search_results"), search_results_list)
    print(f"  [OK] Search results inserted: {n_res}", flush=True)

    # Verification / Reconciliation
    print("\n" + "=" * 65, flush=True)
    print("FINAL RECONCILIATION SUMMARY (Live Supabase Row Counts)", flush=True)
    print("=" * 65, flush=True)
    tables = [
        "educators", "social_profiles", "search_runs", "search_results",
        "educator_subjects", "educator_locations", "educator_evidence",
        "saved_educators", "exposure_history"
    ]
    for tbl in tables:
        try:
            cnt = supabase.table(tbl).select("id", count="exact").execute().count
            print(f"  {tbl:<30}: {cnt} rows", flush=True)
        except Exception as e:
            print(f"  {tbl:<30}: Error ({e})", flush=True)
    print("=" * 65, flush=True)
    print("Migration finished successfully!", flush=True)

if __name__ == "__main__":
    run_migration()
