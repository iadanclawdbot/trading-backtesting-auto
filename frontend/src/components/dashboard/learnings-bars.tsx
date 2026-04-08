"use client";

import { useLearnings } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { LEARNING_CATEGORIES } from "@/lib/constants";
import { LearningCategory } from "@/types/api";

export function LearningsBars() {
  const { data, isLoading } = useLearnings();

  if (isLoading && !data) return <MetricCard title="Learnings por categoría" loading />;

  const learnings = data?.learnings ?? [];
  const total = learnings.length;

  const counts = Object.keys(LEARNING_CATEGORIES).reduce((acc, cat) => {
    acc[cat as LearningCategory] = learnings.filter((l) => l.category === cat).length;
    return acc;
  }, {} as Record<LearningCategory, number>);

  const sorted = Object.entries(counts).sort(([, a], [, b]) => b - a);
  const maxCount = Math.max(...Object.values(counts), 1);

  return (
    <MetricCard title="Learnings por categoría">
      <p className="text-[11px] text-[var(--color-text-2)] mt-2 mb-4 num">{total} aprendizajes</p>

      <div className="space-y-3">
        {sorted.map(([cat, count]) => {
          const cfg = LEARNING_CATEGORIES[cat as LearningCategory];
          const pct = (count / maxCount) * 100;

          return (
            <div key={cat}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[12px] text-[var(--color-text-1)]">{cfg.label}</span>
                <span className="num text-[12px] font-medium" style={{ color: cfg.color }}>{count}</span>
              </div>
              <div className="h-[5px] w-full rounded-full bg-[var(--color-surface-3)] overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${cfg.color}cc, ${cfg.color}60)` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </MetricCard>
  );
}
