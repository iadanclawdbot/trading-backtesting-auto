"use client";

import { motion, useMotionValue, useTransform, animate } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";

/* ─── Staggered section — fades in children sequentially ──── */

export function StaggerSection({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut", delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ─── Stagger grid — each child animates in sequence ──────── */

export function StaggerGrid({
  children,
  baseDelay = 0,
  stagger = 0.05,
  className = "",
}: {
  children: ReactNode;
  baseDelay?: number;
  stagger?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: { staggerChildren: stagger, delayChildren: baseDelay },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ─── Animated number — counts up from 0 to value ─────────── */

export function AnimatedNumber({
  value,
  format = "number",
  duration = 0.8,
  className = "",
}: {
  value: number | null | undefined;
  format?: "number" | "currency" | "percent" | "sharpe";
  duration?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionVal = useMotionValue(0);

  useEffect(() => {
    if (value == null) return;
    const controls = animate(motionVal, value, {
      duration,
      ease: "easeOut",
    });
    return controls.stop;
  }, [value, duration, motionVal]);

  const display = useTransform(motionVal, (v) => {
    if (value == null) return "—";
    switch (format) {
      case "currency":
        return `$${v.toFixed(v >= 1000 ? 0 : 2)}`;
      case "percent":
        return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
      case "sharpe":
        return v.toFixed(3);
      default:
        return v >= 100 ? Math.round(v).toLocaleString() : v.toFixed(1);
    }
  });

  return (
    <motion.span ref={ref} className={className}>
      {display}
    </motion.span>
  );
}
