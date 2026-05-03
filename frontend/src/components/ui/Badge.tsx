import React from "react";

type BadgeVariant =
  | "0g"
  | "gensyn"
  | "keeperhub"
  | "uniswap"
  | "ens"
  | "posted"
  | "assigned"
  | "in_progress"
  | "completed"
  | "disputed"
  | "capability";

const badgeColors: Record<BadgeVariant, string> = {
  "0g": "bg-primary text-white",
  gensyn: "bg-secondary text-white",
  keeperhub: "bg-success text-white",
  uniswap: "bg-warning text-white",
  ens: "bg-blue-500 text-white",
  posted: "bg-warning text-white",
  assigned: "bg-primary text-white",
  in_progress: "bg-secondary text-white",
  completed: "bg-success text-white",
  disputed: "bg-error text-white",
  capability: "bg-surfaceElevated text-body border border-border",
};

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant: BadgeVariant;
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant, className = "", children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`inline-flex items-center text-xs font-semibold uppercase px-2 py-0.5 rounded-full ${badgeColors[variant]} ${className}`.trim()}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";

export default Badge;
