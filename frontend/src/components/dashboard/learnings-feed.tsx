"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Filter } from "lucide-react";
import { useLearnings } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { TooltipHelp } from "./tooltip-help";
import { LEARNING_CATEGORIES } from "@/lib/constants";
import { LearningCategory, Learning } from "@/types/api";
import { timeAgo } from "@/lib/formatters";
import { cn } from "@/lib/utils";

function LearningItem({ learning }: { learning: Learning }) {
  const [expanded, setExpanded] = useState(false);
  const config = LEARNING_CATEGORIES[learning.category];
  const confidencePct = Math.round(learning.confidence * 100);

  return (
    <div
      className="group cursor-pointer rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3 hover:border-[var(--color-border-strong)] transition-colors"
      onClick={() => setExpanded((e) => !e)}
    >
      {/* Header del item */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-sm">{config.emoji}</span>
          <span
            className="text-xs font-medium rounded px-1.5 py-0.5"
            style={{
              backgroundColor: `${config.color}20`,
              color: config.color,
            }}
          >
            {config.label}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-[var(--color-text-muted)]">
            {timeAgo(learning.created_at)}
          </span>
          {expanded ? (
            <ChevronUp className="h-3 w-3 text-[var(--color-text-muted)]" />
          ) : (
            <ChevronDown className="h-3 w-3 text-[var(--color-text-muted)]" />
          )}
        </div>
      </div>

      {/* Contenido */}
      <p
        className={cn(
          "mt-2 text-xs text-[var(--color-text-secondary)] leading-relaxed",
          !expanded && "line-clamp-2"
        )}
      >
        {learning.content}
      </p>

      {/* Barra de confianza */}
      <div className="mt-2 flex items-center gap-2">
        <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              width: `${confidencePct}%`,
              backgroundColor: config.color,
              opacity: 0.7,
            }}
          />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-[var(--color-text-muted)] font-mono">
            {confidencePct}%
          </span>
          <TooltipHelp term="confidence" />
        </div>
      </div>
    </div>
  );
}

const ALL_CATEGORIES = Object.keys(LEARNING_CATEGORIES) as LearningCategory[];

export function LearningsFeed() {
  const { data, isLoading } = useLearnings();
  const [isOpen, setIsOpen] = useState(true);
  const [activeFilter, setActiveFilter] = useState<LearningCategory | "all">("all");
  const [showAll, setShowAll] = useState(false);

  if (isLoading && !data) {
    return <MetricCard title="Razonamiento del agente IA" loading />;
  }

  const allLearnings = data?.learnings ?? [];
  const filtered =
    activeFilter === "all"
      ? allLearnings
      : allLearnings.filter((l) => l.category === activeFilter);

  const visible = showAll ? filtered : filtered.slice(0, 6);

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
      {/* Header colapsable */}
      <button
        className="flex w-full items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors rounded-t-xl"
        onClick={() => setIsOpen((o) => !o)}
      >
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide">
            Razonamiento del agente IA
          </h3>
          <TooltipHelp term="learnings_feed" />
          <span className="text-xs text-[var(--color-text-muted)]">
            ({allLearnings.length} aprendizajes)
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-[var(--color-text-muted)]" />
        ) : (
          <ChevronDown className="h-4 w-4 text-[var(--color-text-muted)]" />
        )}
      </button>

      {isOpen && (
        <div className="px-4 pb-4">
          {/* Filtros por categoria */}
          <div className="flex flex-wrap gap-1.5 mb-4 pb-3 border-b border-[var(--color-border)]">
            <button
              onClick={() => setActiveFilter("all")}
              className={cn(
                "flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors",
                activeFilter === "all"
                  ? "bg-white/15 text-[var(--color-text-primary)]"
                  : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
              )}
            >
              <Filter className="h-3 w-3" />
              Todos
            </button>
            {ALL_CATEGORIES.map((cat) => {
              const config = LEARNING_CATEGORIES[cat];
              const count = allLearnings.filter((l) => l.category === cat).length;
              return (
                <button
                  key={cat}
                  onClick={() => setActiveFilter(cat)}
                  className={cn(
                    "rounded-md px-2 py-1 text-xs transition-colors",
                    activeFilter === cat
                      ? "text-[var(--color-text-primary)]"
                      : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
                  )}
                  style={
                    activeFilter === cat
                      ? { backgroundColor: `${config.color}25`, color: config.color }
                      : {}
                  }
                >
                  {config.emoji} {config.label} ({count})
                </button>
              );
            })}
          </div>

          {/* Lista de learnings */}
          <div className="space-y-2">
            {visible.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)]">
                Sin aprendizajes en esta categoría
              </p>
            ) : (
              visible.map((l) => <LearningItem key={l.id} learning={l} />)
            )}
          </div>

          {/* Ver mas / menos */}
          {filtered.length > 6 && (
            <button
              onClick={() => setShowAll((s) => !s)}
              className="mt-3 w-full text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors py-2"
            >
              {showAll
                ? "Ver menos"
                : `Ver ${filtered.length - 6} aprendizajes más...`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
