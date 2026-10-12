# PW-Mentor-Search — Educator Discovery Platform

A production-ready Full-Stack Educator Discovery Platform for recruiting top-tier IIT-JEE and NEET faculties, mentors, and educators across India.

Backed by **Supabase PostgreSQL** as the primary persistent source of truth, a layered **FastAPI** backend with automated verification and deduplication pipelines, and a modern **React + Vite** frontend.

---

## Architecture Overview

```
┌─────────────────────────┐
│ React + TypeScript UI   │  (Clean, focused discovery, shortlist, compare)
└───────────┬─────────────┘
            │ HTTP / JSON
┌───────────▼─────────────┐
│ FastAPI Backend Engine  │  (app/main.py, app/api/v1/)
└─────┬──────────────┬────┘
      │              │
┌─────▼────────┐  ┌──▼───────────────────┐
│ Repositories │  │ Discovery Pipeline   │
└─────┬────────┘  └──┬───────────────────┘
      │              │ - Search Adapters (DDGS, Anakin)
      │              │ - Identity Normalizer & Deduplicator
      │              │ - Strict Verification (PW Exclusions, Student Exclusions)
      │              │ - Ranking & Evidence Extractor
┌─────▼────────────────────────┐
│ Supabase PostgreSQL Database │  (Educator Discovery Org / wzpxmsiiqmzdkxyygvvy)
│ • educators                  │  (Canonical verified educators)
│ • social_profiles            │  (LinkedIn, YouTube, Instagram profiles)
│ • search_runs                │  (Search audit metadata & metrics)
│ • search_results             │  (Raw & enriched candidates)
│ • educator_subjects          │  (Track-subject mappings)
│ • educator_locations         │  (Operating cities)
│ • educator_evidence          │  (Verified proof & citations)
│ • saved_educators            │  (Recruiter shortlisted candidates)
│ • exposure_history           │  (Seen profile tracking & deduplication)
└──────────────────────────────┘
```

---

## Key Features & Production Improvements

1. **Supabase PostgreSQL as Source of Truth**:
   - Application data is persisted in a centralized Supabase database.
   - Idempotent data migration script migrated all historic records from `search_cache.json`, `resolved_identities.json`, and `enriched_candidates.json`.
   - Backup of pre-migration data preserved in `backend/data_backup_pre_supabase/`.

2. **Strict Educator Quality & Exclusions**:
   - **Physics Wallah Exclusion**: Strict exclusion of current and former PW faculty and Vidyapeeth educators (e.g., Tushar Kumar).
   - **Role Verification**: Students, aspirants, and non-mentors (e.g., Pg Haritha) are excluded from teacher search results.
   - **Institution Exclusion**: Official accounts and coaching channels (e.g., IIT Hyderabad_Official) are excluded from individual educator listings.

3. **Simple, Professional UI**:
   - Clean Discover Educators screen focusing on core inputs: Location, Exam Track, and Subject.
   - No numerical relevance scores, score badges, or tooltips in the user-facing cards.
   - Comprehensive evidence viewer modal and multi-educator comparison matrix.
   - Persistent Saved Educators shortlist backed by Supabase.

4. **Layered FastAPI Architecture**:
   - Versioned endpoints under `/api/v1/` with full backward-compatibility aliases under `/api/`.
   - Centralized configuration with Pydantic BaseSettings in `backend/app/core/config.py`.
   - Structured exception handling and logging with unique request IDs in `backend/app/core/exceptions.py`.
   - Repository layer isolating Supabase PostgreSQL queries from HTTP routers.

---

## Repository Structure

```text
PW-Mentor-Search/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry point
│   │   ├── api/
│   │   │   ├── routes.py               # Top-level API router & backward-compat aliases
│   │   │   └── v1/
│   │   │       ├── router.py           # v1 aggregation router
│   │   │       └── endpoints/
│   │   │           ├── health.py       # Lightweight health & DB connectivity check
│   │   │           ├── locations.py    # Typeahead search & Indian city lists
│   │   │           ├── educators.py    # Supabase educator listings & details
│   │   │           ├── saved_educators.py # Shortlist persistence
│   │   │           └── searches.py     # Discovery & search pipeline orchestrator
│   │   ├── core/
│   │   │   ├── config.py               # Centralized settings & env configuration
│   │   │   ├── database.py             # Supabase client singleton & health check
│   │   │   └── exceptions.py           # Centralized exception classes & handlers
│   │   ├── repositories/
│   │   │   ├── educator_repository.py  # Supabase educators & relations CRUD
│   │   │   ├── saved_educator_repository.py # Shortlist management in Supabase
│   │   │   └── search_repository.py    # Search runs & exposure history
│   │   ├── services/
│   │   │   ├── anakin_search.py        # Search provider query builder
│   │   │   ├── anakin_scraper.py       # Profile web scraper
│   │   │   ├── normalizer.py           # Candidate payload normalizer
│   │   │   ├── deduplication.py        # Identity resolution
│   │   │   ├── validator.py            # Eligibility, PW exclusion, student exclusion
│   │   │   ├── ranking.py              # Candidate ranking engine
│   │   │   └── cache.py                # Local in-memory/file temporary cache
│   │   └── schemas/
│   │       └── educator.py             # Pydantic request & response models
│   ├── data/                           # Runtime reference data (locations.db GeoNames)
│   ├── data_backup_pre_supabase/       # Pre-migration raw data backup
│   ├── scripts/
│   │   └── migrate_local_data_to_supabase.py # Idempotent batch migration script
│   ├── tests/                          # Automated pytest suite (25 tests)
│   ├── pytest.ini                      # Pytest configuration
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── App.tsx                     # Main React dashboard & views
│   │   ├── apiClient.ts                # Centralized typed HTTP API client
│   │   └── main.tsx                    # React DOM entry point
│   ├── package.json                    # Node dependencies
│   ├── vite.config.ts                  # Vite build & proxy configuration
│   └── .env.example                    # Frontend environment template
├── supabase/
│   └── migrations/
│       ├── 00000000000000_initial_schema.sql         # Base PostgreSQL schema
│       └── 00000000000001_saved_and_exposure_schema.sql # Shortlist, exposure, & RLS
├── .env.example                        # Root environment reference
└── README.md                           # Master documentation
```

---

## Database & Supabase Configuration

- **Organization**: `Educator-Discovery`
- **Project Ref**: `wzpxmsiiqmzdkxyygvvy`
- **Project Name**: `suprakashdhar10@gmail.com's Project`
- **Region**: `ap-south-1` (Mumbai)
- **Database Tables**:
  - `educators`: Canonical person records, headline, employer, PW exclusion status.
  - `social_profiles`: Public profile URLs, platforms, follower counts.
  - `educator_subjects`: Associated subjects and exam tracks.
  - `educator_locations`: Operating cities.
  - `educator_evidence`: Extracted textual citations proving qualifications.
  - `educator_scores`: Multi-dimensional calculated component metrics.
  - `search_runs`: Full search query execution audit log.
  - `search_results`: Discovered candidate linkages.
  - `saved_educators`: Recruiter shortlisted candidates with custom notes.
  - `exposure_history`: Log of displayed candidate cards to prevent repeat exposures.

### Running Migrations

Database schema changes are managed via version-controlled SQL files in `supabase/migrations/`:

```sql
-- 00000000000000_initial_schema.sql         (Initial tables, indexes, constraints)
-- 00000000000001_saved_and_exposure_schema.sql (saved_educators, exposure_history, RLS)
```

To run the local data migration script into Supabase:
```bash
cd backend
python scripts/migrate_local_data_to_supabase.py
```

---

## API Endpoints

### Versioned API (`/api/v1/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Lightweight service and database connectivity check |
| `GET` | `/api/v1/locations` | Supported discovery cities across India |
| `GET` | `/api/v1/locations/search` | Typeahead town/city search against 550,000+ GeoNames SQLite records |
| `GET` | `/api/v1/locations/states` | List Indian states |
| `GET` | `/api/v1/tracks` | Supported exam tracks (`IIT-JEE`, `NEET`) |
| `GET` | `/api/v1/subjects?track=IIT-JEE` | Supported subjects for a given track |
| `GET` | `/api/v1/educators` | Query verified educators from Supabase with pagination |
| `GET` | `/api/v1/educators/{id}` | Retrieve comprehensive educator details and verified evidence |
| `GET` | `/api/v1/saved-educators` | Retrieve all recruiter shortlisted educators |
| `POST` | `/api/v1/saved-educators/{id}` | Save an educator to the shortlist with optional notes |
| `DELETE` | `/api/v1/saved-educators/{id}` | Remove an educator from the shortlist |
| `POST` | `/api/v1/searches/search` | Execute candidate discovery, validation, and persistence |
| `GET` | `/api/v1/searches/history` | Audit log of recent search runs |
| `POST` | `/api/v1/searches/exposure` | Record candidate card display events |

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- A connected Supabase project

### Backend Setup
1. Open terminal in `backend/`:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `backend/.env.example` to `backend/.env` and verify keys:
   ```env
   SUPABASE_URL=https://wzpxmsiiqmzdkxyygvvy.supabase.co
   SUPABASE_KEY=<your-supabase-anon-key>
   ANAKIN_API_KEY=ask_<your-anakin-key>
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Open terminal in `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

Run the full backend test suite:
```bash
cd backend
python -m pytest
```

Build the production frontend bundle:
```bash
cd frontend
npm run build
```

---

## Backup & Recovery

- **Pre-Supabase Backup**: A complete copy of pre-migration JSON files is preserved under `backend/data_backup_pre_supabase/`.
- **Database Backup**: Supabase PostgreSQL is automatically protected by point-in-time recovery and database snapshots under the `Educator-Discovery` organization.
- **Data Export**: The Saved Educators view in the frontend includes an **Export JSON** feature allowing recruiters to download shortlists locally at any time.
