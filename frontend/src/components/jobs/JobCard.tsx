import React from "react";
import Badge from "../ui/Badge";

type JobCardProps = {
  id: string;
  title: string;
  status: "posted" | "assigned" | "in_progress" | "completed" | "disputed";
  capabilities: string[];
  escrowAmount: string;
  deadline: string;
  bidCount: number;
  onClick?: (id: string) => void;
};

const statusLabel: Record<JobCardProps["status"], string> = {
  posted: "Posted",
  assigned: "Assigned",
  in_progress: "In Progress",
  completed: "Completed",
  disputed: "Disputed",
};

export const JobCard: React.FC<JobCardProps> = ({
  id,
  title,
  status,
  capabilities,
  escrowAmount,
  deadline,
  bidCount,
  onClick,
}) => {
  const MAX_CAPABILITIES = 5;
  // Show first MAX-1 and always include the last capability when overflowing
  // This ensures the most specific/recent cap (often last) is visible while still indicating overflow
  const hasOverflow = capabilities.length > MAX_CAPABILITIES;
  const visibleCapabilities = hasOverflow
    ? [...capabilities.slice(0, MAX_CAPABILITIES - 1), capabilities[capabilities.length - 1]]
    : capabilities.slice(0, MAX_CAPABILITIES);
  const overflowCount = capabilities.length - visibleCapabilities.length;

  return (
    <button
      type="button"
      onClick={() => onClick?.(id)}
      className="w-full text-left bg-surface border border-border rounded-lg p-4 hover:border-primary hover:shadow-[0_0_15px_rgba(124,58,237,0.2)] transition-all duration-200 cursor-pointer space-y-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={status}>{statusLabel[status]}</Badge>

        {visibleCapabilities.map((capability) => (
          <Badge key={capability} variant="capability" className="text-xs font-medium normal-case">
            {capability}
          </Badge>
        ))}

        {overflowCount > 0 && (
          <span className="text-sm text-muted">{`+${overflowCount} more`}</span>
        )}
      </div>

      <h3 className="text-body font-semibold text-lg leading-tight">{title}</h3>

      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="text-secondary font-semibold">{escrowAmount}</span>
        <span className="text-muted">{deadline}</span>
        <span className="text-muted">{`${bidCount} bids`}</span>
      </div>
    </button>
  );
};

export default JobCard;
