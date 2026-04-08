"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useCycles } from "@/hooks/use-api";
import { formatNumber } from "@/lib/formatters";

interface CyclePoint {
  index: number;
  jobs: number;
  beat: boolean;
  sharpe: number | null;
  date: string;
}

function CycleTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: CyclePoint }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="panel p-2.5 text-[11px] shadow-2xl !bg-[var(--color-surface-2)] min-w-[130px]">
      <div className="font-medium text-[var(--color-text-0)] mb-1">Ciclo #{d.index}</div>
      <div className="space-y-0.5 text-[var(--color-text-1)]">
        <div className="flex justify-between gap-3">
          <span>Jobs</span>
          <span className="num font-medium">{d.jobs}</span>
        </div>
        {d.sharpe !== null && (
          <div className="flex justify-between gap-3">
            <span>Best Sharpe</span>
            <span className="num">{d.sharpe.toFixed(3)}</span>
          </div>
        )}
        <div className="flex justify-between gap-3">
          <span>Beat benchmark</span>
          <span className={d.beat ? "text-[var(--color-green)]" : "text-[var(--color-text-2)]"}>
            {d.beat ? "Sí" : "No"}
          </span>
        </div>
      </div>
    </div>
  );
}

export function CyclesChart() {
  const { data, isLoading } = useCycles(50);

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse">
          <div className="h-2 w-28 rounded bg-[var(--color-surface-3)] mb-4" />
          <div className="h-[140px] w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const cycles = data?.cycles ?? [];
  // Reverse to show oldest first (API returns DESC)
  const sorted = [...cycles].reverse();
  const chartData: CyclePoint[] = sorted.map((c, i) => ({
    index: i + 1,
    jobs: c.jobs_completed,
    beat: c.beat_benchmark,
    sharpe: c.best_sharpe_oos,
    date: c.finished_at,
  }));

  const totalJobs = chartData.reduce((s, c) => s + c.jobs, 0);
  const beatCount = chartData.filter((c) => c.beat).length;
  const beatRate = chartData.length > 0 ? ((beatCount / chartData.length) * 100).toFixed(1) : "0";

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-1">
        <div className="section-label">Ciclos autónomos</div>
        <span className="text-[10px] text-[var(--color-text-2)] num">{cycles.length} ciclos</span>
      </div>

      {/* Summary stats */}
      <div className="flex gap-4 mb-3 text-[10px]">
        <div>
          <span className="text-[var(--color-text-2)]">Total jobs: </span>
          <span className="num text-[var(--color-text-0)]">{formatNumber(totalJobs)}</span>
        </div>
        <div>
          <span className="text-[var(--color-text-2)]">Beat rate: </span>
          <span className="num text-[var(--color-green)]">{beatRate}%</span>
        </div>
        <div>
          <span className="text-[var(--color-text-2)]">Avg jobs/ciclo: </span>
          <span className="num text-[var(--color-text-0)]">
            {chartData.length > 0 ? (totalJobs / chartData.length).toFixed(1) : "—"}
          </span>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="flex h-[140px] items-center justify-center text-sm text-[var(--color-text-2)]">
          Sin ciclos registrados
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
            <XAxis
              dataKey="index"
              tick={{ fill: "var(--color-text-2)", fontSize: 9 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fill: "var(--color-text-2)", fontSize: 9 }}
              tickLine={false}
              axisLine={false}
              width={30}
            />
            <Tooltip content={<CycleTooltip />} cursor={{ fill: "var(--color-surface-1)" }} />
            <Bar dataKey="jobs" radius={[2, 2, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.beat ? "var(--color-green)" : "var(--color-surface-3)"}
                  fillOpacity={entry.beat ? 0.8 : 0.6}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
