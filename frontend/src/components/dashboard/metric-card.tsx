import { TooltipHelp } from "./tooltip-help";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  tooltip?: string;
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
  noPad?: boolean;
}

export function MetricCard({ title, tooltip, loading, children, className, noPad }: MetricCardProps) {
  if (loading) {
    return (
      <div className={cn("panel", noPad ? "" : "p-4", className)}>
        <div className="animate-pulse space-y-3 p-4">
          <div className="h-2.5 w-20 rounded bg-[var(--color-surface-3)]" />
          <div className="h-7 w-28 rounded bg-[var(--color-surface-3)]" />
          <div className="h-2.5 w-16 rounded bg-[var(--color-surface-3)]" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("panel", noPad ? "" : "p-4", className)}>
      {/* Title row */}
      <div className={cn("flex items-center gap-1.5", noPad && "px-4 pt-4")}>
        <span className="section-label">{title}</span>
        {tooltip && <TooltipHelp term={tooltip} />}
      </div>

      {/* Content */}
      {children}
    </div>
  );
}

/* Big number display — reutilizable */
export function BigNumber({
  value,
  suffix,
  color = "var(--color-text-0)",
  glow,
  size = "lg",
}: {
  value: string;
  suffix?: string;
  color?: string;
  glow?: "green" | "red" | "amber";
  size?: "lg" | "xl";
}) {
  return (
    <span
      className={cn(
        "num font-semibold",
        size === "xl" ? "text-3xl" : "text-2xl",
        glow === "green" && "glow-green",
        glow === "red" && "glow-red",
        glow === "amber" && "glow-amber"
      )}
      style={{ color }}
    >
      {value}
      {suffix && (
        <span className="text-sm ml-1 font-medium" style={{ color }}>{suffix}</span>
      )}
    </span>
  );
}

/* Mini stat row */
export function Stat({
  label,
  value,
  tooltip,
  color,
}: {
  label: string;
  value: string;
  tooltip?: string;
  color?: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-1 mb-0.5">
        <span className="text-[11px] text-[var(--color-text-2)]">{label}</span>
        {tooltip && <TooltipHelp term={tooltip} />}
      </div>
      <span className="num text-sm font-medium" style={{ color: color ?? "var(--color-text-0)" }}>
        {value}
      </span>
    </div>
  );
}
