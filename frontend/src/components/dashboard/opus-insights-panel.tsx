"use client";

import { Lightbulb } from "lucide-react";
import { useOpusInsights } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { timeAgo } from "@/lib/formatters";
import { useState } from "react";

const TYPE_COLORS: Record<string, string> = {
  direction: "#4ade80",
  hypothesis: "#60a5fa",
  pattern: "#a78bfa",
  warning: "#f87171",
  dead_zone: "#f59e0b",
};

const TYPE_LABELS: Record<string, string> = {
  direction: "Dirección",
  hypothesis: "Hipótesis",
  pattern: "Patrón",
  warning: "Alerta",
  dead_zone: "Zona muerta",
};

export function OpusInsightsPanel() {
  const { data, isLoading } = useOpusInsights();
  const [expanded, setExpanded] = useState<number | null>(null);

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
          </div>
        </div>
      ) : (
        <div className="mt-3 space-y-1.5 max-h-[320px] overflow-y-auto">
          {insights.map((insight, idx) => {
            const color = TYPE_COLORS[insight.insight_type ?? ""] ?? "#6b7280";
            const label = TYPE_LABELS[insight.insight_type ?? ""] ?? insight.insight_type;
            const isOpen = expanded === idx;

            return (
              <button
                key={insight.id ?? idx}
                onClick={() => setExpanded(isOpen ? null : idx)}
                className="w-full text-left rounded-lg bg-[var(--color-surface-0)] p-2.5 border border-transparent hover:border-[var(--color-border)] transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span
                    className="pill mt-0.5 shrink-0"
                    style={{
                      background: `${color}15`,
                      borderColor: `${color}30`,
                      color,
                      fontSize: "9px",
                    }}
                  >
                    P{insight.priority} {label}
                  </span>
                  <span className="text-[11px] text-[var(--color-text-1)] leading-snug line-clamp-2">
                    {insight.title || insight.content?.slice(0, 80)}
                  </span>
                </div>
                {isOpen && insight.content && (
                  <p className="mt-2 text-[11px] text-[var(--color-text-2)] leading-relaxed whitespace-pre-line">
                    {insight.content}
                  </p>
                )}
                {!isOpen && (
                  <p className="mt-1 text-[10px] text-[var(--color-text-2)] num">
                    {insight.created_at ? timeAgo(insight.created_at) : ""}
                  </p>
                )}
              </button>
            );
          })}
        </div>
      )}
    </MetricCard>
  );
}
