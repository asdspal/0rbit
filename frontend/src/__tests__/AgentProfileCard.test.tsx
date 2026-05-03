import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import React from "react";

import { AgentProfileCard } from "../components/agents/AgentProfileCard";

describe("AgentProfileCard", () => {
  it("renders ENS, reputation with /1000, badges and overflow", () => {
    const html = renderToString(
      React.createElement(AgentProfileCard, {
        ensName: "builder.0rbit.eth",
        reputationScore: 745,
        jobsCompleted: 12,
        capabilities: ["AI", "Data", "Agents", "Solana", "Rust", "Indexing"],
      })
    );

    // Gradient border and ENS name
    expect(html).toContain("bg-gradient-to-r");
    expect(html).toContain("builder.0rbit.eth");

    // Reputation number and denominator
    expect(html).toContain("745");
    expect(html).toContain("/1000");

    // Should be green range (>700)
    expect(html).toContain("text-success");

    // Stats and capabilities with overflow
    expect(html).toContain("Jobs Completed");
    expect(html).toContain("12");
    expect(html).toContain("AI");
    // We cap visible badges to 5 and then show overflow
    expect(html).toContain("+1 more");
  });

  it("applies warning for mid reputation and error for low", () => {
    const mid = renderToString(
      React.createElement(AgentProfileCard, {
        ensName: "mid.0rbit.eth",
        reputationScore: 500,
        jobsCompleted: 0,
        capabilities: [],
      })
    );
    expect(mid).toContain("text-warning");

    const low = renderToString(
      React.createElement(AgentProfileCard, {
        ensName: "low.0rbit.eth",
        reputationScore: 100,
        jobsCompleted: 0,
        capabilities: [],
      })
    );
    expect(low).toContain("text-error");
  });
});
