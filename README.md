# Educator Discovery Platform

## Overview
The Educator Discovery Platform is designed to discover IIT-JEE and NEET educators/teachers based on Location, Track, and Subject. The platform will use Anakin's Search API for web discovery and Anakin's URL Scraper API for profile enrichment.

## Architecture

The project consists of a Clean Architecture based backend and a component-based frontend.

### Frontend
- **Framework**: React + Vite
- **UI Library**: (To be decided, standard vanilla CSS/Tailwind)
- **Role**: Presents dependent dropdowns (Location, Track, Subject) and visualizes the discovered educator profiles as cards.

### Backend
- **Framework**: Python + FastAPI
- **Architecture**: Service-based, modular structure.
  - **`app/api`**: Contains all the API routing and endpoints.
  - **`app/services`**: Business logic, including:
    - `search.py`: Interacts with the Anakin Search API for web discovery.
    - `enrichment.py`: Interacts with the Anakin URL Scraper API to normalize and enrich profiles.
    - `ranking.py`: Handles validation of evidence and ranking candidates using measurable signals.
  - **`app/models`**: Database models (Supabase/PostgreSQL ready).
  - **`app/schemas`**: Pydantic schemas for request/response validation.
  - **`app/core`**: Core configurations (e.g., loading environment variables).

## Folder Structure
```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── main.py
│   │   └── __init__.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

## Running the Project (Development)

### Backend
1. Navigate to the `backend` directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` in the root folder and add API keys.
6. Run the server: `uvicorn app.main:app --reload`

### Frontend
1. Navigate to the `frontend` directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
