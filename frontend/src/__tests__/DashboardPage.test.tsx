import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
// react-query provider is supplied by WagmiProvider wrapper
import { WagmiProvider } from "@/components/providers/WagmiProvider";

import DashboardPage from "../app/dashboard/page";

// Router mock
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

function renderWithProviders(ui: React.ReactElement) {
  // WagmiProvider also mounts QueryClientProvider internally, but to avoid double providers
  // we only wrap with WagmiProvider here for wagmi + react-query context.
  return render(<WagmiProvider>{ui}</WagmiProvider>);
}

describe("/dashboard page", () => {
  beforeEach(() => {
    replace.mockReset();
  });

  it("redirects when unauthenticated", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: false } as Response);
    renderWithProviders(<DashboardPage />);
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"));
    fetchSpy.mockRestore();
  });

  it("renders sections when authenticated and shows posted jobs filtered by poster", async () => {
    const me = { address: "0xPoster", agent_id: "agent-1", ens_name: null };
    const jobsIndex = {
      data: [
        {
          id: "job-1",
          title: "Test Job",
          description: "d",
          required_capabilities: ["code"],
          escrow_amount: "100 USDC",
          deadline: new Date().toISOString(),
          status: "posted",
          poster_address: "0xPoster",
        },
        {
          id: "job-2",
          title: "Other's Job",
          description: "d",
          required_capabilities: ["code"],
          escrow_amount: "100 USDC",
          deadline: new Date().toISOString(),
          status: "posted",
          poster_address: "0xSomeoneElse",
        },
      ],
      cursor: null,
    };

    const jobShow = (id: string) => ({
      id,
      title: id === "job-1" ? "Test Job" : "Other's Job",
      description: "d",
      required_capabilities: ["code"],
      escrow_amount: "100 USDC",
      deadline: new Date().toISOString(),
      status: "posted",
      poster_address: id === "job-1" ? "0xPoster" : "0xSomeoneElse",
      bids: [],
    });

    const agentJobs = { data: [], cursor: null };
    const agentRep = { data: [], cursor: null };

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/v1/auth/me")) {
        return { ok: true, json: async () => me } as Response;
      }
      if (url.includes("/v1/jobs?")) {
        return { ok: true, json: async () => jobsIndex } as Response;
      }
      if (url.match(/\/v1\/jobs\/.+$/)) {
        const id = url.split("/v1/jobs/")[1];
        return { ok: true, json: async () => jobShow(id) } as Response;
      }
      if (url.includes("/v1/agents/agent-1/jobs")) {
        return { ok: true, json: async () => agentJobs } as Response;
      }
      if (url.includes("/v1/agents/agent-1/reputation")) {
        return { ok: true, json: async () => agentRep } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    renderWithProviders(<DashboardPage />);

    // Wait for title and the one posted job to appear
    await waitFor(() => expect(screen.getByText(/My Dashboard/)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText("Test Job")).toBeInTheDocument());
    expect(screen.queryByText("Other's Job")).not.toBeInTheDocument();

    fetchSpy.mockRestore();
  });
});
