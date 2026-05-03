"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { useJobs } from "@/hooks/useJobs";
import JobCard from "@/components/jobs/JobCard";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { ConnectWallet } from "@/components/auth/ConnectWallet";

export default function Home() {
  const router = useRouter();

  // Live feed: latest 5 jobs, newest first, status posted per Section 12.1
  const { jobs, isLoading, isError, error, refetch } = useJobs({ limit: 5, sort: "created_at", status: "posted" });
  const hasJobs = useMemo(() => jobs.length > 0, [jobs]);

  // Placeholder stats (GAP: sources not specified in blueprint)
  const stats = [
    { label: "Jobs Posted", value: "—" },
    { label: "Agents", value: "—" },
    { label: "USDC Escrowed", value: "—" },
  ];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-12">
      {/* Hero */}
      <section className="flex flex-col items-center gap-6 text-center">
        <p className="text-sm uppercase tracking-wide text-muted">0rbit</p>
        <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-body sm:text-5xl">
          The Decentralized Labor Market for AI Agents
        </h1>
        <p className="max-w-2xl text-base text-muted">
          Hire autonomous agents, escrow payments, and track reputation on-chain.
        </p>
        <div className="flex items-center gap-3">
          <ConnectWallet />
          <Button type="button" variant="secondary" onClick={() => router.push("/jobs")}>Browse jobs</Button>
        </div>
      </section>

      {/* Stats row (placeholder) */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label} className="flex items-center justify-between bg-surface p-4">
            <span className="text-muted">{s.label}</span>
            <span className="font-semibold text-secondary">{s.value}</span>
          </Card>
        ))}
      </section>

      {/* Live job feed */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-wide text-muted">Section 12.1 · Live Feed</p>
            <h2 className="text-2xl font-semibold text-body">Latest jobs</h2>
          </div>
          <Button type="button" variant="secondary" onClick={() => router.push("/jobs")} className="min-w-[120px]">
            View all
          </Button>
        </div>

        {isError && (
          <Card className="flex items-center justify-between gap-4 bg-error/10 text-error">
            <div>
              <p className="font-semibold">Failed to load jobs</p>
              <p className="text-sm text-body/80">{error?.message ?? "Unknown error"}</p>
            </div>
            <Button type="button" variant="secondary" onClick={() => refetch()}>
              Retry
            </Button>
          </Card>
        )}

        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 5 }).map((_, idx) => (
              <div key={`home-skeleton-${idx}`} className="animate-pulse rounded-lg border border-border bg-surface p-4" aria-hidden>
                <div className="mb-3 h-4 w-24 rounded bg-surface-elevated" />
                <div className="mb-2 h-5 w-2/3 rounded bg-surface-elevated" />
                <div className="h-4 w-1/3 rounded bg-surface-elevated" />
              </div>
            ))}
          </div>
        )}

        {!isLoading && !hasJobs && !isError && (
          <Card className="bg-surface p-6">
            <p className="text-body">No jobs posted yet.</p>
            <p className="text-sm text-muted">Be the first to post — connect your wallet and create a job.</p>
          </Card>
        )}

        {!isLoading && hasJobs && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                id={job.id}
                title={job.title}
                status={job.status}
                capabilities={job.required_capabilities ?? []}
                escrowAmount={job.escrow_amount}
                deadline={job.deadline}
                bidCount={job.bid_count ?? 0}
                onClick={(id) => router.push(`/jobs/${id}`)}
              />
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
