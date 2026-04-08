# Agent Instructions — trading-backtesting-auto

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

---

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**

- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**

- This is your role. You're responsible for intelligent coordination
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to queue new experiments, read `workflows/run_experiment_cycle.md`, figure out the required inputs, then execute `backend/backtesting/pipeline_runner.py`

**Layer 3: Tools (The Execution)**

- Python scripts in `backend/src/` (AutoLab API) and `backend/backtesting/` (motores)
- API calls, backtests, database queries, Telegram notifications
- Credentials and API keys are stored in `.env` (never anywhere else)
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

---

## What This Project Does

AutoLab es un sistema de mejora continua autónoma de estrategias de trading BTC/USDT. Corre 24/7 en producción sin intervención humana. Cada 30 minutos ejecuta un ciclo:

```
POST /analyze → POST /hypothesize → POST /run-pipeline → POST /learn → Telegram
```

**Stack:**
- `backend/src/autolab_api.py` — FastAPI: cerebro del sistema, todos los endpoints
- `backend/backtesting/` — Motores de backtesting (breakout, VWAP, MR, etc.)
- PostgreSQL/Supabase — Capa de inteligencia (learnings, insights, research)
- SQLite (`coco_lab.db`) — Motor de backtesting (runs, trades, experiments, candles)
- n8n — Orquestación de workflows en producción
- Coolify — Deploy en Oracle Cloud ARM

**Repo:** `iadanclawdbot/trading-backtesting-auto`
**API en producción:** `https://autolab-api.dantelujan.online`

---

## File Structure

```
trading-backtesting-auto/
│
├── workflows/                  ← SOPs — leer antes de ejecutar cualquier tarea
│   ├── deploy.md               ← cómo hacer deploy en Coolify
│   ├── experiment_cycle.md     ← cómo correr un ciclo de experimentos
│   ├── diagnose_stall.md       ← qué hacer cuando el sistema se estanca
│   └── add_strategy.md        ← cómo agregar una nueva estrategia
│
├── backend/
│   ├── src/                    ← AutoLab API (los 4 archivos Python)
│   │   ├── autolab_api.py      ← Core: todos los endpoints
│   │   ├── autolab_fitness.py  ← Fitness function + parameter space (INMUTABLE)
│   │   ├── autolab_brain.py    ← LLM orchestrator (legacy)
│   │   └── autolab_loop.py     ← CLI loop (legacy)
│   │
│   ├── backtesting/            ← Motores de backtesting (tools de ejecución)
│   │   ├── config.py           ← Parámetros, reglas, costos
│   │   ├── motor_base.py       ← Todos los motores: breakout, vwap, MR, etc.
│   │   ├── pipeline_runner.py  ← Consume cola experiments → guarda runs + trades
│   │   └── fase1_motor.py      ← cargar_velas() + guardar_en_db()
│   │
│   ├── deploy/
│   │   ├── Dockerfile          ← CMD: uvicorn src.autolab_api:app
│   │   ├── docker-compose.yml  ← Base Directory: backend/
│   │   └── .env.example        ← Template de variables de entorno
│   │
│   ├── database/               ← Schema PostgreSQL + topic_rotation.json
│   ├── n8n/                    ← Workflows exportados (main loop, daily research, chat)
│   ├── docs/                   ← arquitectura.md, changelog.md — leer antes de tocar infra
│   └── skills/                 ← skill_opus_analyst.md — análisis estratégico profundo
│
├── frontend/                   ← Dashboard Next.js 16 (Vercel deploy)
│   ├── src/app/                ← Rutas: / /learnings /insights
│   ├── src/components/         ← layout/ + dashboard/ (18 componentes)
│   ├── src/hooks/use-api.ts    ← SWR hooks para 9 endpoints
│   ├── src/lib/                ← api.ts, constants.ts, formatters.ts
│   └── src/types/api.ts        ← Interfaces TS verificadas contra API real
│
├── .tmp/                       ← Archivos temporales. Regenerables, nunca commitear
├── .env                        ← API keys y credenciales (NUNCA en otro lugar)
├── CLAUDE.md                   ← Este archivo
└── TASK.md                     ← Checklist vivo — leer al inicio de cada sesión
```

**Core principle:** `TASK.md` es el documento vivo de planificación. Revisarlo y actualizarlo en cada sesión. Nunca empezar sin leerlo.

---

## How to Operate

**1. Leer TASK.md primero — siempre**

Antes de cualquier acción, leer `TASK.md` e identificar el ítem más urgente. Confirmar en voz alta:
- "El ítem más urgente es: [ítem]"
- "La API está: UP / DOWN" → `curl https://autolab-api.dantelujan.online/health`
- "Hoy trabajo en: backend / frontend / infra"

**2. Buscar el workflow correspondiente antes de ejecutar**

Antes de hacer cualquier tarea, revisar si existe un workflow en `workflows/` que la describa. Si existe, seguirlo. Si no existe y la tarea es recurrente, crearlo después de ejecutarla.

**3. Buscar tools existentes antes de crear nuevos**

Antes de escribir código, verificar si ya existe en `backend/src/` o `backend/backtesting/`. Solo crear scripts nuevos cuando no existe nada para esa tarea.

**4. Aprender y adaptar cuando algo falla**

Cuando ocurre un error:
- Leer el mensaje completo y el traceback
- Revisar `backend/docs/changelog.md` — puede que ya fue resuelto antes
- Corregir el script y verificar que funciona
- Actualizar el workflow con lo aprendido (rate limits, comportamientos inesperados, constraints)

**5. Mantener TASK.md actualizado**

Al completar un ítem: marcarlo `[x]`. Al descubrir algo nuevo: agregarlo. Al terminar la sesión: actualizar el estado del sistema en la tabla superior de TASK.md.

**6. Actualizar CHANGELOG.md antes de cada push y al cerrar sesión**

`CHANGELOG.md` está en la raíz del repo. Es el historial de sesiones de trabajo — diferente de `backend/docs/changelog.md` que documenta la evolución técnica del sistema AutoLab.

Formato de entrada en CHANGELOG.md:
```markdown
## YYYY-MM-DD — Título descriptivo de la sesión

### Contexto
[Por qué se abrió esta sesión, qué se quería resolver]

### Completado
[Lista de cambios con commit IDs cuando aplica]

### Pendiente al cierre
[Ítems que quedaron abiertos — deben reflejar TASK.md]

### Estado del sistema al cierre
[Tabla con estado de los componentes clave]
```

**Cuándo actualizar:**
- Antes de cada `git push` → agregar los cambios del push a la entrada activa
- Al cerrar la sesión → completar la entrada con "Pendiente al cierre" y "Estado del sistema"
- Si la sesión es larga → se puede tener una entrada abierta e ir completándola durante el día

---

## The Self-Improvement Loop

Cada falla es una oportunidad para hacer el sistema más robusto:

1. Identificar qué falló
2. Corregir el tool o el workflow
3. Verificar que funciona
4. Actualizar el workflow con el nuevo approach
5. Continuar con un sistema más confiable

Este loop es cómo el framework mejora con el tiempo. Los errores ya documentados están en la sección "NO REPETIR" de `TASK.md`.

---

## Contexto de la Migración (2026-04-07)

Este repo fue separado del monorepo `trading-backtesting` donde vivía en `actualizacion/autoevolucion/`.

**Cómo era antes:**
- Archivos Python en `actualizacion/autoevolucion/scripts/`
- Dockerfile con `context: ../../..` (dependía de la raíz del repo padre)
- Coolify deployaba desde `trading-backtesting`

**Cómo es ahora:**
- Archivos Python en `backend/src/`
- Motores en `backend/backtesting/` (antes `scripts/` del repo manual)
- Dockerfile limpio, `context: ..` desde `backend/`
- `SCRIPTS_PATH` en container = `/app/backtesting`
- CMD = `uvicorn src.autolab_api:app`

**Repo hermano:** `trading-backtesting` — laboratorio manual, backtesting conversacional, fuente original de los motores en `backend/backtesting/`.

---

## Deploy

Un solo repo, dos servicios:

| Servicio | Plataforma | Base Directory | Env clave |
|----------|-----------|---------------|-----------|
| `autolab-api` | Coolify (Oracle ARM) | `backend/` | `SCRIPTS_PATH=/app/backtesting` |
| `frontend` | Vercel | `frontend/` | `NEXT_PUBLIC_API_URL` |

`git push origin main` → Coolify redeploya el backend, Vercel redeploya el frontend.

---

## Bottom Line

Leés `TASK.md`, identificás el próximo ítem, buscás el workflow, ejecutás los tools, manejás errores, actualizás la documentación. Tu trabajo es orquestar — no hacer todo a mano.

Stay pragmatic. Stay reliable. Keep learning.
