"use client";

import { useMemo, useState } from "react";
import JobCard from "@/components/jobs/JobCard";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { useJobs, type JobStatus } from "@/hooks/useJobs";

const statusOptions: { value: JobStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "posted", label: "Posted" },
  { value: "assigned", label: "Assigned" },
  { value: "in_progress", label: "In Progress" },
  { value: "completed", label: "Completed" },
  { value: "disputed", label: "Disputed" },
];

const sortOptions: { value: "created_at" | "deadline"; label: string }[] = [
  { value: "created_at", label: "Newest" },
  { value: "deadline", label: "Nearest deadline" },
];

export default function JobsPage() {
  const [status, setStatus] = useState<JobStatus | "all">("all");
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [sort, setSort] = useState<"created_at" | "deadline">("created_at");

  const { jobs, availableCapabilities, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError, error, refetch } =
    useJobs({ status, capabilities: selectedCapabilities, sort, limit: 12 });

  const capabilityOptions = useMemo(() => availableCapabilities, [availableCapabilities]);

  const toggleCapability = (cap: string) => {
    setSelectedCapabilities((prev) =>
      prev.includes(cap) ? prev.filter((c) => c !== cap) : [...prev, cap]
    );
  };

  const isEmpty = !isLoading && !isError && jobs.length === 0;

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <header className="flex flex-col gap-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-muted">Section 12.1 · Job Board</p>
          <h1 className="text-3xl font-bold text-body">Open Jobs</h1>
          <p className="text-muted">Filter by status and required capabilities. Realtime updates via Supabase are documented as a GAP (Section 5.3).</p>
        </div>

        <Card className="flex flex-col gap-4 bg-surface">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <label className="flex flex-col gap-2 text-sm text-body">
              Status
              <select
                className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                value={status}
                onChange={(e) => setStatus(e.target.value as JobStatus | "all")}
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <fieldset className="flex flex-col gap-2 text-sm text-body">
              <legend className="text-sm font-medium">Capabilities</legend>
              <div className="flex flex-wrap gap-2">
                {capabilityOptions.length === 0 && (
                  <span className="text-muted">No capabilities yet</span>
                )}
                {capabilityOptions.map((cap) => {
                  const checked = selectedCapabilities.includes(cap);
                  return (
                    <label
                      key={cap}
                      className="flex items-center gap-2 rounded-md border border-border bg-surface-elevated px-2 py-1 text-sm focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2"
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-border text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                        checked={checked}
                        onChange={() => toggleCapability(cap)}
                        aria-label={`Capability ${cap}`}
                      />
                      <span className="text-body">{cap}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>

            <label className="flex flex-col gap-2 text-sm text-body">
              Sort
              <select
                className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                value={sort}
                onChange={(e) => setSort(e.target.value as "created_at" | "deadline")}
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </Card>
      </header>

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
          {Array.from({ length: 6 }).map((_, idx) => (
            <div
              key={`skeleton-${idx}`}
              className="animate-pulse rounded-lg border border-border bg-surface p-4"
              aria-hidden
            >
              <div className="mb-3 h-4 w-32 rounded bg-surface-elevated" />
              <div className="mb-2 h-5 w-3/4 rounded bg-surface-elevated" />
              <div className="h-4 w-1/2 rounded bg-surface-elevated" />
            </div>
          ))}
        </div>
      )}

      {isEmpty && (
        <Card className="flex flex-col items-start gap-2 bg-surface">
          <p className="text-body font-semibold">No jobs found</p>
          <p className="text-muted">Try a different status or capability filter.</p>
        </Card>
      )}

      {!isLoading && jobs.length > 0 && (
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
            />
          ))}
        </div>
      )}

      {!isLoading && hasNextPage && (
        <div className="flex justify-center">
          <Button
            type="button"
            variant="secondary"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="min-w-[140px]"
          >
            {isFetchingNextPage ? "Loading..." : "Load more"}
          </Button>
        </div>
      )}
    </main>
  );
}
