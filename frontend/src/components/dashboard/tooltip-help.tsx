"use client";

import { useState } from "react";
import { TOOLTIPS } from "@/lib/constants";

interface TooltipHelpProps {
  term: string;
  text?: string;
  className?: string;
}

export function TooltipHelp({ term, text, className }: TooltipHelpProps) {
  const [open, setOpen] = useState(false);
  const content = text ?? TOOLTIPS[term] ?? "";
  if (!content) return null;

  return (
    <span className={`relative inline-flex ${className ?? ""}`}>
      <button
        type="button"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
        className="inline-flex items-center justify-center h-[14px] w-[14px] rounded-full border border-[var(--color-border-hover)] text-[9px] font-medium text-[var(--color-text-2)] hover:text-[var(--color-text-1)] hover:border-[var(--color-text-2)] transition-colors leading-none"
        aria-label={`Info: ${term}`}
      >
        ?
      </button>

      {open && (
        <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-60 rounded-lg bg-[var(--color-surface-3)] border border-[var(--color-border-hover)] p-2.5 shadow-2xl text-[11px] text-[var(--color-text-1)] leading-relaxed pointer-events-none">
          {content}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-[var(--color-surface-3)]" />
        </span>
      )}
    </span>
  );
}
