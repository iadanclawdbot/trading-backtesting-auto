"use client";

import { useState, Fragment } from "react";
import { ChevronDown, ChevronUp, ChevronRight } from "lucide-react";
import { useApiContext } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatSharpe, formatPercent, timeAgo } from "@/lib/formatters";
import { TopResult } from "@/types/api";
import { cn } from "@/lib/utils";

type SortKey = "sharpe_oos" | "wr_oos" | "dd_oos" | "trades_oos";

const COLUMNS: { key: SortKey; label: string; tooltip: string; format: (v: number) => string; color?: (v: number) => string }[] = [
  { key: "sharpe_oos", label: "Sharpe", tooltip: "sharpe_oos", format: formatSharpe, color: (v) => v >= BENCHMARK_FITNESS ? "var(--color-green)" : "var(--color-text-0)" },
  { key: "wr_oos", label: "WR", tooltip: "win_rate", format: (v) => formatPercent(v, false) },
  { key: "dd_oos", label: "Max DD", tooltip: "max_drawdown", format: (v) => formatPercent(v), color: () => "var(--color-red)" },
  { key: "trades_oos", label: "Trades", tooltip: "total_trades", format: (v) => String(v) },
];

function ExpandedRow({ result }: { result: TopResult }) {
  let params: Record<string, unknown> = {};
  try { params = JSON.parse(result.params_json); } catch {}

  return (
    <div className="px-4 pb-3 pt-2">
      <p className="text-[10px] text-[var(--color-text-2)] mb-2 uppercase tracking-wide font-medium">Parámetros</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-0.5">
        {Object.entries(params).map(([k, v]) => (
          <div key={k} className="text-[11px]">
            <span className="text-[var(--color-text-2)]">{k}: </span>
            <span className="num text-[var(--color-text-0)]">{String(v)}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-[var(--color-text-2)] mt-2 num">
        Sharpe train: {formatSharpe(result.sharpe_train)} · {timeAgo(result.created_at)}
      </p>
    </div>
  );
}

export function RunsTable() {
  const { data, isLoading } = useApiContext(20);
  const [sortKey, setSortKey] = useState<SortKey>("sharpe_oos");
  const [sortDir, setSortDir] = useState<"desc" | "asc">("desc");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (isLoading && !data) {
    return (
      <div className="panel p-5">
        <div className="animate-pulse space-y-2">
          <div className="h-2.5 w-32 rounded bg-[var(--color-surface-3)]" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-9 w-full rounded bg-[var(--color-surface-0)]" />
          ))}
        </div>
      </div>
    );
  }

  const results = data?.top_results ?? [];
  const sorted = [...results].sort((a, b) => (sortDir === "desc" ? -1 : 1) * (a[sortKey] - b[sortKey]));

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDir((d) => d === "desc" ? "asc" : "desc");
    else { setSortKey(key); setSortDir("desc"); }
  }

  return (
    <MetricCard title={`Top experimentos (${results.length})`} noPad>
      {results.length === 0 ? (
        <p className="p-4 text-sm text-[var(--color-text-2)]">Sin datos</p>
      ) : (
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-y border-[var(--color-border)]">
                <th className="text-left px-4 py-2 text-[10px] font-semibold text-[var(--color-text-2)] uppercase tracking-wider">
                  Estrategia
                </th>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className="text-right px-3 py-2 text-[10px] font-semibold text-[var(--color-text-2)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text-0)] transition-colors"
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.label}
                      {sortKey === col.key && (sortDir === "desc" ? <ChevronDown className="h-2.5 w-2.5" /> : <ChevronUp className="h-2.5 w-2.5" />)}
                    </span>
                  </th>
                ))}
                <th className="w-6" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((result, idx) => {
                const strat = getStrategy(result.strategy);
                const beats = result.sharpe_oos >= BENCHMARK_FITNESS;
                const isExpanded = expandedIdx === idx;

                return (
                  <Fragment key={idx}>
                    <tr
                      className={cn(
                        "border-b border-[var(--color-border)] cursor-pointer transition-colors",
                        "hover:bg-[var(--color-surface-2)]",
                        beats && "bg-[var(--color-green-dim)]"
                      )}
                      onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                    >
                      <td className="px-4 py-2.5">
                        <span
                          className="pill text-[10px]"
                          style={{ background: `${strat.color}12`, borderColor: `${strat.color}30`, color: strat.color }}
                        >
                          {strat.label}
                        </span>
                        {result.symbol && result.symbol !== "BTCUSDT" && (
                          <span className="pill text-[9px] ml-1" style={{ background: "rgba(99,102,241,0.1)", borderColor: "rgba(99,102,241,0.3)", color: "#818cf8" }}>
                            {result.symbol.replace("USDT", "")}
                          </span>
                        )}
                      </td>
                      {COLUMNS.map((col) => (
                        <td key={col.key} className="text-right px-3 py-2.5 num">
                          <span style={{ color: col.color ? col.color(result[col.key]) : "var(--color-text-0)" }}>
                            {col.format(result[col.key])}
                          </span>
                        </td>
                      ))}
                      <td className="px-2 py-2.5 text-[var(--color-text-2)]">
                        <ChevronRight className={cn("h-3 w-3 transition-transform", isExpanded && "rotate-90")} />
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-[var(--color-surface-0)]">
                        <td colSpan={COLUMNS.length + 2}><ExpandedRow result={result} /></td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </MetricCard>
  );
}
