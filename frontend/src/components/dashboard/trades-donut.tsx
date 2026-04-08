"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { useStatus } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";

export function TradesDonut() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) return <MetricCard title="Distribución de trades" loading />;
  const champion = data?.champion;
  if (!champion) {
    return <MetricCard title="Distribución de trades"><p className="mt-3 text-sm text-[var(--color-text-2)]">Sin campeón</p></MetricCard>;
  }

  const wins = Math.round((champion.win_rate / 100) * champion.total_trades);
  const losses = champion.total_trades - wins;
  const pie = [
    { name: "WIN", value: wins, color: "var(--color-green)" },
    { name: "LOSS", value: losses, color: "var(--color-red)" },
  ];

  return (
    <MetricCard title="Distribución de trades">
      <div className="flex items-center gap-4 mt-3">
        {/* Donut */}
        <div className="relative w-[120px] h-[120px] flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pie}
                cx="50%"
                cy="50%"
                innerRadius={38}
                outerRadius={55}
                dataKey="value"
                paddingAngle={3}
                startAngle={90}
                endAngle={-270}
                stroke="none"
              >
                {pie.map((e, i) => (
                  <Cell key={i} fill={e.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="num text-xl font-bold text-[var(--color-text-0)]">
              {champion.win_rate.toFixed(0)}%
            </span>
            <span className="text-[9px] text-[var(--color-text-2)] -mt-0.5">WR</span>
          </div>
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="block h-2.5 w-2.5 rounded-sm bg-[var(--color-green)]" />
              <span className="text-xs text-[var(--color-text-1)]">Ganados</span>
            </div>
            <span className="num text-sm font-medium text-[var(--color-text-0)]">{wins}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="block h-2.5 w-2.5 rounded-sm bg-[var(--color-red)]" />
              <span className="text-xs text-[var(--color-text-1)]">Perdidos</span>
            </div>
            <span className="num text-sm font-medium text-[var(--color-text-0)]">{losses}</span>
          </div>
          <div className="pt-2 border-t border-[var(--color-border)]">
            <div className="flex justify-between text-[11px]">
              <span className="text-[var(--color-text-2)]">Total trades</span>
              <span className="num text-[var(--color-text-0)]">{champion.total_trades}</span>
            </div>
          </div>
        </div>
      </div>
    </MetricCard>
  );
}
