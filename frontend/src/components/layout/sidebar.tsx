"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BookOpen, Lightbulb, Activity } from "lucide-react";
import { useHealth } from "@/hooks/use-api";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/learnings", label: "Learnings", icon: BookOpen },
  { href: "/insights", label: "Insights", icon: Lightbulb },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: health } = useHealth();
  const isOk = health?.status === "ok";

  return (
    <aside className="hidden lg:flex flex-col w-[200px] flex-shrink-0 border-r border-[var(--color-border)] bg-[var(--color-surface-0)]">
      {/* Brand */}
      <div className="flex items-center gap-2.5 h-12 px-4 border-b border-[var(--color-border)]">
        <Activity className="h-4 w-4 text-[var(--color-green)]" />
        <span className="num text-xs font-semibold tracking-wide text-[var(--color-text-0)]">
          AUTOLAB
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-all",
                active
                  ? "bg-[var(--color-green-dim)] text-[var(--color-green)]"
                  : "text-[var(--color-text-1)] hover:text-[var(--color-text-0)] hover:bg-[var(--color-surface-2)]"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-[var(--color-border)] space-y-3">
        {/* System status */}
        <div className="flex items-center gap-2 px-1">
          <span className={cn("dot", isOk ? "dot-ok" : health ? "dot-err" : "dot-warn")} />
          <span className="text-[11px] text-[var(--color-text-2)]">
            {isOk ? "Operativo" : health ? "Degradado" : "Conectando…"}
          </span>
        </div>
        <ThemeToggle />
      </div>
    </aside>
  );
}
