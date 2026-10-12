-- Supabase / PostgreSQL Schema Migration: Educator Discovery Platform
-- Version: 002 - Saved Educators, Exposure Tracking, Extended Metadata & RLS Policies

-- =====================================================================================
-- 1. EXTEND EDUCATORS TABLE
-- =====================================================================================
ALTER TABLE educators
    ADD COLUMN IF NOT EXISTS professional_headline TEXT,
    ADD COLUMN IF NOT EXISTS current_job_title TEXT,
    ADD COLUMN IF NOT EXISTS current_employer TEXT,
    ADD COLUMN IF NOT EXISTS pw_exclusion_status TEXT DEFAULT 'ELIGIBLE',
    ADD COLUMN IF NOT EXISTS identity_confidence NUMERIC(4,3) DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS employment_verification_status TEXT DEFAULT 'unconfirmed',
    ADD COLUMN IF NOT EXISTS primary_location TEXT,
    ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'verified';

-- =====================================================================================
-- 2. EXTEND SEARCH RUNS TABLE
-- =====================================================================================
ALTER TABLE search_runs
    ADD COLUMN IF NOT EXISTS target_count INTEGER DEFAULT 50,
    ADD COLUMN IF NOT EXISTS total_results INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS target_shortfall INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS unique_candidates_discovered INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS profiles_enriched INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS search_duration_seconds NUMERIC(6,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS credits_used NUMERIC(6,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS credits_estimated NUMERIC(6,2) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rejected_counts JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS review_queue_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS sources_searched INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS provider_errors JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS cache_status TEXT DEFAULT 'MISS';

-- =====================================================================================
-- 3. SAVED EDUCATORS TABLE (Recruiter Shortlist)
-- =====================================================================================
CREATE TABLE IF NOT EXISTS saved_educators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(educator_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_educators_educator_id ON saved_educators(educator_id);

-- =====================================================================================
-- 4. EXPOSURE HISTORY TABLE (Deduplication across search runs)
-- =====================================================================================
CREATE TABLE IF NOT EXISTS exposure_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    educator_id UUID NOT NULL REFERENCES educators(id) ON DELETE CASCADE,
    search_run_id UUID REFERENCES search_runs(id) ON DELETE SET NULL,
    interaction_type TEXT DEFAULT 'displayed',
    exposed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exposure_history_educator_id ON exposure_history(educator_id);
CREATE INDEX IF NOT EXISTS idx_exposure_history_search_run ON exposure_history(search_run_id);

-- =====================================================================================
-- 5. ENABLE ROW LEVEL SECURITY & DEFINE POLICIES
-- =====================================================================================
ALTER TABLE search_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE educators ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE educator_subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE educator_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE educator_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE educator_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_educators ENABLE ROW LEVEL SECURITY;
ALTER TABLE exposure_history ENABLE ROW LEVEL SECURITY;

-- Allow access policies for authenticated and anon clients
DO $$
BEGIN
    -- search_runs
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'search_runs' AND policyname = 'Allow all access to search_runs') THEN
        CREATE POLICY "Allow all access to search_runs" ON search_runs FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- search_results
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'search_results' AND policyname = 'Allow all access to search_results') THEN
        CREATE POLICY "Allow all access to search_results" ON search_results FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- educators
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'educators' AND policyname = 'Allow all access to educators') THEN
        CREATE POLICY "Allow all access to educators" ON educators FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- social_profiles
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'social_profiles' AND policyname = 'Allow all access to social_profiles') THEN
        CREATE POLICY "Allow all access to social_profiles" ON social_profiles FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- educator_subjects
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'educator_subjects' AND policyname = 'Allow all access to educator_subjects') THEN
        CREATE POLICY "Allow all access to educator_subjects" ON educator_subjects FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- educator_locations
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'educator_locations' AND policyname = 'Allow all access to educator_locations') THEN
        CREATE POLICY "Allow all access to educator_locations" ON educator_locations FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- educator_evidence
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'educator_evidence' AND policyname = 'Allow all access to educator_evidence') THEN
        CREATE POLICY "Allow all access to educator_evidence" ON educator_evidence FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- educator_scores
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'educator_scores' AND policyname = 'Allow all access to educator_scores') THEN
        CREATE POLICY "Allow all access to educator_scores" ON educator_scores FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- saved_educators
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'saved_educators' AND policyname = 'Allow all access to saved_educators') THEN
        CREATE POLICY "Allow all access to saved_educators" ON saved_educators FOR ALL USING (true) WITH CHECK (true);
    END IF;

    -- exposure_history
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'exposure_history' AND policyname = 'Allow all access to exposure_history') THEN
        CREATE POLICY "Allow all access to exposure_history" ON exposure_history FOR ALL USING (true) WITH CHECK (true);
    END IF;
END
$$;
