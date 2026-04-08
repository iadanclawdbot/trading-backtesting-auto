"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard, BigNumber, Stat } from "./metric-card";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatSharpe, formatPercent, timeAgo } from "@/lib/formatters";

export function BestOOSCard() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Mejor OOS" loading />;
  }

  const best = data?.best_oos;
  if (!best) {
    return (
      <MetricCard title="Mejor OOS">
        <p className="mt-3 text-sm text-[var(--color-text-2)]">Sin datos</p>
      </MetricCard>
    );
  }

  const strat = getStrategy(best.strategy);
  const beats = best.sharpe_ratio > BENCHMARK_FITNESS;

  return (
    <MetricCard title="Mejor OOS" tooltip="sharpe_oos">
      <div className="mt-3 space-y-4">
        {/* Strategy pill */}
        <span
          className="pill"
          style={{
            background: `${strat.color}15`,
            borderColor: `${strat.color}40`,
            color: strat.color,
          }}
        >
          <span className="dot" style={{ background: strat.color }} />
          {strat.label}
        </span>

        {/* Sharpe hero */}
        <div className="flex items-baseline gap-3">
          <BigNumber value={formatSharpe(best.sharpe_ratio)} glow={beats ? "green" : undefined} />
          {beats && (
            <span className="text-xs text-[var(--color-green)] font-medium">
              ✓ supera benchmark
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 pt-3 border-t border-[var(--color-border)]">
          <Stat label="Win Rate" value={formatPercent(best.win_rate, false)} tooltip="win_rate" />
          <Stat label="Max DD" value={formatPercent(best.max_drawdown)} tooltip="max_drawdown" color="var(--color-red)" />
          <Stat label="Trades" value={String(best.total_trades)} />
        </div>

        <p className="text-[10px] text-[var(--color-text-2)] num">{timeAgo(best.created_at)}</p>
      </div>
    </MetricCard>
  );
}
