import { cn } from "@/lib/utils";
import { TooltipHelp } from "./tooltip-help";

interface MetricCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  tooltip?: string;
  variant?: "default" | "success" | "danger" | "warning";
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
}

const variantStyles = {
  default: "",
  success: "border-[var(--color-success)]/20",
  danger: "border-[var(--color-danger)]/20",
  warning: "border-[var(--color-warning)]/20",
};

const valueStyles = {
  default: "text-[var(--color-text-primary)]",
  success: "text-[var(--color-success)]",
  danger: "text-[var(--color-danger)]",
  warning: "text-[var(--color-warning)]",
};

export function MetricCard({
  title,
  value,
  subtitle,
  tooltip,
  variant = "default",
  loading = false,
  children,
  className,
}: MetricCardProps) {
  if (loading) {
    return (
      <div
        className={cn(
          "rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4",
          className
        )}
      >
        <div className="animate-pulse space-y-3">
          <div className="h-3 w-24 rounded bg-white/10" />
          <div className="h-8 w-32 rounded bg-white/10" />
          <div className="h-3 w-20 rounded bg-white/10" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border bg-[var(--color-surface)] p-4 transition-colors",
        "border-[var(--color-border)]",
        variantStyles[variant],
        className
      )}
    >
      {/* Titulo */}
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wide">
          {title}
        </span>
        {tooltip && <TooltipHelp term={tooltip} />}
      </div>

      {/* Valor principal */}
      {value !== undefined && (
        <div
          className={cn(
            "font-mono text-2xl font-semibold tabular-nums",
            valueStyles[variant]
          )}
        >
          {value}
        </div>
      )}

      {/* Subtitulo */}
      {subtitle && (
        <div className="mt-1 text-xs text-[var(--color-text-muted)]">{subtitle}</div>
      )}

      {/* Contenido custom */}
      {children}
    </div>
  );
}
