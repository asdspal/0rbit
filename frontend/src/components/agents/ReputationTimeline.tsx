"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export type ReputationEvent = {
  created_at: string;
  new_score: number;
  reason: string;
  delta: number;
  job_id?: string | null;
};

export type ReputationTimelineProps = {
  events: ReputationEvent[];
  /**
   * For tests or fixed layouts where ResponsiveContainer cannot measure width in jsdom,
   * set responsive to false to render with fixed chart dimensions.
   */
  responsive?: boolean;
};

type ChartPoint = {
  time: string;
  date: Date;
  score: number;
  reason: string;
  delta: number;
  job_id?: string | null;
};

const dotColor = (reason: string): string => {
  const r = reason.toLowerCase();
  if (r === "job_completed" || r === "completed") return "#10B981"; // green/success
  if (r === "job_disputed" || r === "disputed") return "#EF4444"; // red/error
  if (r === "keeperhub_update" || r === "keeperhub") return "#3B82F6"; // blue
  return "#94A3B8"; // slate-400 muted default
};

function formatDate(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleDateString(undefined, { month: "short", day: "2-digit" });
}

type DotProps = { cx?: number; cy?: number; payload?: ChartPoint };
function CustomDot(props: DotProps) {
  const { cx, cy, payload } = props;
  if (typeof cx !== "number" || typeof cy !== "number" || !payload) return null;
  const fill = dotColor(payload.reason);
  return (
    <g>
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={fill}
        stroke="hsl(var(--ring))"
        strokeWidth={2}
        data-testid="event-dot"
        data-reason={payload.reason}
      />
    </g>
  );
}

type TooltipPayload = { payload: ChartPoint };
function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[]; label?: unknown }) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0]?.payload as ChartPoint | undefined;
  if (!p) return null;
  const signed = p.delta > 0 ? `+${p.delta}` : String(p.delta);
  const reasonLabel = p.reason
    .replace(/^job_/i, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return (
    <div className="rounded-md border border-border bg-surface-elevated p-3 text-xs shadow-md">
      <div className="mb-1 flex items-center gap-2">
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ backgroundColor: dotColor(p.reason) }}
          aria-hidden
        />
        <span className="font-medium text-body">{reasonLabel}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span className="text-muted">Date</span>
        <span className="text-body">{formatDate(p.time)}</span>
        <span className="text-muted">Delta</span>
        <span className="text-body">{signed}</span>
        <span className="text-muted">Score</span>
        <span className="text-body">{p.score}</span>
        {p.job_id && (
          <>
            <span className="text-muted">Job</span>
            <a
              className="text-primary underline underline-offset-2"
              href={`/jobs/${p.job_id}`}
            >
              {p.job_id}
            </a>
          </>
        )}
      </div>
    </div>
  );
}

export default function ReputationTimeline({ events, responsive = true }: ReputationTimelineProps) {
  const data: ChartPoint[] = useMemo(() => {
    const sorted = [...(events ?? [])].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
    return sorted.map((e) => ({
      time: e.created_at,
      date: new Date(e.created_at),
      score: e.new_score,
      reason: e.reason,
      delta: e.delta,
      job_id: e.job_id ?? undefined,
    }));
  }, [events]);

  const ChartEl = (
    <LineChart width={640} height={260} data={data} margin={{ top: 12, right: 24, bottom: 12, left: 12 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
      <XAxis
        dataKey="time"
        tickFormatter={formatDate}
        stroke="hsl(var(--muted-foreground))"
        tick={{ fontSize: 12 }}
      />
      <YAxis
        domain={[0, 1000]}
        stroke="hsl(var(--muted-foreground))"
        tick={{ fontSize: 12 }}
      />
      <Tooltip content={<CustomTooltip />} />
      <Line
        type="monotone"
        dataKey="score"
        stroke="hsl(var(--primary))"
        strokeWidth={2}
        dot={<CustomDot />}
        isAnimationActive={false}
      />
    </LineChart>
  );

  if (!responsive) return ChartEl;

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        {ChartEl}
      </ResponsiveContainer>
    </div>
  );
}
