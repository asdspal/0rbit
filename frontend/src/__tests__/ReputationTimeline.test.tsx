import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ReputationTimeline, { type ReputationEvent } from "@/components/agents/ReputationTimeline";

describe("ReputationTimeline", () => {
  const base: Omit<ReputationEvent, "created_at"> = {
    new_score: 600,
    reason: "job_completed",
    delta: 10,
    job_id: "job-1",
  };

  const events: ReputationEvent[] = [
    { ...base, created_at: "2024-01-01T00:00:00Z", reason: "job_completed", delta: 25, new_score: 525, job_id: "a" },
    { ...base, created_at: "2024-02-01T00:00:00Z", reason: "job_disputed", delta: -40, new_score: 485, job_id: "b" },
    { ...base, created_at: "2024-03-01T00:00:00Z", reason: "keeperhub_update", delta: 15, new_score: 500, job_id: null },
    { ...base, created_at: "2024-04-01T00:00:00Z", reason: "other", delta: 0, new_score: 500, job_id: undefined },
  ];

  it("renders a dot for each event", () => {
    render(<ReputationTimeline events={events} responsive={false} />);
    const dots = screen.getAllByTestId("event-dot");
    expect(dots).toHaveLength(events.length);
  });

  it("uses expected colors per reason", () => {
    render(<ReputationTimeline events={events} responsive={false} />);
    const dots = screen.getAllByTestId("event-dot");
    const fills = dots.map((d) => ((d as unknown) as SVGCircleElement).getAttribute("fill"));
    // job_completed → green
    expect(fills[0]).toBe("#10B981");
    // job_disputed → red
    expect(fills[1]).toBe("#EF4444");
    // keeperhub_update → blue
    expect(fills[2]).toBe("#3B82F6");
    // other → muted
    expect(fills[3]).toBe("#94A3B8");
  });
});
