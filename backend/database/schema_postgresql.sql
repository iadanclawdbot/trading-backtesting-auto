-- =============================================================================
-- schema_postgresql.sql — AutoLab Intelligence Layer
-- =============================================================================
-- Coco Stonks Lab — Fase 2: AutoLab
-- Base de datos: autolab_db (PostgreSQL / Supabase)
--
-- SEPARACIÓN DE RESPONSABILIDADES:
--   coco_lab.db (SQLite)      → Backtesting: candles, runs, trades, experiments
--   autolab_db (PostgreSQL)   → Inteligencia: cycles, learnings, research, opus
--
-- Deploy: ejecutar en Supabase SQL Editor o psql
-- =============================================================================


-- =============================================================================
-- TABLA: autolab_cycles
-- Log de cada ciclo del loop autónomo
-- =============================================================================

CREATE TABLE IF NOT EXISTS autolab_cycles (
    id              SERIAL PRIMARY KEY,
    cycle_num       INTEGER NOT NULL,
    session_id      TEXT NOT NULL,
    phase           TEXT NOT NULL
                        CHECK (phase IN ('analyze','hypothesize','queue','run','evaluate','learn','complete')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,

    -- LLM metadata
    llm_provider    TEXT,
    llm_model       TEXT,
    llm_tokens_in   INTEGER DEFAULT 0,
    llm_tokens_out  INTEGER DEFAULT 0,

    -- Resultados del ciclo
    hypothesis_json TEXT,           -- JSON del output de hypothesize
    jobs_queued     INTEGER DEFAULT 0,
    jobs_completed  INTEGER DEFAULT 0,
    best_fitness    REAL,
    best_sharpe_oos REAL,
    beat_benchmark  BOOLEAN DEFAULT FALSE,

    notes           TEXT,
    error_msg       TEXT
);

CREATE INDEX IF NOT EXISTS idx_cycles_session
    ON autolab_cycles(session_id, cycle_num);
CREATE INDEX IF NOT EXISTS idx_cycles_beat
    ON autolab_cycles(beat_benchmark) WHERE beat_benchmark = TRUE;


-- =============================================================================
-- TABLA: autolab_learnings
-- Conocimiento acumulado — insights estructurados por el LLM
-- =============================================================================

CREATE TABLE IF NOT EXISTS autolab_learnings (
    id          SERIAL PRIMARY KEY,
    cycle_num   INTEGER NOT NULL,
    session_id  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    category    TEXT NOT NULL
                    CHECK (category IN (
                        'parameter_insight',
                        'dead_end',
                        'promising_direction',
                        'strategy_ranking',
                        'external_research'  -- ideas de Brave Search
                    )),
    content     TEXT NOT NULL,
    confidence  REAL NOT NULL DEFAULT 0.5
                    CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Para marcar learnings obsoletos sin borrarlos
    superseded      BOOLEAN DEFAULT FALSE,
    superseded_by   INTEGER REFERENCES autolab_learnings(id),
    superseded_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_learnings_category
    ON autolab_learnings(category, superseded);
CREATE INDEX IF NOT EXISTS idx_learnings_session
    ON autolab_learnings(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_learnings_active
    ON autolab_learnings(superseded, confidence DESC)
    WHERE superseded = FALSE;


-- =============================================================================
-- TABLA: opus_insights
-- Directivas estratégicas del Director Senior (Claude Opus 4.6)
-- Escritas manualmente via /opus-analyst skill
-- Leídas automáticamente por el loop en cada ciclo
-- =============================================================================

CREATE TABLE IF NOT EXISTS opus_insights (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_version   TEXT NOT NULL DEFAULT 'claude-opus-4-6',

    insight_type    TEXT NOT NULL
                        CHECK (insight_type IN (
                            'pattern',           -- patrón identificado en datos
                            'direction',         -- dirección estratégica a seguir
                            'warning',           -- algo a evitar explícitamente
                            'hypothesis',        -- hipótesis nueva a probar
                            'dead_zone'          -- zona del espacio a no explorar
                        )),
    priority        INTEGER NOT NULL DEFAULT 3
                        CHECK (priority BETWEEN 1 AND 5),
                        -- 1=referencia, 3=importante, 5=urgente explorar

    title           TEXT NOT NULL,      -- resumen en 1 línea (para el prompt)
    content         TEXT NOT NULL,      -- análisis completo

    action_items    JSONB,              -- lista de experimentos concretos a probar
    data_basis      TEXT,              -- qué datos analizó Opus (fechas, N runs, batch_ids)

    applied_count   INTEGER DEFAULT 0, -- cuántos ciclos usaron este insight
    expired         BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMPTZ        -- NULL = sin expiración
);

CREATE INDEX IF NOT EXISTS idx_opus_active
    ON opus_insights(priority DESC, created_at DESC)
    WHERE expired = FALSE;


-- =============================================================================
-- TABLA: search_history
-- Historial de búsquedas Brave Search — deduplicación y rotación
-- =============================================================================

CREATE TABLE IF NOT EXISTS search_history (
    id          SERIAL PRIMARY KEY,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    query       TEXT NOT NULL,
    query_hash  TEXT UNIQUE NOT NULL,  -- SHA256 del query normalizado
    topic       TEXT NOT NULL,         -- topic de la rotación (ej: 'vwap_pullback')

    results_json    TEXT,              -- JSON raw de Brave Search
    ideas_generated TEXT,              -- hipótesis/ideas derivadas de la búsqueda
    used_in_cycles  INTEGER DEFAULT 0  -- cuántos ciclos usaron estas ideas
);

CREATE INDEX IF NOT EXISTS idx_search_topic
    ON search_history(topic, searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_hash
    ON search_history(query_hash);


-- =============================================================================
-- TABLA: external_research
-- Ideas de investigación externa con tracking de si fueron probadas
-- =============================================================================

CREATE TABLE IF NOT EXISTS external_research (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    topic           TEXT NOT NULL,
    source_url      TEXT,
    key_finding     TEXT NOT NULL,     -- el concepto/idea encontrado
    hypothesis      TEXT,              -- hipótesis concreta derivada del finding

    -- Tracking de si se probó en backtesting
    tested          BOOLEAN DEFAULT FALSE,
    test_batch_id   TEXT,              -- batch_id del test en coco_lab.db
    test_sharpe_oos REAL,
    test_trades_oos INTEGER,
    outcome         TEXT DEFAULT 'pending'
                        CHECK (outcome IN ('pending', 'testing', 'promising', 'dead_end'))
);

CREATE INDEX IF NOT EXISTS idx_research_topic
    ON external_research(topic, tested);
CREATE INDEX IF NOT EXISTS idx_research_untested
    ON external_research(tested, created_at DESC)
    WHERE tested = FALSE;


-- =============================================================================
-- TABLA: topic_rotation_state
-- Estado de la rotación de tópicos de Brave Search
-- =============================================================================

CREATE TABLE IF NOT EXISTS topic_rotation_state (
    topic           TEXT PRIMARY KEY,
    last_searched   TIMESTAMPTZ,
    search_count    INTEGER DEFAULT 0,
    ideas_generated INTEGER DEFAULT 0,
    ideas_tested    INTEGER DEFAULT 0,
    enabled         BOOLEAN DEFAULT TRUE
);

-- Insertar tópicos iniciales
INSERT INTO topic_rotation_state (topic, enabled) VALUES
    ('btc_breakout_strategy',        TRUE),
    ('vwap_pullback_crypto',         TRUE),
    ('adx_regime_filter',            TRUE),
    ('mean_reversion_bitcoin',       TRUE),
    ('bitcoin_momentum_backtest',    TRUE),
    ('crypto_market_microstructure', TRUE),
    ('btc_funding_rate_signal',      TRUE),
    ('bitcoin_onchain_indicators',   TRUE),
    ('crypto_options_sentiment',     TRUE),
    ('btc_volume_profile_strategy',  TRUE),
    ('bitcoin_halving_cycle',        TRUE),
    ('crypto_trend_following',       TRUE)
ON CONFLICT (topic) DO NOTHING;


-- =============================================================================
-- VISTA: active_learnings
-- Learnings activos ordenados por relevancia
-- =============================================================================

CREATE OR REPLACE VIEW active_learnings AS
SELECT
    id,
    category,
    content,
    confidence,
    session_id,
    cycle_num,
    created_at
FROM autolab_learnings
WHERE superseded = FALSE
ORDER BY
    CASE category
        WHEN 'dead_end'            THEN 1  -- Dead ends primero (más urgentes de recordar)
        WHEN 'parameter_insight'   THEN 2
        WHEN 'promising_direction' THEN 3
        WHEN 'strategy_ranking'    THEN 4
        WHEN 'external_research'   THEN 5
    END,
    confidence DESC,
    created_at DESC;


-- =============================================================================
-- VISTA: active_opus_insights
-- Insights de Opus no expirados, ordenados por prioridad
-- =============================================================================

CREATE OR REPLACE VIEW active_opus_insights AS
SELECT
    id,
    insight_type,
    priority,
    title,
    content,
    action_items,
    data_basis,
    created_at,
    applied_count
FROM opus_insights
WHERE expired = FALSE
  AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY priority DESC, created_at DESC;


-- =============================================================================
-- FUNCIÓN: next_search_topic()
-- Retorna el tópico que lleva más tiempo sin buscarse
-- =============================================================================

CREATE OR REPLACE FUNCTION next_search_topic()
RETURNS TEXT AS $$
    SELECT topic
    FROM topic_rotation_state
    WHERE enabled = TRUE
    ORDER BY last_searched ASC NULLS FIRST, search_count ASC
    LIMIT 1;
$$ LANGUAGE SQL;


-- =============================================================================
-- RLS (Row Level Security) — si usás Supabase con auth
-- Descommentear si querés restricciones de acceso por usuario
-- =============================================================================

-- ALTER TABLE autolab_learnings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE opus_insights ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "service_role_only" ON autolab_learnings
--     USING (auth.role() = 'service_role');


-- Confirmar creación
DO $$
BEGIN
    RAISE NOTICE 'AutoLab schema creado correctamente.';
    RAISE NOTICE 'Tablas: autolab_cycles, autolab_learnings, opus_insights, search_history, external_research, topic_rotation_state';
    RAISE NOTICE 'Vistas: active_learnings, active_opus_insights';
    RAISE NOTICE 'Funciones: next_search_topic()';
END $$;
