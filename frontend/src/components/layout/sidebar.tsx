"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BookOpen, Lightbulb, ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useHealth } from "@/hooks/use-api";
import { ThemeToggle } from "./theme-toggle";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/learnings", label: "Learnings", icon: BookOpen },
  { href: "/insights", label: "Insights", icon: Lightbulb },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { data: health } = useHealth();

  const isOk = health?.status === "ok";

  return (
    <aside
      className={cn(
        "hidden lg:flex flex-col flex-shrink-0 border-r transition-all duration-200",
        "border-[var(--color-border)] bg-[var(--color-surface)]",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo / titulo */}
      <div className="flex h-14 items-center gap-2 px-4 border-b border-[var(--color-border)]">
        <span className="text-[var(--color-success)] font-mono text-sm font-semibold shrink-0">
          AL
        </span>
        {!collapsed && (
          <span className="text-[var(--color-text-primary)] text-sm font-medium truncate">
            AutoLab
          </span>
        )}
      </div>

      {/* Navegacion */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                active
                  ? "bg-[var(--color-success)]/10 text-[var(--color-success)]"
                  : "text-[var(--color-text-secondary)] hover:bg-white/5 hover:text-[var(--color-text-primary)]"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer: status + theme + collapse */}
      <div className="p-2 border-t border-[var(--color-border)] space-y-2">
        {/* Status del sistema */}
        <div className={cn("flex items-center gap-2 px-2 py-1", collapsed && "justify-center")}>
          <span
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              isOk ? "bg-[var(--color-success)]" : "bg-[var(--color-danger)]"
            )}
          />
          {!collapsed && (
            <span className="text-xs text-[var(--color-text-muted)]">
              {isOk ? "Sistema OK" : health ? "Degradado" : "Conectando..."}
            </span>
          )}
        </div>

        <div className={cn("flex items-center gap-1", collapsed ? "justify-center" : "px-1")}>
          <ThemeToggle />
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-white/10 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
            aria-label={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}
