"use client";

import { Lightbulb } from "lucide-react";
import { useOpusInsights } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { timeAgo } from "@/lib/formatters";

export function OpusInsightsPanel() {
  const { data, isLoading } = useOpusInsights();

  if (isLoading && !data) {
    return <MetricCard title="Insights estratégicos (Opus)" loading />;
  }

  const insights = data?.insights ?? [];

  return (
    <MetricCard title="Insights estratégicos (Opus)">
      {insights.length === 0 ? (
        <div className="mt-4 flex flex-col items-center gap-3 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-surface-3)]">
            <Lightbulb className="h-5 w-5 text-[var(--color-text-2)]" />
          </div>
          <div className="text-center">
            <p className="text-[12px] text-[var(--color-text-1)]">
              No hay insights estratégicos activos aún
            </p>
            <p className="text-[11px] text-[var(--color-text-2)] mt-1.5 max-w-[260px] leading-relaxed">
              El agente Opus analiza los resultados semanalmente y genera directivas de alto nivel para guiar la exploración.
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-3 space-y-2">
          {insights.map((insight, idx) => (
            <div
              key={insight.id ?? idx}
              className="rounded-lg bg-[var(--color-surface-0)] p-3 border border-transparent hover:border-[var(--color-border)] transition-colors"
            >
              {insight.content && (
                <p className="text-[12px] text-[var(--color-text-1)] leading-relaxed">
                  {insight.content}
                </p>
              )}
              {insight.created_at && (
                <p className="mt-2 text-[10px] text-[var(--color-text-2)] num">
                  {timeAgo(insight.created_at)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </MetricCard>
  );
}
