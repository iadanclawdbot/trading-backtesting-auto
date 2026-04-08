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
        <div className="mt-3 flex flex-col items-center gap-3 py-4">
          <Lightbulb className="h-8 w-8 text-[var(--color-text-muted)]" />
          <div className="text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              No hay insights estratégicos activos aún.
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-1 max-w-[240px]">
              El agente Opus analiza los resultados semanalmente y genera directivas de alto nivel para guiar la exploración.
            </p>
          </div>
        </div>
      ) : (
        <div className="mt-3 space-y-3">
          {insights.map((insight, idx) => (
            <div
              key={insight.id ?? idx}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3"
            >
              {insight.content && (
                <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                  {insight.content}
                </p>
              )}
              {insight.created_at && (
                <p className="mt-2 text-xs text-[var(--color-text-muted)]">
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
