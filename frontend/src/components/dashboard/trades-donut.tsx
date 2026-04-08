"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { useStatus } from "@/hooks/use-api";

export function TradesDonut() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse">
          <div className="h-2 w-28 rounded bg-[var(--color-surface-3)] mb-4" />
          <div className="h-[100px] w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const champion = data?.champion;
  if (!champion) {
    return (
      <div className="panel p-4">
        <div className="section-label">Distribución de trades</div>
        <p className="mt-3 text-[11px] text-[var(--color-text-2)]">Sin campeón</p>
      </div>
    );
  }

  const wins = Math.round((champion.win_rate / 100) * champion.total_trades);
  const losses = champion.total_trades - wins;
  const pie = [
    { name: "WIN", value: wins, color: "var(--color-green)" },
    { name: "LOSS", value: losses, color: "var(--color-red)" },
  ];

  return (
    <div className="panel p-4">
      <div className="section-label">Distribución de trades</div>
      <div className="flex items-center gap-3 mt-3">
        {/* Donut */}
        <div className="relative w-[80px] h-[80px] flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pie}
                cx="50%"
                cy="50%"
                innerRadius={24}
                outerRadius={36}
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
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-1.5">
          <div className="flex items-center gap-1.5 text-[10px]">
            <span className="dot dot-ok" />
            <span className="text-[var(--color-text-1)]">WIN</span>
            <span className="num text-[var(--color-text-0)] ml-auto">{champion.win_rate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px]">
            <span className="dot dot-err" />
            <span className="text-[var(--color-text-1)]">LOSS</span>
            <span className="num text-[var(--color-text-0)] ml-auto">{(100 - champion.win_rate).toFixed(1)}%</span>
          </div>
          <div className="text-[10px] text-[var(--color-text-2)] pt-1.5 border-t border-[var(--color-border)]">
            Total: <span className="num text-[var(--color-text-0)]">{champion.total_trades}</span> trades
          </div>
        </div>
      </div>

      {/* Win/Loss bars */}
      <div className="mt-3 space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[var(--color-text-2)] min-w-[50px]">Ganados</span>
          <div className="pbar-track">
            <div className="pbar-fill" style={{ width: `${champion.win_rate}%`, background: "var(--color-green)" }} />
          </div>
          <span className="num text-[10px] text-[var(--color-text-0)] min-w-[20px] text-right">{wins}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[var(--color-text-2)] min-w-[50px]">Perdidos</span>
          <div className="pbar-track">
            <div className="pbar-fill" style={{ width: `${100 - champion.win_rate}%`, background: "var(--color-red)" }} />
          </div>
          <span className="num text-[10px] text-[var(--color-text-0)] min-w-[20px] text-right">{losses}</span>
        </div>
      </div>
    </div>
  );
}
