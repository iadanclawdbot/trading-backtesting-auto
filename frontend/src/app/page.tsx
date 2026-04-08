"use client";

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

export default function DashboardPage() {
  return (
    <>
      <Header title="Dashboard" />

      <div className="p-4 lg:p-6 space-y-5">
        {/* Desktop title */}
        <div className="hidden lg:flex items-center justify-between animate-in">
          <div>
            <h1 className="text-sm font-semibold text-[var(--color-text-0)] tracking-wide">
              AutoLab Dashboard
            </h1>
            <p className="text-[11px] text-[var(--color-text-2)] mt-0.5">
              Sistema autónomo BTC/USDT · ciclos cada 30 min
            </p>
          </div>
          <SystemHealth />
        </div>

        {/* Mobile: system health below header */}
        <div className="lg:hidden animate-in">
          <SystemHealth />
        </div>

        {/* ─── Row 1: Key metrics ─────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 animate-in" style={{ animationDelay: "0.05s" }}>
          <ErrorBoundary fallbackTitle="Error cargando campeón">
            <ChampionCard />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando mejor OOS">
            <BestOOSCard />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando gauge">
            <FitnessGauge />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando cola">
            <QueueStatus />
          </ErrorBoundary>
        </div>

        {/* ─── Row 2: Donut + Learning bars ───────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-in" style={{ animationDelay: "0.1s" }}>
          <ErrorBoundary fallbackTitle="Error cargando donut">
            <TradesDonut />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando learnings">
            <LearningsBars />
          </ErrorBoundary>
        </div>

        {/* ─── Autoresearch chart — full width ────────────────── */}
        <div className="animate-in" style={{ animationDelay: "0.15s" }}>
          <ErrorBoundary fallbackTitle="Error cargando gráfico de investigación">
            <AutoresearchChart />
          </ErrorBoundary>
        </div>

        {/* ─── Top runs table — full width ────────────────────── */}
        <div className="animate-in" style={{ animationDelay: "0.2s" }}>
          <ErrorBoundary fallbackTitle="Error cargando tabla de runs">
            <RunsTable />
          </ErrorBoundary>
        </div>

        {/* ─── Learnings + Insights ───────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 animate-in" style={{ animationDelay: "0.25s" }}>
          <ErrorBoundary fallbackTitle="Error cargando razonamiento IA">
            <LearningsFeed />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando insights Opus">
            <OpusInsightsPanel />
          </ErrorBoundary>
        </div>
      </div>
    </>
  );
}
