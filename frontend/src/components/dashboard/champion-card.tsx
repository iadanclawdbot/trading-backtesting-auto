"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { getStrategy } from "@/lib/constants";
import { formatCurrency, formatPercent, formatSharpe } from "@/lib/formatters";
import { Trophy } from "lucide-react";

function StatItem({
  label,
  value,
  tooltip,
}: {
  label: string;
  value: string;
  tooltip?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-center gap-1">
        <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
        {tooltip && <TooltipHelp term={tooltip} />}
      </div>
      <span className="font-mono text-sm font-medium text-[var(--color-text-primary)]">
        {value}
      </span>
    </div>
  );
}

export function ChampionCard() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Campeón actual" loading />;
  }

  const champion = data?.champion;

  if (!champion) {
    return (
      <MetricCard title="Campeón actual">
        <div className="mt-3 flex flex-col items-center justify-center gap-2 py-4">
          <Trophy className="h-8 w-8 text-[var(--color-text-muted)]" />
          <p className="text-sm text-[var(--color-text-muted)] text-center">
            Aún no hay un campeón. El sistema está explorando estrategias.
          </p>
        </div>
      </MetricCard>
    );
  }

  const strategy = getStrategy(champion.strategy);
  const pnlPositive = champion.pnl_pct >= 0;

  return (
    <MetricCard title="Campeón actual" variant={pnlPositive ? "success" : "danger"}>
      {/* Badge de estrategia */}
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

      {/* Capital principal */}
      <div className="flex items-baseline gap-2 mb-1">
        <span className="font-mono text-2xl font-bold text-[var(--color-text-primary)]">
          {formatCurrency(champion.capital_final)}
        </span>
        <span
          className="text-sm font-mono font-medium"
          style={{
            color: pnlPositive
              ? "var(--color-success)"
              : "var(--color-danger)",
          }}
        >
          {formatPercent(champion.pnl_pct)}
        </span>
      </div>

      {/* Grid de metricas */}
      <div className="grid grid-cols-3 gap-3 mt-4 pt-3 border-t border-[var(--color-border)]">
        <StatItem
          label="Sharpe"
          value={formatSharpe(champion.sharpe_ratio)}
          tooltip="sharpe_ratio"
        />
        <StatItem
          label="Win Rate"
          value={formatPercent(champion.win_rate, false)}
          tooltip="win_rate"
        />
        <StatItem
          label="Trades"
          value={String(champion.total_trades)}
          tooltip="total_trades"
        />
      </div>
    </MetricCard>
  );
}
