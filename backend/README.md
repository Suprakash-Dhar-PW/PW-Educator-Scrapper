# PW-Mentor-Search — Backend Architecture & Service Documentation

## Overview

The backend is built with **FastAPI** following Clean Layered Architecture:

```text
HTTP Request (Client)
      ↓
FastAPI Router (app/api/v1/endpoints/)
      ↓
Application Services (Discovery, Normalizer, Validator, Deduplication, Ranking)
      ↓
Repository Layer (app/repositories/)
      ↓
Supabase PostgreSQL Database
```

---

## Directory Organization

- **`app/main.py`**: Initializes the FastAPI application, mounts CORS middleware, registers global exception handlers, and mounts the API router.
- **`app/core/config.py`**: Centralized configuration management using `pydantic-settings`. Loads `.env` with override safety.
- **`app/core/database.py`**: Singleton Supabase client manager and health checker.
- **`app/core/exceptions.py`**: Custom domain exceptions (`EntityNotFoundException`, `DatabaseException`, `ProviderException`, `ValidationException`) and global JSON exception handlers.
- **`app/repositories/`**:
  - `educator_repository.py`: CRUD operations for `educators`, `social_profiles`, `educator_subjects`, `educator_locations`, and `educator_evidence`.
  - `saved_educator_repository.py`: Shortlist management and persistence in `saved_educators`.
  - `search_repository.py`: Search run auditing in `search_runs` and exposure history in `exposure_history`.
- **`app/services/`**:
  - `anakin_search.py`: Query builder for search provider.
  - `anakin_scraper.py`: URL scraper integration.
  - `normalizer.py`: Normalizes candidate payloads from heterogeneous web sources.
  - `deduplication.py`: Cross-platform identity resolution based on exact name and profile URLs.
  - `validator.py`: Enforces educator eligibility:
    - Current & former Physics Wallah faculty exclusion.
    - Role verification: rejects students and aspirants.
    - Institution exclusion: rejects coaching channels and generic institutional accounts.
  - `ranking.py`: Calculates multi-dimensional relevance factors.
  - `cache.py`: In-memory and file cache service for temporary deduplication.
- **`app/schemas/`**: Pydantic models for validation and serialization.
- **`tests/`**: Automated test suite with 25 unit and integration tests.

---

## Supabase Connection Details

The backend connects to Supabase PostgreSQL using the official Python client:

- **Library**: `supabase>=2.32.0` (using `httpx` and `postgrest-py`)
- **Credentials**: Configured via `SUPABASE_URL` and `SUPABASE_KEY` (Anon key) in `backend/.env`.
- **Database Tables**:
  - `educators`
  - `social_profiles`
  - `educator_subjects`
  - `educator_locations`
  - `educator_evidence`
  - `educator_scores`
  - `search_runs`
  - `search_results`
  - `saved_educators`
  - `exposure_history`

---

## Running Backend Tests

```bash
cd backend
python -m pytest
```

All 25 automated tests run without requiring live Anakin API credits.
