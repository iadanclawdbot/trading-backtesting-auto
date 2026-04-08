"use client";

import {
  ComposedChart,
  Scatter,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useApiContext } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { getStrategy, BENCHMARK_FITNESS } from "@/lib/constants";
import { formatSharpe, formatPercent } from "@/lib/formatters";

interface ChartPoint {
  index: number;
  sharpe: number;
  wr: number;
  dd: number;
  strategy: string;
  isImprovement: boolean;
  runningBest: number;
}

function buildChartData(topResults: Array<{
  strategy: string;
  sharpe_oos: number;
  wr_oos: number;
  dd_oos: number;
}>): ChartPoint[] {
  let runningBest = 0;
  return topResults.map((r, i) => {
    const isImprovement = r.sharpe_oos > runningBest;
    if (isImprovement) runningBest = r.sharpe_oos;
    return {
      index: i + 1,
      sharpe: r.sharpe_oos,
      wr: r.wr_oos,
      dd: r.dd_oos,
      strategy: r.strategy,
      isImprovement,
      runningBest: isImprovement ? r.sharpe_oos : runningBest,
    };
  });
}

// Tooltip custom del grafico
function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartPoint }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const strat = getStrategy(d.strategy);
  return (
    <div className="rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-surface-elevated)] p-3 text-xs shadow-xl">
      <div className="flex items-center gap-2 mb-2">
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ backgroundColor: strat.color }}
        />
        <span className="font-medium text-[var(--color-text-primary)]">
          Exp #{d.index} — {strat.label}
        </span>
      </div>
      <div className="space-y-1 text-[var(--color-text-secondary)]">
        <div>Sharpe OOS: <span className="font-mono text-[var(--color-text-primary)]">{formatSharpe(d.sharpe)}</span></div>
        <div>Win Rate: <span className="font-mono text-[var(--color-text-primary)]">{formatPercent(d.wr, false)}</span></div>
        <div>Max DD: <span className="font-mono text-[var(--color-danger)]">{formatPercent(d.dd)}</span></div>
        {d.isImprovement && (
          <div className="text-[var(--color-success)] mt-1">✓ Nuevo mejor resultado</div>
        )}
      </div>
    </div>
  );
}

export function AutoresearchChart() {
  const { data, isLoading } = useApiContext(50);

  if (isLoading && !data) {
    return (
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <div className="animate-pulse">
          <div className="h-3 w-48 rounded bg-white/10 mb-4" />
          <div className="h-64 w-full rounded bg-white/5" />
        </div>
      </div>
    );
  }

  const results = data?.top_results ?? [];
  const chartData = buildChartData(results);

  // Separar mejoras vs descartados para dos series Scatter
  const improvements = chartData.filter((d) => d.isImprovement);
  const discarded = chartData.filter((d) => !d.isImprovement);

  // Datos para la linea escalonada de running best
  const lineData = chartData.map((d) => ({ index: d.index, runningBest: d.runningBest }));

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide">
          Progreso de la investigación autónoma
        </h3>
        <TooltipHelp term="autoresearch" />
      </div>

      {results.length === 0 ? (
        <div className="flex h-48 items-center justify-center">
          <p className="text-sm text-[var(--color-text-muted)]">Sin datos aún</p>
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
              {/* Benchmark */}
              <ReferenceLine
                y={BENCHMARK_FITNESS}
                stroke="var(--color-warning)"
                strokeDasharray="4 3"
                strokeWidth={1}
                label={{ value: `Benchmark ${BENCHMARK_FITNESS}`, position: "insideTopRight", fill: "var(--color-warning)", fontSize: 10 }}
                yAxisId="left"
              />

              <XAxis
                dataKey="index"
                type="number"
                tick={{ fill: "var(--color-text-muted)", fontSize: 10 }}
                tickLine={false}
                axisLine={{ stroke: "var(--color-border)" }}
                label={{ value: "Experimento #", position: "insideBottomRight", offset: -5, fill: "var(--color-text-muted)", fontSize: 10 }}
              />
              <YAxis
                yAxisId="left"
                tick={{ fill: "var(--color-text-muted)", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => v.toFixed(1)}
                label={{ value: "Sharpe OOS", angle: -90, position: "insideLeft", fill: "var(--color-text-muted)", fontSize: 10 }}
              />

              {/* Tooltip */}
              <Tooltip content={<CustomTooltip />} />

              {/* Experimentos descartados — puntos grises */}
              <Scatter
                data={discarded}
                dataKey="sharpe"
                xAxisId={undefined}
                yAxisId="left"
                fill="rgba(255,255,255,0.15)"
                r={3}
              />

              {/* Mejoras retenidas — puntos verdes */}
              <Scatter
                data={improvements}
                dataKey="sharpe"
                yAxisId="left"
                fill="var(--color-success)"
                r={5}
              />

              {/* Linea escalonada del running best */}
              <Line
                data={lineData}
                type="stepAfter"
                dataKey="runningBest"
                yAxisId="left"
                stroke="var(--color-success)"
                strokeWidth={2}
                dot={false}
                activeDot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* Leyenda */}
          <div className="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-[var(--color-success)]" />
              <span>Mejoras ({improvements.length})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-white/20" />
              <span>Descartados ({discarded.length})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="block h-0.5 w-4 bg-[var(--color-warning)] opacity-70" />
              <span>Benchmark</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
