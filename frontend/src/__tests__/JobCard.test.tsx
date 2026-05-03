import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";

import React from "react";
import { JobCard } from "../components/jobs/JobCard";

describe("JobCard", () => {
  it("renders status, caps with overflow, and footer fields", () => {
    const html = renderToString(
      React.createElement(JobCard, {
        id: "job-1",
        title: "Build data pipeline",
        status: "in_progress",
        capabilities: ["AI", "Data", "Agents", "Solana", "Rust", "Indexing"],
        escrowAmount: "$1,200 USDC",
        deadline: "Due in 3 days",
        bidCount: 7,
      })
    );

    expect(html).toContain("In Progress");
    expect(html).toContain("AI");
    expect(html).toContain("Indexing");
    expect(html).toContain("+1 more");
    expect(html).toContain("$1,200 USDC");
    expect(html).toContain("Due in 3 days");
    expect(html).toContain("7 bids");
  });
});
