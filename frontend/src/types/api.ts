// ─── Tipos derivados de respuestas reales de la API (2026-04-08) ───────────

// GET /health
export interface HealthResponse {
  status: "ok" | "degraded";
  sqlite: boolean;
  postgresql: boolean;
  timestamp: string;
}

// GET /status
export interface Champion {
  strategy: string;
  capital_final: number;
  pnl_pct: number;
  sharpe_ratio: number;
  total_trades: number;
  win_rate: number;
}

export interface BestOOS {
  strategy: string;
  sharpe_ratio: number;
  total_trades: number;
  win_rate: number;
  max_drawdown: number;
  created_at: string;
}

export interface Queue {
  done: number;
  failed: number;
}

export interface Benchmark {
  fitness: number;
  label: string;
}

export interface StatusResponse {
  status: string;
  timestamp: string;
  queue: Queue;
  best_oos: BestOOS;
  champion: Champion | null; // PUEDE SER null
  benchmark?: Benchmark;
  sqlite_path: string;
}

// GET /context?top_n=N
export interface TopResult {
  strategy: string;
  params_json: string; // JSON string — parsear al mostrar
  sharpe_oos: number;
  trades_oos: number;
  wr_oos: number;
  dd_oos: number;
  created_at: string;
  sharpe_train: number;
}

export interface ContextLearning {
  category: LearningCategory;
  content: string;
  confidence: number;
}

export interface ContextResponse {
  top_results: TopResult[];
  last_cycle_results: TopResult[];
  learnings: ContextLearning[];
  opus_insights: OpusInsight[];
}

// GET /learnings
// OJO: devuelve { learnings: [], count: N } — NO es array plano
export type LearningCategory =
  | "parameter_insight"
  | "dead_end"
  | "promising_direction"
  | "strategy_ranking"
  | "external_research";

export interface Learning {
  id: number;
  category: LearningCategory;
  content: string;
  confidence: number;
  created_at: string;
}

export interface LearningsResponse {
  learnings: Learning[];
  count: number;
}

// GET /opus-insights
// OJO: devuelve { insights: [], count: N } — actualmente vacio
export interface OpusInsight {
  id?: number;
  content?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface OpusInsightsResponse {
  insights: OpusInsight[];
  count: number;
}
