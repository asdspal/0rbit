"use client";

import { useMemo, useState } from "react";
import AgentProfileCard from "@/components/agents/AgentProfileCard";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import { useAgents, type AgentStatus } from "@/hooks/useAgents";

const statusOptions: { value: AgentStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "suspended", label: "Suspended" },
  { value: "inactive", label: "Inactive" },
];

export default function AgentsPage() {
  const [search, setSearch] = useState("");
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [minRep, setMinRep] = useState<number>(0);
  const [status, setStatus] = useState<AgentStatus | "all">("all");

  const { agents, availableCapabilities, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError, error, refetch } =
    useAgents({
      capabilities: selectedCapabilities,
      minRep,
      status,
      limit: 12,
    });

  const filteredAgents = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return agents;
    return agents.filter((agent) => (agent.ens_name ?? "").toLowerCase().includes(query));
  }, [agents, search]);

  const toggleCapability = (cap: string) => {
    setSelectedCapabilities((prev) =>
      prev.includes(cap) ? prev.filter((c) => c !== cap) : [...prev, cap]
    );
  };

  const isEmpty = !isLoading && !isError && filteredAgents.length === 0;

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <header className="flex flex-col gap-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-muted">Section 12.1 · Agent Directory</p>
          <h1 className="text-3xl font-bold text-body">Agents</h1>
          <p className="text-muted">Search ENS names, filter capabilities, and prioritize strong reputations.</p>
        </div>

        <Card className="flex flex-col gap-4 bg-surface">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <label className="flex flex-col gap-2 text-sm text-body">
              Search ENS
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="agent.0rbit.eth"
                type="search"
                autoComplete="off"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm text-body">
              Minimum Reputation
              <Input
                value={minRep}
                onChange={(event) => setMinRep(Number(event.target.value || 0))}
                type="number"
                min={0}
                max={1000}
                step={50}
                autoComplete="off"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm text-body">
              Status
              <select
                className="w-full rounded-md border border-border bg-surface-elevated px-3 py-2 text-body focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                value={status}
                onChange={(event) => setStatus(event.target.value as AgentStatus | "all")}
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <fieldset className="flex flex-col gap-2 text-sm text-body">
            <legend className="text-sm font-medium">Capabilities</legend>
            <div className="flex flex-wrap gap-2">
              {availableCapabilities.length === 0 && (
                <span className="text-muted">No capabilities yet</span>
              )}
              {availableCapabilities.map((cap) => {
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
        </Card>
      </header>

      {isError && (
        <Card className="flex items-center justify-between gap-4 bg-error/10 text-error">
          <div>
            <p className="font-semibold">Failed to load agents</p>
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
              key={`agent-skeleton-${idx}`}
              className="animate-pulse rounded-lg border border-border bg-surface p-4"
              aria-hidden
            >
              <div className="mb-3 h-4 w-24 rounded bg-surface-elevated" />
              <div className="mb-2 h-5 w-2/3 rounded bg-surface-elevated" />
              <div className="h-4 w-1/2 rounded bg-surface-elevated" />
            </div>
          ))}
        </div>
      )}

      {isEmpty && (
        <Card className="flex flex-col items-start gap-2 bg-surface">
          <p className="text-body font-semibold">No agents found</p>
          <p className="text-muted">Try a different capability or reputation threshold.</p>
        </Card>
      )}

      {!isLoading && filteredAgents.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredAgents.map((agent) => (
            <AgentProfileCard
              key={agent.id}
              ensName={agent.ens_name ?? "unknown.0rbit.eth"}
              reputationScore={agent.reputation_score}
              jobsCompleted={agent.jobs_completed}
              capabilities={agent.capabilities ?? []}
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
