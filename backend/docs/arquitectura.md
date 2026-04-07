# Arquitectura — AutoLab Sistema Completo

> Documentación para developers. Describe todos los servicios, conexiones, archivos y decisiones de infraestructura del sistema AutoLab (Fase 2 del proyecto Coco Stonks Lab).

---

## Visión General

AutoLab es un sistema de mejora continua autónoma de estrategias de trading. Corre 24/7 en un servidor VPS y ejecuta un loop: analiza resultados históricos → hipotiza nuevas estrategias → las testea → aprende de los resultados.

```
┌─────────────────────────────────────────────────────────┐
│                     VPS Oracle (Ubuntu 20.04 ARM)        │
│                     IP: <SERVER_IP>                      │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │  autolab-api │   │     n8n      │   │  Supabase   │  │
│  │  :8000       │   │  :5678       │   │  (PostgreSQL│  │
│  │  FastAPI     │◄──│  Workflows   │   │  + Studio)  │  │
│  └──────┬───────┘   └──────────────┘   └──────┬──────┘  │
│         │                                      │         │
│         │ red: <SUPABASE_NETWORK_ID>           │         │
│         └──────────────────────────────────────┘         │
│                                                          │
│  Proxy: Traefik (gestionado por Coolify)                 │
│  Orquestador: Coolify (autogestión de containers)        │
└─────────────────────────────────────────────────────────┘
```

---

## Servicios

### 1. autolab-api
**Qué hace:** API REST self-contained que orquesta todo el ciclo de AutoLab. Cada endpoint LLM (`/analyze`, `/hypothesize`, `/learn`) es autónomo: lee contexto internamente, llama al LLM, y guarda resultados. n8n solo dispara POSTs vacíos.

| Campo | Valor |
|-------|-------|
| URL pública | `https://autolab-api.dantelujan.online` |
| Puerto interno | `8000` |
| Framework | FastAPI + uvicorn |
| Imagen | Build desde repo (`deploy/Dockerfile`) |
| Gestionado por | Coolify |
| Container name | `<COOLIFY_UUID>-XXXXXXXXXX` (varía en cada deploy) |

**Endpoints principales:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del sistema (sqlite, postgresql) |
| `GET` | `/status` | Queue status + benchmark actual |
| `GET` | `/context?top_n=N` | Top N resultados históricos + learnings + opus insights |
| `GET` | `/learnings` | Learnings acumulados desde PostgreSQL |
| `GET` | `/opus-insights` | Directivas del Director Senior |
| `GET` | `/results/cycle?batch_id=X` | Resultados de un ciclo específico |
| `POST` | `/analyze` | LLM analiza patrones (top 20 OOS + 30 learnings + benchmark dinámico) → guarda en session_state (sin body) |
| `POST` | `/hypothesize` | LLM genera experimentos → valida rangos → deduplica → encola en SQLite (sin body) |
| `POST` | `/run-pipeline` | Ejecuta pipeline_runner.py (body opcional) |
| `POST` | `/learn` | LLM extrae learnings → deduplica → guarda en PostgreSQL → evalúa ideas externas (sin body) |
| `POST` | `/daily-research` | Self-contained: Brave Search → LLM → guarda en external_research (sin body) |
| `POST` | `/experiments` | Encola experimentos manualmente (con body) |
| `POST` | `/learnings` | Guarda learnings manualmente (con body) |
| `POST` | `/opus-insights` | Guarda insights de Opus manualmente |
| `DELETE` | `/learnings/all` | Borra todos los learnings (admin) |
| `DELETE` | `/runs/contaminated` | Marca learnings como superseded (admin) |

**Middleware ASGI — StripNullByteMiddleware:**
n8n HTTP Request node (v2.13.2) inyecta un null byte (`\x00`) al inicio del body en requests POST. El middleware lo stripea antes de que FastAPI lo procese.

**Variables de entorno (configuradas en Coolify):**
```
NVIDIA_API_KEY=nvapi-...
SUPABASE_DB_URL=postgresql://postgres:PASSWORD@supabase-db-<SUPABASE_NETWORK_ID>:5432/postgres
SQLITE_DB_PATH=/app/data/coco_lab.db
SCRIPTS_PATH=/app/backtesting
LLM_MODEL=moonshotai/kimi-k2-instruct          # Modelo rápido para /hypothesize y /learn
LLM_MODEL_ANALYSIS=moonshotai/kimi-k2-instruct  # Modelo para /analyze (overridable a nemotron-120B)
```

---

### 2. n8n
**Qué hace:** Orquestador de workflows. Ejecuta los dos workflows de AutoLab en los horarios configurados.

| Campo | Valor |
|-------|-------|
| URL pública | `https://n8n.dantelujan.online` |
| Puerto interno | `5678` |
| Imagen | `n8nio/n8n:latest` (v2.13.2) |
| Gestionado por | Coolify (instalación separada) |
| API Key | generada en n8n UI → Settings → API → Create API Key |

**Workflows activos:**

| Nombre | ID | Trigger | Flujo simplificado |
|--------|----|---------|-------------------|
| AutoLab — Main Loop | `RJgzeedKorHQOYRD` | Cada 30min | Cron → POST /analyze → POST /hypothesize → POST /run-pipeline → POST /learn |
| AutoLab — Daily Research | `WOJji6MHwdrsbTI1` | 9am diario | Cron → POST /daily-research |
| AutoLab Chat — Telegram Interactivo | `hANSvWyqiH6KpYxi` | Telegram message | Telegram Trigger → POST /chat → Telegram Responder |

**Flujo Main Loop simplificado (v3):**
```
Cron 30min → POST /analyze → POST /hypothesize → POST /run-pipeline → POST /learn
     │              │                │                    │                  │
     │         Top 20 OOS        Lee análisis +       Ejecuta cola       Lee 20 OOS
     │         + 30 learnings    ideas externas       pipeline_runner    Llama LLM
     │         + benchmark din.  Valida rangos        Corre backtests    Dedup + guarda
     │         Llama LLM         Deduplica            Exporta dashboard  Evalúa ideas ext.
     │         Guarda en         Encola 5-8 exp.                         En PostgreSQL
     │         session_state     en SQLite
```

**Daily Research — flujo self-contained (v4.1):**
```
Cron 9am → POST /daily-research (sin body)
                  │
                  ├── Lee topic_rotation_state → selecciona topic menos buscado
                  ├── Mapea slug → query legible (12 temas configurados)
                  ├── Brave Search con query seleccionado
                  ├── Sanitiza resultados (anti-prompt-injection)
                  ├── LLM extrae 2-3 ideas
                  ├── Deduplica por source_url
                  ├── Guarda en external_research (PostgreSQL) con outcome='pending'
                  ├── Guarda en search_history (query, hash, topic, results, ideas)
                  └── Actualiza topic_rotation_state (last_searched, search_count, ideas_generated)
```

**Chat Interactivo — flujo (v4.0):**
```
Telegram message → POST /chat
                       │
                       ├── Carga contexto: campeón + top 5 capital + runs/estrategia + learnings + opus
                       ├── Llama LLM (nemotron-super-49b-v1, fallback: kimi-k2)
                       └── Responde en Telegram (plain text)
```

> Daily Research migró de 6 nodos n8n (Brave + NVIDIA + Supabase REST) a 2 nodos (Cron → POST) por el bug de n8n con HTTP body.

> **Nota:** n8n solo dispara requests vacíos (sin body). Todos los endpoints LLM son self-contained. Esto evita el bug de n8n que inyecta null bytes o envía body vacío.

**Credenciales configuradas en n8n:**
- `NVIDIA Build API` — httpBearerAuth → NVIDIA integrate API

---

### 3. Supabase (self-hosted)
**Qué hace:** Base de datos PostgreSQL donde se guardan los aprendizajes del sistema.

| Campo | Valor |
|-------|-------|
| URL pública (Studio + API) | `https://supabase.dantelujan.online` |
| Puerto interno PostgreSQL | `5432` |
| Container DB | `supabase-db-<SUPABASE_NETWORK_ID>` |
| Red Docker | `<SUPABASE_NETWORK_ID>` |
| Gestionado por | Coolify (one-click app) |

**Schema visual — ambas bases de datos:**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  SQLite — coco_lab.db  (backtesting)                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌──────────────┐     ┌──────────────────────────────────────────────────┐  ║
║  │   candles    │     │               experiments                        │  ║
║  │──────────────│     │──────────────────────────────────────────────────│  ║
║  │ id           │     │ id · strategy · params_json · dataset            │  ║
║  │ symbol       │     │ priority · notes · status · created_at          │  ║
║  │ timeframe    │     │ (status: pending → running → done/failed)        │  ║
║  │ dataset      │     └──────────────────┬───────────────────────────────┘  ║
║  │ open/high/   │                        │ 1                                ║
║  │ low/close/   │                        │                                  ║
║  │ volume       │                        ▼ N                                ║
║  │ open_time    │     ┌──────────────────────────────────────────────────┐  ║
║  └──────────────┘     │                  runs                            │  ║
║         ▲             │──────────────────────────────────────────────────│  ║
║         │ (read)      │ run_id · experiment_id (FK) · batch_id (FK)      │  ║
║         │             │ strategy · params_json · dataset · symbol        │  ║
║  ┌──────────────┐     │ sharpe_ratio · total_trades · win_rate           │  ║
║  │  batches     │     │ max_drawdown · capital_final · notes             │  ║
║  │──────────────│     └──────┬─────────────────────┬────────────────────┘  ║
║  │ batch_id(PK) │◄───────────┘ 1                   │ 1                     ║
║  │ created_at   │                                   │                       ║
║  │ strategy     │             ┌─────────────────────┘                       ║
║  │ total_runs   │             │ N                   │ N                     ║
║  └──────────────┘             ▼                     ▼                       ║
║                    ┌──────────────────┐  ┌──────────────────────────────┐  ║
║                    │     trades       │  │      candle_states           │  ║
║                    │────────────────  │  │──────────────────────────────│  ║
║                    │ run_id (FK)      │  │ run_id (FK)                  │  ║
║                    │ entry/exit price │  │ candle_time · signal         │  ║
║                    │ pnl · resultado  │  │ position · capital           │  ║
║                    │ velas_abierto    │  └──────────────────────────────┘  ║
║                    └──────────────────┘                                     ║
║                                                                              ║
║  ┌──────────────────────────────────┐  ┌───────────────────────────────┐   ║
║  │       session_state              │  │       funding_rates           │   ║
║  │──────────────────────────────────│  │───────────────────────────────│   ║
║  │ key (PK) · value(JSON/str)       │  │ open_time · funding_rate      │   ║
║  │ updated_at                       │  │ symbol                        │   ║
║  │ keys: last_analysis              │  └───────────────────────────────┘   ║
║  │        last_champion             │                                       ║
║  │        last_pipeline_batch       │  ┌───────────────────────────────┐   ║
║  └──────────────────────────────────┘  │       champions               │   ║
║                                        │───────────────────────────────│   ║
║                                        │ id · promoted_at · run_id     │   ║
║                                        │ strategy · params_json        │   ║
║                                        │ capital_final · pnl_pct       │   ║
║                                        │ sharpe_ratio · total_trades   │   ║
║                                        └───────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║  PostgreSQL — Supabase  (inteligencia / aprendizaje)                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌──────────────────────────────────┐  ┌───────────────────────────────┐   ║
║  │       autolab_learnings          │  │       opus_insights           │   ║
║  │──────────────────────────────────│  │───────────────────────────────│   ║
║  │ id (PK, SERIAL)                  │  │ id (PK, SERIAL)               │   ║
║  │ cycle_num · session_id           │  │ insight_type · priority (1-5) │   ║
║  │ category (CHECK):                │  │ title · content               │   ║
║  │   parameter_insight              │  │ action_items (JSONB)          │   ║
║  │   dead_end ← prioridad en view   │  │ expired · expires_at          │   ║
║  │   promising_direction            │  │ applied_count                 │   ║
║  │   strategy_ranking               │  └───────────────────────────────┘   ║
║  │   external_research              │                                       ║
║  │ content · confidence (0-1)       │  ┌───────────────────────────────┐   ║
║  │ superseded (BOOL)                │  │       autolab_cycles          │   ║
║  │ superseded_by (FK → self)  ◄─┐  │  │───────────────────────────────│   ║
║  └──────────────────────────────┘  │  │ id · cycle_num · session_id   │   ║
║           Vista: active_learnings  │  │ phase · llm_model · tokens    │   ║
║           (dead_ends primero)       │  │ jobs_queued · best_sharpe_oos │   ║
║                                    │  │ beat_benchmark (BOOL)         │   ║
║                                    │  └───────────────────────────────┘   ║
║  ┌──────────────────────────────────┐                                       ║
║  │       external_research          │  ┌───────────────────────────────┐   ║
║  │──────────────────────────────────│  │       search_history          │   ║
║  │ id (PK, SERIAL)                  │  │───────────────────────────────│   ║
║  │ topic · source_url               │  │ query · query_hash (UNIQUE)   │   ║
║  │ key_finding · hypothesis         │  │ topic · results_json          │   ║
║  │ outcome (CHECK):                 │  │ ideas_generated               │   ║
║  │   pending  → nueva               │  │ used_in_cycles                │   ║
║  │   testing  → en evaluación       │  └───────────────────────────────┘   ║
║  │   promising→ superó benchmark    │                                       ║
║  │   dead_end → descartada          │  ┌───────────────────────────────┐   ║
║  │ test_batch_id · test_sharpe_oos  │  │    topic_rotation_state       │   ║
║  │ test_trades_oos                  │  │───────────────────────────────│   ║
║  └──────────────────────────────────┘  │ topic (PK)                    │   ║
║                                        │ last_searched · search_count  │   ║
║                                        │ ideas_generated · enabled     │   ║
║                                        └───────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Tablas principales** (schema completo en `autoevolucion/database/schema_postgresql.sql`):
- `autolab_learnings` — aprendizajes del Main Loop (categorías: parameter_insight, dead_end, promising_direction, strategy_ranking, external_research)
- `external_research` — resultados del Daily Research (Brave Search), con ciclo de maduración
- `opus_insights` — análisis profundos del Opus Analyst
- `autolab_cycles` — log de cada ciclo (fases, tokens, fitness)
- `search_history` — tracking de búsquedas Brave
- `topic_rotation_state` — rotación de temas de búsqueda

---

## Redes Docker

| Red | Nombre | Qué conecta |
|-----|--------|-------------|
| `coolify` | `coolify` | Todos los containers → Traefik (proxy) |
| Supabase | `<SUPABASE_NETWORK_ID>` | Todos los servicios de Supabase entre sí |

**Problema conocido:** Coolify fuerza todos sus containers a la red `coolify` e ignora la sección `networks:` del docker-compose. Por eso autolab-api no entra automáticamente a la red de Supabase.

**Solución implementada:** Cron job en el servidor que reconecta autolab-api a la red de Supabase cada minuto:
```bash
# /var/spool/cron/crontabs/root
* * * * * docker network connect <SUPABASE_NETWORK_ID> $(docker ps -q --filter 'name=<COOLIFY_APP_UUID>') 2>/dev/null || true
```

---

## Persistencia de Datos

### SQLite (coco_lab.db)
- **Qué contiene:** Todos los resultados de backtesting (candles, runs, trades, experiments, session_state)
- **Tamaño:** ~863MB
- **Path en el container:** `/app/data/coco_lab.db`
- **Path en el servidor:** `/data/autolab/coco_lab.db`
- **Montado via:** Coolify Persistent Storage → Directory Mount (`/data/autolab` → `/app/data`)

### PostgreSQL (Supabase)
- **Qué contiene:** Aprendizajes, research externo, insights de Opus
- **Persiste en:** Volumen Docker gestionado por Coolify para Supabase

### session_state (SQLite)
- **Qué contiene:** Estado intermedio entre endpoints (ej: último análisis para que /hypothesize lo lea)
- **Tabla:** `session_state` (key TEXT, value TEXT JSON, updated_at)
- **Creada automáticamente** por autolab_api.py

---

## Estructura de Archivos del Repo

**Repo:** `iadanclawdbot/trading-backtesting-auto`

```
trading-backtesting-auto/
│
├── workflows/                  # SOPs — leer antes de ejecutar cualquier tarea
│   ├── deploy.md               # Cómo hacer deploy en Coolify
│   ├── experiment_cycle.md     # Cómo correr un ciclo de experimentos
│   ├── diagnose_stall.md       # Qué hacer cuando el sistema se estanca
│   └── add_strategy.md         # Cómo agregar una nueva estrategia
│
├── backend/
│   ├── src/                    # AutoLab API (FastAPI)
│   │   ├── autolab_api.py      # Core: todos los endpoints
│   │   ├── autolab_fitness.py  # Fitness function + PARAMETER_SPACE (INMUTABLE)
│   │   ├── autolab_brain.py    # LLM orchestrator (legacy)
│   │   └── autolab_loop.py     # CLI loop (legacy)
│   │
│   ├── backtesting/            # Motores de backtesting (tools de ejecución)
│   │   ├── config.py           # Parámetros, reglas, costos
│   │   ├── motor_base.py       # Todos los motores: breakout, vwap, MR, etc.
│   │   ├── pipeline_runner.py  # Consume cola experiments → guarda runs + trades
│   │   └── fase1_motor.py      # cargar_velas() + guardar_en_db()
│   │
│   ├── deploy/
│   │   ├── Dockerfile          # CMD: uvicorn src.autolab_api:app
│   │   ├── docker-compose.yml  # Base Directory: backend/
│   │   └── .env.example        # Template de variables de entorno
│   │
│   ├── database/               # Schema PostgreSQL + topic_rotation.json
│   ├── n8n/                    # Workflows exportados (main loop, daily research, chat)
│   ├── docs/                   # arquitectura.md, changelog.md
│   ├── skills/                 # skill_opus_analyst.md
│   └── requirements.txt        # Dependencias Python
│
├── frontend/                   # Dashboard (por construir)
│
├── .tmp/                       # Archivos temporales. Regenerables, nunca commitear
├── .env                        # API keys y credenciales (NUNCA en otro lugar)
├── CLAUDE.md                   # Instrucciones del agente + arquitectura WAT
└── TASK.md                     # Checklist vivo — leer al inicio de cada sesión
```

---

## Flujo de Datos — Main Loop (v2 simplificado)

```
[Cada 30 min — n8n Main Loop v3]

POST /analyze (sin body)
    ├── Lee top 20 resultados OOS + 30 learnings + opus insights
    ├── Benchmark dinámico: MAX(sharpe_ratio) de la DB
    ├── Llama LLM (kimi-k2 o nemotron-120B)
    ├── Parsea JSON con raw_decode (maneja {} en strings)
    └── Guarda análisis en session_state (SQLite)
    │
    ▼
POST /hypothesize (sin body)
    ├── Lee último análisis de session_state
    ├── Lee ideas externas: WHERE outcome IN ('pending', 'testing') LIMIT 3
    ├── Llama LLM → genera 5-8 experimentos
    ├── Valida parámetros (REQUIRED keys + rangos numéricos)
    ├── Deduplica: skip si params_json ya existe en experiments
    ├── Inserta en experiments (SQLite) con notes="external:ID_N" si viene de idea externa
    └── Marca ideas externas como outcome='testing'
    │
    ▼
POST /run-pipeline (sin body)
    ├── Ejecuta pipeline_runner.py --quiet --limit 10
    ├── pipeline_runner consume experiments pending
    ├── Corre backtests (breakout/vwap_pullback)
    ├── Guard: sl_distance <= 0 → skip (no ZeroDivisionError)
    ├── Log: DataFrame vacío → warning en log
    ├── Guarda resultados en runs (SQLite)
    ├── Exporta al dashboard automáticamente
    └── Guarda batch_id en session_state (para que /learn filtre por ciclo)
    │
    ▼
POST /learn (sin body)
    ├── Lee batch_id del ciclo actual desde session_state
    ├── Lee resultados OOS del ciclo actual (filtrado por batch_id)
    ├── Lee últimos 20 resultados OOS (para contexto LLM)
    ├── Benchmark dinámico: MAX(sharpe_ratio) de la DB
    ├── Llama LLM → extrae 3-5 learnings + cycle_summary (sugerencia próximo ciclo)
    ├── Valida categorías (CHECK constraint PostgreSQL)
    ├── Deduplica: skip si ya existe learning con mismo category+content
    ├── Guarda en autolab_learnings (PostgreSQL) — commit por fila
    ├── Evalúa ideas externas: busca runs con notes="external:ID_N"
    │      → outcome='promising' si Sharpe > benchmark × 0.8 y trades ≥ 15
    │      → outcome='dead_end' si Sharpe ≤ 0
    │      → actualiza test_sharpe_oos + test_trades_oos en external_research
    ├── Compara mejor run del ciclo vs campeón → corona si supera capital_final
    ├── Inserta fila en autolab_cycles (jobs_completed, best_sharpe_oos, beat_benchmark)
    └── Envía Telegram con detalle por run (WR, Sharpe, capital→final) + cycle_summary
```

```
[9am diario — n8n Daily Research]

POST /daily-research (self-contained)
    ├── Lee topic_rotation_state → topic con last_searched más antiguo (NULL first)
    ├── Mapea slug → query legible (12 topics: btc_breakout_strategy, vwap_pullback_crypto, etc.)
    ├── Brave Search con el query seleccionado
    ├── Sanitiza resultados (trunca campos, tags XML anti-injection)
    ├── LLM extrae 2-3 ideas
    ├── Deduplica por source_url
    ├── Guarda en external_research con outcome='pending'
    ├── Guarda en search_history (query, hash, topic, results_json, ideas)
    └── Actualiza topic_rotation_state (last_searched, search_count, ideas_generated)
```

**Ciclo de maduración de ideas externas:**
```
external_research.outcome:
  'pending'  → nueva, aún no vista por /hypothesize
  'testing'  → /hypothesize la usó como inspiración (experimentos en cola)
  'promising'→ experimentos corrieron, Sharpe > benchmark × 0.8
  'dead_end' → experimentos corrieron, Sharpe ≤ 0 o < benchmark × 0.8

/hypothesize lee 'pending' + 'testing'
/learn evalúa resultados y actualiza outcome + test_sharpe_oos + test_trades_oos
Las ideas 'promising' se mantienen visibles para nuevos ciclos
```

---

## Modelos LLM

| Variable env | Default | Alternativa | Uso |
|-------------|---------|-------------|-----|
| `LLM_MODEL` | `moonshotai/kimi-k2-instruct` | — | /hypothesize, /learn |
| `LLM_MODEL_ANALYSIS` | `moonshotai/kimi-k2-instruct` | `nvidia/nemotron-3-super-120b-a12b` (1M ctx) | /analyze |

189 modelos disponibles en NVIDIA Build API. Otros candidatos evaluados:
- `deepseek-ai/deepseek-v3.2` — buen razonamiento, JSON limpio
- `meta/llama-3.3-70b-instruct` — probado, funciona pero lento
- `minimaxai/minimax-m2.5` — usado inicialmente, JSON malformado frecuente
- `z-ai/glm5` — usado en Daily Research

---

## APIs Externas

| Servicio | Uso | Endpoint |
|----------|-----|----------|
| NVIDIA Build API | LLM para análisis, hipótesis, aprendizaje | `https://integrate.api.nvidia.com/v1/chat/completions` |
| Brave Search API | Investigación diaria de estrategias | `https://api.search.brave.com/res/v1/web/search` |

---

## Estrategias Válidas

Solo dos estrategias son soportadas por el pipeline:

| Estrategia | Motor | Timeframe | Parámetros clave |
|------------|-------|-----------|-----------------|
| `breakout` | `correr_backtest_breakout` | 4h | lookback, vol_ratio_min, atr_period, sl_atr_mult, trail_atr_mult, ema_trend_period, ema_trend_daily_period, adx_filter, breakeven_after_r |
| `vwap_pullback` | `correr_backtest_vwap` | 4h | sl_atr_mult, trail_atr_mult, adx_filter, vol_ratio_min, breakeven_after_r, ema_trend_period, ema_trend_daily_period |

> **Nota:** `breakeven_after_r=0` se trata como "desactivado". Valores válidos: 0 (off) o 0.5-1.5.

---

## Acceso SSH al Servidor

```bash
ssh -i /path/to/your/key.pem ubuntu@<SERVER_IP>
# Nota: usar 'ubuntu', no 'root'. Para Docker usar sudo.
```

---

## Comandos Útiles en el Servidor

```bash
# Ver containers corriendo
sudo docker ps

# Ver logs de autolab-api
sudo docker logs $(sudo docker ps -q --filter 'name=<COOLIFY_APP_UUID>') -f

# Verificar redes del container
sudo docker inspect $(sudo docker ps -q --filter 'name=<COOLIFY_APP_UUID>') --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'

# Reconectar manualmente a red Supabase
sudo docker network connect <SUPABASE_NETWORK_ID> $(sudo docker ps -q --filter 'name=<COOLIFY_APP_UUID>')

# Ver cron jobs
sudo crontab -l

# Copiar nuevo coco_lab.db al servidor (desde Mac)
scp -i /path/to/key.pem /path/to/coco_lab.db ubuntu@<SERVER_IP>:/data/autolab/coco_lab.db
```

---

## Health Check

```bash
curl https://autolab-api.dantelujan.online/health
# → {"status":"ok","sqlite":true,"postgresql":true,...}
```

Si `sqlite: false` → el archivo `/data/autolab/coco_lab.db` no existe en el servidor.
Si `postgresql: false` → el container no está en la red de Supabase (esperar 1 min al cron, o reconectar manualmente).

---

## Validación de Parámetros (v3)

`/hypothesize` rechaza experiments con params fuera de estos rangos:

| Param | breakout | vwap_pullback |
|-------|---------|--------------|
| `lookback` | 10-40 | — |
| `vol_ratio_min` | 0.8-3.0 | 0.8-3.0 |
| `atr_period` | 10-20 | — |
| `sl_atr_mult` | 0.75-4.0 | 0.75-4.0 |
| `trail_atr_mult` | 1.5-4.0 | 1.5-4.0 |
| `ema_trend_period` | 10-50 | 10-50 |
| `ema_trend_daily_period` | 15-60 | 15-60 |
| `adx_filter` | 0-35 | 0-35 |
| `breakeven_after_r` | 0-1.5 (0=off) | 0-1.5 (0=off) |

---

## Migración Supabase — CHECK constraint (v3)

Al actualizar a v3, ejecutar en Supabase SQL Editor:

```sql
ALTER TABLE external_research DROP CONSTRAINT IF EXISTS external_research_outcome_check;
ALTER TABLE external_research ADD CONSTRAINT external_research_outcome_check
    CHECK (outcome IN ('pending', 'testing', 'promising', 'dead_end'));
```

---

*Documentación v4.2 — Actualizada 2026-04-07 — Migración a repo independiente `trading-backtesting-auto`, estructura limpia `backend/src/` + `backend/backtesting/`*
