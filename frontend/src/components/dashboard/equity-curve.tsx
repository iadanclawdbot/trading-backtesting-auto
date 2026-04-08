"use client";

import { useStatus } from "@/hooks/use-api";
import { formatCurrency } from "@/lib/formatters";
import { TrendingUp } from "lucide-react";

export function EquityCurve() {
  const { data, isLoading } = useStatus();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse">
          <div className="h-2 w-32 rounded bg-[var(--color-surface-3)] mb-4" />
          <div className="h-[110px] w-full rounded bg-[var(--color-surface-0)]" />
        </div>
      </div>
    );
  }

  const champion = data?.champion;

  return (
    <div className="panel p-4">
      <div className="section-label mb-0.5">Equity curve — campeón actual</div>
      <div className="text-[10px] text-[var(--color-text-2)] mb-3">
        capital bar-a-bar desde candle_states
      </div>

      {champion ? (
        <div className="relative h-[110px] rounded bg-[var(--color-surface-0)] overflow-hidden">
          {/* Simulated equity gradient based on available data */}
          <svg viewBox="0 0 400 110" className="w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-green)" stopOpacity="0.15" />
                <stop offset="100%" stopColor="var(--color-green)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* Placeholder line showing start→end */}
            <path
              d="M 0 90 Q 100 85, 150 70 T 250 50 T 350 35 L 400 30 L 400 110 L 0 110 Z"
              fill="url(#eqFill)"
            />
            <path
              d="M 0 90 Q 100 85, 150 70 T 250 50 T 350 35 L 400 30"
              fill="none"
              stroke="var(--color-green)"
              strokeWidth="2"
            />
          </svg>
          {/* Overlay with real data points */}
          <div className="absolute top-2 left-3 text-[10px] text-[var(--color-text-2)]">
            $250
          </div>
          <div className="absolute top-2 right-3 num text-[10px] text-[var(--color-green)]">
            {formatCurrency(champion.capital_final)}
          </div>
          {/* Pending endpoint notice */}
          <div className="absolute bottom-2 right-3 text-[9px] text-[var(--color-text-2)] opacity-60">
            requiere /metrics/equity-curve
          </div>
        </div>
      ) : (
        <div className="h-[110px] rounded bg-[var(--color-surface-0)] flex items-center justify-center">
          <div className="text-center text-[var(--color-text-2)]">
            <TrendingUp className="h-5 w-5 mx-auto mb-1.5 opacity-50" />
            <span className="text-[11px]">Sin campeón activo</span>
          </div>
        </div>
      )}
    </div>
  );
}
