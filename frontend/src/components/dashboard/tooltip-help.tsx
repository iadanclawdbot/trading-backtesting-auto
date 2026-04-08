"use client";

import { useState } from "react";
import { HelpCircle } from "lucide-react";
import { TOOLTIPS } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface TooltipHelpProps {
  term: string;
  text?: string; // texto directo (alternativa a buscar por term)
  className?: string;
}

export function TooltipHelp({ term, text, className }: TooltipHelpProps) {
  const [open, setOpen] = useState(false);
  const content = text ?? TOOLTIPS[term] ?? "";

  if (!content) return null;

  return (
    <span className={cn("relative inline-flex", className)}>
      <button
        type="button"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((o) => !o)}
        className="text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
        aria-label={`Explicacion: ${term}`}
      >
        <HelpCircle className="h-3.5 w-3.5" />
      </button>

      {open && (
        <span
          className={cn(
            "absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2",
            "w-64 rounded-lg border border-[var(--color-border-strong)]",
            "bg-[var(--color-surface-elevated)] p-3 shadow-xl",
            "text-xs text-[var(--color-text-secondary)] leading-relaxed",
            "pointer-events-none"
          )}
        >
          {content}
          {/* flecha */}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[var(--color-border-strong)]" />
        </span>
      )}
    </span>
  );
}
