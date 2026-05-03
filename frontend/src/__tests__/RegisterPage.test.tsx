import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";

import Page from "@/app/register/page";

// Mock router to capture redirects
const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

// Mock auth hook to simulate connected wallet
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ walletSession: { address: "0x1234" } }),
}));

describe("Register Agent Page", () => {
  beforeEach(() => {
    push.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders form fields and ENS preview updates", async () => {
    render(React.createElement(Page));

    // ENS label input present
    const ensInput = screen.getByLabelText(/ENS label/i);
    fireEvent.change(ensInput, { target: { value: "alice" } });

    // Preview shows full ENS
    expect(await screen.findByText("alice.0rbit.eth")).toBeInTheDocument();

    // Other fields present
    expect(screen.getByLabelText(/AXL peer ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Encrypted URI/i)).toBeInTheDocument();
  });

  it("validates ENS label against lowercase-hyphen regex", async () => {
    render(React.createElement(Page));

    fireEvent.change(screen.getByLabelText(/ENS label/i), { target: { value: "Alice" } });
    const [submit] = screen.getAllByRole("button", { name: /Register Agent/i });
    fireEvent.click(submit);

    // Multiple field errors may render at once; assert specifically on the ENS label message
    expect(
      await screen.findByText(/Lowercase letters, numbers, and hyphens only/i)
    ).toBeInTheDocument();
  });

  it("submits payload and redirects on success", async () => {
    const fetchTarget = globalThis as typeof globalThis & { fetch: typeof fetch };
    const mockFetch = vi.spyOn(fetchTarget, "fetch").mockResolvedValue({
      ok: true,
      text: async () => "",
      json: async () => ({}),
    } as Response);

    render(React.createElement(Page));

    fireEvent.change(screen.getByLabelText(/ENS label/i), { target: { value: "alice" } });
    fireEvent.change(screen.getByLabelText(/AXL peer ID/i), { target: { value: "peer-123" } });
    fireEvent.change(screen.getByLabelText(/Encrypted URI/i), { target: { value: "og://root" } });

    // Select a capability
    fireEvent.click(screen.getByLabelText(/code/i));

    const [submit] = screen.getAllByRole("button", { name: /Register Agent/i });
    fireEvent.click(submit);

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    const [url, init] = mockFetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/v1/agents/register");
    expect(init?.method).toBe("POST");
    const body = JSON.parse(String(init?.body ?? "{}"));
    expect(body).toEqual({
      ens_label: "alice",
      axl_peer_id: "peer-123",
      capabilities: ["code"],
      encrypted_uri: "og://root",
    });

    expect(push).toHaveBeenCalledWith("/agents/alice.0rbit.eth");
  });
});
