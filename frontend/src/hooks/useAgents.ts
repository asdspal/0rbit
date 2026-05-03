import { useInfiniteQuery, type InfiniteData } from "@tanstack/react-query";
import { useMemo } from "react";

export type AgentStatus = "active" | "suspended" | "inactive";

export type Agent = {
  id: string;
  wallet_address: string;
  ens_name: string | null;
  axl_peer_id: string;
  encrypted_uri: string;
  capabilities: string[];
  reputation_score: number;
  jobs_completed: number;
  jobs_disputed: number;
  status: AgentStatus;
  created_at?: string;
  updated_at?: string;
};

type AgentsResponse = {
  data: Agent[];
  cursor: string | null;
};

export type UseAgentsFilters = {
  capabilities?: string[];
  minRep?: number;
  status?: AgentStatus | "all";
  limit?: number;
};

type NormalizedFilters = {
  capabilities?: string[];
  minRep?: number;
  status?: AgentStatus;
  limit: number;
};

export function normalizeAgentFilters(filters: UseAgentsFilters): NormalizedFilters {
  return {
    capabilities:
      filters.capabilities && filters.capabilities.length > 0
        ? Array.from(new Set(filters.capabilities)).sort()
        : undefined,
    minRep: typeof filters.minRep === "number" ? filters.minRep : undefined,
    status: filters.status && filters.status !== "all" ? filters.status : undefined,
    limit: filters.limit ?? 12,
  };
}

export function buildAgentsQueryParams(
  filters: NormalizedFilters,
  pageCursor?: string | null
): string {
  const params = new URLSearchParams();

  filters.capabilities?.forEach((capability) => params.append("capabilities[]", capability));
  if (filters.minRep !== undefined) params.set("min_rep", String(filters.minRep));
  if (filters.status) params.set("status", filters.status);
  params.set("limit", String(filters.limit));
  if (pageCursor) params.set("cursor", pageCursor);

  return params.toString();
}

async function fetchAgentsPage(
  filters: NormalizedFilters,
  pageCursor?: string | null
): Promise<AgentsResponse> {
  const queryString = buildAgentsQueryParams(filters, pageCursor);
  const response = await fetch(`/v1/agents?${queryString}`, { credentials: "include" });

  if (!response.ok) {
    throw new Error("Failed to load agents");
  }

  const json = (await response.json()) as AgentsResponse;
  if (!json || !Array.isArray(json.data)) {
    throw new Error("Invalid agents response");
  }

  return json;
}

export function useAgents(filters: UseAgentsFilters) {
  const normalized = useMemo(() => normalizeAgentFilters(filters), [filters]);

  const query = useInfiniteQuery<AgentsResponse, Error, AgentsResponse, ["agents", NormalizedFilters], string | null>({
    queryKey: ["agents", normalized],
    initialPageParam: null,
    queryFn: ({ pageParam }) => fetchAgentsPage(normalized, pageParam),
    getNextPageParam: (lastPage) => lastPage.cursor,
  });

  const agents = useMemo<Agent[]>(() => {
    const pages = (query.data as InfiniteData<AgentsResponse, string | null> | undefined)?.pages ?? [];
    return pages.flatMap((page) => page.data);
  }, [query.data]);

  const availableCapabilities = useMemo(() => {
    const caps = new Set<string>();
    agents.forEach((agent: Agent) => {
      agent.capabilities?.forEach((cap: string) => caps.add(cap));
    });
    return Array.from(caps).sort();
  }, [agents]);

  return {
    agents,
    availableCapabilities,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: query.hasNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}

export type UseAgentsReturn = ReturnType<typeof useAgents>;
