# TASK.md — trading-backtesting-auto

> Documento vivo de planificación. Revisar y actualizar en cada sesión.
> Marcar `[x]` al completar. Agregar ítems nuevos cuando aparezcan.
> Última actualización: 2026-04-07

---

## 📊 ESTADO DEL SISTEMA

> Actualizar al inicio de cada sesión con lo que se observa en producción.

| Componente                           | Estado                                        | Verificado |
| ------------------------------------ | --------------------------------------------- | ---------- |
| autolab-api (`/health`)              | ✅ UP — sqlite y postgresql conectados        | 2026-04-08 |
| n8n Main Loop (30min)                | ⚪ No verificado                              | —          |
| n8n Daily Research (9am)             | ⚪ Cron puede estar en `*/3`                  | —          |
| n8n Chat Telegram                    | ⚪ No verificado                              | —          |
| Supabase CHECK constraint            | ❌ Migración SQL pendiente                    | 2026-04-07 |
| GitHub repo creado                   | ✅ `iadanclawdbot/trading-backtesting-auto`   | 2026-04-07 |
| Coolify apuntando a este repo        | ✅ Deployado — commit 948aca2                 | 2026-04-08 |
| Fixes estancamiento (3 RCAs)         | ✅ En producción desde deploy 2026-04-08      | 2026-04-08 |
| Ciclo autónomo mejorando resultados  | 🔄 En observación — fixes activos             | 2026-04-08 |

**Campeón actual** (al 2026-04-08):
`vwap_pullback` | Capital: $338.30 (+35.3%) | Sharpe OOS: 1.593 | Trades: 19

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
- [ ] **Deploy en Coolify** — `git push` hecho, falta redeploy en Coolify para activar los fixes
- [ ] **Verificar** — 24h después del deploy, revisar learnings para ver mean_reversion y params limpios

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

- [x] **Fix `/status` y `/context`** — Sharpe 4.189 WR 100% era artifact de `breakeven_after_r=0`

  - Filtro agregado: `AND win_rate < 95.0` en `/status` y `/context`
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
