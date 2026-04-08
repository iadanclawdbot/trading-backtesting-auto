"use client";

import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { BENCHMARK_FITNESS, BENCHMARK_LABEL } from "@/lib/constants";
import { formatSharpe } from "@/lib/formatters";

// Convierte sharpe (aprox fitness) a angulo en arco semicircular (0-180 grados)
function valueToAngle(value: number, min = 0, max = 2.5): number {
  const clamped = Math.max(min, Math.min(max, value));
  return ((clamped - min) / (max - min)) * 180;
}

interface GaugeArcProps {
  value: number;
  benchmark: number;
}

function GaugeArc({ value, benchmark }: GaugeArcProps) {
  const size = 160;
  const cx = size / 2;
  const cy = size / 2 + 10;
  const r = 60;

  // Convertir angulos a coordenadas
  function angleToXY(deg: number) {
    const rad = ((deg - 180) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  }

  const valueAngle = valueToAngle(value);
  const benchAngle = valueToAngle(benchmark);
  const fillPos = angleToXY(valueAngle);
  const benchPos = angleToXY(benchAngle);
  const startPos = angleToXY(0);

  const beatsBenchmark = value >= benchmark;
  const fillColor = beatsBenchmark
    ? "var(--color-success)"
    : "var(--color-warning)";

  // Arco del fill (de 0 al valor actual)
  const fillLargeArc = valueAngle > 90 ? 1 : 0;

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="w-full max-w-[160px]"
      aria-hidden="true"
    >
      {/* Track (arco de fondo) */}
      <path
        d={`M ${angleToXY(0).x} ${angleToXY(0).y} A ${r} ${r} 0 1 1 ${angleToXY(180).x} ${angleToXY(180).y}`}
        fill="none"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="8"
        strokeLinecap="round"
      />

      {/* Fill del valor actual */}
      {value > 0 && (
        <path
          d={`M ${startPos.x} ${startPos.y} A ${r} ${r} 0 ${fillLargeArc} 1 ${fillPos.x} ${fillPos.y}`}
          fill="none"
          stroke={fillColor}
          strokeWidth="8"
          strokeLinecap="round"
        />
      )}

      {/* Linea de benchmark */}
      <line
        x1={cx}
        y1={cy}
        x2={benchPos.x}
        y2={benchPos.y}
        stroke="var(--color-warning)"
        strokeWidth="2"
        strokeDasharray="3 2"
        opacity="0.7"
      />
      <circle cx={benchPos.x} cy={benchPos.y} r="3" fill="var(--color-warning)" />

      {/* Punto del valor actual */}
      {value > 0 && (
        <circle cx={fillPos.x} cy={fillPos.y} r="5" fill={fillColor} />
      )}

      {/* Valor central */}
      <text
        x={cx}
        y={cy - 5}
        textAnchor="middle"
        fill="var(--color-text-primary)"
        fontSize="18"
        fontFamily="var(--font-mono, monospace)"
        fontWeight="bold"
      >
        {formatSharpe(value)}
      </text>
      <text
        x={cx}
        y={cy + 12}
        textAnchor="middle"
        fill="var(--color-text-muted)"
        fontSize="9"
      >
        Sharpe OOS
      </text>
    </svg>
  );
}

export function FitnessGauge() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Gauge de fitness" loading />;
  }

  const sharpe = data?.best_oos?.sharpe_ratio ?? 0;
  const beatsBenchmark = sharpe >= BENCHMARK_FITNESS;

  return (
    <MetricCard title="Gauge de fitness">
      <div className="flex flex-col items-center mt-2">
        <GaugeArc value={sharpe} benchmark={BENCHMARK_FITNESS} />

        <div className="flex items-center gap-4 mt-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="h-2 w-4 rounded-sm bg-[var(--color-warning)] opacity-70" />
            <span className="text-[var(--color-text-muted)]">
              {BENCHMARK_LABEL} ({BENCHMARK_FITNESS})
            </span>
          </div>
        </div>

        <div className="mt-2 flex items-center gap-1.5">
          <TooltipHelp term="fitness_score" />
          <span
            className="text-xs font-medium"
            style={{
              color: beatsBenchmark
                ? "var(--color-success)"
                : "var(--color-warning)",
            }}
          >
            {beatsBenchmark
              ? `+${(sharpe - BENCHMARK_FITNESS).toFixed(3)} sobre benchmark`
              : `${(sharpe - BENCHMARK_FITNESS).toFixed(3)} del benchmark`}
          </span>
        </div>
      </div>
    </MetricCard>
  );
}
