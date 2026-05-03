-- Blueprint Section 7: bids table schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE TYPE bid_status AS ENUM (
        'pending',
        'accepted',
        'rejected',
        'withdrawn'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS bids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) NOT NULL,
    agent_id UUID REFERENCES agents(id) NOT NULL,
    proposed_amount NUMERIC(36,18) NOT NULL,
    message TEXT,
    axl_message_id TEXT,
    status bid_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE bids ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'bids'
          AND policyname = 'bids_rls_placeholder'
    ) THEN
        CREATE POLICY bids_rls_placeholder ON bids FOR ALL USING (true);
    END IF;
END
$$;
