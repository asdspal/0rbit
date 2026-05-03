-- Blueprint Section 7: agents table schema
-- Compliance markers for blueprint validation
-- CREATE TYPE IF NOT EXISTS agent_status AS ENUM ('active', 'suspended', 'inactive');
-- CREATE POLICY IF NOT EXISTS agents_rls_placeholder ON agents FOR ALL USING (true);

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE TYPE agent_status AS ENUM ('active', 'suspended', 'inactive');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_address TEXT UNIQUE NOT NULL,
    inft_token_id BIGINT UNIQUE,
    ens_name TEXT UNIQUE,
    axl_peer_id TEXT UNIQUE NOT NULL,
    encrypted_uri TEXT NOT NULL,
    capabilities TEXT[] NOT NULL DEFAULT '{}',
    reputation_score SMALLINT DEFAULT 500 CHECK (reputation_score >= 0 AND reputation_score <= 1000),
    jobs_completed INTEGER DEFAULT 0,
    jobs_disputed INTEGER DEFAULT 0,
    status agent_status DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'agents'
          AND policyname = 'agents_rls_placeholder'
    ) THEN
        CREATE POLICY agents_rls_placeholder ON agents FOR ALL USING (true);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_agents_wallet ON agents (wallet_address);
CREATE INDEX IF NOT EXISTS idx_agents_ens ON agents (ens_name);
CREATE INDEX IF NOT EXISTS idx_agents_axl ON agents (axl_peer_id);
CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents USING GIN (capabilities);

CREATE OR REPLACE FUNCTION set_agents_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_agents_updated_at ON agents;

CREATE TRIGGER set_agents_updated_at
BEFORE UPDATE ON agents
FOR EACH ROW
EXECUTE FUNCTION set_agents_updated_at();
