"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { formatNumber } from "@/lib/formatters";

export function QueueStatus() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Cola de experimentos" loading />;
  }

  const queue = data?.queue;
  const done = queue?.done ?? 0;
  const failed = queue?.failed ?? 0;
  const total = done + failed;
  const successRate = total > 0 ? (done / total) * 100 : 0;

  return (
    <MetricCard title="Cola de experimentos">
      <div className="mt-3 space-y-3">
        {/* Done y Failed */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <span className="text-xs text-[var(--color-text-muted)]">Completados</span>
              <TooltipHelp term="queue_done" />
            </div>
            <span className="font-mono text-xl font-semibold text-[var(--color-success)]">
              {formatNumber(done)}
            </span>
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <span className="text-xs text-[var(--color-text-muted)]">Fallidos</span>
              <TooltipHelp term="queue_failed" />
            </div>
            <span
              className="font-mono text-xl font-semibold"
              style={{
                color:
                  failed > 0
                    ? "var(--color-danger)"
                    : "var(--color-text-muted)",
              }}
            >
              {formatNumber(failed)}
            </span>
          </div>
        </div>

        {/* Barra de exito */}
        <div>
          <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-1">
            <span>Tasa de éxito</span>
            <span className="font-mono">{successRate.toFixed(1)}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-[var(--color-success)] transition-all duration-500"
              style={{ width: `${successRate}%` }}
            />
          </div>
        </div>
      </div>
    </MetricCard>
  );
}
