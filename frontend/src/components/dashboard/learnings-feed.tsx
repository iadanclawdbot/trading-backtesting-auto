"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useLearnings } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { LEARNING_CATEGORIES } from "@/lib/constants";
import { LearningCategory, Learning } from "@/types/api";
import { timeAgo } from "@/lib/formatters";
import { cn } from "@/lib/utils";

function LearningItem({ learning }: { learning: Learning }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = LEARNING_CATEGORIES[learning.category];
  const confPct = Math.round(learning.confidence * 100);

  return (
    <div
      className="cursor-pointer rounded-lg bg-[var(--color-surface-0)] p-3 hover:bg-[var(--color-surface-2)] transition-colors border border-transparent hover:border-[var(--color-border)]"
      onClick={() => setExpanded((e) => !e)}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="pill text-[10px]"
          style={{ background: `${cfg.color}12`, borderColor: `${cfg.color}30`, color: cfg.color }}
        >
          {cfg.label}
        </span>
        <span className="text-[10px] text-[var(--color-text-2)] num shrink-0">
          {confPct}% · {timeAgo(learning.created_at)}
        </span>
      </div>

      <p className={cn("mt-2 text-[12px] text-[var(--color-text-1)] leading-relaxed", !expanded && "line-clamp-2")}>
        {learning.content}
      </p>

      {/* Confidence bar */}
      <div className="mt-2 h-[3px] w-full rounded-full bg-[var(--color-surface-3)] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${confPct}%`, background: cfg.color, opacity: 0.6 }} />
      </div>
    </div>
  );
}

const ALL_CATS = Object.keys(LEARNING_CATEGORIES) as LearningCategory[];

export function LearningsFeed() {
  const { data, isLoading } = useLearnings();
  const [isOpen, setIsOpen] = useState(true);
  const [filter, setFilter] = useState<LearningCategory | "all">("all");
  const [showAll, setShowAll] = useState(false);

  if (isLoading && !data) return <MetricCard title="Razonamiento del agente IA" loading />;

  const all = data?.learnings ?? [];
  const filtered = filter === "all" ? all : all.filter((l) => l.category === filter);
  const visible = showAll ? filtered : filtered.slice(0, 5);

  return (
    <div className="panel">
      {/* Header */}
      <div
        role="button"
        tabIndex={0}
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-[var(--color-surface-2)] transition-colors rounded-t-xl"
        onClick={() => setIsOpen((o) => !o)}
        onKeyDown={(e) => e.key === "Enter" && setIsOpen((o) => !o)}
      >
        <div className="flex items-center gap-2">
          <span className="section-label">Razonamiento del agente IA</span>
          <span className="text-[10px] text-[var(--color-text-2)] num">({all.length})</span>
        </div>
        {isOpen ? <ChevronUp className="h-3.5 w-3.5 text-[var(--color-text-2)]" /> : <ChevronDown className="h-3.5 w-3.5 text-[var(--color-text-2)]" />}
      </div>

      {isOpen && (
        <div className="px-4 pb-4">
          {/* Filter pills */}
          <div className="flex flex-wrap gap-1.5 mb-3 pb-3 border-b border-[var(--color-border)]">
            <button
              onClick={() => setFilter("all")}
              className={cn("pill text-[10px] cursor-pointer transition-colors",
                filter === "all" ? "bg-[var(--color-surface-3)] border-[var(--color-border-hover)] text-[var(--color-text-0)]" : "border-transparent text-[var(--color-text-2)] hover:text-[var(--color-text-1)]"
              )}
            >
              Todos
            </button>
            {ALL_CATS.map((cat) => {
              const cfg = LEARNING_CATEGORIES[cat];
              const n = all.filter((l) => l.category === cat).length;
              const active = filter === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setFilter(cat)}
                  className="pill text-[10px] cursor-pointer transition-colors"
                  style={active
                    ? { background: `${cfg.color}18`, borderColor: `${cfg.color}40`, color: cfg.color }
                    : { borderColor: "transparent", color: "var(--color-text-2)" }
                  }
                >
                  {cfg.label} ({n})
                </button>
              );
            })}
          </div>

          {/* Items */}
          <div className="space-y-2">
            {visible.length === 0
              ? <p className="text-sm text-[var(--color-text-2)] py-2">Sin resultados</p>
              : visible.map((l) => <LearningItem key={l.id} learning={l} />)
            }
          </div>

          {filtered.length > 5 && (
            <button
              onClick={() => setShowAll((s) => !s)}
              className="mt-3 w-full text-[11px] text-[var(--color-text-2)] hover:text-[var(--color-text-0)] transition-colors py-1.5 num"
            >
              {showAll ? "Mostrar menos" : `Ver ${filtered.length - 5} más…`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
