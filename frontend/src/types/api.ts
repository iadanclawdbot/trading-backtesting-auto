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
  symbol?: string;
  params_json: string; // JSON string — parsear al mostrar
  sharpe_oos: number;
  trades_oos: number;
  wr_oos: number;
  dd_oos: number;
  created_at: string;
  capital_final: number;
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
  insight_type?: string;
  priority?: number;
  title?: string;
  content?: string;
  data_basis?: string;
  created_at?: string;
  expires_at?: string;
}

export interface OpusInsightsResponse {
  insights: OpusInsight[];
  count: number;
}

// GET /metrics/equity-curve?run_id=X
export interface EquityCurvePoint {
  bar: number;
  ts: number;
  equity: number;
  in_pos: number;
}

export interface EquityCurveResponse {
  run_id: string | null;
  strategy: string | null;
  capital_final?: number;
  sharpe_ratio?: number;
  total_trades?: number;
  win_rate?: number;
  points: EquityCurvePoint[];
  message?: string;
}

// GET /metrics/champion-history
export interface ChampionHistoryEntry {
  id: number;
  promoted_at: string;
  run_id: string;
  strategy: string;
  capital_final: number;
  pnl_pct: number | null;
  sharpe_ratio: number | null;
  total_trades: number | null;
  win_rate: number | null;
  max_drawdown: number | null;
}

export interface ChampionHistoryResponse {
  champions: ChampionHistoryEntry[];
  count: number;
}

// GET /metrics/cycles?limit=N
export interface CycleEntry {
  id: number;
  cycle_num: number;
  session_id: string;
  phase: string;
  finished_at: string;
  jobs_completed: number;
  best_sharpe_oos: number | null;
  beat_benchmark: boolean;
  notes: string | null;
}

export interface CyclesResponse {
  cycles: CycleEntry[];
  count: number;
}

// GET /metrics/candles
export interface CandlePoint {
  ts: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume_usdt: number;
}

export interface ChampionTrade {
  entrada_fecha: string;
  salida_fecha: string;
  precio_entrada: number;
  precio_salida: number;
  resultado: string;
  pnl_pct: number;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: string;
  dataset: string;
  candles: CandlePoint[];
  count: number;
  champion_trades: ChampionTrade[];
}

// GET /metrics/system
export interface SystemMetricsResponse {
  db_size_mb: number;
  total_runs: number;
  total_trades: number;
  total_experiments: number;
  total_candle_states: number;
  strategies_tested: number;
}
