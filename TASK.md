# TASK.md — trading-backtesting-auto

> Documento vivo de planificación. Revisar y actualizar en cada sesión.
> Marcar `[x]` al completar. Agregar ítems nuevos cuando aparezcan.
> Última actualización: 2026-04-07

---

## 📊 ESTADO DEL SISTEMA

> Actualizar al inicio de cada sesión con lo que se observa en producción.

| Componente                           | Estado                                        | Verificado |
| ------------------------------------ | --------------------------------------------- | ---------- |
| autolab-api (`/health`)              | ✅ UP — sqlite y postgresql conectados        | 2026-04-07 |
| n8n Main Loop (30min)                | ⚪ No verificado                              | —          |
| n8n Daily Research (9am)             | ⚪ Cron puede estar en `*/3`                  | —          |
| n8n Chat Telegram                    | ⚪ No verificado                              | —          |
| Supabase CHECK constraint            | ❌ Migración SQL pendiente                    | 2026-04-07 |
| GitHub repo creado                   | ✅ `iadanclawdbot/trading-backtesting-auto`   | 2026-04-07 |
| Coolify apuntando a este repo        | ❌ Pendiente — acción manual requerida        | 2026-04-07 |
| Ciclo autónomo mejorando resultados  | ❌ Estancado ~1 semana                        | 2026-03-25 |

**Campeón actual** (al 2026-03-25):
`ema_crossover` | Capital: $308.91 (+23.6%) | Sharpe OOS: 1.432 | Trades: 15 ⚠️ (menos de 30, frágil)

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
- [ ] **Actualizar Coolify** — apuntar al nuevo repo

  - Repository → `iadanclawdbot/trading-backtesting-auto`
  - Base Directory → `backend/`
  - Dockerfile → `deploy/Dockerfile`
  - Env var: `SCRIPTS_PATH` → `/app/backtesting`
  - → Redeploy
- [ ] **Verificar que funciona**

  ```bash
  curl https://autolab-api.dantelujan.online/health
  # Esperado: {"status":"ok","sqlite":"connected","postgresql":"connected"}
  ```

---

## 🟡 PENDIENTE — Deuda técnica heredada

- [ ] **Migración SQL en Supabase** — CHECK constraint `outcome='testing'`

  ```sql
  ALTER TABLE external_research DROP CONSTRAINT IF EXISTS external_research_outcome_check;
  ALTER TABLE external_research ADD CONSTRAINT external_research_outcome_check
      CHECK (outcome IN ('pending', 'testing', 'promising', 'dead_end'));
  ```

  _Dónde: Supabase Studio → SQL Editor_
- [ ] **Cron Daily Research** — verificar que está en `0 9 * * *` y no en `*/3 * * * *`
  _Dónde: n8n UI → Workflow `WOJji6MHwdrsbTI1` → Cron node_
- [ ] **Verificar cron Docker en servidor** — Si Coolify reasignó UUID al container, el cron que conecta autolab-api a la red de Supabase puede estar roto

  ```bash
  ssh oracle-vps && crontab -l
  # Buscar: docker network connect pgo4kkk4sg80cg0wwkkg0css $(docker ps -q --filter 'name=...')
  ```

---

## 🟠 CORTO PLAZO — Resolver el estancamiento del ciclo autónomo

El sistema dejó de mejorar resultados. Diagnosticar antes de proponer soluciones.

- [ ] **Paso 1 — Diagnóstico con Opus** (`backend/skills/skill_opus_analyst.md`)

  ```bash
  curl https://autolab-api.dantelujan.online/context?top_n=50
  curl https://autolab-api.dantelujan.online/learnings
  ```

  Responder: ¿espacio paramétrico agotado? ¿deduplicación muy agresiva? ¿LLM sin diversidad?
- [ ] **Opción A — Ampliar PARAMETER_SPACE** en `backend/src/autolab_fitness.py`

  - Rangos más amplios o parámetros nuevos (`rsi_entry_filter`, `use_funding_filter`)
- [ ] **Opción B — Activar `mean_reversion`** en el pipeline

  - Motor existe en `backend/backtesting/motor_base.py`
  - Agregar a `ENABLED_STRATEGIES` en `autolab_fitness.py`
- [ ] **Opción C — Extender datos históricos a 2022-2023** (bear market)

  - Modifica `backend/backtesting/fase1_datos.py` para descargar años anteriores
- [ ] **Opción D — Separar fitness de exploración vs campeón**

  - El umbral 1.193 es muy alto para exploración — frenar la búsqueda

---

## 🔵 MEDIANO PLAZO — Frontend dashboard

- [ ] **Definir stack** — React + Vite (recomendado: solo usuarios logueados, sin SEO)
- [ ] **Páginas mínimas**
  - `/` → estado general (campeón, último ciclo, learnings recientes)
  - `/ciclos` → historial de ciclos (Sharpe OOS, capital, beat benchmark)
  - `/learnings` → tabla de learnings por categoría y confianza
  - `/experimentos` → cola actual + runs recientes
- [ ] **Conexión a API** — los endpoints ya están listos:
  - `GET /status` → campeón + benchmark
  - `GET /context` → top runs + learnings
  - `GET /learnings` → tabla de learnings
  - `GET /results/cycle?batch_id=X` → detalle de un ciclo
- [ ] **Deploy en Coolify** — Base Directory: `frontend/`

---

## 🟢 LIMPIEZA — Baja prioridad

- [ ] **Fix `/status`** — Sharpe 4.189 WR 100% es artifact de runs viejos (`breakeven_after_r=0`)

  - Filtrar: `WHERE total_trades >= 15 AND win_rate < 0.95`
  - Archivo: `backend/src/autolab_api.py`
- [ ] **Fix benchmark en `generar_batch_report.py`**

  - Línea ~30: hardcodeado a V2 (Sharpe 0.581) → cambiar a V5 (1.166)
  - Archivo: `backend/backtesting/generar_batch_report.py`
- [ ] **Re-exportar workflows n8n** — los JSON en `backend/n8n/` no reflejan la arquitectura v3
- [ ] **Autenticación en la API** — todos los endpoints son públicos

  - Agregar `X-API-Key` header con FastAPI `Security()`

---

## ✅ COMPLETADO

- [x] Separar AutoLab en repo independiente `trading-backtesting-auto` (2026-04-07)
- [x] Estructura limpia: `backend/src/`, `backend/backtesting/`, `frontend/`
- [x] Dockerfile con `uvicorn src.autolab_api:app` y `SCRIPTS_PATH=/app/backtesting`
- [x] CLAUDE.md con arquitectura completa del ecosistema
- [x] TASK.md como documento vivo de planificación
- [x] Repo `iadanclawdbot/trading-backtesting-auto` creado y pusheado en GitHub (2026-04-07)
- [x] Todos los archivos del repo actualizados para reflejar nueva estructura (2026-04-07)

---

## 🧠 NO REPETIR — Errores ya resueltos

| Error                       | Qué pasó                                           | Regla                                                   |
| --------------------------- | ---------------------------------------------------- | ------------------------------------------------------- |
| `breakeven_after_r=0`     | WR 100% artificial                                   | Nunca usar 0 en parámetros de ratio                    |
| n8n body bug                | Null bytes al inicio del body                        | Los endpoints LLM no reciben body — son self-contained |
| `signal_type` default     | Todos los runs guardados como "ema_crossover"        | Siempre pasar `signal_type` explícitamente           |
| Learnings no se guardaban   | CHECK constraint en Supabase fallaba silenciosamente | Verificar constraints antes de asumir que funciona      |
| Ciclo mostraba datos viejos | `/learn` leía todos los runs globales             | Siempre filtrar por `batch_id` del ciclo actual       |
