-- Blueprint Section 7: axl_messages table schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE TYPE axl_message_type AS ENUM (
        'bid',
        'job_accepted',
        'output_ready',
        'ping'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

CREATE TABLE IF NOT EXISTS axl_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    src_peer_id TEXT NOT NULL,
    dst_peer_id TEXT NOT NULL,
    message_type axl_message_type NOT NULL,
    payload_hash TEXT NOT NULL,
    job_id UUID REFERENCES jobs(id) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE axl_messages ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'axl_messages'
          AND policyname = 'axl_messages_rls_placeholder'
    ) THEN
        CREATE POLICY axl_messages_rls_placeholder ON axl_messages FOR ALL USING (true);
    END IF;
END
$$;
