"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import JobCard from "@/components/jobs/JobCard";
import ReputationTimeline, { type ReputationEvent } from "@/components/agents/ReputationTimeline";
import { Button } from "@/components/ui/Button";

type MeResponse = {
  address: string;
  agent_id: string | null;
  ens_name: string | null;
};

type JobRecord = {
  id: string;
  title: string;
  description?: string;
  required_capabilities: string[];
  escrow_amount: string;
  deadline: string;
  status: "posted" | "assigned" | "in_progress" | "completed" | "disputed";
  poster_address: string;
  assigned_agent_id?: string | null;
  created_at?: string;
};

type JobsIndexResponse = { data: JobRecord[]; cursor: string | null };

type Bid = {
  id: string;
  job_id: string;
  agent_id: string;
  proposed_amount: string;
  message: string;
  status: "pending" | "accepted" | "withdrawn" | string;
  created_at?: string;
};

type JobShowResponse = JobRecord & { bids: Bid[] };

async function fetchMe(): Promise<MeResponse | null> {
  try {
    const res = await fetch("/v1/auth/me", { credentials: "include" });
    if (!res.ok) return null; // treat as not authenticated
    return (await res.json()) as MeResponse;
  } catch {
    return null;
  }
}

async function fetchJobs(limit = 50): Promise<JobsIndexResponse> {
  const res = await fetch(`/v1/jobs?limit=${limit}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load jobs");
  return res.json();
}

async function fetchJobWithBids(id: string): Promise<JobShowResponse> {
  const res = await fetch(`/v1/jobs/${id}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load job details");
  return res.json();
}

async function fetchAgentJobs(agentId: string, limit = 50): Promise<JobsIndexResponse> {
  const res = await fetch(`/v1/agents/${agentId}/jobs?limit=${limit}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load agent jobs");
  return res.json();
}

async function fetchAgentReputation(agentId: string, limit = 50): Promise<{ data: ReputationEvent[]; cursor: string | null }> {
  const res = await fetch(`/v1/agents/${agentId}/reputation?limit=${limit}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load reputation");
  return res.json();
}

async function assignBid(jobId: string, bidId: string): Promise<void> {
  const res = await fetch(`/v1/jobs/${jobId}/assign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ bid_id: bidId }),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to accept bid");
  }
}

function Section({ title, children, actions }: { title: string; children: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-body">{title}</h2>
        {actions}
      </div>
      <div className="rounded-lg border border-border bg-surface p-4">{children}</div>
    </section>
  );
}

export default function DashboardPage() {
  const [tab, setTab] = useState<"posted" | "bids" | "work" | "rep">("posted");
  const router = useRouter();

  // Require auth
  const meQuery = useQuery({ queryKey: ["me"], queryFn: fetchMe });
  const isAuthed = !!meQuery.data?.address;
  // Auth required → redirect unauthenticated users per Blueprint Section 12.1
  useEffect(() => {
    if (!isAuthed) router.replace("/");
  }, [isAuthed, router]);

  // Posted jobs (filter client-side until backend exposes poster filter)
  const postedQuery = useQuery({
    queryKey: ["jobs", "posted"],
    queryFn: () => fetchJobs(100),
    enabled: isAuthed,
  });

  const postedJobs: JobRecord[] = useMemo(() => {
    const all = postedQuery.data?.data ?? [];
    const addr = meQuery.data?.address?.toLowerCase();
    return all.filter((j) => j.poster_address?.toLowerCase?.() === addr);
  }, [postedQuery.data, meQuery.data?.address]);

  // For incoming bids, fetch details for each posted job in a single stable query to avoid dynamic hook counts
  const jobDetailsQuery = useQuery({
    queryKey: ["incoming-bids", postedJobs.map((j) => j.id)],
    queryFn: async () => {
      const results = await Promise.all(postedJobs.map((j) => fetchJobWithBids(j.id)));
      return results as JobShowResponse[];
    },
    enabled: isAuthed && postedJobs.length > 0,
  });

  const incomingBids: Array<{ job: JobRecord; bid: Bid }> = useMemo(() => {
    const rows: Array<{ job: JobRecord; bid: Bid }> = [];
    const details = jobDetailsQuery.data ?? [];
    details.forEach((job) => {
      const bids = (job?.bids ?? []).filter((b) => b.status === "pending");
      bids.forEach((b) => rows.push({ job, bid: b }));
    });
    return rows.sort((a, b) => (new Date(b.bid.created_at || 0).getTime() - new Date(a.bid.created_at || 0).getTime()));
  }, [jobDetailsQuery.data]);

  // My Work — jobs assigned to my agent
  const agentId = meQuery.data?.agent_id ?? null;
  const workQuery = useQuery({
    queryKey: ["agent-jobs", agentId],
    queryFn: () => fetchAgentJobs(agentId as string, 100),
    enabled: isAuthed && !!agentId,
  });

  // Reputation timeline
  const repQuery = useQuery({
    queryKey: ["agent-rep", agentId],
    queryFn: () => fetchAgentReputation(agentId as string, 100),
    enabled: isAuthed && !!agentId,
  });

  const [accepting, setAccepting] = useState<string | null>(null);

  async function onAccept(jobId: string, bidId: string) {
    try {
      setAccepting(bidId);
      await assignBid(jobId, bidId);
      // refresh lists
      await Promise.all([postedQuery.refetch(), jobDetailsQuery.refetch(), workQuery.refetch(), repQuery.refetch()]);
    } finally {
      setAccepting(null);
    }
  }

  // Tabs UI (button group)
  const tabs: Array<{ key: typeof tab; label: string; badge?: number | null }> = [
    { key: "posted", label: "Posted Jobs", badge: postedJobs.length },
    { key: "bids", label: "Incoming Bids", badge: incomingBids.length },
    { key: "work", label: "My Work", badge: (workQuery.data?.data?.length ?? 0) || null },
    { key: "rep", label: "Reputation", badge: null },
  ];

  if (meQuery.isLoading) {
    return (
      <main className="mx-auto max-w-6xl p-6">
        <div className="h-6 w-40 animate-pulse rounded bg-muted" aria-hidden />
      </main>
    );
  }

  if (!isAuthed) return null; // allow redirect

  return (
    <main className="mx-auto max-w-6xl p-6 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-body">My Dashboard</h1>
        <nav className="flex gap-2" aria-label="Dashboard sections">
          {tabs.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`rounded-md border px-3 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                tab === t.key ? "border-primary text-primary bg-primary/10" : "border-border text-body hover:bg-muted/20"
              }`}
              aria-pressed={tab === t.key}
            >
              {t.label}
              {typeof t.badge === "number" ? (
                <span className="ml-2 inline-flex min-w-[20px] items-center justify-center rounded-full bg-primary px-1.5 text-xs font-medium text-white">
                  {t.badge}
                </span>
              ) : null}
            </button>
          ))}
        </nav>
      </header>

      {tab === "posted" && (
        <Section title="Posted Jobs">
          {postedQuery.isLoading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy>
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-40 animate-pulse rounded-lg border border-border bg-muted/30" />
              ))}
            </div>
          ) : postedQuery.isError ? (
            <div className="flex items-center justify-between rounded-md border border-error/40 bg-error/10 p-3 text-sm">
              <span className="text-body">Failed to load posted jobs.</span>
              <Button type="button" variant="secondary" onClick={() => postedQuery.refetch()}>
                Retry
              </Button>
            </div>
          ) : postedJobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <p className="text-body">No jobs posted yet.</p>
              <p className="text-muted text-sm">Create a job to start receiving bids.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {postedJobs.map((j) => (
                <JobCard
                  key={j.id}
                  id={j.id}
                  title={j.title}
                  status={j.status}
                  capabilities={j.required_capabilities || []}
                  escrowAmount={j.escrow_amount}
                  deadline={new Date(j.deadline).toLocaleDateString()}
                  bidCount={0}
                  onClick={(id) => (window.location.href = `/jobs/${id}`)}
                />
              ))}
            </div>
          )}
        </Section>
      )}

      {tab === "bids" && (
        <Section title="Incoming Bids" actions={<span className="text-xs text-muted">Accept is available; decline flow is not implemented in the API</span>}>
          {jobDetailsQuery.isLoading ? (
            <div className="space-y-3" aria-busy>
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-md border border-border bg-muted/30" />
              ))}
            </div>
          ) : jobDetailsQuery.isError ? (
            <div className="flex items-center justify-between rounded-md border border-error/40 bg-error/10 p-3 text-sm">
              <span className="text-body">Failed to load bids for one or more jobs.</span>
              <Button type="button" variant="secondary" onClick={() => jobDetailsQuery.refetch()}>
                Retry all
              </Button>
            </div>
          ) : incomingBids.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <p className="text-body">No pending bids right now.</p>
              <p className="text-muted text-sm">When agents bid on your jobs, they will appear here.</p>
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {incomingBids.map(({ job, bid }) => (
                <li key={bid.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <a href={`/jobs/${job.id}`} className="text-body font-medium underline-offset-2 hover:underline">
                        {job.title}
                      </a>
                      <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted">{job.status}</span>
                    </div>
                    <div className="mt-1 text-sm text-muted">{bid.message}</div>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span className="text-sm font-semibold text-body">{bid.proposed_amount}</span>
                    <Button
                      type="button"
                      onClick={() => onAccept(job.id, bid.id)}
                      disabled={accepting === bid.id}
                      aria-busy={accepting === bid.id}
                    >
                      {accepting === bid.id ? "Accepting…" : "Accept"}
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}

      {tab === "work" && (
        <Section title="My Work">
          {!agentId ? (
            <p className="text-muted">No agent linked to your wallet. Register an agent to start working jobs.</p>
          ) : workQuery.isLoading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy>
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-40 animate-pulse rounded-lg border border-border bg-muted/30" />
              ))}
            </div>
          ) : workQuery.isError ? (
            <div className="flex items-center justify-between rounded-md border border-error/40 bg-error/10 p-3 text-sm">
              <span className="text-body">Failed to load assigned jobs.</span>
              <Button type="button" variant="secondary" onClick={() => workQuery.refetch()}>
                Retry
              </Button>
            </div>
          ) : (workQuery.data?.data?.length ?? 0) === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <p className="text-body">No assigned jobs.</p>
              <p className="text-muted text-sm">When a poster assigns you, the job will appear here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {(workQuery.data?.data ?? []).map((j) => (
                <JobRecordCardFromApi key={j.id} job={j as JobRecord} />
              ))}
            </div>
          )}
        </Section>
      )}

      {tab === "rep" && (
        <Section title="Reputation">
          {!agentId ? (
            <p className="text-muted">No agent linked to your wallet. Register an agent to build reputation.</p>
          ) : repQuery.isLoading ? (
            <div className="h-[280px] animate-pulse rounded-md border border-border bg-muted/30" aria-busy />
          ) : repQuery.isError ? (
            <div className="flex items-center justify-between rounded-md border border-error/40 bg-error/10 p-3 text-sm">
              <span className="text-body">Failed to load reputation.</span>
              <Button type="button" variant="secondary" onClick={() => repQuery.refetch()}>
                Retry
              </Button>
            </div>
          ) : (repQuery.data?.data?.length ?? 0) === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
              <p className="text-body">No reputation events yet.</p>
              <p className="text-muted text-sm">As you complete jobs, events will appear here.</p>
            </div>
          ) : (
            <ReputationTimeline events={repQuery.data?.data ?? []} />
          )}
        </Section>
      )}
    </main>
  );
}

function JobRecordCardFromApi({ job }: { job: JobRecord }) {
  return (
    <JobCard
      id={job.id}
      title={job.title}
      status={job.status}
      capabilities={job.required_capabilities || []}
      escrowAmount={job.escrow_amount}
      deadline={new Date(job.deadline).toLocaleDateString()}
      bidCount={0}
      onClick={(id) => (window.location.href = `/jobs/${id}`)}
    />
  );
}
