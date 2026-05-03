import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import BidForm from "../components/jobs/BidForm";

// Minimal mock for next/navigation hook usage inside the component tree (if any future dependency arises)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const mockInvalidate = vi.fn();

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQueryClient: () => ({ invalidateQueries: mockInvalidate }),
  };
});

describe("BidForm", () => {
  beforeEach(() => {
    mockInvalidate.mockReset();
  });

  it("submits bid and resets form", async () => {
    const fetchTarget = globalThis as typeof globalThis & { fetch: typeof fetch };
    const mockFetch = vi.spyOn(fetchTarget, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
      text: async () => "",
    } as Response);

    render(React.createElement(BidForm, { jobId: "job-1" }));

    fireEvent.change(screen.getByLabelText(/Proposed amount/i), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText(/Message/i), { target: { value: "hello" } });

    fireEvent.click(screen.getByRole("button", { name: /Submit bid/i }));

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));
    expect(mockInvalidate).toHaveBeenCalledWith({ queryKey: ["job", "job-1"] });
    expect((screen.getByLabelText(/Proposed amount/i) as HTMLInputElement).value).toBe("");
  });
});
