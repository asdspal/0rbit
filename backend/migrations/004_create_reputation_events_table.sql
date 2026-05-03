-- Blueprint Section 7: reputation_events table schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE TYPE reputation_reason AS ENUM (
        'job_completed',
        'job_disputed',
        'keeperhub_update',
        'slash'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS reputation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) NOT NULL,
    job_id UUID REFERENCES jobs(id),
    delta SMALLINT NOT NULL,
    new_score SMALLINT NOT NULL,
    reason reputation_reason NOT NULL,
    onchain_tx TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE reputation_events ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'reputation_events'
          AND policyname = 'reputation_events_rls_placeholder'
    ) THEN
        CREATE POLICY reputation_events_rls_placeholder ON reputation_events FOR ALL USING (true);
    END IF;
END
$$;
