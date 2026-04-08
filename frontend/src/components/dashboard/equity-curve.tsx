"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useEquityCurve } from "@/hooks/use-api";
import { getStrategy } from "@/lib/constants";
import { formatCurrency } from "@/lib/formatters";
import { TrendingUp } from "lucide-react";

const INITIAL_CAPITAL = 250;

function CurveTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { equity: number; bar: number; in_pos: number } }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="panel p-2.5 text-[11px] shadow-2xl !bg-[var(--color-surface-2)] min-w-[120px]">
      <div className="flex justify-between gap-3">
        <span className="text-[var(--color-text-2)]">Equity</span>
        <span className="num font-medium text-[var(--color-text-0)]">{formatCurrency(d.equity)}</span>
      </div>
      <div className="flex justify-between gap-3 mt-0.5">
        <span className="text-[var(--color-text-2)]">Bar</span>
        <span className="num text-[var(--color-text-1)]">#{d.bar}</span>
      </div>
      {d.in_pos === 1 && (
        <div className="mt-1 text-[var(--color-green)] text-[10px]">En posición</div>
      )}
    </div>
  );
}

export function EquityCurve() {
  const { data, isLoading, error } = useEquityCurve();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse">
          <div className="h-2 w-32 rounded bg-[var(--color-surface-3)] mb-4" />
          <div className="h-[140px] w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const points = data?.points ?? [];
  const strategy = data?.strategy;
  const strat = strategy ? getStrategy(strategy) : null;
  const hasData = points.length > 0;

  // Determine color based on final equity vs initial
  const finalEquity = hasData ? points[points.length - 1].equity : INITIAL_CAPITAL;
  const isPositive = finalEquity >= INITIAL_CAPITAL;
  const lineColor = isPositive ? "var(--color-green)" : "var(--color-red)";

  // Sample points for performance if there are too many
  const chartPoints = points.length > 500
    ? points.filter((_, i) => i % Math.ceil(points.length / 500) === 0 || i === points.length - 1)
    : points;

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-0.5">
        <div className="section-label">Equity curve — campeón actual</div>
        {strat && (
          <span className="pill" style={{ background: `${strat.color}12`, borderColor: `${strat.color}30`, color: strat.color }}>
            {strat.label}
          </span>
        )}
      </div>
      <div className="text-[10px] text-[var(--color-text-2)] mb-3">
        capital bar-a-bar · {hasData ? `${points.length} barras` : "sin datos"}
        {hasData && (
          <span className="ml-2 num" style={{ color: lineColor }}>
            {formatCurrency(INITIAL_CAPITAL)} → {formatCurrency(finalEquity)}
          </span>
        )}
      </div>

      {!hasData ? (
        <div className="h-[140px] rounded bg-[var(--color-surface-0)] flex items-center justify-center">
          <div className="text-center text-[var(--color-text-2)]">
            <TrendingUp className="h-5 w-5 mx-auto mb-1.5 opacity-50" />
            <span className="text-[11px]">
              {error ? "Error cargando datos" : data?.message || "Sin campeón activo"}
            </span>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={140}>
          <AreaChart data={chartPoints} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.2} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
            </defs>

            <ReferenceLine
              y={INITIAL_CAPITAL}
              stroke="var(--color-amber)"
              strokeDasharray="3 3"
              strokeWidth={1}
              strokeOpacity={0.4}
            />

            <XAxis dataKey="bar" hide />
            <YAxis
              tick={{ fill: "var(--color-text-2)", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${v}`}
              width={45}
              domain={["auto", "auto"]}
            />

            <Tooltip content={<CurveTooltip />} cursor={{ stroke: "var(--color-surface-3)", strokeWidth: 1 }} />

            <Area
              type="monotone"
              dataKey="equity"
              stroke={lineColor}
              strokeWidth={1.5}
              fill="url(#eqGrad)"
              dot={false}
              activeDot={{ r: 3, fill: lineColor }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
