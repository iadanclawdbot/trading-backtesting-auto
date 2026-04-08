"use client";

import { useStatus } from "@/hooks/use-api";
import { BENCHMARK_FITNESS, BENCHMARK_LABEL } from "@/lib/constants";
import { formatSharpe } from "@/lib/formatters";
import { TooltipHelp } from "./tooltip-help";

function GaugeArc({ value, benchmark }: { value: number; benchmark: number }) {
  const r = 48;
  const cx = 65;
  const cy = 58;
  const strokeW = 8;
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
    <svg viewBox="0 0 130 76" className="w-full max-w-[160px]">
      <path
        d={`M ${start.x} ${start.y} A ${r} ${r} 0 1 1 ${end.x} ${end.y}`}
        fill="none" stroke="var(--color-surface-3)" strokeWidth={strokeW} strokeLinecap="round"
      />
      {value > 0 && (
        <path
          d={`M ${start.x} ${start.y} A ${r} ${r} 0 0 1 ${valPos.x} ${valPos.y}`}
          fill="none" stroke={fillColor} strokeWidth={strokeW} strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${beats ? "rgba(74,222,128,0.4)" : "rgba(251,191,36,0.3)"})` }}
        />
      )}
      <line
        x1={benchPos.x + (benchPos.x - cx) * 0.15} y1={benchPos.y + (benchPos.y - cy) * 0.15}
        x2={benchPos.x - (benchPos.x - cx) * 0.15} y2={benchPos.y - (benchPos.y - cy) * 0.15}
        stroke="var(--color-amber)" strokeWidth="2" strokeLinecap="round"
      />
      <text x={cx} y={cy - 2} textAnchor="middle" fill="var(--color-text-0)" fontSize="17" fontWeight="600" fontFamily="var(--font-mono, monospace)">
        {formatSharpe(value)}
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="var(--color-text-2)" fontSize="8">
        Sharpe OOS
      </text>
    </svg>
  );
}

export function FitnessGauge() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-2 w-24 rounded bg-[var(--color-surface-3)]" />
          <div className="h-16 w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const sharpe = data?.best_oos?.sharpe_ratio ?? 0;
  const beats = sharpe >= BENCHMARK_FITNESS;
  const delta = sharpe - BENCHMARK_FITNESS;

  return (
    <div className="panel p-4">
      <div className="flex items-center gap-1">
        <span className="section-label">Fitness vs benchmark</span>
        <TooltipHelp term="fitness_score" />
      </div>

      <div className="flex flex-col items-center mt-1">
        <GaugeArc value={sharpe} benchmark={BENCHMARK_FITNESS} />
        <div className="flex items-center gap-2 text-[10px] -mt-1">
          <span className="flex items-center gap-1">
            <span className="block h-[2px] w-3 rounded bg-[var(--color-amber)]" />
            <span className="text-[var(--color-text-2)]">{BENCHMARK_LABEL} ({BENCHMARK_FITNESS})</span>
          </span>
        </div>
        <span
          className="num text-[11px] font-semibold mt-1"
          style={{ color: beats ? "var(--color-green)" : "var(--color-amber)" }}
        >
          {delta >= 0 ? "+" : ""}{delta.toFixed(3)}
        </span>
      </div>
    </div>
  );
}
