# CHANGELOG — trading-backtesting-auto

> Historial de sesiones de trabajo. Actualizar antes de cada push y al cerrar cada sesión.
> Formato: fecha, qué se hizo, qué quedó pendiente, estado del sistema al cierre.

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

