from pathlib import Path


SQL_PATH = Path(__file__).resolve().parents[1] / "migrations" / "001_create_agents_table.sql"


EXPECTED_SNIPPETS = [
    "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";",
    "CREATE TYPE IF NOT EXISTS agent_status AS ENUM ('active', 'suspended', 'inactive');",
    "CREATE TABLE IF NOT EXISTS agents (",
    "id UUID PRIMARY KEY DEFAULT gen_random_uuid()",
    "wallet_address TEXT UNIQUE NOT NULL",
    "inft_token_id BIGINT UNIQUE",
    "ens_name TEXT UNIQUE",
    "axl_peer_id TEXT UNIQUE NOT NULL",
    "encrypted_uri TEXT NOT NULL",
    "capabilities TEXT[] NOT NULL DEFAULT '{}'",
    "reputation_score SMALLINT DEFAULT 500 CHECK (reputation_score >= 0 AND reputation_score <= 1000)",
    "jobs_completed INTEGER DEFAULT 0",
    "jobs_disputed INTEGER DEFAULT 0",
    "status agent_status DEFAULT 'active'",
    "created_at TIMESTAMPTZ DEFAULT now()",
    "updated_at TIMESTAMPTZ DEFAULT now()",
    "ALTER TABLE agents ENABLE ROW LEVEL SECURITY;",
    "CREATE POLICY IF NOT EXISTS agents_rls_placeholder ON agents FOR ALL USING (true);",
    "CREATE INDEX IF NOT EXISTS idx_agents_wallet ON agents (wallet_address);",
    "CREATE INDEX IF NOT EXISTS idx_agents_ens ON agents (ens_name);",
    "CREATE INDEX IF NOT EXISTS idx_agents_axl ON agents (axl_peer_id);",
    "CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON agents USING GIN (capabilities);",
    "CREATE OR REPLACE FUNCTION set_agents_updated_at()",
    "NEW.updated_at = now();",
    "CREATE TRIGGER set_agents_updated_at",
]


def read_sql() -> str:
    return SQL_PATH.read_text()


def test_migration_contains_expected_snippets():
    sql = read_sql()
    missing = [snippet for snippet in EXPECTED_SNIPPETS if snippet not in sql]
    assert not missing, f"Migration is missing expected snippets: {missing}"
