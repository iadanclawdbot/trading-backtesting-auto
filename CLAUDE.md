# trading-backtesting-auto
> Ecosistema autónomo del proyecto Coco Stonks Lab.
> Repo hermano de `trading-backtesting` (el laboratorio manual).
> Leer `TASK.md` al inicio de cada sesión — es el documento vivo de planificación.

---

## 🎯 QUÉ ES ESTE PROYECTO

Sistema de mejora continua autónoma de estrategias de trading BTC/USDT. Mientras el repo manual (`trading-backtesting`) se usa para experimentar a mano, este repo corre 24/7 en producción sin intervención humana.

**El ciclo autónomo cada 30 minutos:**
```
analizar resultados → hipotetizar experimentos → correr backtests → aprender → notificar Telegram
```

**Stack:**
- Backend: FastAPI (Python) + SQLite (backtesting) + PostgreSQL/Supabase (inteligencia)
- Orquestación: n8n (workflows) + Coolify (deploy en Oracle Cloud)
- LLMs: NVIDIA Build API gratuito (kimi-k2-instruct, 45 RPM)
- Notificaciones: Telegram (@dante_ia_bot)

---

## 📂 ARQUITECTURA DEL REPO

```
trading-backtesting-auto/
│
├── backend/                    ← API autónoma (FastAPI)
│   ├── src/                    ← Código Python principal
│   │   ├── autolab_api.py      ← Core: todos los endpoints del sistema
│   │   ├── autolab_fitness.py  ← Fitness function + parameter space (INMUTABLE)
│   │   ├── autolab_brain.py    ← LLM orchestrator (legacy)
│   │   └── autolab_loop.py     ← CLI loop (legacy)
│   │
│   ├── backtesting/            ← Motores de backtesting (copia de trading-backtesting/scripts/)
│   │   ├── config.py           ← Parámetros, reglas, costos
│   │   ├── motor_base.py       ← Todos los motores: breakout, vwap, MR, etc.
│   │   ├── pipeline_runner.py  ← Consume cola de experiments → guarda runs + trades
│   │   └── fase1_motor.py      ← cargar_velas() + guardar_en_db()
│   │
│   ├── deploy/
│   │   ├── Dockerfile          ← uvicorn src.autolab_api:app
│   │   ├── docker-compose.yml
│   │   └── .env.example
│   │
│   ├── database/               ← Schema PostgreSQL + topic_rotation.json
│   ├── n8n/                    ← Workflows exportados (main loop, daily research, chat)
│   ├── docs/                   ← arquitectura.md, changelog.md, setup
│   ├── skills/                 ← skill_opus_analyst.md
│   ├── data/                   ← gitignored — coco_lab.db (~863MB)
│   ├── CLAUDE.md               ← Instrucciones específicas del backend
│   ├── TASK.md                 ← Checklist del backend
│   └── requirements.txt        ← backtesting + API unificado
│
└── frontend/                   ← Dashboard (por construir)
    └── ...
```

---

## 🔄 FLUJO DE TRABAJO POR ROL

| Si vas a... | Carpeta | Skill a leer |
|-------------|---------|-------------|
| Modificar la API o el ciclo autónomo | `backend/` | `backend/CLAUDE.md` |
| Resolver por qué el sistema se estancó | `backend/` | `backend/skills/skill_opus_analyst.md` |
| Construir el dashboard | `frontend/` | `frontend/CLAUDE.md` (cuando exista) |
| Deploy o infra | `backend/deploy/` | `backend/docs/arquitectura.md` |

---

## 📋 PASO 0 — INICIO DE SESIÓN (SIEMPRE)

**Antes de tocar cualquier archivo:**

1. Leer `TASK.md` → identificar el ítem más urgente
2. Decidir en qué subcarpeta se trabaja hoy (`backend/` o `frontend/`)
3. Leer el `CLAUDE.md` de esa subcarpeta
4. Si el trabajo es en el backend → verificar que la API esté up:
   ```bash
   curl https://autolab-api.dantelujan.online/health
   ```

**Confirmá en voz alta antes de empezar:**
- "Hoy trabajo en: [backend / frontend]"
- "El ítem más urgente de TASK.md es: [ítem]"
- "La API está: [UP / DOWN]"

---

## 🚀 DEPLOY

Un solo repo, dos servicios independientes en Coolify:

| Servicio | Base Directory | Dockerfile |
|----------|---------------|------------|
| `autolab-api` | `backend/` | `deploy/Dockerfile` |
| `frontend` | `frontend/` | `deploy/Dockerfile` (cuando exista) |

**Deploy:** `git push origin main` → Coolify detecta cambios y redeploya el servicio correspondiente.

---

## 🔗 RELACIÓN CON trading-backtesting (el manual)

`backend/backtesting/` es una **copia** de `trading-backtesting/scripts/`. Si se mejora un motor en el manual y es relevante para AutoLab, sincronizar a mano.

No hay dependencia en runtime — son repos totalmente independientes.

---

## 📖 INFRA DEPLOYADA

| Servicio | URL |
|----------|-----|
| autolab-api | https://autolab-api.dantelujan.online |
| n8n | https://n8n.dantelujan.online |
| Supabase | https://supabase.dantelujan.online |
| Telegram | @dante_ia_bot |

**Repo GitHub:** `iadanclawdbot/trading-backtesting-auto`

---

## 📝 TASK.md — EL DOCUMENTO VIVO

`TASK.md` es el centro de planificación de este proyecto. Se actualiza en cada sesión:
- Al iniciar: revisar qué está pendiente
- Al completar un ítem: marcarlo como `[x]`
- Al descubrir algo nuevo: agregarlo en la sección correspondiente
- Al terminar la sesión: actualizar el estado del sistema

**Nunca empezar a trabajar sin haber leído TASK.md primero.**

---

*Creado el 2026-04-07 | AutoLab v4.2 | Benchmark: Sharpe OOS 1.166 (V5 Portfolio)*
