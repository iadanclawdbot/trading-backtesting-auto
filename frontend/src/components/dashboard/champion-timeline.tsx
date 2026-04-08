"use client";

import { useChampionHistory } from "@/hooks/use-api";
import { getStrategy } from "@/lib/constants";
import { formatCurrency, formatSharpe, timeAgo } from "@/lib/formatters";
import { Crown } from "lucide-react";

export function ChampionTimeline() {
  const { data, isLoading } = useChampionHistory();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-2 w-32 rounded bg-[var(--color-surface-3)]" />
          <div className="h-12 w-full rounded bg-[var(--color-surface-0)]" />
          <div className="h-12 w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const champions = data?.champions ?? [];

  if (champions.length === 0) {
    return (
      <div className="panel p-4">
        <div className="section-label">Historial de campeones</div>
        <div className="mt-3 flex items-center gap-2 text-[var(--color-text-2)]">
          <Crown className="h-4 w-4 opacity-50" />
          <span className="text-[11px]">Sin campeones aún</span>
        </div>
      </div>
    );
  }

  // Show latest first
  const sorted = [...champions].reverse();
  const best = Math.max(...champions.map((c) => c.capital_final));

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="section-label">Historial de campeones</div>
        <span className="text-[10px] text-[var(--color-text-2)] num">{champions.length} coronados</span>
      </div>

      <div className="space-y-0 relative">
        {/* Vertical timeline line */}
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-[var(--color-surface-3)]" />

        {sorted.map((champ, i) => {
          const strat = getStrategy(champ.strategy);
          const isBest = champ.capital_final === best;
          const isLatest = i === 0;

          return (
            <div key={champ.id} className="relative pl-6 py-1.5 group">
              {/* Timeline dot */}
              <div
                className="absolute left-0.5 top-3 h-3 w-3 rounded-full border-2"
                style={{
                  borderColor: isLatest ? "var(--color-green)" : "var(--color-surface-3)",
                  background: isLatest ? "var(--color-green)" : "var(--color-surface-1)",
                }}
              />

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="pill"
                    style={{
                      background: `${strat.color}12`,
                      borderColor: `${strat.color}30`,
                      color: strat.color,
                      fontSize: 10,
                    }}
                  >
                    {strat.label}
                  </span>
                  {isBest && (
                    <Crown className="h-3 w-3 text-[var(--color-amber)]" />
                  )}
                </div>
                <span className="num text-[12px] font-medium text-[var(--color-green)] glow-green">
                  {formatCurrency(champ.capital_final)}
                </span>
              </div>

              <div className="flex items-center gap-3 mt-0.5 text-[10px] text-[var(--color-text-2)]">
                <span className="num">Sharpe {champ.sharpe_ratio ? formatSharpe(champ.sharpe_ratio) : "—"}</span>
                <span className="num">WR {champ.win_rate ? champ.win_rate.toFixed(1) + "%" : "—"}</span>
                <span className="num">{champ.total_trades ?? "—"} trades</span>
                <span className="ml-auto">{timeAgo(champ.promoted_at)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
