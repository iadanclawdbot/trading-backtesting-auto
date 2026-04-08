"use client";

import { useStatus } from "@/hooks/use-api";
import { getStrategy } from "@/lib/constants";
import { formatCurrency, formatPercent, formatSharpe, timeAgo } from "@/lib/formatters";
import { Trophy } from "lucide-react";

export function ChampionCard() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-2 w-24 rounded bg-[var(--color-surface-3)]" />
          <div className="h-5 w-20 rounded bg-[var(--color-surface-3)]" />
        </div>
      </div>
    );
  }

  const champion = data?.champion;

  if (!champion) {
    return (
      <div className="panel p-4">
        <div className="section-label">Campeón actual</div>
        <div className="mt-3 flex items-center gap-2 text-[var(--color-text-2)]">
          <Trophy className="h-4 w-4 opacity-50" />
          <span className="text-[11px]">Sin campeón activo</span>
        </div>
      </div>
    );
  }

  const strat = getStrategy(champion.strategy);

  return (
    <div className="panel p-4">
      <div className="section-label mb-1">Campeón actual</div>

      {/* Strategy + capital */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="pill"
          style={{ background: `${strat.color}15`, borderColor: `${strat.color}40`, color: strat.color }}
        >
          {strat.label}
          <span className="pill" style={{ background: "var(--color-green-dim)", borderColor: "rgba(74,222,128,0.2)", color: "var(--color-green)", marginLeft: 4, padding: "0 5px", fontSize: 9 }}>
            actual
          </span>
        </span>
        <span className="num text-[15px] font-medium text-[var(--color-green)] glow-green">
          {formatCurrency(champion.capital_final)}
        </span>
      </div>

      {/* Stats rows */}
      <div className="space-y-1 text-[11px]">
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Sharpe</span>
          <span className="num text-[var(--color-text-0)]">{formatSharpe(champion.sharpe_ratio)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Win Rate</span>
          <span className="num text-[var(--color-text-0)]">{formatPercent(champion.win_rate, false)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">Trades</span>
          <span className="num text-[var(--color-text-0)]">{champion.total_trades}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-text-2)]">PnL</span>
          <span className={`num font-medium ${champion.pnl_pct >= 0 ? "text-[var(--color-green)]" : "text-[var(--color-red)]"}`}>
            {formatPercent(champion.pnl_pct)}
          </span>
        </div>
      </div>
    </div>
  );
}
