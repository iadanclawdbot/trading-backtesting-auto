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

// Config para hooks GLOBALES (no dependen de coin) — mantener datos previos
const SWR_GLOBAL = {
  keepPreviousData: true,
  revalidateOnFocus: false,
  errorRetryInterval: 60_000,
};

// Config para hooks PER-COIN — NO keepPreviousData para evitar mezcla cross-coin
const SWR_COIN = {
  keepPreviousData: false,
  revalidateOnFocus: false,
  errorRetryInterval: 60_000,
};

// ─── HOOKS GLOBALES (no dependen de coin) ────────────────────

export function useHealth() {
  return useSWR<HealthResponse>("/health", fetcher, {
    ...SWR_GLOBAL,
    refreshInterval: 30_000,
  });
}

export function useLearnings() {
  return useSWR<LearningsResponse>("/learnings", fetcher, {
    ...SWR_GLOBAL,
    refreshInterval: 60_000,
  });
}

export function useOpusInsights() {
  return useSWR<OpusInsightsResponse>("/opus-insights", fetcher, {
    ...SWR_GLOBAL,
    refreshInterval: 60_000,
  });
}

export function useCycles(limit: number = 100) {
  return useSWR<CyclesResponse>(`/metrics/cycles?limit=${limit}`, fetcher, {
    ...SWR_GLOBAL,
    refreshInterval: 60_000,
  });
}

export function useSystemMetrics() {
  return useSWR<SystemMetricsResponse>("/metrics/system", fetcher, {
    ...SWR_GLOBAL,
    refreshInterval: 60_000,
  });
}

// ─── HOOKS PER-COIN (filtrados por moneda seleccionada) ──────

export function useStatus() {
  const { coin } = useCoin();
  return useSWR<StatusResponse>(`/status?symbol=${coin}`, fetcher, {
    ...SWR_COIN,
    refreshInterval: 30_000,
  });
}

export function useApiContext(topN: number = 20) {
  const { coin } = useCoin();
  return useSWR<ContextResponse>(`/context?top_n=${topN}&symbol=${coin}`, fetcher, {
    ...SWR_COIN,
    refreshInterval: 60_000,
  });
}

export function useEquityCurve(runId?: string) {
  const { coin } = useCoin();
  const key = runId
    ? `/metrics/equity-curve?run_id=${runId}`
    : `/metrics/equity-curve?symbol=${coin}`;
  return useSWR<EquityCurveResponse>(key, fetcher, {
    ...SWR_COIN,
    refreshInterval: 60_000,
  });
}

export function useChampionHistory() {
  const { coin } = useCoin();
  return useSWR<ChampionHistoryResponse>(`/metrics/champion-history?symbol=${coin}`, fetcher, {
    ...SWR_COIN,
    refreshInterval: 60_000,
  });
}

export function useCandles(timeframe: string = "4h", dataset: string = "valid", limit: number = 3000, symbol?: string) {
  const { coin } = useCoin();
  const sym = symbol ?? coin;
  return useSWR<CandlesResponse>(
    `/metrics/candles?timeframe=${timeframe}&dataset=${dataset}&limit=${limit}&symbol=${sym}`,
    fetcher,
    { ...SWR_COIN, refreshInterval: 300_000 }
  );
}
