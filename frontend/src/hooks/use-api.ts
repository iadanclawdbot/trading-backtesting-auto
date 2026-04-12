"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { useCoin } from "@/context/coin-context";
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

// Health: cada 30s — es el "latido" del sistema (global, no depende de coin)
export function useHealth() {
  return useSWR<HealthResponse>("/health", fetcher, {
    ...SWR_BASE,
    refreshInterval: 30_000,
  });
}

// Status: cada 30s — champion, queue, best_oos (filtrado por coin)
export function useStatus() {
  const { coin } = useCoin();
  return useSWR<StatusResponse>(`/status?symbol=${coin}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 30_000,
  });
}

// Context: cada 60s — top_results filtrados por coin, learnings globales
export function useApiContext(topN: number = 20) {
  const { coin } = useCoin();
  return useSWR<ContextResponse>(`/context?top_n=${topN}&symbol=${coin}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Learnings completos: cada 60s (global, no depende de coin)
export function useLearnings() {
  return useSWR<LearningsResponse>("/learnings", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Opus insights: cada 60s (global, no depende de coin)
export function useOpusInsights() {
  return useSWR<OpusInsightsResponse>("/opus-insights", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Equity curve del campeón per coin (o de un run específico): cada 60s
export function useEquityCurve(runId?: string) {
  const { coin } = useCoin();
  const key = runId
    ? `/metrics/equity-curve?run_id=${runId}`
    : `/metrics/equity-curve?symbol=${coin}`;
  return useSWR<EquityCurveResponse>(key, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Historial de campeones per coin: cada 60s
export function useChampionHistory() {
  const { coin } = useCoin();
  return useSWR<ChampionHistoryResponse>(`/metrics/champion-history?symbol=${coin}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Ciclos autónomos: cada 60s (global, no depende de coin)
export function useCycles(limit: number = 100) {
  return useSWR<CyclesResponse>(`/metrics/cycles?limit=${limit}`, fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Métricas del sistema: cada 60s (global, no depende de coin)
export function useSystemMetrics() {
  return useSWR<SystemMetricsResponse>("/metrics/system", fetcher, {
    ...SWR_BASE,
    refreshInterval: 60_000,
  });
}

// Velas OHLCV de backtesting per coin: cada 5 min
export function useCandles(timeframe: string = "4h", dataset: string = "valid", limit: number = 3000, symbol?: string) {
  const { coin } = useCoin();
  const sym = symbol ?? coin;
  return useSWR<CandlesResponse>(
    `/metrics/candles?timeframe=${timeframe}&dataset=${dataset}&limit=${limit}&symbol=${sym}`,
    fetcher,
    { ...SWR_BASE, refreshInterval: 300_000 }
  );
}
