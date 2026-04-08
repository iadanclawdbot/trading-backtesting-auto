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

interface ColumnConfig {
  key: SortKey;
  label: string;
  tooltip: string;
  format: (v: number) => string;
  color?: (v: number) => string;
}

const COLUMNS: ColumnConfig[] = [
  {
    key: "sharpe_oos",
    label: "Sharpe OOS",
    tooltip: "sharpe_oos",
    format: formatSharpe,
    color: (v) => (v >= BENCHMARK_FITNESS ? "var(--color-success)" : "var(--color-text-primary)"),
  },
  {
    key: "wr_oos",
    label: "Win Rate",
    tooltip: "win_rate",
    format: (v) => formatPercent(v, false),
  },
  {
    key: "dd_oos",
    label: "Max DD",
    tooltip: "max_drawdown",
    format: (v) => formatPercent(v),
    color: () => "var(--color-danger)",
  },
  {
    key: "trades_oos",
    label: "Trades",
    tooltip: "total_trades",
    format: (v) => String(v),
  },
];

function ExpandedRow({ result }: { result: TopResult }) {
  let params: Record<string, unknown> = {};
  try {
    params = JSON.parse(result.params_json);
  } catch {}

  return (
    <div className="px-4 pb-3 pt-1">
      <p className="text-xs text-[var(--color-text-muted)] mb-2">Parámetros del experimento:</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1">
        {Object.entries(params).map(([k, v]) => (
          <div key={k} className="text-xs">
            <span className="text-[var(--color-text-muted)]">{k}: </span>
            <span className="font-mono text-[var(--color-text-primary)]">{String(v)}</span>
          </div>
        ))}
      </div>
      <p className="text-xs text-[var(--color-text-muted)] mt-2">
        Sharpe train: <span className="font-mono">{formatSharpe(result.sharpe_train)}</span>
        {" · "}
        <TooltipHelp term="sharpe_train" />
        {" · "}
        {timeAgo(result.created_at)}
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
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-3 w-40 rounded bg-white/10" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 w-full rounded bg-white/5" />
          ))}
        </div>
      </div>
    );
  }

  const results = data?.top_results ?? [];

  const sorted = [...results].sort((a, b) => {
    const mult = sortDir === "desc" ? -1 : 1;
    return (a[sortKey] - b[sortKey]) * mult;
  });

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide">
          Top experimentos
        </h3>
        <span className="text-xs text-[var(--color-text-muted)]">({results.length})</span>
      </div>

      {results.length === 0 ? (
        <p className="p-4 text-sm text-[var(--color-text-muted)]">Sin datos aún</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-2 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">
                  Estrategia
                </th>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    className="text-right px-3 py-2 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide cursor-pointer select-none hover:text-[var(--color-text-primary)] transition-colors"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center justify-end gap-1">
                      <span>{col.label}</span>
                      <TooltipHelp term={col.tooltip} />
                      {sortKey === col.key ? (
                        sortDir === "desc" ? (
                          <ChevronDown className="h-3 w-3" />
                        ) : (
                          <ChevronUp className="h-3 w-3" />
                        )
                      ) : null}
                    </div>
                  </th>
                ))}
                <th className="w-6" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((result, idx) => {
                const strategy = getStrategy(result.strategy);
                const beatsBenchmark = result.sharpe_oos >= BENCHMARK_FITNESS;
                const isExpanded = expandedIdx === idx;

                return (
                  <Fragment key={idx}>
                    <tr
                      className={cn(
                        "border-b border-[var(--color-border)] cursor-pointer transition-colors",
                        "hover:bg-white/5",
                        beatsBenchmark && "bg-[var(--color-success)]/5"
                      )}
                      onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                    >
                      <td className="px-4 py-3">
                        <span
                          className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium"
                          style={{
                            backgroundColor: `${strategy.color}20`,
                            color: strategy.color,
                            border: `1px solid ${strategy.color}30`,
                          }}
                        >
                          {strategy.label}
                        </span>
                      </td>
                      {COLUMNS.map((col) => (
                        <td key={col.key} className="text-right px-3 py-3 font-mono text-xs">
                          <span
                            style={{
                              color: col.color
                                ? col.color(result[col.key])
                                : "var(--color-text-primary)",
                            }}
                          >
                            {col.format(result[col.key])}
                          </span>
                        </td>
                      ))}
                      <td className="px-2 py-3 text-[var(--color-text-muted)]">
                        <ChevronRight
                          className={cn(
                            "h-3 w-3 transition-transform",
                            isExpanded && "rotate-90"
                          )}
                        />
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-[var(--color-surface-elevated)]">
                        <td colSpan={COLUMNS.length + 2}>
                          <ExpandedRow result={result} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
