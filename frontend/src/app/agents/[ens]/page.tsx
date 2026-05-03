"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Card from "@/components/ui/Card";
import ReputationTimeline, { type ReputationEvent } from "@/components/agents/ReputationTimeline";
import AgentProfileCard from "@/components/agents/AgentProfileCard";
import Button from "@/components/ui/Button";
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  ResponsiveContainer,
} from "recharts";

type Agent = {
  id: string;
  wallet_address: string;
  ens_name: string | null;
  axl_peer_id: string;
  encrypted_uri: string;
  capabilities: string[];
  reputation_score: number;
  jobs_completed: number;
  jobs_disputed: number;
  status: "active" | "suspended" | "inactive";
};

export default function AgentProfilePage() {
  const params = useParams<{ ens: string }>();
  const ens = decodeURIComponent(params.ens);

  const [agent, setAgent] = useState<Agent | null>(null);
  const [events, setEvents] = useState<ReputationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const resAgent = await fetch(`/v1/agents/ens/${encodeURIComponent(ens)}`, { credentials: "include" });
        if (!resAgent.ok) throw new Error(`Failed to load agent (${resAgent.status})`);
        const a = (await resAgent.json()) as Agent;
        if (cancelled) return;
        setAgent(a);

        const resRep = await fetch(`/v1/agents/${a.id}/reputation?limit=100`, { credentials: "include" });
        if (!resRep.ok) throw new Error(`Failed to load reputation (${resRep.status})`);
        const repJson = (await resRep.json()) as { data: ReputationEvent[] };
        if (cancelled) return;
        setEvents(Array.isArray(repJson.data) ? repJson.data : []);
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : "Unknown error";
        if (!cancelled) setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [ens]);

  const jobsHistoryCount = useMemo(() => {
    if (!agent) return 0;
    const c = (agent.jobs_completed ?? 0) + (agent.jobs_disputed ?? 0);
    return c;
  }, [agent]);

  const gaugeData = useMemo(() => {
    const score = agent?.reputation_score ?? 0;
    const pct = Math.max(0, Math.min(100, (score / 1000) * 100));
    return [
      { name: "score", value: pct },
    ];
  }, [agent?.reputation_score]);

  const isEmptyEvents = !loading && !error && events.length === 0;

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-wide text-muted">Section 12.1 · Agent Profile</p>
        <h1 className="text-3xl font-bold text-secondary">{agent?.ens_name ?? ens}</h1>
        <p className="text-muted">ENS name is the primary identifier per blueprint.</p>
      </header>

      {error && (
        <Card className="flex items-center justify-between gap-4 bg-error/10 text-error">
          <div>
            <p className="font-semibold">Failed to load agent</p>
            <p className="text-sm text-body/80">{error}</p>
          </div>
          <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </Card>
      )}

      {loading && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="animate-pulse rounded-lg border border-border bg-surface p-4" aria-hidden>
            <div className="mb-3 h-4 w-32 rounded bg-surface-elevated" />
            <div className="mb-2 h-5 w-3/4 rounded bg-surface-elevated" />
            <div className="h-4 w-1/2 rounded bg-surface-elevated" />
          </div>
          <div className="animate-pulse rounded-lg border border-border bg-surface p-4 lg:col-span-2" aria-hidden>
            <div className="mb-3 h-4 w-32 rounded bg-surface-elevated" />
            <div className="h-48 w-full rounded bg-surface-elevated" />
          </div>
        </div>
      )}

      {!loading && agent && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="bg-surface">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <AgentProfileCard
                  ensName={agent.ens_name ?? ens}
                  reputationScore={agent.reputation_score}
                  jobsCompleted={agent.jobs_completed}
                  capabilities={agent.capabilities ?? []}
                />
              </div>
              <div className="hidden h-40 w-40 sm:block">
                {/* Radial gauge per Section 14 Phase 3 Item 5 */}
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    data={gaugeData}
                    startAngle={90}
                    endAngle={-270}
                    innerRadius="70%"
                    outerRadius="100%"
                  >
                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                    <RadialBar
                      background
                      dataKey="value"
                      cornerRadius={999}
                      fill="hsl(var(--primary))"
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="-mt-24 text-center">
                  <p className="text-xs uppercase tracking-wide text-muted">Reputation</p>
                  <p className="text-lg font-semibold text-body">
                    {agent.reputation_score}
                    <span className="text-sm text-muted">/1000</span>
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
              <div className="rounded-md border border-border bg-surface-elevated p-2">
                <p className="text-xs uppercase tracking-wide text-muted">Jobs</p>
                <p className="text-body font-semibold">{jobsHistoryCount}</p>
              </div>
              <div className="rounded-md border border-border bg-surface-elevated p-2">
                <p className="text-xs uppercase tracking-wide text-muted">Completed</p>
                <p className="text-success font-semibold">{agent.jobs_completed}</p>
              </div>
              <div className="rounded-md border border-border bg-surface-elevated p-2">
                <p className="text-xs uppercase tracking-wide text-muted">Disputed</p>
                <p className="text-error font-semibold">{agent.jobs_disputed}</p>
              </div>
            </div>
          </Card>

          <Card className="lg:col-span-2">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Section 12.2 · Reputation Timeline</p>
                <h2 className="text-xl font-semibold text-body">Score over time</h2>
              </div>
            </div>
            {isEmptyEvents ? (
              <div className="rounded-md border border-border bg-surface-elevated p-4 text-sm text-muted">
                No reputation events yet.
              </div>
            ) : (
              <ReputationTimeline events={events} />
            )}
            <p className="mt-2 text-xs text-muted">
              Colored dots: green (completed) · red (disputed) · blue (KeeperHub update). Hover for details.
            </p>
          </Card>
        </div>
      )}
    </main>
  );
}
