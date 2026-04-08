"use client";

import { motion } from "motion/react";
import { SystemHealth } from "@/components/dashboard/system-health";
import { ChampionCard } from "@/components/dashboard/champion-card";
import { QueueStatus } from "@/components/dashboard/queue-status";
import { BestOOSCard } from "@/components/dashboard/best-oos-card";
import { FitnessGauge } from "@/components/dashboard/fitness-gauge";
import { AutoresearchChart } from "@/components/dashboard/autoresearch-chart";
import { TradesDonut } from "@/components/dashboard/trades-donut";
import { LearningsBars } from "@/components/dashboard/learnings-bars";
import { RunsTable } from "@/components/dashboard/runs-table";
import { LearningsFeed } from "@/components/dashboard/learnings-feed";
import { OpusInsightsPanel } from "@/components/dashboard/opus-insights-panel";
import { Header } from "@/components/layout/header";
import { ErrorBoundary } from "@/components/error-boundary";

// Animacion de entrada con stagger para los children
const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.07 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, type: "tween" as const },
  },
};

function AnimatedSection({ children }: { children: React.ReactNode }) {
  return (
    <motion.div variants={itemVariants}>
      {children}
    </motion.div>
  );
}

export default function DashboardPage() {
  return (
    <>
      {/* Header solo en mobile */}
      <Header title="Dashboard" />

      <motion.div
        className="p-4 lg:p-6 space-y-6"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Desktop: titulo */}
        <motion.div variants={itemVariants} className="hidden lg:flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
              AutoLab Dashboard
            </h1>
            <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
              Sistema autónomo BTC/USDT · ciclos cada 30 min
            </p>
          </div>
        </motion.div>

        {/* ─── Fila 1: Métricas principales ──────────────────────────── */}
        <section>
          <motion.h2
            variants={itemVariants}
            className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-3"
          >
            Estado general
          </motion.h2>
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
            variants={containerVariants}
          >
            <AnimatedSection>
              <ErrorBoundary fallbackTitle="Error cargando estado del sistema">
                <SystemHealth />
              </ErrorBoundary>
            </AnimatedSection>
            <AnimatedSection>
              <ErrorBoundary fallbackTitle="Error cargando campeón">
                <ChampionCard />
              </ErrorBoundary>
            </AnimatedSection>
            <AnimatedSection>
              <ErrorBoundary fallbackTitle="Error cargando mejor OOS">
                <BestOOSCard />
              </ErrorBoundary>
            </AnimatedSection>
            <AnimatedSection>
              <ErrorBoundary fallbackTitle="Error cargando cola">
                <QueueStatus />
              </ErrorBoundary>
            </AnimatedSection>
          </motion.div>
        </section>

        {/* ─── Fila 2: Gauge + Donut + Bars ─────────────────────────── */}
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          variants={containerVariants}
        >
          <AnimatedSection>
            <ErrorBoundary fallbackTitle="Error cargando gauge">
              <FitnessGauge />
            </ErrorBoundary>
          </AnimatedSection>
          <AnimatedSection>
            <ErrorBoundary fallbackTitle="Error cargando donut de trades">
              <TradesDonut />
            </ErrorBoundary>
          </AnimatedSection>
          <AnimatedSection>
            <ErrorBoundary fallbackTitle="Error cargando learnings">
              <LearningsBars />
            </ErrorBoundary>
          </AnimatedSection>
        </motion.div>

        {/* ─── Autoresearch chart — full width ───────────────────────── */}
        <AnimatedSection>
          <ErrorBoundary fallbackTitle="Error cargando gráfico de investigación">
            <AutoresearchChart />
          </ErrorBoundary>
        </AnimatedSection>

        {/* ─── Top runs table — full width ───────────────────────────── */}
        <AnimatedSection>
          <ErrorBoundary fallbackTitle="Error cargando tabla de runs">
            <RunsTable />
          </ErrorBoundary>
        </AnimatedSection>

        {/* ─── Learnings + Insights ──────────────────────────────────── */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 gap-4"
          variants={containerVariants}
        >
          <AnimatedSection>
            <ErrorBoundary fallbackTitle="Error cargando razonamiento IA">
              <LearningsFeed />
            </ErrorBoundary>
          </AnimatedSection>
          <AnimatedSection>
            <ErrorBoundary fallbackTitle="Error cargando insights Opus">
              <OpusInsightsPanel />
            </ErrorBoundary>
          </AnimatedSection>
        </motion.div>
      </motion.div>
    </>
  );
}
