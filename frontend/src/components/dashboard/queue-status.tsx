"use client";

import { useStatus } from "@/hooks/use-api";
import { TooltipHelp } from "./tooltip-help";
import { formatNumber } from "@/lib/formatters";

export function QueueStatus() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-2 w-20 rounded bg-[var(--color-surface-3)]" />
          <div className="h-5 w-16 rounded bg-[var(--color-surface-3)]" />
        </div>
      </div>
    );
  }

  const queue = data?.queue;
  const done = queue?.done ?? 0;
  const failed = queue?.failed ?? 0;
  const total = done + failed;
  const rate = total > 0 ? (done / total) * 100 : 0;

  return (
    <div className="panel p-4">
      <div className="section-label mb-2">Jobs en cola</div>
      <div className="grid grid-cols-2 gap-2">
        <div className="mcard">
          <div className="lbl flex items-center gap-1">done <TooltipHelp term="queue_done" /></div>
          <div className="val up" style={{ fontSize: 15 }}>{formatNumber(done)}</div>
        </div>
        <div className="mcard">
          <div className="lbl flex items-center gap-1">failed <TooltipHelp term="queue_failed" /></div>
          <div className="val dn" style={{ fontSize: 15 }}>{formatNumber(failed)}</div>
        </div>
      </div>
      <div className="mt-2 text-[10px] text-[var(--color-text-2)]">
        Tasa de éxito: <span className="num text-[var(--color-text-0)]">{rate.toFixed(1)}%</span>
      </div>
    </div>
  );
}
