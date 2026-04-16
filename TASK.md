# TASK.md — trading-backtesting-auto

> Documento vivo de planificación. Revisar y actualizar en cada sesión.
> Marcar `[x]` al completar. Agregar ítems nuevos cuando aparezcan.
> Última actualización: 2026-04-12

---

## 📊 ESTADO DEL SISTEMA

> Actualizar al inicio de cada sesión con lo que se observa en producción.

| Componente                           | Estado                                        | Verificado |
| ------------------------------------ | --------------------------------------------- | ---------- |
| autolab-api (`/health`)              | ✅ UP — sqlite y postgresql conectados        | 2026-04-12 |
| n8n Main Loop                        | ✅ cada 15min (hasta lunes), luego 30min      | 2026-04-12 |
| n8n Daily Research (9am)             | ✅ Cron `0 0 9 * * *` correcto                | 2026-04-08 |
| n8n Chat Telegram                    | ✅ activo                                      | 2026-04-12 |
| Supabase CHECK constraint            | ✅ Migración aplicada                         | 2026-04-08 |
| GitHub repo creado                   | ✅ `iadanclawdbot/trading-backtesting-auto`   | 2026-04-07 |
| Coolify                              | ✅ Deploy final — commit `20cbda5`            | 2026-04-12 |
| Frontend dashboard (Vercel)          | ✅ Coin selector global BTC/ETH/SOL, 0 contaminación | 2026-04-12 |
| Backend /metrics/* endpoints         | ✅ 6 endpoints + admin + auth X-API-Key       | 2026-04-12 |
| Fixes estancamiento (RCA-1 a RCA-7)  | ✅ 7 RCAs resueltos — 6 estrategias habilitadas | 2026-04-12 |
| Opus Insights                        | ✅ 17 insights publicados — plan mensual completo | 2026-04-12 |
| Multi-moneda                         | ✅ BTC + ETH + SOL — campeón independiente por coin | 2026-04-12 |
| API auth (X-API-Key)                 | ✅ 12 POST endpoints + 3 workflows n8n         | 2026-04-12 |
| n8n workflows exportados             | ✅ 3 workflows actualizados en backend/n8n/    | 2026-04-12 |
| Ciclo autónomo                       | 🔄 Multi-coin cada 15min — generando experiments | 2026-04-12 |

**Campeones actuales** (al 2026-04-12 ~20:00):
- **BTC**: `vwap_pullback` | $338.30 | Sharpe 1.593 | 19 trades
- **ETH**: `breakout` | **$360.04** | Sharpe 1.632 | 18 trades
- **SOL**: `vwap_pullback` | $344.14 | Sharpe **1.827** | 16 trades

**Stats:** 17,812 runs | 428,063 trades | DB 6.7 GB | 11 estrategias testeadas
**Velas:** BTC 4h/1h + ETH 4h/1h + SOL 4h/1h (~75K velas totales)

---

## 🔴 INMEDIATO — Setup inicial del repo

Hacer en orden. Bloquean todo lo demás.

- [x] **Crear repo en GitHub**

  ```
  github.com/iadanclawdbot → New repository → "trading-backtesting-auto"
  Vacío: sin README, sin .gitignore
  ```
- [x] **Conectar y pushear**

  ```bash
  cd /Users/mac/Documents/IA/Antigravity/trading-backtesting-auto
  git remote add origin https://github.com/iadanclawdbot/trading-backtesting-auto.git
  git push -u origin main
  ```
- [x] **Actualizar Coolify** — deployado commit `948aca2` ✅ 2026-04-08
- [x] **Verificar que funciona** — `/health` → sqlite:true, postgresql:true ✅ 2026-04-08

---

## 🟡 PENDIENTE — Deuda técnica heredada

- [x] **Migración SQL en Supabase** — CHECK constraint `outcome='testing'` aplicada ✅ 2026-04-08
- [x] **Cron Daily Research** — verificado `0 0 9 * * *` (9am diario) ✅ 2026-04-08
  _Dónde: n8n UI → Workflow `WOJji6MHwdrsbTI1` → Cron node_
- [x] **Verificar cron Docker en servidor** — container `owcwccs8c8oowk0k80848c4c-054332678510` matchea filtro ✅ 2026-04-08

---

## 🟠 CORTO PLAZO — Resolver el estancamiento del ciclo autónomo

**DIAGNÓSTICO COMPLETADO (2026-04-07)** — 3 causas raíz identificadas:

**RCA-1: Contexto contaminado ✅ RESUELTO**
- 13/50 top results tenían WR=100% (artefacto `breakeven_after_r=0` en ema_crossover y vwap)
- Fix: filtro `win_rate < 95.0` en `/status` (best_oos) y `/context` (top_n)

**RCA-2: Params fantasma silenciosos ✅ RESUELTO**
- LLM generaba `stagger_orders`, `funding_filter`, `polymarket_threshold`, etc. que no existen en el motor
- Motor los ignoraba → runs idénticos, learnings falsos sobre params fantasma
- Fix: strip de ghost params en `/hypothesize` antes de dedup → dedup ahora funciona sobre params reales

**RCA-3: mean_reversion excluida del pipeline ✅ RESUELTO**
- Estaba en `ENABLED_STRATEGIES` pero no en `REQUIRED`/prompt de `/hypothesize` → LLM nunca la generaba
- Fix: agregada a REQUIRED, VALID_RANGES y prompt de `/hypothesize`

- [x] Diagnóstico completado con evidencia numérica (2026-04-07)
- [x] Fix RCA-1: filtro win_rate en /status y /context (`autolab_api.py`)
- [x] Fix RCA-2: strip ghost params en /hypothesize (`autolab_api.py`)
- [x] Fix RCA-3: mean_reversion habilitada en /hypothesize (`autolab_api.py`)
- [x] **Deploy en Coolify** — commit `948aca2` en producción ✅ 2026-04-08
- [x] **Verificar** — mean_reversion en learnings, ghost params limpios, WR sin artefactos ✅ 2026-04-12
- [x] **Fix RCA-4 a RCA-7** — estancamiento del ciclo autónomo (commit `0319b4e`) ✅ 2026-04-12
  - RCA-4: /analyze excluía mean_reversion
  - RCA-5: /context saturado 49/50 vwap_pullback → UNION per-strategy
  - RCA-6: ghost params en runs históricos → strip en output
  - RCA-7: sin detección de estancamiento → staleness counter + presión exploración

---

## 🔵 MEDIANO PLAZO — Frontend dashboard

- [x] **Definir stack** — Next.js 16.2.2 + Tailwind 4.1 + Recharts + SWR ✅ 2026-04-08
- [x] **Páginas implementadas** ✅ 2026-04-08
  - `/` → Dashboard completo con 18 componentes
  - `/learnings` → Learnings por categoría + feed completo con filtros
  - `/insights` → Panel de insights estratégicos Opus
- [x] **Conexión a API** — 9 endpoints conectados con SWR polling (30-60s) ✅ 2026-04-08
  - `GET /health` → status dots (API, SQLite, PG)
  - `GET /status` → campeón + best OOS + cola + benchmark
  - `GET /context?top_n=N` → autoresearch chart (capital Y-axis) + runs table
  - `GET /learnings` → feed + barras por categoría
  - `GET /opus-insights` → panel de insights
  - `GET /metrics/equity-curve` → equity curve real del campeón (bar-by-bar)
  - `GET /metrics/champion-history` → timeline de evolución del campeón
  - `GET /metrics/cycles` → bar chart de ciclos autónomos
  - `GET /metrics/system` → métricas de infraestructura (DB size, runs, trades)
- [x] **Design system profesional** — dark/light toggle, IBM Plex fonts, layered surfaces, glow effects, pill badges ✅ 2026-04-08
- [x] **Responsive mobile-first** — sidebar desktop + bottom tabs mobile ✅ 2026-04-08
- [x] **Tooltips (?)** — 16 métricas explicadas en lenguaje simple ✅ 2026-04-08
- [x] **Deploy en Vercel** — Root Directory: `frontend/`, auto-deploy en push ✅ 2026-04-08
- [x] **Market context** — BTC price, 24h change, market cap, volumen, Fear & Greed Index ✅ 2026-04-08
- [x] **Backend /metrics/* endpoints** — equity-curve, champion-history, cycles, system ✅ 2026-04-08

**Pendiente frontend:**
- [x] Redeploy backend en Coolify para activar /metrics/* endpoints ✅ 2026-04-12
- [x] Animaciones con Motion — StaggerSection, StaggerGrid, AnimatedNumber ✅ 2026-04-12
- [x] Candlestick chart con lightweight-charts v5 — velas DB + trades campeón ✅ 2026-04-12
- [x] Quitar logo TradingView + rediseñar Opus Insights panel ✅ 2026-04-12
- [x] Eliminar página /learnings (redundante con Overview) ✅ 2026-04-12
- [x] Selector multi-moneda BTC/ETH/SOL en candlestick chart ✅ 2026-04-12
- [x] Badge de moneda en RunsTable ✅ 2026-04-12

---

## 🟠 CORTO PLAZO — Mejoras del motor y ciclo autónomo

- [x] Fix RCA-4 a RCA-7: estancamiento del ciclo (commit `0319b4e`) ✅ 2026-04-12
- [x] Habilitar 6 estrategias nuevas en /hypothesize (commit `d9b8b62`) ✅ 2026-04-12
- [x] Opus Analyst: 17 insights + plan mensual 4 semanas (commit `d9b8b62`) ✅ 2026-04-12
- [x] Fix ghost params de ema_crossover — usaba params que el motor ignora (commit `37bf1f7`) ✅ 2026-04-12
- [x] Endpoint /metrics/analysis para analytics profundo (commit `aaf081e`) ✅ 2026-04-12
- [x] Skill /update + limpieza artefactos testing (commit `62096ff`) ✅ 2026-04-12
- [x] **Fix LEFT JOIN duplicados en /context** — subquery LIMIT 1 para sharpe_train ✅ 2026-04-12
- [x] **Upgrade ema_crossover a ATR trailing** — nuevo motor `correr_backtest_ema_trailing` + `calcular_indicadores_ema_atr` ✅ 2026-04-12
- [x] **Fix benchmark en generar_batch_report.py** — actualizado a vwap_pullback campeón ✅ 2026-04-12
- [x] **Fix n8n Main Loop connections** — key `Cron 5min` → `Cron 15min`, workflow ejecutaba Cron y salía en 3ms ✅ 2026-04-14
- [x] **Verificar 24-48h post-fix n8n** — ciclo completamente funcional ✅ 2026-04-16
  - Genera 6-8 experiments por ciclo, ejecuta backtests en 23-30s
  - Guarda learnings en Supabase, envía reportes a Telegram
  - Sistema autónomo operativo 24/7 sin intervención humana
- [x] **Backtesting multi-moneda** — ETH + SOL habilitados (commit `2484f6d`) ✅ 2026-04-12
  - ACTIVE_SYMBOLS = [BTCUSDT, ETHUSDT, SOLUSDT]
  - Velas descargadas: ETH 4h (4,740) + 1h (19,441) + SOL 4h (4,861) + 1h (19,441)
  - API: symbol en ExperimentConfig, /hypothesize, /context, dedup
  - POST /admin/download-candles para descargar nuevas monedas
- [x] **Dashboard coin selector global** — BTC/ETH/SOL en Topbar + Header mobile (commit `418fa77`) ✅ 2026-04-12
  - CoinContext + CoinProvider + useCoin()
  - 5 hooks filtrados por coin: useStatus, useApiContext, useEquityCurve, useChampionHistory, useCandles
  - keepPreviousData:false en hooks per-coin para evitar contaminación
- [x] **Fix contaminación cross-coin** (commits `834b322`, `35ef71f`) ✅ 2026-04-12
  - 100 runs legacy con symbol='ETHUSDT' corregidos a BTCUSDT
  - SWR_COIN (keepPreviousData:false) vs SWR_GLOBAL (keepPreviousData:true)
  - AnimatedNumber: early return "—" para null
  - Testeado desktop+mobile: BTC→ETH→SOL→BTC — 0 contaminación
- [x] **Campeón por moneda** — `_maybe_crown_champion()` per-symbol (commit `a19cda6`) ✅ 2026-04-12
- [x] **Fix candles markers cross-coin** — `setMarkers([])` al cambiar coin (commit `2becca2`) ✅ 2026-04-12
- [x] **Fix candles champion trades** — `/metrics/candles` usa `_get_champion(symbol)` (commit `68ed09f`) ✅ 2026-04-12
- [x] **Distribución balanceada 3-3-3 en /hypothesize** — BTC/ETH/SOL en partes iguales (commit `d164cd3`) ✅ 2026-04-16
  - Prompt: "exactamente 9 experimentos, 3 en BTCUSDT, 3 en ETHUSDT, 3 en SOLUSDT"
  - Enforcement: post-LLM redistribuye si LLM ignora instrucción
  - Test: consistente 9 experiments encolados, balanceados por moneda

---

## 🟢 LIMPIEZA — Baja prioridad

- [x] **Fix `/status` y `/context`** — Sharpe 4.189 WR 100% era artifact de `breakeven_after_r=0`

  - Filtro agregado: `AND win_rate < 95.0` en `/status` y `/context`
  - Archivo: `backend/src/autolab_api.py`
- [x] **Fix benchmark en `generar_batch_report.py`** — actualizado a campeón actual ✅ 2026-04-12
- [x] **Re-exportar workflows n8n** — 3 workflows exportados desde API n8n ✅ 2026-04-12
- [x] **Autenticación en la API** — X-API-Key en 12 POST endpoints + 3 workflows n8n ✅ 2026-04-12

---

## ✅ COMPLETADO

- [x] Separar AutoLab en repo independiente `trading-backtesting-auto` (2026-04-07)
- [x] Estructura limpia: `backend/src/`, `backend/backtesting/`, `frontend/`
- [x] Dockerfile con `uvicorn src.autolab_api:app` y `SCRIPTS_PATH=/app/backtesting`
- [x] CLAUDE.md con arquitectura completa del ecosistema
- [x] TASK.md como documento vivo de planificación
- [x] Repo `iadanclawdbot/trading-backtesting-auto` creado y pusheado en GitHub (2026-04-07)
- [x] Todos los archivos del repo actualizados para reflejar nueva estructura (2026-04-07)
- [x] Fix estancamiento RCA-4 a RCA-7 (2026-04-12) — commit `0319b4e`
- [x] Opus Analyst: 17 insights + plan mensual + 6 estrategias (2026-04-12)
- [x] Fix ghost params ema_crossover + upgrade ATR trailing (2026-04-12)
- [x] Análisis profundo DB: sensibilidad params, overfitting, distribuciones (2026-04-12)
- [x] Motion animations + candlestick chart lightweight-charts (2026-04-12)
- [x] Eliminar /learnings, rediseñar Opus panel, quitar logo TV (2026-04-12)
- [x] Multi-moneda + coin selector + fix contaminación (2026-04-12) — commits `2484f6d`→`35ef71f`

---

## 🧠 NO REPETIR — Errores ya resueltos

| Error                       | Qué pasó                                           | Regla                                                   |
| --------------------------- | ---------------------------------------------------- | ------------------------------------------------------- |
| `breakeven_after_r=0`     | WR 100% artificial                                   | Nunca usar 0 en parámetros de ratio                    |
| n8n body bug                | Null bytes al inicio del body                        | Los endpoints LLM no reciben body — son self-contained |
| `signal_type` default     | Todos los runs guardados como "ema_crossover"        | Siempre pasar `signal_type` explícitamente           |
| Learnings no se guardaban   | CHECK constraint en Supabase fallaba silenciosamente | Verificar constraints antes de asumir que funciona      |
| Ciclo mostraba datos viejos | `/learn` leía todos los runs globales             | Siempre filtrar por `batch_id` del ciclo actual       |
| ema_crossover ghost params | Motor usa SL/TP fijo pero se generaban sl_atr_mult | Verificar qué params LEE el motor antes de agregarlos |
| LEFT JOIN duplicados        | JOIN con train crea filas duplicadas en /context  | Usar subquery LIMIT 1 para sharpe_train               |
