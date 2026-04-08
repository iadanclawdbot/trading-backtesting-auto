"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Lightbulb,
  FlaskConical,
  Activity,
} from "lucide-react";
import { useHealth } from "@/hooks/use-api";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const NAV = [
  { section: "Monitor", items: [
    { href: "/", label: "Overview", icon: LayoutDashboard },
  ]},
  { section: "Inteligencia", items: [
    { href: "/learnings", label: "Learnings", icon: BookOpen },
    { href: "/insights", label: "Opus insights", icon: Lightbulb },
  ]},
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: health } = useHealth();
  const isOk = health?.status === "ok";

  return (
    <aside className="hidden lg:flex flex-col w-[200px] flex-shrink-0 border-r border-[var(--color-border)] sticky top-0 h-screen overflow-hidden">
      {/* Brand */}
      <div className="px-5 pt-5 pb-4 border-b border-[var(--color-border)]">
        <div className="num text-[15px] font-medium text-[var(--color-green)]" style={{ letterSpacing: "-0.02em" }}>
          AutoLab
        </div>
        <div className="text-[10px] text-[var(--color-text-2)] mt-0.5 uppercase tracking-widest">
          BTC/USDT · 30 min
        </div>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 py-2 px-3 overflow-y-auto">
        {NAV.map(({ section, items }) => (
          <div key={section}>
            <div className="px-2 pt-3 pb-1 text-[9px] font-medium uppercase tracking-widest text-[var(--color-text-2)]">
              {section}
            </div>
            {items.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-2 py-1.5 text-[12px] transition-all border-l-2",
                    active
                      ? "border-[var(--color-green)] text-[var(--color-green)] bg-[var(--color-green-dim)]"
                      : "border-transparent text-[var(--color-text-1)] hover:text-[var(--color-text-0)] hover:bg-[var(--color-surface-2)]"
                  )}
                >
                  <span className={cn("dot", active ? "dot-ok" : "")} style={!active ? { background: "currentColor", opacity: 0.4 } : {}} />
                  {label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className={cn("dot animate-pulse-soft", isOk ? "dot-ok" : health ? "dot-err" : "dot-warn")} />
          <span className="text-[10px] text-[var(--color-text-2)]">
            {isOk ? "Sistema activo" : health ? "Degradado" : "Conectando…"}
          </span>
        </div>
        <ThemeToggle />
      </div>
    </aside>
  );
}
