"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard, BigNumber, Stat } from "./metric-card";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatCurrency, formatPercent, formatSharpe } from "@/lib/formatters";
import { Trophy } from "lucide-react";

export function ChampionCard() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Campeón actual" loading />;
  }

  const champion = data?.champion;

  if (!champion) {
    return (
      <MetricCard title="Campeón actual">
        <div className="mt-4 flex items-center gap-3 text-[var(--color-text-2)]">
          <Trophy className="h-5 w-5" />
          <span className="text-sm">Sin campeón — el sistema está explorando</span>
        </div>
      </MetricCard>
    );
  }

  const strat = getStrategy(champion.strategy);
  const pnlPositive = champion.pnl_pct >= 0;

  return (
    <MetricCard title="Campeón actual">
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

        {/* Capital + PnL */}
        <div className="flex items-baseline gap-2.5">
          <BigNumber
            value={formatCurrency(champion.capital_final)}
            glow={pnlPositive ? "green" : "red"}
          />
          <span
            className="num text-sm font-semibold"
            style={{ color: pnlPositive ? "var(--color-green)" : "var(--color-red)" }}
          >
            {formatPercent(champion.pnl_pct)}
          </span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-4 pt-3 border-t border-[var(--color-border)]">
          <Stat label="Sharpe" value={formatSharpe(champion.sharpe_ratio)} tooltip="sharpe_ratio" />
          <Stat label="Win Rate" value={formatPercent(champion.win_rate, false)} tooltip="win_rate" />
          <Stat label="Trades" value={String(champion.total_trades)} tooltip="total_trades" />
        </div>
      </div>
    </MetricCard>
  );
}
