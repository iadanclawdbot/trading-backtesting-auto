"use client";

import { useStatus, useApiContext, useHealth } from "@/hooks/use-api";
import { SystemHealth } from "@/components/dashboard/system-health";
import { ChampionCard } from "@/components/dashboard/champion-card";
import { QueueStatus } from "@/components/dashboard/queue-status";
import { BestOOSCard } from "@/components/dashboard/best-oos-card";
import { FitnessGauge } from "@/components/dashboard/fitness-gauge";
import { EquityCurve } from "@/components/dashboard/equity-curve";
import { AutoresearchChart } from "@/components/dashboard/autoresearch-chart";
import { TradesDonut } from "@/components/dashboard/trades-donut";
import { LearningsBars } from "@/components/dashboard/learnings-bars";
import { RunsTable } from "@/components/dashboard/runs-table";
import { LearningsFeed } from "@/components/dashboard/learnings-feed";
import { OpusInsightsPanel } from "@/components/dashboard/opus-insights-panel";
import { ChampionTimeline } from "@/components/dashboard/champion-timeline";
import { CyclesChart } from "@/components/dashboard/cycles-chart";
import { SystemStats } from "@/components/dashboard/system-stats";
import { MarketContext } from "@/components/dashboard/market-context";
import { Header } from "@/components/layout/header";
import { ErrorBoundary } from "@/components/error-boundary";
import { BENCHMARK_FITNESS } from "@/lib/constants";
import { formatCurrency, formatPercent, formatSharpe, formatNumber, timeAgo } from "@/lib/formatters";
import { getStrategy } from "@/lib/constants";

/* ─── KPI Row — dense metric cards like a trading terminal ────── */
function KPIRow() {
  const { data, isLoading } = useStatus();
  const { data: ctx } = useApiContext(10);

  if (isLoading && !data) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="mcard">
            <div className="animate-pulse space-y-2">
              <div className="h-2 w-12 rounded bg-[var(--color-surface-3)]" />
              <div className="h-5 w-16 rounded bg-[var(--color-surface-3)]" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const champion = data?.champion;
  const best = data?.best_oos;
  const queue = data?.queue;
  const done = queue?.done ?? 0;
  const failed = queue?.failed ?? 0;
  const beats = (best?.sharpe_ratio ?? 0) >= BENCHMARK_FITNESS;

  // Train vs OOS consistency from top results
  const topResults = ctx?.top_results ?? [];
  const bestResult = topResults[0];
  const consistency = bestResult && bestResult.sharpe_train > 0
    ? bestResult.sharpe_oos / bestResult.sharpe_train
    : null;

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        <div className="mcard">
          <div className="lbl">Fitness score</div>
          <div className="val">{best ? formatSharpe(best.sharpe_ratio) : "—"}</div>
          <div className={`sub ${beats ? "up" : ""}`}>
            {beats ? `↑ +${(best!.sharpe_ratio - BENCHMARK_FITNESS).toFixed(3)} vs benchmark` : "bajo benchmark"}
          </div>
        </div>
        <div className="mcard">
          <div className="lbl">Sharpe OOS</div>
          <div className="val">{best ? formatSharpe(best.sharpe_ratio) : "—"}</div>
          <div className="sub warn">
            Train: {bestResult ? formatSharpe(bestResult.sharpe_train) : "—"}
          </div>
        </div>
        <div className="mcard">
          <div className="lbl">Win rate</div>
          <div className="val">{best ? formatPercent(best.win_rate, false) : "—"}</div>
          <div className="sub">{best ? `${best.total_trades} trades` : ""}</div>
        </div>
        <div className="mcard">
          <div className="lbl">Max drawdown</div>
          <div className="val dn">{best ? formatPercent(best.max_drawdown) : "—"}</div>
          <div className="sub">capital: {champion ? formatCurrency(champion.capital_final) : "—"}</div>
        </div>
        <div className="mcard">
          <div className="lbl">Beat benchmark</div>
          <div className={`val ${beats ? "up" : "dn"}`}>{beats ? "Sí" : "No"}</div>
          <div className="sub">vs {BENCHMARK_FITNESS} target</div>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        <div className="mcard">
          <div className="lbl">PnL total</div>
          <div className={`val ${champion && champion.pnl_pct >= 0 ? "up" : "dn"}`}>
            {champion ? formatPercent(champion.pnl_pct) : "—"}
          </div>
          <div className="sub">{champion ? `desde $250` : ""}</div>
        </div>
        <div className="mcard">
          <div className="lbl">Consistency ratio</div>
          <div className="val">{consistency !== null ? consistency.toFixed(2) : "—"}</div>
          <div className="sub">{consistency !== null && consistency > 0.7 ? "sin overfitting" : "revisar"}</div>
        </div>
        <div className="mcard">
          <div className="lbl">Capital final</div>
          <div className="val up">{champion ? formatCurrency(champion.capital_final) : "—"}</div>
          <div className={`sub ${champion && champion.pnl_pct >= 0 ? "up" : ""}`}>
            {champion ? `${formatPercent(champion.pnl_pct)} desde $250` : ""}
          </div>
        </div>
        <div className="mcard">
          <div className="lbl">Experimentos done</div>
          <div className="val up">{formatNumber(done)}</div>
          <div className="sub dn">{failed > 0 ? `failed: ${failed}` : "0 failures"}</div>
        </div>
        <div className="mcard">
          <div className="lbl">Tasa de éxito</div>
          <div className="val up">{done + failed > 0 ? ((done / (done + failed)) * 100).toFixed(1) + "%" : "—"}</div>
          <div className="sub">ratio done/total</div>
        </div>
      </div>
    </>
  );
}

/* ─── Topbar with cycle info ─────────────────────────────── */
function Topbar() {
  const { data: health } = useHealth();
  const { data: status } = useStatus();
  const isOk = health?.status === "ok";
  const champion = status?.champion;
  const strat = champion ? getStrategy(champion.strategy) : null;
  const beats = status?.best_oos ? status.best_oos.sharpe_ratio >= BENCHMARK_FITNESS : false;

  return (
    <div className="flex items-center justify-between px-5 py-2 border-b border-[var(--color-border)] bg-[var(--color-bg)] sticky top-0 z-10">
      <div className="flex items-center gap-2 num text-[12px] text-[var(--color-text-2)]">
        <span>Overview</span>
        <span className="text-[var(--color-text-0)] font-medium">
          / exp #{formatNumber(status?.queue?.done ?? 0)}
        </span>
      </div>
      <div className="flex items-center gap-3">
        {beats && (
          <span className="pill" style={{ background: "var(--color-green-dim)", borderColor: "rgba(74,222,128,0.2)", color: "var(--color-green)" }}>
            beat benchmark
          </span>
        )}
        {strat && (
          <span className="pill" style={{ background: `${strat.color}12`, borderColor: `${strat.color}30`, color: strat.color }}>
            {strat.label}
          </span>
        )}
        <div className="flex items-center gap-1.5">
          <span className={`dot ${isOk ? "dot-ok" : health ? "dot-err" : "dot-warn"}`} />
          <span className="text-[11px] text-[var(--color-text-2)] num">
            {health ? timeAgo(health.timestamp) : "conectando…"}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <>
      <Header title="Dashboard" />

      {/* Desktop topbar */}
      <div className="hidden lg:block">
        <Topbar />
      </div>

      <div className="p-3 lg:px-5 lg:py-4 space-y-2">
        {/* Mobile: system health */}
        <div className="lg:hidden animate-in">
          <SystemHealth />
        </div>

        {/* ─── KPIs ────────────────────────────────────────── */}
        <div className="section-divider" style={{ marginTop: 0 }}>Rendimiento — campeón actual</div>
        <div className="space-y-2 animate-in">
          <ErrorBoundary fallbackTitle="Error cargando KPIs">
            <KPIRow />
          </ErrorBoundary>
        </div>

        {/* ─── Equity + Donut + Market ─────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr_1fr] gap-2 animate-in" style={{ animationDelay: "0.05s" }}>
          <ErrorBoundary fallbackTitle="Error cargando equity curve">
            <EquityCurve />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando donut">
            <TradesDonut />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando mercado">
            <MarketContext />
          </ErrorBoundary>
        </div>

        {/* ─── Autoresearch chart ──────────────────────────── */}
        <div className="section-divider">Autoresearch progress</div>
        <div className="animate-in" style={{ animationDelay: "0.1s" }}>
          <ErrorBoundary fallbackTitle="Error cargando autoresearch">
            <AutoresearchChart />
          </ErrorBoundary>
        </div>

        {/* ─── Ciclos + Champions/Gauge + Learnings ────────── */}
        <div className="section-divider">Ciclos y aprendizaje</div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 animate-in" style={{ animationDelay: "0.15s" }}>
          <ErrorBoundary fallbackTitle="Error cargando ciclos">
            <CyclesChart />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando gauge">
            <FitnessGauge />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando learnings">
            <LearningsBars />
          </ErrorBoundary>
        </div>

        {/* ─── Champion history + details ──────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-2 animate-in" style={{ animationDelay: "0.17s" }}>
          <ErrorBoundary fallbackTitle="Error cargando campeón">
            <ChampionCard />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando historial">
            <ChampionTimeline />
          </ErrorBoundary>
        </div>

        {/* ─── Runs table ──────────────────────────────────── */}
        <div className="section-divider">Top experimentos</div>
        <div className="animate-in" style={{ animationDelay: "0.2s" }}>
          <ErrorBoundary fallbackTitle="Error cargando tabla">
            <RunsTable />
          </ErrorBoundary>
        </div>

        {/* ─── Queue + System ──────────────────────────────── */}
        <div className="section-divider">Sistema</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 animate-in" style={{ animationDelay: "0.25s" }}>
          <ErrorBoundary fallbackTitle="Error cargando cola">
            <QueueStatus />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando best OOS">
            <BestOOSCard />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando infraestructura">
            <SystemStats />
          </ErrorBoundary>
          <ErrorBoundary fallbackTitle="Error cargando razonamiento IA">
            <OpusInsightsPanel />
          </ErrorBoundary>
        </div>

        {/* ─── Learnings feed (full width) ─────────────────── */}
        <div className="animate-in" style={{ animationDelay: "0.3s" }}>
          <ErrorBoundary fallbackTitle="Error cargando razonamiento IA">
            <LearningsFeed />
          </ErrorBoundary>
        </div>
      </div>
    </>
  );
}
