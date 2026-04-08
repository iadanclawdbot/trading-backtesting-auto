"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatSharpe, formatPercent, timeAgo } from "@/lib/formatters";

export function BestOOSCard() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Mejor resultado OOS" loading />;
  }

  const best = data?.best_oos;
  if (!best) {
    return (
      <MetricCard title="Mejor resultado OOS">
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">Sin datos</p>
      </MetricCard>
    );
  }

  const strategy = getStrategy(best.strategy);
  const beatsBenchmark = best.sharpe_ratio > BENCHMARK_FITNESS;

  return (
    <MetricCard
      title="Mejor resultado OOS"
      variant={beatsBenchmark ? "success" : "default"}
    >
      {/* Estrategia */}
      <div className="mt-2 mb-3">
        <span
          className="inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium"
          style={{
            backgroundColor: `${strategy.color}20`,
            color: strategy.color,
            border: `1px solid ${strategy.color}40`,
          }}
        >
          {strategy.label}
        </span>
      </div>

      {/* Sharpe principal */}
      <div className="flex items-baseline gap-2 mb-1">
        <div className="flex items-center gap-1">
          <span className="font-mono text-2xl font-bold text-[var(--color-text-primary)]">
            {formatSharpe(best.sharpe_ratio)}
          </span>
          <TooltipHelp term="sharpe_oos" />
        </div>
        {beatsBenchmark && (
          <span className="text-xs text-[var(--color-success)]">✓ supera benchmark</span>
        )}
      </div>
      <p className="text-xs text-[var(--color-text-muted)] mb-3">Sharpe OOS</p>

      {/* Grid de stats */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-[var(--color-border)]">
        <div>
          <div className="flex items-center gap-1 mb-1">
            <span className="text-xs text-[var(--color-text-muted)]">Win Rate</span>
            <TooltipHelp term="win_rate" />
          </div>
          <span className="font-mono text-sm font-medium">
            {formatPercent(best.win_rate, false)}
          </span>
        </div>
        <div>
          <div className="flex items-center gap-1 mb-1">
            <span className="text-xs text-[var(--color-text-muted)]">Max DD</span>
            <TooltipHelp term="max_drawdown" />
          </div>
          <span
            className="font-mono text-sm font-medium"
            style={{ color: "var(--color-danger)" }}
          >
            {formatPercent(best.max_drawdown)}
          </span>
        </div>
        <div>
          <span className="text-xs text-[var(--color-text-muted)] block mb-1">Trades</span>
          <span className="font-mono text-sm font-medium">{best.total_trades}</span>
        </div>
      </div>

      <p className="mt-3 text-xs text-[var(--color-text-muted)]">
        {timeAgo(best.created_at)}
      </p>
    </MetricCard>
  );
}
