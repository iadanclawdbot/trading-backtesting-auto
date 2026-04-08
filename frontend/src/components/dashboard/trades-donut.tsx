"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { formatPercent } from "@/lib/formatters";

function CustomLabel({
  cx,
  cy,
  winRate,
}: {
  cx: number;
  cy: number;
  winRate: number;
}) {
  return (
    <>
      <text
        x={cx}
        y={cy - 6}
        textAnchor="middle"
        fill="var(--color-text-primary)"
        fontSize={22}
        fontWeight="bold"
        fontFamily="var(--font-mono, monospace)"
      >
        {winRate.toFixed(0)}%
      </text>
      <text
        x={cx}
        y={cy + 12}
        textAnchor="middle"
        fill="var(--color-text-muted)"
        fontSize={10}
      >
        win rate
      </text>
    </>
  );
}

export function TradesDonut() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return <MetricCard title="Distribución de trades" loading />;
  }

  const champion = data?.champion;

  if (!champion) {
    return (
      <MetricCard title="Distribución de trades">
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">Sin campeón aún</p>
      </MetricCard>
    );
  }

  const wins = Math.round((champion.win_rate / 100) * champion.total_trades);
  const losses = champion.total_trades - wins;

  const pieData = [
    { name: "Ganados", value: wins, color: "var(--color-success)" },
    { name: "Perdidos", value: losses, color: "var(--color-danger)" },
  ];

  return (
    <MetricCard title="Distribución de trades">
      <div className="mt-2">
        <ResponsiveContainer width="100%" height={160}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              dataKey="value"
              paddingAngle={3}
              startAngle={90}
              endAngle={-270}
            >
              {pieData.map((entry, idx) => (
                <Cell key={idx} fill={entry.color} />
              ))}
              {/* Label central custom */}
              {/* Recharts labelLine=false and label as custom component */}
            </Pie>
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0];
                return (
                  <div className="rounded-lg border border-[var(--color-border-strong)] bg-[var(--color-surface-elevated)] px-3 py-2 text-xs shadow-xl">
                    <span style={{ color: d.payload.color }}>{d.name}: </span>
                    <span className="font-mono">{d.value} trades</span>
                  </div>
                );
              }}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Centro manual con el WR */}
        <div className="relative -mt-[148px] flex items-center justify-center pointer-events-none" style={{ height: 160 }}>
          <div className="text-center">
            <div className="font-mono text-2xl font-bold text-[var(--color-text-primary)]">
              {champion.win_rate.toFixed(0)}%
            </div>
            <div className="text-xs text-[var(--color-text-muted)]">win rate</div>
          </div>
        </div>

        {/* Leyenda */}
        <div className="flex justify-center gap-6 mt-2 text-xs">
          {pieData.map((d) => (
            <div key={d.name} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
              <span className="text-[var(--color-text-muted)]">
                {d.name}: <span className="font-mono text-[var(--color-text-primary)]">{d.value}</span>
              </span>
            </div>
          ))}
        </div>

        <div className="mt-3 pt-3 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)] text-center">
          Total: <span className="font-mono text-[var(--color-text-primary)]">{champion.total_trades}</span> trades
          · Campeón: <span style={{ color: "var(--color-vwap)" }}>{champion.strategy}</span>
        </div>
      </div>
    </MetricCard>
  );
}
