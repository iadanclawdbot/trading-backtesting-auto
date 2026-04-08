"use client";

import { useHealth } from "@/hooks/use-api";
import { timeAgo } from "@/lib/formatters";
import { cn } from "@/lib/utils";

export function SystemHealth() {
  const { data, isLoading } = useHealth();

  if (isLoading && !data) {
    return (
      <div className="flex items-center gap-3">
        <div className="dot dot-warn animate-pulse-soft" />
        <span className="text-[11px] text-[var(--color-text-2)]">Conectando…</span>
      </div>
    );
  }

  const items = [
    { label: "API", ok: data?.status === "ok" },
    { label: "SQLite", ok: data?.sqlite === true },
    { label: "PG", ok: data?.postgresql === true },
  ];

  return (
    <div className="flex items-center gap-4">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <span className={cn("dot", item.ok ? "dot-ok" : "dot-err")} />
          <span className="text-[11px] text-[var(--color-text-2)]">{item.label}</span>
        </div>
      ))}
      {data && (
        <span className="text-[10px] text-[var(--color-text-2)] num ml-2">
          {timeAgo(data.timestamp)}
        </span>
      )}
    </div>
  );
}
