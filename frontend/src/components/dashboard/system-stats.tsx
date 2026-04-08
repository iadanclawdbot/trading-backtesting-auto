"use client";

import { useSystemMetrics } from "@/hooks/use-api";
import { formatNumber } from "@/lib/formatters";
import { Database, FlaskConical, BarChart3, Layers } from "lucide-react";

export function SystemStats() {
  const { data, isLoading } = useSystemMetrics();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-2 w-24 rounded bg-[var(--color-surface-3)]" />
          <div className="h-16 w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const stats = [
    { icon: FlaskConical, label: "Experimentos", value: formatNumber(data?.total_experiments ?? 0), color: "var(--color-vwap)" },
    { icon: BarChart3, label: "Runs", value: formatNumber(data?.total_runs ?? 0), color: "var(--color-breakout)" },
    { icon: Layers, label: "Trades", value: formatNumber(data?.total_trades ?? 0), color: "var(--color-amber)" },
    { icon: Database, label: "DB size", value: `${data?.db_size_mb ?? 0} MB`, color: "var(--color-cat-research)" },
  ];

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="section-label">Infraestructura</div>
        <span className="text-[10px] text-[var(--color-text-2)] num">
          {data?.strategies_tested ?? 0} estrategias · {formatNumber(data?.total_candle_states ?? 0)} candle states
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {stats.map((s) => (
          <div key={s.label} className="mcard">
            <div className="lbl flex items-center gap-1">
              <s.icon className="h-3 w-3" style={{ color: s.color }} />
              {s.label}
            </div>
            <div className="val" style={{ fontSize: 14 }}>{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
