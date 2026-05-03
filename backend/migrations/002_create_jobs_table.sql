-- Blueprint Section 7: jobs table schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE TYPE job_status AS ENUM (
        'posted',
        'assigned',
        'in_progress',
        'completed',
        'disputed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onchain_job_id BIGINT UNIQUE,
    poster_address TEXT NOT NULL,
    assigned_agent_id UUID REFERENCES agents(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    job_spec_hash TEXT NOT NULL,
    output_hash TEXT,
    required_capabilities TEXT[] NOT NULL DEFAULT '{}',
    payment_token TEXT NOT NULL,
    escrow_amount NUMERIC(36,18) NOT NULL,
    uniswap_swap_tx TEXT,
    status job_status NOT NULL DEFAULT 'posted',
    deadline TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'jobs'
          AND policyname = 'jobs_rls_placeholder'
    ) THEN
        CREATE POLICY jobs_rls_placeholder ON jobs FOR ALL USING (true);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_poster ON jobs (poster_address);
CREATE INDEX IF NOT EXISTS idx_jobs_agent ON jobs (assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_jobs_capabilities ON jobs USING GIN (required_capabilities);
