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

export default function DashboardPage() {
  return (
    <>
      {/* Header solo en mobile */}
      <Header title="Dashboard" />

      <div className="p-4 lg:p-6 space-y-6">
        {/* Desktop: titulo + ultima actualizacion */}
        <div className="hidden lg:flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
              AutoLab Dashboard
            </h1>
            <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
              Sistema autónomo BTC/USDT · ciclos cada 30 min
            </p>
          </div>
        </div>

        {/* ─── Fila 1: Métricas principales ──────────────────────────── */}
        <section>
          <h2 className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-3">
            Estado general
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SystemHealth />
            <ChampionCard />
            <BestOOSCard />
            <QueueStatus />
          </div>
        </section>

        {/* ─── Fila 2: Gauge + Donut ─────────────────────────────────── */}
        <section>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <FitnessGauge />
            <TradesDonut />
            <LearningsBars />
          </div>
        </section>

        {/* ─── Autoresearch chart — full width ───────────────────────── */}
        <section>
          <AutoresearchChart />
        </section>

        {/* ─── Top runs table — full width ───────────────────────────── */}
        <section>
          <RunsTable />
        </section>

        {/* ─── Learnings + Insights ──────────────────────────────────── */}
        <section>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <LearningsFeed />
            <OpusInsightsPanel />
          </div>
        </section>
      </div>
    </>
  );
}
