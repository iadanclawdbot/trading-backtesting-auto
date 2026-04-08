"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { BENCHMARK_FITNESS, BENCHMARK_LABEL } from "@/lib/constants";
import { formatSharpe } from "@/lib/formatters";

function GaugeArc({ value, benchmark }: { value: number; benchmark: number }) {
  const r = 56;
  const cx = 80;
  const cy = 72;
  const strokeW = 10;
  const max = 2.5;

  const toAngle = (v: number) => ((Math.min(Math.max(v, 0), max)) / max) * 180;
  const toXY = (deg: number) => ({
    x: cx + r * Math.cos(((deg - 180) * Math.PI) / 180),
    y: cy + r * Math.sin(((deg - 180) * Math.PI) / 180),
  });

  const valAngle = toAngle(value);
  const benchAngle = toAngle(benchmark);
  const start = toXY(0);
  const end = toXY(180);
  const valPos = toXY(valAngle);
  const benchPos = toXY(benchAngle);
  const beats = value >= benchmark;

  const fillColor = beats ? "var(--color-green)" : "var(--color-amber)";

  return (
    <svg viewBox="0 0 160 100" className="w-full max-w-[200px]">
      {/* Track */}
      <path
        d={`M ${start.x} ${start.y} A ${r} ${r} 0 1 1 ${end.x} ${end.y}`}
        fill="none"
        stroke="var(--color-surface-3)"
        strokeWidth={strokeW}
        strokeLinecap="round"
      />
      {/* Value fill */}
      {value > 0 && (
        <path
          d={`M ${start.x} ${start.y} A ${r} ${r} 0 ${valAngle > 90 ? 1 : 0} 1 ${valPos.x} ${valPos.y}`}
          fill="none"
          stroke={fillColor}
          strokeWidth={strokeW}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${beats ? "rgba(74,222,128,0.4)" : "rgba(251,191,36,0.3)"})` }}
        />
      )}
      {/* Benchmark tick */}
      <line
        x1={benchPos.x + (benchPos.x - cx) * 0.15}
        y1={benchPos.y + (benchPos.y - cy) * 0.15}
        x2={benchPos.x - (benchPos.x - cx) * 0.15}
        y2={benchPos.y - (benchPos.y - cy) * 0.15}
        stroke="var(--color-amber)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* Value text */}
      <text x={cx} y={cy - 4} textAnchor="middle" fill="var(--color-text-0)" fontSize="20" fontWeight="600" fontFamily="var(--font-mono, monospace)">
        {formatSharpe(value)}
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="var(--color-text-2)" fontSize="9">
        Sharpe OOS
      </text>
    </svg>
  );
}

export function FitnessGauge() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Fitness vs benchmark" loading />;
  }

  const sharpe = data?.best_oos?.sharpe_ratio ?? 0;
  const beats = sharpe >= BENCHMARK_FITNESS;
  const delta = sharpe - BENCHMARK_FITNESS;

  return (
    <MetricCard title="Fitness vs benchmark" tooltip="fitness_score">
      <div className="flex flex-col items-center mt-2">
        <GaugeArc value={sharpe} benchmark={BENCHMARK_FITNESS} />

        <div className="flex items-center gap-3 mt-1 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="block h-[2px] w-3 rounded bg-[var(--color-amber)]" />
            <span className="text-[var(--color-text-2)]">{BENCHMARK_LABEL} ({BENCHMARK_FITNESS})</span>
          </div>
        </div>

        <span
          className="num text-xs font-semibold mt-2"
          style={{ color: beats ? "var(--color-green)" : "var(--color-amber)" }}
        >
          {delta >= 0 ? "+" : ""}{delta.toFixed(3)}
        </span>
      </div>
    </MetricCard>
  );
}
