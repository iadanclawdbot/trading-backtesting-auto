**eady for review**Select text to add comments on the plan

# Inventario Exhaustivo de Datos, Metricas y KPIs — AutoLab Dashboard

## Context

AutoLab es un sistema autonomo de mejora continua de estrategias BTC/USDT que corre 24/7. Cada 30 minutos ejecuta un ciclo completo: analisis -> hipotesis -> backtesting -> aprendizaje. Los datos viven en dos capas: **SQLite** (backtesting engine, ~863MB) y **PostgreSQL/Supabase** (inteligencia acumulada). Este inventario mapea cada dato extraible para construir un dashboard de monitoreo integral.

---

## 1. Rendimiento del Backtesting y Trading (Metricas de Negocio)

| Metrica                                   | Descripcion                                                                                    | Origen del Dato (Tabla/Script/Log)                                                        | Frecuencia de Actualizacion |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------- |
| **Win Rate (%)**                    | Porcentaje de trades ganadores vs totales                                                      | SQLite:`runs.win_rate`, `trades.resultado`                                            | Cada ciclo (30 min)         |
| **Sharpe Ratio OOS**                | Retorno ajustado por riesgo en datos out-of-sample (validacion 2025). Anualizado con sqrt(365) | SQLite:`runs.sharpe_ratio` WHERE `dataset='valid'`                                    | Cada ciclo                  |
| **Sharpe Ratio Train**              | Sharpe en datos in-sample (2024). Detecta overfitting si train >> valid                        | SQLite:`runs.sharpe_ratio` WHERE `dataset='train'`                                    | Cada ciclo                  |
| **Consistency Ratio**               | `min(sharpe_oos / sharpe_train, 1.0)` — mide sobreajuste                                    | Calculado:`autolab_fitness.py:compute_fitness()`                                        | Cada ciclo                  |
| **Max Drawdown (%)**                | Caida maxima desde pico de equity durante el backtest                                          | SQLite:`runs.max_drawdown`                                                              | Cada ciclo                  |
| **Capital Final (USDT)**            | Capital al cierre del backtest, partiendo de $250                                              | SQLite:`runs.capital_final`                                                             | Cada ciclo                  |
| **PnL Total (USDT)**                | Ganancia/perdida absoluta:`capital_final - 250`                                              | SQLite:`runs.pnl_total`                                                                 | Cada ciclo                  |
| **PnL (%)**                         | Ganancia/perdida porcentual                                                                    | SQLite:`runs.pnl_pct`                                                                   | Cada ciclo                  |
| **Profit Factor**                   | `abs(sum_wins / sum_losses)` — >1 es rentable                                               | SQLite:`runs.profit_factor`                                                             | Cada ciclo                  |
| **Total Trades**                    | Cantidad de operaciones ejecutadas en el backtest                                              | SQLite:`runs.total_trades`                                                              | Cada ciclo                  |
| **Trades Ganadores**                | Cantidad de trades con resultado WIN                                                           | SQLite:`runs.wins`                                                                      | Cada ciclo                  |
| **Trades Perdedores**               | Cantidad de trades con resultado LOSS                                                          | SQLite:`runs.losses`                                                                    | Cada ciclo                  |
| **Avg Win (USDT)**                  | Promedio de ganancia por trade ganador                                                         | SQLite:`trades` WHERE `resultado='WIN'` → avg(`pnl_neto`)                          | Cada ciclo                  |
| **Avg Loss (USDT)**                 | Promedio de perdida por trade perdedor                                                         | SQLite:`trades` WHERE `resultado='LOSS'` → avg(`pnl_neto`)                         | Cada ciclo                  |
| **R:R Ratio Promedio**              | Reward-to-risk ratio promedio realizado                                                        | SQLite:`trades.rr_ratio` → avg                                                         | Cada ciclo                  |
| **Duracion Promedio (bars)**        | Promedio de barras que un trade estuvo abierto                                                 | SQLite:`runs.avg_velas`                                                                 | Cada ciclo                  |
| **Stops Diarios Activados**         | Cantidad de veces que se activo el stop diario (-6%)                                           | SQLite:`runs.stops_diarios`                                                             | Cada ciclo                  |
| **Fitness Score**                   | Score compuesto: 70% Sharpe + trade bonus + consistency + DD                                   | Calculado:`autolab_fitness.py:compute_fitness()`                                        | Cada ciclo                  |
| **Beat Benchmark (bool)**           | Si el fitness supera al benchmark V5 (1.193)                                                   | Calculado:`autolab_fitness.py:beats_benchmark()`                                        | Cada ciclo                  |
| **Fitness Delta**                   | Diferencia vs benchmark:`fitness - 1.193`                                                    | Calculado:`autolab_fitness.py:fitness_delta()`                                          | Cada ciclo                  |
| **Champion Actual**                 | Estrategia con mayor `capital_final` historico                                               | SQLite:`champions` (ultima entrada)                                                     | Al detectar nuevo champion  |
| **Historial de Champions**          | Timeline de cambios de champion con fecha y metricas                                           | SQLite: tabla `champions` completa                                                      | Al detectar nuevo champion  |
| **Capital del Champion**            | Capital final del champion vigente                                                             | SQLite:`champions.capital_final`                                                        | Al detectar nuevo champion  |
| **Best Sharpe OOS del Ciclo**       | Mejor Sharpe OOS en el batch actual                                                            | PG:`autolab_cycles.best_sharpe_oos`                                                     | Cada ciclo                  |
| **Ciclos que Batieron Benchmark**   | Porcentaje de ciclos con `beat_benchmark = TRUE`                                             | PG:`autolab_cycles` WHERE `beat_benchmark = TRUE`                                     | Diario                      |
| **Equity Curve por Run**            | Serie temporal de equity bar-a-bar para reconstruir curva                                      | SQLite:`candle_states.equity` por `run_id`                                            | Cada ciclo                  |
| **Unrealized PnL por Bar**          | PnL no realizado en cada barra del backtest                                                    | SQLite:`candle_states.unrealized_pnl`                                                   | Cada ciclo                  |
| **Distribucion de Estrategias**     | % de runs por estrategia (breakout, vwap, MR)                                                  | SQLite:`runs` GROUP BY `strategy`                                                     | Diario                      |
| **Exposicion al Mercado**           | % del tiempo en posicion vs flat                                                               | SQLite:`candle_states.in_position` (count !=0 / total)                                  | Cada ciclo                  |
| **Senales Generadas vs Ejecutadas** | Ratio de senales que pasaron filtros vs totales                                                | SQLite:`candle_states` → `signal_passed` / (`signal_passed` + `signal_filtered`) | Cada ciclo                  |
| **Motivos de Filtrado**             | Breakdown de por que se filtraron senales                                                      | SQLite:`candle_states.filter_reason` GROUP BY                                           | Cada ciclo                  |
| **PnL por Dia de la Semana**        | Rendimiento desglosado por dia                                                                 | SQLite:`trades.entrada_fecha` + `pnl_neto` agrupado                                   | Semanal                     |
| **Direccion de Trades**             | Distribucion LONG vs SHORT                                                                     | SQLite:`trades.direction` GROUP BY                                                      | Cada ciclo                  |

---

## 2. Salud del Sistema y Velocidad (System Health)

| Metrica                                     | Descripcion                                            | Origen del Dato (Tabla/Script/Log)                                                  | Frecuencia de Actualizacion   |
| ------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------- | ----------------------------- |
| **API Health Status**                 | Estado general: ok / degraded                          | `GET /health` → `status`                                                       | Cada 30s (Docker healthcheck) |
| **SQLite Conectado**                  | Si el archivo coco_lab.db existe y es accesible        | `GET /health` → `sqlite` (boolean)                                             | Cada 30s                      |
| **PostgreSQL Conectado**              | Si la conexion a Supabase funciona                     | `GET /health` → `postgresql` (boolean)                                         | Cada 30s                      |
| **Tiempo de Ejecucion del Pipeline**  | Duracion total del pipeline en segundos                | `POST /run-pipeline` → `duration_seconds`                                      | Cada ciclo                    |
| **Tiempo por Experimento**            | `finished_at - started_at` por job individual        | SQLite:`experiments.finished_at` - `experiments.started_at`                     | Cada ciclo                    |
| **Jobs en Cola**                      | Cantidad de experimentos pendientes por estado         | `GET /status` → `queue` (dict por status)                                      | Cada ciclo                    |
| **Pipeline Timeout**                  | Si el pipeline excedio 600s (10 min)                   | `POST /run-pipeline` → HTTP 504                                                  | Cada ciclo                    |
| **Uptime del Container**              | Tiempo que lleva corriendo sin restart                 | Docker:`docker ps --format '{{.Status}}'`                                         | Cada minuto                   |
| **Docker Healthcheck Status**         | healthy / unhealthy / starting                         | Docker: healthcheck con `curl -f /health`                                         | Cada 30s                      |
| **Uso de Workers Uvicorn**            | Actualmente 1 worker (posible cuello de botella)       | `Dockerfile` CMD: `--workers 1`                                                 | Estatico                      |
| **LLM Model en Uso**                  | Modelo activo para analisis/hipotesis/chat             | Env vars:`LLM_MODEL`, `LLM_MODEL_ANALYSIS`                                      | Al cambiar config             |
| **LLM Tokens In/Out**                 | Tokens consumidos por llamada LLM                      | PG:`autolab_cycles.llm_tokens_in`, `llm_tokens_out`                             | Cada ciclo                    |
| **LLM Provider**                      | Provider activo (NVIDIA, etc.)                         | PG:`autolab_cycles.llm_provider`                                                  | Cada ciclo                    |
| **Null Byte Incidents**               | Requests con null bytes (bug n8n) que fueron limpiados | `StripNullByteMiddleware` en `autolab_api.py` (actualmente solo strip, sin log) | Cada request                  |
| **API Response Codes**                | Distribucion de 200/500/503/504                        | Logs de uvicorn stdout                                                              | Continuo                      |
| **Experimentos Exitosos vs Fallidos** | Ratio exito/fallo del pipeline                         | SQLite:`experiments.status` GROUP BY (`done` vs `failed`)                     | Cada ciclo                    |
| **Experimentos Sin Trades**           | Runs donde los parametros no generaron trades          | Pipeline stdout: counter `sin_trades`                                             | Cada ciclo                    |

---

## 3. Estado y Gestion de la Base de Datos

| Metrica                                   | Descripcion                                             | Origen del Dato (Tabla/Script/Log)                                | Frecuencia de Actualizacion               |
| ----------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------- |
| **Tamano SQLite (MB)**              | Tamano del archivo `coco_lab.db` (actualmente ~863MB) | `os.path.getsize(SQLITE_DB_PATH)`                               | Diario                                    |
| **Crecimiento Diario SQLite**       | Delta de tamano dia a dia                               | Historico de mediciones de tamano                                 | Diario                                    |
| **Total de Runs**                   | Cantidad total de registros en tabla `runs`           | SQLite:`SELECT COUNT(*) FROM runs`                              | Cada ciclo                                |
| **Total de Trades**                 | Cantidad total de registros en tabla `trades`         | SQLite:`SELECT COUNT(*) FROM trades`                            | Cada ciclo                                |
| **Total de Candle States**          | Registros bar-a-bar (tabla mas grande)                  | SQLite:`SELECT COUNT(*) FROM candle_states`                     | Diario                                    |
| **Total de Candles Historicos**     | Cantidad de velas BTC almacenadas                       | SQLite:`SELECT COUNT(*) FROM candles`                           | Estatico (solo cambia al ingestar nuevas) |
| **Rango de Datos Train**            | Periodo cubierto: 2024-01-01 a 2024-12-31               | SQLite:`candles` WHERE `dataset='train'` → min/max timestamp | Estatico                                  |
| **Rango de Datos Valid**            | Periodo cubierto: 2025-01-01 a 2026-03-20               | SQLite:`candles` WHERE `dataset='valid'` → min/max timestamp | Al ingestar nuevas velas                  |
| **Total Experiments**               | Registros en cola de experimentos                       | SQLite:`SELECT COUNT(*) FROM experiments`                       | Cada ciclo                                |
| **Experiments por Status**          | Breakdown: pending, running, done, failed               | SQLite:`experiments` GROUP BY `status`                        | Cada ciclo                                |
| **Total Batches**                   | Cantidad de batches ejecutados                          | SQLite:`SELECT COUNT(*) FROM batches`                           | Cada ciclo                                |
| **Total Champions Historicos**      | Cantidad de cambios de champion                         | SQLite:`SELECT COUNT(*) FROM champions`                         | Al detectar nuevo champion                |
| **Funding Rates Records**           | Registros de funding rate almacenados                   | SQLite:`SELECT COUNT(*) FROM funding_rates`                     | Al ingestar nuevos                        |
| **Total Learnings (PG)**            | Learnings acumulados en PostgreSQL                      | PG:`SELECT COUNT(*) FROM autolab_learnings`                     | Cada ciclo                                |
| **Learnings Activos vs Superseded** | Ratio de learnings vigentes vs reemplazados             | PG:`autolab_learnings` GROUP BY `superseded`                  | Diario                                    |
| **Total Opus Insights**             | Insights estrategicos acumulados                        | PG:`SELECT COUNT(*) FROM opus_insights`                         | Semanal                                   |
| **Opus Insights Activos**           | Insights no expirados                                   | PG: view `active_opus_insights` COUNT                           | Semanal                                   |
| **Total Search History**            | Busquedas Brave ejecutadas                              | PG:`SELECT COUNT(*) FROM search_history`                        | Diario                                    |
| **External Research Records**       | Ideas de investigacion externa                          | PG:`SELECT COUNT(*) FROM external_research`                     | Diario                                    |
| **PG Connection Status**            | Estado de la conexion PostgreSQL                        | `autolab_api.py:get_postgres()` → exito o HTTPException 503    | Cada request                              |
| **Conexiones PG Activas**           | Conexiones abiertas al pool de Supabase                 | `pg_stat_activity` en Supabase                                  | Cada 5 min                                |

---

## 4. Monitoreo de Automatizaciones y Flujos de Trabajo

| Metrica                                           | Descripcion                                                                                      | Origen del Dato (Tabla/Script/Log)                                         | Frecuencia de Actualizacion |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | --------------------------- |
| **Ciclos Completados (total)**              | Total de ciclos autonomos ejecutados                                                             | PG:`SELECT COUNT(*) FROM autolab_cycles WHERE phase='complete'`          | Cada ciclo                  |
| **Ciclos por Dia**                          | Throughput diario (esperado: ~48)                                                                | PG:`autolab_cycles` GROUP BY `DATE(started_at)`                        | Diario                      |
| **Ciclos Fallidos**                         | Ciclos que terminaron con error                                                                  | PG:`autolab_cycles` WHERE `error_msg IS NOT NULL`                      | Cada ciclo                  |
| **Fase de Fallo**                           | En que fase fallo el ciclo (analyze, hypothesize, run, learn)                                    | PG:`autolab_cycles.phase` WHERE `error_msg IS NOT NULL`                | Cada ciclo                  |
| **Duracion del Ciclo Completo**             | `finished_at - started_at` del ciclo end-to-end                                                | PG:`autolab_cycles.finished_at - started_at`                             | Cada ciclo                  |
| **Jobs Queued vs Completed**                | Eficiencia del pipeline: cuantos se encolaron vs terminaron                                      | PG:`autolab_cycles.jobs_queued` vs `jobs_completed`                    | Cada ciclo                  |
| **Experimentos Generados por Ciclo**        | Cuantas hipotesis genero el LLM                                                                  | `POST /hypothesize` → `total_generated`                               | Cada ciclo                  |
| **Duplicados Descartados**                  | Experimentos descartados por deduplicacion                                                       | `POST /hypothesize` → `skipped_duplicates`                            | Cada ciclo                  |
| **Out-of-Range Descartados**                | Experimentos con params fuera de rango valido                                                    | `POST /hypothesize` → `skipped_out_of_range`                          | Cada ciclo                  |
| **Ghost Params Stripped**                   | Parametros fantasma removidos del LLM output                                                     | Logs `[hypothesize]`: "Removed ghost params"                             | Cada ciclo                  |
| **Ideas Externas Usadas**                   | Ideas de external_research incorporadas al ciclo                                                 | `POST /hypothesize` → `external_ideas_used`                           | Cada ciclo                  |
| **Learnings Guardados por Ciclo**           | Nuevos learnings generados                                                                       | `POST /learn` → `saved`                                               | Cada ciclo                  |
| **Learnings Duplicados Descartados**        | Learnings identicos ya existentes                                                                | `POST /learn` → `skipped_duplicates`                                  | Cada ciclo                  |
| **External Research Evaluadas**             | Ideas externas evaluadas contra resultados                                                       | `POST /learn` → `external_evaluated`                                  | Cada ciclo                  |
| **Tasa de Conversion Research**             | % de ideas externas que resultan "promising"                                                     | PG:`external_research` WHERE `outcome='promising'` / total tested      | Semanal                     |
| **Topic Rotation Coverage**                 | Cuantos de los 12 topics se han buscado                                                          | PG:`topic_rotation_state.search_count` por topic                         | Diario                      |
| **Brave Search Queries Usadas**             | Queries ejecutadas vs budget mensual (2000)                                                      | PG:`SELECT COUNT(*) FROM search_history` este mes                        | Diario                      |
| **Ideas Generadas por Topic**               | Productividad de cada topic de investigacion                                                     | PG:`topic_rotation_state.ideas_generated`                                | Diario                      |
| **n8n Main Loop Status**                    | Si el workflow de 30 min esta activo                                                             | n8n API: workflow `RJgzeedKorHQOYRD` status                              | Cada 5 min                  |
| **n8n Daily Research Status**               | Si el workflow diario esta activo                                                                | n8n API: workflow `WOJji6MHwdrsbTI1` status                              | Cada hora                   |
| **n8n Telegram Chat Status**                | Si el bot de chat responde                                                                       | n8n API: workflow `hANSvWyqiH6KpYxi` status                              | Cada hora                   |
| **Docker Network Status**                   | Si el container esta en la red de Supabase                                                       | Cron `* * * * *`: `docker network connect` result                      | Cada minuto                 |
| **Telegram Mensajes Enviados**              | Notificaciones enviadas por ciclo                                                                | `POST /learn` y `/daily-research` → campo `telegram_msg`            | Cada ciclo                  |
| **New Champion Events**                     | Cuando se corona un nuevo champion                                                               | `POST /learn` → `new_champion` (no null)                              | Al ocurrir                  |
| **Distribucion de Learnings por Categoria** | Breakdown: parameter_insight, dead_end, promising_direction, strategy_ranking, external_research | PG:`autolab_learnings` GROUP BY `category`                             | Diario                      |
| **Confianza Promedio de Learnings**         | Media de `confidence` en learnings activos                                                     | PG:`autolab_learnings` WHERE `superseded=FALSE` → avg(`confidence`) | Diario                      |
| **Cron Schedule Drift**                     | Si los crons estan en la frecuencia correcta (30min, 9am)                                        | n8n UI / crontab del servidor                                              | Manual / Semanal            |
| **NVIDIA API Rate Usage**                   | Requests/minuto vs limite (45 RPM free tier)                                                     | Conteo de calls LLM por ventana de tiempo                                  | Cada ciclo                  |

---

## 5. Registro de Errores y Alertas (Logs)

| Metrica                                               | Descripcion                                                             | Origen del Dato (Tabla/Script/Log)                                                    | Frecuencia de Actualizacion |
| ----------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------- |
| **Errores de Pipeline (total)**                 | Jobs que fallaron durante ejecucion                                     | SQLite:`experiments` WHERE `status='failed'`                                      | Cada ciclo                  |
| **Error Messages de Pipeline**                  | Texto del error (truncado a 500 chars)                                  | SQLite:`experiments.error_msg`                                                      | Cada ciclo                  |
| **LLM Parse Failures**                          | Veces que el JSON del LLM no se pudo parsear                            | Logs `[analyze]`, `[hypothesize]`: regex fallback / raw_decode                    | Cada ciclo                  |
| **LLM Fallback Events**                         | Cuando el modelo primario falla y se usa fallback (nemotron -> kimi-k2) | Logs `[chat]`: "nemotron fallback to kimi-k2"                                       | Por request                 |
| **PostgreSQL Connection Failures**              | Intentos fallidos de conectar a Supabase                                | `autolab_api.py:get_postgres()` → exception / 503                                  | Cada request                |
| **SQLite File Missing**                         | El archivo coco_lab.db no se encontro                                   | `GET /health` → `sqlite: false`                                                  | Cada 30s                    |
| **Pipeline Timeouts**                           | Ejecuciones que excedieron 10 minutos                                   | `POST /run-pipeline` → HTTP 504 `TimeoutExpired`                                 | Cada ciclo                  |
| **HTTP 500 Errors**                             | Errores internos del servidor en cualquier endpoint                     | Logs uvicorn /`raise HTTPException(500)`                                            | Continuo                    |
| **HTTP 503 Errors**                             | PostgreSQL no disponible                                                | `get_postgres()` → 503 cuando `PG_DSN` no configurado                            | Continuo                    |
| **Estrategia Desconocida**                      | Pipeline recibio una estrategia no registrada                           | `motor_base.py:correr_experimento()` → `ValueError`                              | Cada ciclo                  |
| **Zero SL Distance**                            | Trades saltados por distancia de stop loss = 0                          | `motor_base.py`: silently skipped (no log actualmente)                              | Cada ciclo                  |
| **Capital Depletion**                           | Capital llego a 0 durante backtest                                      | `motor_base.py`: capital clamped to 0.0                                             | Cada ciclo                  |
| **Sanity Alerts: WR < 35%**                     | Win rate sospechosamente bajo                                           | `fase1_motor.py:verificar_sanity()` → print warning                                | Cada ciclo                  |
| **Sanity Alerts: WR > 70%**                     | Win rate sospechosamente alto (posible lookahead)                       | `fase1_motor.py:verificar_sanity()` → print warning                                | Cada ciclo                  |
| **Sanity Alerts: Trades < 30**                  | Muy pocos trades (filtros demasiado restrictivos)                       | `fase1_motor.py:verificar_sanity()` → print warning                                | Cada ciclo                  |
| **Sanity Alerts: Sharpe > 3.0**                 | Sharpe sospechosamente alto (posible overfitting)                       | `fase1_motor.py:verificar_sanity()` → print warning                                | Cada ciclo                  |
| **WR 100% Artifacts**                           | Runs con WR=100% (artefacto breakeven_after_r=0) — filtrados           | Filtro en `/status` y `/context`: `win_rate < 95.0`                             | Cada ciclo                  |
| **Ghost Params Detectados**                     | Params generados por LLM que no existen en el motor                     | Logs `[hypothesize]`: stripped params list                                          | Cada ciclo                  |
| **Duplicate Learnings**                         | Learnings que ya existian (mismo category+content)                      | `POST /learn` → `skipped_duplicates` count                                       | Cada ciclo                  |
| **External Research CHECK Constraint Failures** | INSERT fallido por constraint en outcome                                | PG: constraint `external_research_outcome_check` (PENDIENTE de migracion)           | Cada daily research         |
| **Docker Network Disconnect**                   | Container perdio conexion a la red de Supabase                          | Cron `* * * * *` → `docker network connect` exitoso (implica desconexion previa) | Cada minuto                 |
| **n8n Workflow Failures**                       | Ejecuciones fallidas de workflows n8n                                   | n8n execution history (no hay `errorWorkflow` configurado)                          | Cada ejecucion              |
| **Brave Search Rate Limit**                     | Queries que excedieron el limite de 2000/mes                            | `POST /daily-research` → HTTP error de Brave API                                   | Diario                      |
| **NVIDIA API Rate Limit**                       | Requests rechazados por exceder 45 RPM                                  | Logs: HTTP 429 de NVIDIA API                                                          | Cada ciclo                  |
| **Data Gaps in Candles**                        | Velas faltantes en el rango historico                                   | SQLite: gaps en `candles.timestamp` por symbol/timeframe                            | Semanal                     |
| **Empty DataFrame After Indicators**            | Todos los datos eliminados por dropna (params extremos)                 | `motor_base.py`: print warning + 0 trades                                           | Cada ciclo                  |

---

## Resumen de Origenes de Datos

| Origen                      | Tipo   | Metricas Principales                        |
| --------------------------- | ------ | ------------------------------------------- |
| SQLite:`runs`             | Tabla  | Sharpe, WR, PnL, DD, capital, profit_factor |
| SQLite:`trades`           | Tabla  | PnL por trade, R:R, duracion, direccion     |
| SQLite:`candle_states`    | Tabla  | Equity curve, senales, filtros, indicadores |
| SQLite:`experiments`      | Tabla  | Cola, status, timing, errores               |
| SQLite:`champions`        | Tabla  | Historial de champions                      |
| SQLite:`candles`          | Tabla  | Datos historicos BTC                        |
| SQLite:`funding_rates`    | Tabla  | Funding rates historicos                    |
| SQLite:`session_state`    | Tabla  | Estado del ultimo ciclo                     |
| PG:`autolab_cycles`       | Tabla  | Ciclos, fases, LLM tokens, beat_benchmark   |
| PG:`autolab_learnings`    | Tabla  | Insights acumulados, categorias, confianza  |
| PG:`opus_insights`        | Tabla  | Directivas estrategicas Opus                |
| PG:`external_research`    | Tabla  | Ideas externas, lifecycle, resultados       |
| PG:`search_history`       | Tabla  | Brave Search dedup, queries                 |
| PG:`topic_rotation_state` | Tabla  | Rotacion de topics, productividad           |
| `autolab_fitness.py`      | Script | Fitness score, benchmark, gates             |
| `autolab_api.py`          | Script | Todos los endpoints, health, status         |
| `pipeline_runner.py`      | Script | Timing, counters, batch processing          |
| `motor_base.py`           | Script | 8 motores, metricas, indicadores            |
| Docker healthcheck          | Infra  | Container health cada 30s                   |
| n8n executions              | Infra  | Workflow status, failures                   |
| Server crontab              | Infra  | Network reconnection                        |
| Logs uvicorn                | Infra  | HTTP errors, request logs                   |

---

## Implementacion Recomendada

Para construir el dashboard, los endpoints ya disponibles cubren ~60% de las metricas:

* `GET /health` — health del sistema
* `GET /status` — champion, cola, best OOS
* `GET /context` — top runs, learnings, opus insights
* `GET /learnings` — tabla completa de learnings
* `GET /opus-insights` — insights estrategicos
* `GET /results/cycle?batch_id=X` — detalle de un ciclo

**Endpoints nuevos necesarios:**

1. `GET /metrics/system` — tamano SQLite, contadores de tablas, PG status
2. `GET /metrics/cycles` — historial de ciclos con timing y success rate
3. `GET /metrics/research` — topic rotation, search budget, conversion rate
4. `GET /metrics/errors` — errores recientes, sanity alerts, LLM failures
5. `GET /metrics/champion-history` — timeline de champions
6. `GET /metrics/equity-curve?run_id=X` — candle_states para graficar equity
