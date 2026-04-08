"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type {
  HealthResponse,
  StatusResponse,
  ContextResponse,
  LearningsResponse,
  OpusInsightsResponse,
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
export function useContext(topN: number = 20) {
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
