"use client";

import { useStatus } from "@/hooks/use-api";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatSharpe, formatPercent, timeAgo } from "@/lib/formatters";

export function BestOOSCard() {
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

  const best = data?.best_oos;
  if (!best) {
    return (
      <div className="panel p-4">
        <div className="section-label">Mejor OOS</div>
        <p className="mt-2 text-[11px] text-[var(--color-text-2)]">Sin datos</p>
      </div>
    );
  }

  const strat = getStrategy(best.strategy);
  const beats = best.sharpe_ratio >= BENCHMARK_FITNESS;

  return (
    <div className="panel p-4">
      <div className="section-label mb-2">Mejor resultado OOS</div>

      <div className="flex items-center justify-between mb-2">
        <span className="pill" style={{ background: `${strat.color}15`, borderColor: `${strat.color}40`, color: strat.color }}>
          {strat.label}
        </span>
        {beats && (
          <span className="pill" style={{ background: "var(--color-green-dim)", borderColor: "rgba(74,222,128,0.2)", color: "var(--color-green)", fontSize: 9 }}>
            ✓ benchmark
          </span>
        )}
      </div>

      <div className="space-y-1 text-[11px]">
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Sharpe OOS</span>
          <span className="num font-medium text-[var(--color-text-0)]">{formatSharpe(best.sharpe_ratio)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Win Rate</span>
          <span className="num text-[var(--color-text-0)]">{formatPercent(best.win_rate, false)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Max DD</span>
          <span className="num text-[var(--color-red)]">{formatPercent(best.max_drawdown)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Trades</span>
          <span className="num text-[var(--color-text-0)]">{best.total_trades}</span>
        </div>
      </div>

      <div className="mt-2 text-[10px] text-[var(--color-text-2)] num">{timeAgo(best.created_at)}</div>
    </div>
  );
}
