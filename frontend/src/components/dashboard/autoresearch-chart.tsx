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
  Area,
} from "recharts";
import { useApiContext } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
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

function buildData(results: Array<{ strategy: string; sharpe_oos: number; wr_oos: number; dd_oos: number }>): ChartPoint[] {
  let best = -Infinity;
  return results.map((r, i) => {
    const isImprovement = r.sharpe_oos > best;
    if (isImprovement) best = r.sharpe_oos;
    return { index: i + 1, sharpe: r.sharpe_oos, wr: r.wr_oos, dd: r.dd_oos, strategy: r.strategy, isImprovement, runningBest: best };
  });
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartPoint }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const strat = getStrategy(d.strategy);
  return (
    <div className="panel p-3 text-[11px] shadow-2xl !bg-[var(--color-surface-2)] min-w-[160px]">
      <div className="flex items-center gap-1.5 mb-2">
        <span className="dot" style={{ background: strat.color }} />
        <span className="font-medium text-[var(--color-text-0)]">#{d.index} {strat.label}</span>
      </div>
      <div className="space-y-1 text-[var(--color-text-1)]">
        <div className="flex justify-between">
          <span>Sharpe OOS</span>
          <span className="num font-medium text-[var(--color-text-0)]">{formatSharpe(d.sharpe)}</span>
        </div>
        <div className="flex justify-between">
          <span>Win Rate</span>
          <span className="num">{formatPercent(d.wr, false)}</span>
        </div>
        <div className="flex justify-between">
          <span>Max DD</span>
          <span className="num text-[var(--color-red)]">{formatPercent(d.dd)}</span>
        </div>
      </div>
      {d.isImprovement && (
        <div className="mt-2 pt-2 border-t border-[var(--color-border)] text-[var(--color-green)] font-medium">
          ✓ Nuevo mejor resultado
        </div>
      )}
    </div>
  );
}

export function AutoresearchChart() {
  const { data, isLoading } = useApiContext(50);

  if (isLoading && !data) {
    return (
      <div className="panel p-5">
        <div className="animate-pulse">
          <div className="h-2.5 w-48 rounded bg-[var(--color-surface-3)] mb-6" />
          <div className="h-[220px] w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const results = data?.top_results ?? [];
  const chartData = buildData(results);
  const improvements = chartData.filter((d) => d.isImprovement);
  const discarded = chartData.filter((d) => !d.isImprovement);

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="section-label">Sharpe OOS por experimento</div>
          <div className="text-[10px] text-[var(--color-text-2)] mt-0.5">descartados vs mejoras retenidas · running best en verde</div>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-[var(--color-text-2)]">
          <div className="flex items-center gap-1.5">
            <span className="block h-2 w-2 rounded-full bg-[var(--color-green)]" />
            Mejoras ({improvements.length})
          </div>
          <div className="flex items-center gap-1.5">
            <span className="block h-2 w-2 rounded-full bg-[var(--color-surface-3)]" />
            Descartados ({discarded.length})
          </div>
          <div className="flex items-center gap-1.5">
            <span className="block h-[2px] w-3 bg-[var(--color-amber)] opacity-70" />
            Benchmark
          </div>
        </div>
      </div>

      {results.length === 0 ? (
        <div className="flex h-48 items-center justify-center text-sm text-[var(--color-text-2)]">
          Sin datos aún
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
            <defs>
              <linearGradient id="bestFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-green)" stopOpacity={0.15} />
                <stop offset="100%" stopColor="var(--color-green)" stopOpacity={0} />
              </linearGradient>
            </defs>

            <ReferenceLine
              y={BENCHMARK_FITNESS}
              stroke="var(--color-amber)"
              strokeDasharray="4 3"
              strokeWidth={1}
              strokeOpacity={0.5}
              yAxisId="left"
            />

            <XAxis
              dataKey="index"
              type="number"
              tick={{ fill: "var(--color-text-2)", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "var(--color-text-2)", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => v.toFixed(1)}
              width={35}
            />

            <Tooltip content={<ChartTooltip />} cursor={false} />

            {/* Running best area fill */}
            <Area
              data={chartData}
              type="stepAfter"
              dataKey="runningBest"
              yAxisId="left"
              stroke="none"
              fill="url(#bestFill)"
            />

            {/* Descartados */}
            <Scatter data={discarded} dataKey="sharpe" yAxisId="left" fill="var(--color-surface-3)" fillOpacity={0.8} r={2.5} />

            {/* Mejoras */}
            <Scatter data={improvements} dataKey="sharpe" yAxisId="left" fill="var(--color-green)" r={4} />

            {/* Running best line */}
            <Line
              data={chartData}
              type="stepAfter"
              dataKey="runningBest"
              yAxisId="left"
              stroke="var(--color-green)"
              strokeWidth={2}
              dot={false}
              activeDot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
