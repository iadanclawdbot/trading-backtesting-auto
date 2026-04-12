"use client";

import { useOpusInsights } from "@/hooks/use-api";
import { Header } from "@/components/layout/header";
import { StaggerSection, StaggerGrid, StaggerItem } from "@/components/motion";
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

export default function InsightsPage() {
  const { data, isLoading } = useOpusInsights();
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const insights = data?.insights ?? [];

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const expandAll = () => {
    if (expanded.size === insights.length) {
      setExpanded(new Set());
    } else {
      setExpanded(new Set(insights.map((_, i) => i)));
    }
  };

  return (
    <>
      <Header title="Insights" />

      <div className="p-4 lg:p-6 space-y-4">
        <StaggerSection>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-sm font-semibold text-[var(--color-text-0)] tracking-wide">
                Insights estratégicos (Opus)
              </h1>
              <p className="text-[11px] text-[var(--color-text-2)] mt-0.5">
                Directivas de alto nivel generadas por Claude Opus 4.6 — guían la exploración del ciclo autónomo
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="num text-[11px] text-[var(--color-text-2)]">
                {insights.length} activos
              </span>
              {insights.length > 0 && (
                <button
                  onClick={expandAll}
                  className="px-2 py-1 text-[10px] num rounded text-[var(--color-text-2)] hover:text-[var(--color-text-1)] border border-[var(--color-border)] hover:border-[var(--color-text-2)] transition-colors"
                >
                  {expanded.size === insights.length ? "colapsar" : "expandir"} todos
                </button>
              )}
            </div>
          </div>
        </StaggerSection>

        {isLoading && !data ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="panel animate-pulse">
                <div className="h-4 w-48 rounded bg-[var(--color-surface-3)]" />
                <div className="h-3 w-full rounded bg-[var(--color-surface-3)] mt-3" />
                <div className="h-3 w-3/4 rounded bg-[var(--color-surface-3)] mt-2" />
              </div>
            ))}
          </div>
        ) : (
          <StaggerGrid className="space-y-2" stagger={0.04}>
            {insights.map((insight, idx) => {
              const color = TYPE_COLORS[insight.insight_type ?? ""] ?? "#6b7280";
              const label = TYPE_LABELS[insight.insight_type ?? ""] ?? insight.insight_type;
              const isOpen = expanded.has(idx);

              return (
                <StaggerItem key={insight.id ?? idx}>
                  <div
                    className="panel cursor-pointer hover:border-[var(--color-border)] transition-colors"
                    onClick={() => toggle(idx)}
                  >
                    {/* Header row */}
                    <div className="flex items-start gap-3">
                      <div className="flex items-center gap-2 shrink-0 mt-0.5">
                        <span
                          className="pill"
                          style={{
                            background: `${color}15`,
                            borderColor: `${color}30`,
                            color,
                            fontSize: "10px",
                          }}
                        >
                          P{insight.priority}
                        </span>
                        <span
                          className="pill"
                          style={{
                            background: `${color}10`,
                            borderColor: `${color}20`,
                            color,
                            fontSize: "10px",
                          }}
                        >
                          {label}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-[12px] font-medium text-[var(--color-text-0)] leading-snug">
                          {insight.title}
                        </h3>
                        {!isOpen && (
                          <p className="text-[11px] text-[var(--color-text-2)] mt-1 line-clamp-1">
                            {insight.content?.slice(0, 120)}...
                          </p>
                        )}
                      </div>
                      <span className="text-[10px] text-[var(--color-text-2)] num shrink-0">
                        {insight.created_at ? timeAgo(insight.created_at) : ""}
                      </span>
                    </div>

                    {/* Expanded content */}
                    {isOpen && (
                      <div className="mt-3 pt-3 border-t border-[var(--color-border)]">
                        {insight.content && (
                          <p className="text-[11px] text-[var(--color-text-1)] leading-relaxed whitespace-pre-line">
                            {insight.content}
                          </p>
                        )}
                        {insight.data_basis && (
                          <div className="mt-3 px-2.5 py-2 rounded bg-[var(--color-surface-0)] border border-[var(--color-border)]">
                            <span className="text-[9px] text-[var(--color-text-2)] uppercase tracking-wider">Base de datos</span>
                            <p className="text-[10px] text-[var(--color-text-2)] mt-1 leading-relaxed">
                              {insight.data_basis}
                            </p>
                          </div>
                        )}
                        {insight.expires_at && (
                          <p className="mt-2 text-[10px] text-[var(--color-text-2)] num">
                            Expira: {new Date(insight.expires_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </StaggerItem>
              );
            })}
          </StaggerGrid>
        )}
      </div>
    </>
  );
}
