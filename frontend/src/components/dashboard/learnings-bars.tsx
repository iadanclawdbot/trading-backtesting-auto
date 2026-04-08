"use client";

import { useLearnings } from "@/hooks/use-api";
import { LEARNING_CATEGORIES } from "@/lib/constants";
import { LearningCategory } from "@/types/api";

export function LearningsBars() {
  const { data, isLoading } = useLearnings();

  if (isLoading && !data) {
    return (
      <div className="panel p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-2 w-28 rounded bg-[var(--color-surface-3)]" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-2 w-full rounded bg-[var(--color-surface-3)]" />
          ))}
        </div>
      </div>
    );
  }

  const learnings = data?.learnings ?? [];
  const total = learnings.length;
  const avgConf = learnings.length > 0
    ? (learnings.reduce((s, l) => s + l.confidence, 0) / learnings.length).toFixed(2)
    : "0";

  const counts = Object.keys(LEARNING_CATEGORIES).reduce((acc, cat) => {
    acc[cat as LearningCategory] = learnings.filter((l) => l.category === cat).length;
    return acc;
  }, {} as Record<LearningCategory, number>);

  const sorted = Object.entries(counts).sort(([, a], [, b]) => b - a);
  const maxCount = Math.max(...Object.values(counts), 1);

  return (
    <div className="panel p-4">
      <div className="section-label">Learnings — por categoría</div>
      <div className="text-[10px] text-[var(--color-text-2)] mt-0.5 mb-3">
        confianza prom. {avgConf}
      </div>

      <div className="space-y-1.5">
        {sorted.map(([cat, count]) => {
          const cfg = LEARNING_CATEGORIES[cat as LearningCategory];
          const pct = (count / maxCount) * 100;

          return (
            <div key={cat} className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--color-text-1)] min-w-[100px] truncate">{cfg.label}</span>
              <div className="pbar-track">
                <div className="pbar-fill" style={{ width: `${pct}%`, background: cfg.color }} />
              </div>
              <span className="num text-[10px] text-[var(--color-text-0)] min-w-[24px] text-right">{count}</span>
            </div>
          );
        })}
      </div>

      <div className="mt-3 text-[10px] text-[var(--color-text-2)]">
        Total: <span className="num text-[var(--color-text-1)]">{total}</span> aprendizajes
      </div>
    </div>
  );
}
