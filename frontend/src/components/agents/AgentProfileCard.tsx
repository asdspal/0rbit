import React from "react";
import Badge from "@/components/ui/Badge";

type AgentProfileCardProps = {
  ensName: string;
  reputationScore: number;
  jobsCompleted: number;
  capabilities: string[];
};

const getReputationColor = (score: number) => {
  if (score < 400) return "text-error";
  if (score <= 700) return "text-warning";
  return "text-success";
};

export function AgentProfileCard({
  ensName,
  reputationScore,
  jobsCompleted,
  capabilities,
}: AgentProfileCardProps) {
  const MAX_CAPABILITIES = 5;
  const visibleCapabilities = capabilities.slice(0, MAX_CAPABILITIES);
  const overflowCount = capabilities.length - visibleCapabilities.length;
  const reputationColor = getReputationColor(reputationScore);

  const repClass = "text-lg font-semibold " + reputationColor;

  return (
    <div className="animate-gradient-border rounded-lg bg-gradient-to-r from-primary to-secondary p-[1px]">
      <div className="rounded-lg bg-surface p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-sm uppercase tracking-wide text-muted">Agent</p>
            <h3 className="text-xl font-bold text-secondary">{ensName}</h3>
          </div>

          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-muted">Reputation</p>
            <p className={repClass}>
              {reputationScore}
              <span className="text-sm text-muted">/1000</span>
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 text-sm">
          <div className="rounded-md border border-border bg-surface-elevated px-3 py-2">
            <p className="text-xs uppercase tracking-wide text-muted">Jobs Completed</p>
            <p className="text-base font-semibold text-body">{jobsCompleted}</p>
          </div>
        </div>

        <div className="mt-4">
          <p className="text-xs uppercase tracking-wide text-muted">Capabilities</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {visibleCapabilities.length === 0 && (
              <span className="text-sm text-muted">No capabilities listed</span>
            )}
            {visibleCapabilities.map((capability) => (
              <Badge
                key={capability}
                variant="capability"
                className="text-xs font-medium normal-case"
              >
                {capability}
              </Badge>
            ))}
            {overflowCount > 0 && (
              <span className="text-sm text-muted">{`+${overflowCount} more`}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentProfileCard;
