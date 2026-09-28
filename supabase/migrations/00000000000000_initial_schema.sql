-- Supabase / PostgreSQL Schema Migration: Educator Discovery Platform
-- Version: 001

-- =====================================================================================
-- 1. SEARCH SYSTEM
-- =====================================================================================

-- Table: search_runs
-- Purpose: Traceability. Records every time a search query is fired (e.g. searching for "Physics IIT-JEE Lucknow").
CREATE TABLE search_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requested_location TEXT NOT NULL,
    requested_track TEXT NOT NULL,
    requested_subject TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: search_results
-- Purpose: Traceability. Maps 1:N to search_runs. Stores the raw extracted snippet/result before enrichment.
CREATE TABLE search_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_run_id UUID NOT NULL REFERENCES search_runs(id) ON DELETE CASCADE,
    raw_title TEXT,
    raw_url TEXT NOT NULL,
    raw_snippet TEXT,
    discovery_source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'discovered', -- 'discovered', 'enriched', 'deduplicated'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================================
-- 2. EDUCATOR CORE
-- =====================================================================================

-- Table: educators
-- Purpose: The consolidated, deduplicated real-world person. 
CREATE TABLE educators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    primary_track TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: social_profiles
-- Purpose: Maps 1:N to educators. Stores platform-specific scraped data preserving the source URL.
CREATE TABLE social_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    username TEXT,
    followers INTEGER,
    connections INTEGER,
    bio TEXT,
    scrape_status TEXT NOT NULL DEFAULT 'pending',
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================================
-- 3. EDUCATOR ATTRIBUTES & EVIDENCE
-- =====================================================================================

-- Table: educator_subjects
-- Purpose: Maps 1:N to educators. An educator can teach multiple subjects across multiple tracks.
CREATE TABLE educator_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    track TEXT NOT NULL,
    subject TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(educator_id, track, subject)
);

-- Table: educator_locations
-- Purpose: Maps 1:N to educators. An educator might operate in multiple cities.
CREATE TABLE educator_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    location_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(educator_id, location_name)
);

-- Table: educator_evidence
-- Purpose: Auditing/Traceability. Maps 1:N to educators. Stores the exact text/source that proves a trait.
CREATE TABLE educator_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    dimension TEXT NOT NULL, -- e.g., 'subject', 'location', 'track', 'teaching_experience'
    detected_value TEXT NOT NULL,
    source_platform TEXT NOT NULL,
    source_url TEXT,
    evidence_text TEXT NOT NULL,
    confidence_score NUMERIC(4,3) NOT NULL,
    verification_status TEXT NOT NULL, -- 'verified', 'likely', 'uncertain'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================================
-- 4. RANKING
-- =====================================================================================

-- Table: educator_scores
-- Purpose: Reproducible ranking. Stores the independent calculated components and overall score.
CREATE TABLE educator_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE UNIQUE,
    track_relevance NUMERIC(5,2) DEFAULT 0,
    subject_relevance NUMERIC(5,2) DEFAULT 0,
    location_relevance NUMERIC(5,2) DEFAULT 0,
    teaching_evidence NUMERIC(5,2) DEFAULT 0,
    professional_evidence NUMERIC(5,2) DEFAULT 0,
    cross_platform_presence NUMERIC(5,2) DEFAULT 0,
    audience_signal NUMERIC(5,2) DEFAULT 0,
    profile_completeness NUMERIC(5,2) DEFAULT 0,
    evidence_quality NUMERIC(5,2) DEFAULT 0,
    overall_score NUMERIC(5,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================================
-- 5. INDEXES (Performance Optimization)
-- =====================================================================================

-- Track & Subject (For fast dropdown filtering)
CREATE INDEX idx_educator_subjects_track ON educator_subjects(track);
CREATE INDEX idx_educator_subjects_subject ON educator_subjects(subject);

-- Location (For fast dropdown filtering)
CREATE INDEX idx_educator_locations_name ON educator_locations(location_name);

-- Platform (For platform-specific filtering and stats)
CREATE INDEX idx_social_profiles_platform ON social_profiles(platform);

-- Foreign Keys (To optimize JOINs)
CREATE INDEX idx_social_profiles_educator_id ON social_profiles(educator_id);
CREATE INDEX idx_educator_subjects_educator_id ON educator_subjects(educator_id);
CREATE INDEX idx_educator_locations_educator_id ON educator_locations(educator_id);
CREATE INDEX idx_educator_evidence_educator_id ON educator_evidence(educator_id);

-- Overall Score (For sorting search results quickly)
CREATE INDEX idx_educator_scores_overall ON educator_scores(overall_score DESC);
