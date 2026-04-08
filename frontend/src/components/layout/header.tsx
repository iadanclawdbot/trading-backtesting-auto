"use client";

import { useHealth } from "@/hooks/use-api";
import { timeAgo } from "@/lib/formatters";
import { ThemeToggle } from "./theme-toggle";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { data: health } = useHealth();
  const isOk = health?.status === "ok";

  return (
    <header className="flex h-12 items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-surface-0)] lg:hidden">
      <div className="flex items-center gap-2.5">
        <Activity className="h-4 w-4 text-[var(--color-green)]" />
        <span className="num text-xs font-semibold tracking-wide">{title.toUpperCase()}</span>
      </div>

      <div className="flex items-center gap-3">
        {health && (
          <div className="flex items-center gap-1.5">
            <span className={cn("dot", isOk ? "dot-ok" : "dot-err")} />
            <span className="text-[10px] text-[var(--color-text-2)] num">
              {timeAgo(health.timestamp)}
            </span>
          </div>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
