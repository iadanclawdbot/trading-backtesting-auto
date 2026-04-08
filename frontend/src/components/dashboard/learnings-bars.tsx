"use client";

import { useLearnings } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { LEARNING_CATEGORIES } from "@/lib/constants";
import { LearningCategory } from "@/types/api";

export function LearningsBars() {
  const { data, isLoading } = useLearnings();

  if (isLoading && !data) {
    return <MetricCard title="Learnings por categoría" loading />;
  }

  const learnings = data?.learnings ?? [];
  const total = learnings.length;

  // Contar por categoria
  const counts = Object.keys(LEARNING_CATEGORIES).reduce(
    (acc, cat) => {
      acc[cat as LearningCategory] = learnings.filter(
        (l) => l.category === cat
      ).length;
      return acc;
    },
    {} as Record<LearningCategory, number>
  );

  // Ordenar de mayor a menor
  const sorted = Object.entries(counts).sort(([, a], [, b]) => b - a);
  const maxCount = Math.max(...Object.values(counts), 1);

  return (
    <MetricCard title="Learnings por categoría">
      <div className="flex items-center gap-1 mb-3 mt-1">
        <span className="text-xs text-[var(--color-text-muted)]">
          {total} aprendizajes totales
        </span>
        <TooltipHelp term="learnings_feed" />
      </div>

      <div className="space-y-3">
        {sorted.map(([cat, count]) => {
          const config = LEARNING_CATEGORIES[cat as LearningCategory];
          const pct = (count / maxCount) * 100;
          const totalPct = total > 0 ? ((count / total) * 100).toFixed(0) : "0";

          return (
            <div key={cat}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-[var(--color-text-secondary)]">
                  {config.emoji} {config.label}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {totalPct}%
                  </span>
                  <span
                    className="font-mono text-xs font-medium"
                    style={{ color: config.color }}
                  >
                    {count}
                  </span>
                </div>
              </div>
              <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: config.color,
                    opacity: 0.8,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </MetricCard>
  );
}
