"use client";

import { useHealth } from "@/hooks/use-api";
import { timeAgo } from "@/lib/formatters";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { data: health } = useHealth();
  const isOk = health?.status === "ok";

  return (
    <header className="flex h-14 items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-surface)] lg:hidden">
      <div className="flex items-center gap-3">
        <span className="text-[var(--color-success)] font-mono text-sm font-semibold">AL</span>
        <h1 className="text-sm font-medium text-[var(--color-text-primary)]">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {health && (
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                isOk ? "bg-[var(--color-success)]" : "bg-[var(--color-danger)]"
              )}
            />
            <span className="text-xs text-[var(--color-text-muted)]">
              {timeAgo(health.timestamp)}
            </span>
          </div>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
