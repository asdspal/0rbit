### Manual Supabase Project Creation (Section 14 Phase 0 Item 4)

1. Sign in or register at https://supabase.com and create a new project named `0rbit-backend` (or similar).
2. Select PostgreSQL version 15 as mandated by Section 4 and link it to the desired region or workload tier.
3. In the Supabase dashboard, copy the `Connection string` (PostgreSQL URI) and paste it into your local `.env` or secrets manager as `DATABASE_URL`.
4. From the same dashboard, visit Settings → API and copy the `service_role` key to store as `SUPABASE_SERVICE_ROLE_KEY`; treat this value as sensitive.
5. Execute the schema migrations defined in Section 7 (agents, jobs, bids, reputation_events, axl_messages) against the new database. Supabase provides SQL editor or CLI; ensure every table includes Row Level Security (RLS) policies per blueprint constraints.
6. Enable and review RLS policies on all five tables (agents, jobs, bids, reputation_events, axl_messages). At minimum, keep the default `auth.uid()`/(service role) allowances while adding fine-grained policies later in future steps.
7. Confirm that the Supabase project is reachable from the FastAPI backend by verifying the `DATABASE_URL` resolves and running a simple `SELECT 1` once the service-role client is connected.

> **Note:** Actual Supabase onboarding is manual and must be completed before Step M.0.6. The files in this repo only reference environment variables and the Supabase client setup; they do not store the real connection strings.
