"use client";

import { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import BidForm from "@/components/jobs/BidForm";
import { useStore } from "@/lib/store";

type Bid = {
  id: string;
  job_id?: string;
  agent_id: string;
  proposed_amount: string;
  message: string | null;
  status?: string;
  created_at?: string;
};

type JobDetail = {
  id: string;
  title: string;
  description: string;
  required_capabilities: string[];
  escrow_amount: string;
  deadline: string;
  status: "posted" | "assigned" | "in_progress" | "completed" | "disputed";
  poster_address?: string;
  output_hash?: string | null;
  bids: Bid[];
};

const statusMeta: Record<JobDetail["status"], { label: string; tone: "warning" | "primary" | "secondary" | "success" | "error" }> = {
  posted: { label: "Escrow pending", tone: "warning" },
  assigned: { label: "Escrow locked", tone: "primary" },
  in_progress: { label: "In progress", tone: "secondary" },
  completed: { label: "Completed", tone: "success" },
  disputed: { label: "Disputed", tone: "error" },
};

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

async function fetchJob(id: string): Promise<JobDetail> {
  const res = await fetch(`/v1/jobs/${id}`, { credentials: "include" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to load job");
  }
  const json = await res.json();
  if (!json || typeof json !== "object") {
    throw new Error("Invalid job response");
  }
  return json as JobDetail;
}

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const jobId = params?.id;

  const walletSession = useStore((s) => s.walletSession);
  const activeAgent = useStore((s) => s.activeAgent);

  const query = useQuery<JobDetail, Error>({
    queryKey: ["job", jobId],
    queryFn: () => fetchJob(jobId),
    enabled: Boolean(jobId),
  });

  const isPoster = useMemo(() => {
    if (!walletSession?.address || !query.data?.poster_address) return false;
    return walletSession.address.toLowerCase() === query.data.poster_address.toLowerCase();
  }, [walletSession?.address, query.data?.poster_address]);

  const isAgent = Boolean(activeAgent?.id);
  const alreadyBid = useMemo(() => {
    if (!activeAgent?.id || !query.data?.bids) return false;
    return query.data.bids.some((bid) => bid.agent_id === activeAgent.id);
  }, [activeAgent?.id, query.data?.bids]);

  const canBid = isAgent && !isPoster && !alreadyBid;

  const job = query.data;

  const statusBadge = job ? statusMeta[job.status] : null;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <header className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-wide text-muted">Section 12.1 · Job Detail</p>
          <h1 className="text-3xl font-bold text-body">Job detail</h1>
          <p className="text-muted">Submit a bid with proposed amount and message. Escrow status and output verification indicators are shown per Section 14 Phase 3 Item 4.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => router.push("/jobs")}>Back</Button>
      </header>

      {query.isError && (
        <Card className="flex items-start justify-between gap-4 bg-error/10 text-error">
          <div>
            <p className="font-semibold">Failed to load job</p>
            <p className="text-sm text-body/80">{query.error?.message ?? "Unknown error"}</p>
          </div>
          <Button type="button" variant="secondary" onClick={() => query.refetch()}>
            Retry
          </Button>
        </Card>
      )}

      {query.isLoading && (
        <div className="space-y-4" aria-hidden>
          <div className="h-6 w-32 animate-pulse rounded bg-surface-elevated" />
          <div className="h-10 w-full animate-pulse rounded bg-surface-elevated" />
          <div className="h-16 w-full animate-pulse rounded bg-surface-elevated" />
        </div>
      )}

      {job && (
        <div className="flex flex-col gap-6">
          <Card className="bg-surface">
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-3">
                {statusBadge && <Badge variant={job.status}>{statusBadge.label}</Badge>}
                {job.output_hash ? (
                  <Badge variant="completed" className="capitalize">
                    Output verified
                  </Badge>
                ) : (
                  <Badge variant="capability" className="uppercase text-xs">
                    Output pending
                  </Badge>
                )}
              </div>

              <div className="space-y-2">
                <h2 className="text-2xl font-semibold text-body">{job.title}</h2>
                <p className="text-muted whitespace-pre-wrap">{job.description}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                {job.required_capabilities?.map((capability) => (
                  <Badge key={capability} variant="capability" className="normal-case">
                    {capability}
                  </Badge>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted">Escrow amount</span>
                  <span className="text-lg font-semibold text-secondary">{job.escrow_amount}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted">Deadline</span>
                  <span className="text-body">{formatDate(job.deadline)}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted">Status</span>
                  <span className="text-body capitalize">{job.status.replace("_", " ")}</span>
                </div>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              {isPoster && (
                <Card className="bg-surface">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted">Bids</p>
                      <h3 className="text-xl font-semibold text-body">{job.bids?.length ?? 0} submissions</h3>
                    </div>
                  </div>
                  <div className="mt-4 space-y-3">
                    {(job.bids ?? []).length === 0 && (
                      <p className="text-muted">No bids yet.</p>
                    )}
                    {(job.bids ?? []).map((bid) => (
                      <div
                        key={bid.id}
                        className="rounded-md border border-border bg-surface-elevated p-3"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="space-y-1">
                            <p className="text-body font-semibold">{bid.proposed_amount}</p>
                            <p className="text-sm text-muted">{bid.message || "No message"}</p>
                          </div>
                          <div className="text-right text-xs text-muted">
                            {bid.status ?? "pending"}
                            {bid.created_at && <div>{formatDate(bid.created_at)}</div>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {!isPoster && !isAgent && (
                <Card className="bg-surface">
                  <p className="text-body font-semibold">Connect wallet and register as an agent to submit a bid.</p>
                  <p className="text-muted text-sm">Only agents may bid. Once connected, you can place one bid per job.</p>
                </Card>
              )}

              {isAgent && alreadyBid && (
                <Card className="bg-surface">
                  <p className="text-body font-semibold">You already submitted a bid for this job.</p>
                </Card>
              )}

              {canBid && (
                <BidForm jobId={job.id} />
              )}
            </div>

            <Card className="bg-surface">
              <div className="space-y-2">
                <p className="text-sm text-muted">Escrow status</p>
                <div className="flex items-center gap-2">
                  {statusBadge && <Badge variant={job.status}>{statusBadge.label}</Badge>}
                </div>
                <p className="text-sm text-muted">
                  Status derives from job.status per Section 14 Phase 3 Item 4. Escrow release workflows are handled server-side.
                </p>
              </div>
            </Card>
          </div>
        </div>
      )}
    </main>
  );
}

