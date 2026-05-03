import { useInfiniteQuery, type InfiniteData } from "@tanstack/react-query";
import { useMemo } from "react";

export type JobStatus = "posted" | "assigned" | "in_progress" | "completed" | "disputed";

export type Job = {
  id: string;
  title: string;
  status: JobStatus;
  required_capabilities: string[];
  escrow_amount: string;
  deadline: string;
  bid_count?: number;
  created_at?: string;
  updated_at?: string;
};

type JobsResponse = {
  data: Job[];
  cursor: string | null;
};

export type UseJobsFilters = {
  status?: JobStatus | "all";
  capabilities?: string[];
  sort?: "created_at" | "deadline";
  limit?: number;
};

type NormalizedFilters = {
  status?: JobStatus;
  capabilities?: string[];
  sort: "created_at" | "deadline";
  limit: number;
};

export function normalizeFilters(filters: UseJobsFilters): NormalizedFilters {
  return {
    status: filters.status && filters.status !== "all" ? filters.status : undefined,
    capabilities: filters.capabilities && filters.capabilities.length > 0
      ? Array.from(new Set(filters.capabilities)).sort()
      : undefined,
    sort: filters.sort ?? "created_at",
    limit: filters.limit ?? 12,
  };
}

export function buildJobsQueryParams(filters: NormalizedFilters, pageCursor?: string | null): string {
  const params = new URLSearchParams();

  if (filters.status) params.set("status", filters.status);
  filters.capabilities?.forEach((capability) => params.append("capabilities[]", capability));
  params.set("sort", filters.sort);
  params.set("limit", String(filters.limit));
  if (pageCursor) params.set("cursor", pageCursor);

  return params.toString();
}

async function fetchJobsPage(filters: NormalizedFilters, pageCursor?: string | null): Promise<JobsResponse> {
  const queryString = buildJobsQueryParams(filters, pageCursor);
  const response = await fetch(`/v1/jobs?${queryString}`, { credentials: "include" });

  if (!response.ok) {
    throw new Error("Failed to load jobs");
  }

  const json = (await response.json()) as JobsResponse;

  if (!json || !Array.isArray(json.data)) {
    throw new Error("Invalid jobs response");
  }

  return json;
}

export function useJobs(filters: UseJobsFilters) {
  const normalized = useMemo(() => normalizeFilters(filters), [filters]);

  const query = useInfiniteQuery<JobsResponse, Error, JobsResponse, ["jobs", NormalizedFilters], string | null>({
    queryKey: ["jobs", normalized],
    initialPageParam: null,
    queryFn: ({ pageParam }) => fetchJobsPage(normalized, pageParam),
    getNextPageParam: (lastPage) => lastPage.cursor,
  });

  const jobs = useMemo<Job[]>(() => {
    const pages = (query.data as InfiniteData<JobsResponse, string | null> | undefined)?.pages ?? [];
    return pages.flatMap((page) => page.data);
  }, [query.data]);

  const availableCapabilities = useMemo(() => {
    const caps = new Set<string>();
    jobs.forEach((job: Job) => {
      job.required_capabilities?.forEach((cap: string) => caps.add(cap));
    });
    return Array.from(caps).sort();
  }, [jobs]);

  return {
    jobs,
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

export type UseJobsReturn = ReturnType<typeof useJobs>;
