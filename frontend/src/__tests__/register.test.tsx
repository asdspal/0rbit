import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

import Page from "@/app/register/page";

// Mock router
const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

// Mock auth as connected for unit test scope
vi.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ walletSession: { address: "0xabc" } }) }));

describe("/register page", () => {
  it("shows ENS preview when typing label", async () => {
    render(React.createElement(Page));
    fireEvent.change(screen.getByLabelText(/ENS label/i), { target: { value: "bob" } });
    expect(await screen.findByText("bob.0rbit.eth")).toBeInTheDocument();
  });
});

