"use client";

import { useHealth } from "@/hooks/use-api";
import { useCoin, COINS } from "@/context/coin-context";
import { timeAgo } from "@/lib/formatters";
import { ThemeToggle } from "./theme-toggle";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { data: health } = useHealth();
  const { coin, setCoin } = useCoin();
  const isOk = health?.status === "ok";

  return (
    <header className="flex h-12 items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-surface-0)] lg:hidden">
      <div className="flex items-center gap-2">
        <Activity className="h-4 w-4 text-[var(--color-green)]" />
        {/* Coin selector mobile */}
        <div className="flex items-center gap-0.5 bg-[var(--color-surface-2)] rounded p-0.5">
          {COINS.map((c) => (
            <button
              key={c.symbol}
              onClick={() => setCoin(c.symbol)}
              className={cn(
                "px-1.5 py-0.5 text-[10px] num rounded transition-all",
                coin === c.symbol
                  ? "bg-[var(--color-surface-3)] font-medium shadow-sm"
                  : "text-[var(--color-text-2)]"
              )}
              style={coin === c.symbol ? { color: c.color } : undefined}
            >
              {c.label}
            </button>
          ))}
        </div>
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
