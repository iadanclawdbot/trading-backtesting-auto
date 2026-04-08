"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard, BigNumber } from "./metric-card";
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
  const rate = total > 0 ? (done / total) * 100 : 0;

  return (
    <MetricCard title="Cola de experimentos">
      <div className="mt-3 space-y-4">
        {/* Numbers */}
        <div className="flex items-end gap-6">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <span className="text-[11px] text-[var(--color-text-2)]">Completados</span>
              <TooltipHelp term="queue_done" />
            </div>
            <BigNumber value={formatNumber(done)} glow="green" color="var(--color-green)" />
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <span className="text-[11px] text-[var(--color-text-2)]">Fallidos</span>
              <TooltipHelp term="queue_failed" />
            </div>
            <span className="num text-2xl font-semibold" style={{ color: failed > 0 ? "var(--color-red)" : "var(--color-text-2)" }}>
              {formatNumber(failed)}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="pt-3 border-t border-[var(--color-border)]">
          <div className="flex justify-between text-[11px] text-[var(--color-text-2)] mb-1.5">
            <span>Tasa de éxito</span>
            <span className="num">{rate.toFixed(1)}%</span>
          </div>
          <div className="h-1 w-full rounded-full bg-[var(--color-surface-3)] overflow-hidden">
            <div
              className="h-full rounded-full bg-[var(--color-green)] transition-all duration-700"
              style={{ width: `${rate}%` }}
            />
          </div>
        </div>
      </div>
    </MetricCard>
  );
}
