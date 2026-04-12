"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type {
  HealthResponse,
  StatusResponse,
  ContextResponse,
  LearningsResponse,
  OpusInsightsResponse,
  EquityCurveResponse,
  ChampionHistoryResponse,
  CyclesResponse,
  SystemMetricsResponse,
  CandlesResponse,
} from "@/types/api";

// Config base de polling — datos cambian cada 30 min en el backend
const SWR_BASE = {
  keepPreviousData: true,
  revalidateOnFocus: false,
  errorRetryInterval: 60_000,
};

// Health: cada 30s — es el "latido" del sistema
export function useHealth() {
  return useSWR<HealthResponse>("/health", fetcher, {
    ...SWR_BASE,
    refreshInterval: 30_000,
  });
}

// Status: cada 30s — champion, queue, best_oos
export function useStatus() {
  return useSWR<StatusResponse>("/status", fetcher, {
    ...SWR_BASE,
    refreshInterval: 30_000,
  });
}

// Context: cada 60s — top_results, learnings resumidos, opus_insights
export function useApiContext(topN: number = 20) {
  return useSWR<ContextResponse>(`/context?top_n=${topN}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Learnings completos: cada 60s
export function useLearnings() {
  return useSWR<LearningsResponse>("/learnings", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Opus insights: cada 60s
export function useOpusInsights() {
  return useSWR<OpusInsightsResponse>("/opus-insights", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Equity curve del campeón (o de un run específico): cada 60s
export function useEquityCurve(runId?: string) {
  const key = runId ? `/metrics/equity-curve?run_id=${runId}` : "/metrics/equity-curve";
  return useSWR<EquityCurveResponse>(key, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Historial de campeones: cada 60s
export function useChampionHistory() {
  return useSWR<ChampionHistoryResponse>("/metrics/champion-history", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Ciclos autónomos: cada 60s
export function useCycles(limit: number = 100) {
  return useSWR<CyclesResponse>(`/metrics/cycles?limit=${limit}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Métricas del sistema: cada 60s
export function useSystemMetrics() {
  return useSWR<SystemMetricsResponse>("/metrics/system", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Velas OHLCV de backtesting: cada 5 min (datos estáticos)
export function useCandles(timeframe: string = "4h", dataset: string = "valid", limit: number = 3000) {
  return useSWR<CandlesResponse>(
    `/metrics/candles?timeframe=${timeframe}&dataset=${dataset}&limit=${limit}`,
    fetcher,
    { ...SWR_BASE, refreshInterval: 300_000 }
  );
}
