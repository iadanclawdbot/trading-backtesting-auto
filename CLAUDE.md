# trading-backtesting-auto
> Repo separado del manual. Contiene el backend autónomo y el frontend del dashboard.
> El proyecto manual vive en `trading-backtesting/` (repo hermano).

---

## 📂 ESTRUCTURA

```
trading-backtesting-auto/
├── backend/                ← AutoLab API (FastAPI + motores de backtesting)
│   ├── src/                ← autolab_api.py, fitness, brain, loop
│   ├── backtesting/        ← copia de los motores del proyecto manual
│   ├── deploy/             ← Dockerfile + docker-compose
│   ├── database/           ← schema PostgreSQL
│   ├── n8n/                ← workflows exportados
│   ├── docs/               ← arquitectura, changelog
│   ├── skills/             ← skill_opus_analyst.md
│   ├── CLAUDE.md           ← instrucciones específicas del backend
│   ├── TASK.md             ← checklist de sesión
│   └── requirements.txt
│
└── frontend/               ← Dashboard (por construir)
    └── ...
```

---

## 🚀 ARRANCAR UNA SESIÓN

1. Leer `backend/CLAUDE.md` si vas a trabajar en la API
2. Leer `frontend/CLAUDE.md` si vas a trabajar en el dashboard
3. Siempre revisar `backend/TASK.md` primero

---

## 🔗 DEPLOY

| Servicio | Repo | Base Directory | Dockerfile |
|----------|------|---------------|------------|
| autolab-api | `iadanclawdbot/trading-backtesting-auto` | `backend/` | `deploy/Dockerfile` |
| frontend | `iadanclawdbot/trading-backtesting-auto` | `frontend/` | `deploy/Dockerfile` |

Push a `main` → Coolify redeploya automáticamente cada servicio desde su subcarpeta.

---

*Separado el 2026-04-07*
