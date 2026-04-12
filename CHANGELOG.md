# CHANGELOG — trading-backtesting-auto

> Historial de sesiones de trabajo. Actualizar antes de cada push y al cerrar cada sesión.
> Formato: fecha, qué se hizo, qué quedó pendiente, estado del sistema al cierre.

---

## 2026-04-12 — Fix estancamiento + Opus Analyst + 6 estrategias nuevas

### Contexto
El campeón `vwap_pullback` ($338.30) llevaba 15 días sin ser superado (desde 2026-03-28). Análisis reveló 0/20 ciclos beat benchmark, 49/50 resultados en `/context` eran vwap_pullback, ghost params en datos históricos, y 6 de 9 estrategias del motor completamente sin usar.

### Completado

**Diagnóstico profundo via API** (sin acceso directo a SQLite):
- `/context?top_n=50`: 49/50 resultados = vwap_pullback, 38 con capital_final idéntico ($338.3)
- `/metrics/cycles?limit=20`: 0/20 ciclos beat benchmark, todos "Explorar vwap_pullback con..."
- Ghost params (`polymarket_threshold`, `stagger_orders`, etc.) aún presentes en runs históricos
- `/analyze` excluía mean_reversion explícitamente del prompt

**4 fixes aplicados** (commit `0319b4e`):

| RCA | Problema | Fix |
|-----|----------|-----|
| 4 | `/analyze` decía "ÚNICAS estrategias: breakout, vwap_pullback" | Incluir mean_reversion + instrucción de exploración diversa |
| 5 | `/context` query sin diversificación → 98% vwap_pullback | UNION per-strategy (top N/4 por estrategia) |
| 6 | Ghost params en runs históricos contaminan LLM | Strip de params inválidos en output de `/context` y campeón en `/hypothesize` |
| 7 | Sin detección de estancamiento | Staleness counter + 3 niveles de presión de exploración (normal/<10/>=20 ciclos) |

**Opus Analyst — análisis estratégico profundo** (commit `d9b8b62`):

6 insights publicados en `opus_insights` con prioridad 3-5:

| # | Tipo | Prio | Insight |
|---|------|------|---------|
| 1 | dead_zone | 5 | vwap_pullback micro-optimización agotada — 12/12 top results idénticos |
| 2 | direction | 5 | ema_crossover es la oportunidad más grande — primer campeón, params inexplorados |
| 3 | hypothesis | 5 | Breakout con lookback alto (35-40) + stops amplios → Sharpe 1.3 |
| 4 | direction | 4 | 6 estrategias del motor no están habilitadas en el loop |
| 5 | hypothesis | 4 | mean_reversion genera muy pocos trades — relajar filtros RSI y Bollinger |
| 6 | warning | 3 | LEFT JOIN en /context duplica resultados |

**Estrategias habilitadas en /hypothesize** (commit `d9b8b62`):
- `ema_crossover` — timeframe 1h, fue el primer campeón ($309)
- `breakdown_short` — posiciones SHORT, cobertura bajista
- `retest` — entrada en pullback post-breakout, menor drawdown
- REQUIRED, VALID_RANGES, prompt y /context actualizados para 6 estrategias

**Análisis profundo de la DB** (17,561 runs):
- Endpoint `/metrics/analysis` con distribución por estrategia, overfitting check, sensibilidad de params
- Hallazgo: breakout tiene overfit masivo (train 1.42 → valid -0.26)
- Hallazgo: vwap_pullback tiene el menor overfit (gap 0.335)
- Hallazgo: win rate óptimo es 60-70%, NO más alto
- Hallazgo CRÍTICO: ema_crossover usaba ghost params — motor usa SL/TP fijo, no ATR

**Fixes adicionales:**
- LEFT JOIN duplicados en /context → subquery LIMIT 1
- Benchmark en generar_batch_report.py → actualizado a campeón actual
- ema_crossover upgradeado a ATR trailing (`correr_backtest_ema_trailing` + `calcular_indicadores_ema_atr`)
- Limpieza: 11 PNGs + .playwright-mcp/ eliminados, .gitignore actualizado
- Skill `/update` creada en `.claude/skills/update/SKILL.md`
- 17 Opus insights publicados (6 iniciales + 7 plan mensual + 4 análisis profundo)

### Pendiente al cierre
- [ ] Verificar redeploy exitoso en Coolify
- [ ] 24-48h después: confirmar diversidad en experiments nuevos
- [ ] Animaciones con Motion (frontend)
- [ ] Candlestick chart con lightweight-charts
- [ ] Re-exportar workflows n8n
- [ ] Autenticación en la API (X-API-Key)

### Estado del sistema al cierre
| Componente | Estado |
|------------|--------|
| AutoLab API | ✅ UP — pendiente redeploy con cambios de hoy |
| GitHub repo | ✅ main al día |
| Coolify | ⏳ Redeploy en proceso |
| Opus Insights | ✅ 17 insights publicados — plan mensual 4 semanas |
| Champion | `vwap_pullback` — $338.30 (+35.3%) — Sharpe 1.593 (15 días sin cambio) |
| Estrategias habilitadas | 6 (antes 3): +ema_crossover (ATR trailing v2), +breakdown_short, +retest |
| ema_crossover | ✅ Upgradeado a ATR trailing (antes SL/TP fijo) |
| Ciclo autónomo | 🔄 Pendiente redeploy — diversidad forzada + 6 estrategias + staleness detection |
| Runs totales | 17,561 runs / 8,812 experiments / 423k trades / DB 6.6 GB |

---

## 2026-04-07 — Sesión de migración y diagnóstico

### Contexto
Primera sesión en el repo independiente `trading-backtesting-auto`, separado del monorepo `trading-backtesting` el mismo día.

### Completado

**Setup inicial del repo:**
- Repo `iadanclawdbot/trading-backtesting-auto` creado y pusheado a GitHub
- Remote configurado con credenciales en `.git/config`
- Estructura verificada: `backend/src/`, `backend/backtesting/`, `workflows/`, `frontend/`

**Actualización de archivos post-migración** (commit `315d7a2`):
- `TASK.md` — estado del sistema actualizado, ítems completados marcados
- `backend/deploy/.env.example` — `SCRIPTS_PATH=/app/backtesting`, `BRAVE_API_KEY` (nombre correcto)
- `backend/docs/arquitectura.md` — estructura de repo nueva, `SCRIPTS_PATH` correcto, v4.2
- `workflows/add_strategy.md` — path `backend/backtesting/motor_base.py`
- `backend/src/autolab_api.py` — comentario deploy `uvicorn src.autolab_api:app`
- `backend/backtesting/pipeline_runner.py` — paths en comentario header

**Diagnóstico y fix del estancamiento del ciclo autónomo** (commit `7f687f4`):

Se identificaron 3 causas raíz con evidencia numérica:

| RCA | Descripción | Fix |
|-----|-------------|-----|
| 1 | 13/50 top results en `/context` tenían WR=100% (artefacto `breakeven_after_r=0`). LLM veía Sharpe 4.189 fantasma como referencia | Filtro `win_rate < 95.0` en `/status` y `/context` |
| 2 | LLM generaba params inexistentes en `motor_base.py` (`stagger_orders`, `funding_filter`, `polymarket_threshold`, etc.). Motor los ignoraba silenciosamente → learnings falsos, dedup rota | Strip de ghost params en `/hypothesize` antes de dedup y storage |
| 3 | `mean_reversion` estaba en `ENABLED_STRATEGIES` pero ausente en `REQUIRED`/prompt de `/hypothesize` → LLM nunca la generaba | Agregada a REQUIRED, VALID_RANGES y prompt |

**Memoria del sistema:**
- Archivos de memoria creados en `/Users/mac/.claude/projects/.../memory/`
- `project_context.md`, `project_stall_diagnosis.md`, `user_profile.md`

**Deploy en Coolify** (2026-04-08):
- Configuración manual: Repository → `iadanclawdbot/trading-backtesting-auto`, Base Directory → `backend/`, Dockerfile → `deploy/Dockerfile`
- Persistent Storage: `/app/data` montado en el container
- Redeploy exitoso — commit `948aca2` en producción
- Verificado: `/health` → `sqlite:true, postgresql:true` ✅
- Verificado: `/status` → `best_oos = vwap_pullback WR=66.67%` (sin contaminación WR=100%) ✅

### Pendiente al cierre
- [ ] Migración SQL en Supabase: CHECK constraint `outcome='testing'` en `external_research`
- [ ] Verificar cron Daily Research en n8n (`0 9 * * *`, no `*/3 * * * *`)
- [ ] Verificar cron Docker en servidor — UUID del container puede haber cambiado con nuevo deploy
- [ ] 24h post-deploy: verificar que learnings muestren `mean_reversion` y params limpios (sin ghost params)

### Estado del sistema al cierre
| Componente | Estado |
|---|---|
| `autolab-api /health` | ✅ UP — sqlite y postgresql conectados |
| GitHub repo | ✅ Pusheado, rama `main` al día |
| Coolify | ✅ Apuntando a `iadanclawdbot/trading-backtesting-auto` — commit `948aca2` |
| Champion | `vwap_pullback` — $338.30 (+35.3%) — Sharpe 1.593 — 19 trades |
| Ciclo autónomo | ✅ Fixes en producción — en observación 24h |

---


## 2026-04-08 — Build inicial del dashboard frontend

### Contexto
Se construyó el dashboard frontend de AutoLab desde cero en `frontend/`. La carpeta solo tenía 3 documentos de contexto (BACKEND_NOTES, brief, requisitos). Se ejecutó el plan ultra-detallado diseñado en plan mode.

### Completado
- Next.js 16.2.2 + React 19 + Tailwind CSS 4.1 + SWR + Recharts + Motion inicializado
- Capa de datos: tipos TS verificados contra API real, hooks SWR con polling 30-60s
- 14 componentes de dashboard conectados a los 5 endpoints disponibles
- Layout responsive: sidebar colapsable (desktop) + bottom tabs (mobile)
- Dark/light theme toggle persistente
- Tooltips (?) explicativos en lenguaje simple en cada métrica
- Gauge de fitness SVG, AutoresearchChart estilo Karpathy, RunsTable sortable
- `npm run build` exitoso sin errores, HTTP 200 en dev server

**Rediseño visual completo** (mismo día, segunda iteración):
- Nuevo design system: superficies con profundidad (#080a09 → #1e2321), `.panel/.pill/.dot/.num/.glow-*` utilities
- Todos los 14 componentes reescritos con nuevo sistema de color (text-0/1/2, surface-0/1/2/3)
- Error boundaries con retry en cada sección
- CSS `animate-in` con stagger delays (eliminada dependencia de Motion en page.tsx)
- Variables de categoría de learnings agregadas a globals.css
- Light theme completo verificado visualmente

### Pendiente al cierre (sesión mañana)
- Deploy en Vercel completado en sesión posterior

### Estado del sistema al cierre
| Componente | Estado |
|------------|--------|
| AutoLab API | ✅ UP (health: ok) |
| Dashboard frontend | ✅ Build exitoso, rediseño completo, dark+light, mobile+desktop |
| Deploy Vercel | ⏳ Pendiente push + configuración |

---

## 2026-04-08 — Endpoints /metrics/*, equity curve real, market context

### Contexto
Sesión continuación del build frontend. Dashboard ya deployado en Vercel y funcionando. Se corrigieron bugs visuales (gauge arc SVG, autoresearch chart sort), se agregaron 4 endpoints backend nuevos, y se expandió el dashboard con componentes de mayor profundidad.

### Completado

**Fixes de producción** (commit `6e4294f`):
- Gauge SVG arc: `large-arc-flag` siempre `0` (arco nunca supera 180°)
- Autoresearch chart: sort cronológico antes de calcular running best (API devuelve por Sharpe desc)

**Backend — 4 endpoints nuevos** (commit `6df095d`):
- `GET /metrics/equity-curve?run_id=X` — candle_states equity bar-by-bar (default: campeón)
- `GET /metrics/champion-history` — timeline de todos los campeones coronados
- `GET /metrics/cycles?limit=N` — ciclos autónomos desde PostgreSQL autolab_cycles
- `GET /metrics/system` — DB size, total runs/trades/experiments/candle_states
- Agregado `capital_final` al query de `/context` para el autoresearch chart

**Frontend — Componentes nuevos** (commit `9be4989`):
- **Equity curve real**: Recharts AreaChart con datos de `/metrics/equity-curve` (reemplaza placeholder SVG)
- **Autoresearch chart**: Y-axis cambiado de Sharpe OOS a Capital Final ($), referencia $250
- **Champion Timeline**: timeline visual con dots, pills de estrategia, métricas por campeón
- **Cycles Chart**: barras por ciclo autónomo, verde = beat benchmark, stats resumen
- **System Stats**: 4 mcards con métricas de infraestructura (experiments, runs, trades, DB size)
- **Market Context**: BTC/USD en tiempo real (CoinGecko), Fear & Greed Index (Alternative.me), polling 5 min

**Dashboard layout actualizado:**
- Equity + Donut + Market Context en row de 3 columnas
- Cycles Chart + Fitness Gauge + Learnings Bars en row de 3
- Champion Card + Champion Timeline side by side
- Queue + Best OOS + System Stats + Opus Insights en row de 4

### Pendiente al cierre
- [ ] Redeploy backend en Coolify para activar /metrics/* endpoints
- [ ] Animaciones con Motion (entrada staggered, números animados)
- [ ] Candlestick chart con lightweight-charts (requiere datos OHLCV)

### Estado del sistema al cierre
| Componente | Estado |
|------------|--------|
| AutoLab API | ✅ UP — pendiente redeploy para /metrics/* |
| Dashboard frontend (Vercel) | ✅ 18 componentes, 9 endpoints, 3 páginas, dark+light |
| GitHub repo | ✅ main al día — commit `9be4989` |
| Champion | `vwap_pullback` — $338.30 (+35.3%) — Sharpe 1.593 — 19 trades |
