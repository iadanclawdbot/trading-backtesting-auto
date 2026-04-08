# Notas del Backend Engineer para el Frontend

> Contexto que no sale de la documentacion pero que te va a ahorrar horas de debug.
> Escrito por el agente que mantiene autolab-api y conoce cada trampa del sistema.

---

## 1. Setup critico

**Variable de entorno obligatoria:**
```
VITE_API_URL=https://autolab-api.dantelujan.online
```
Sin esto, nada funciona. En Vercel: Settings > Environment Variables.

**CORS:** ya esta abierto (`allow_origins=["*"]`). No necesitas proxy ni middleware.

**Auth:** no hay. Todos los endpoints son publicos. No implementes auth en el frontend hasta que el backend lo tenga.

---

## 2. Endpoints que existen HOY vs los que faltan

**Listos para consumir (produccion):**
```
GET /health          -> { status, sqlite, postgresql }
GET /status          -> champion, queue, best_oos, benchmark
GET /context?top_n=N -> top N runs + learnings + opus_insights
GET /learnings       -> tabla completa de learnings
GET /opus-insights   -> insights estrategicos activos
GET /results/cycle?batch_id=X -> detalle de un ciclo
```

**NO existen todavia** (listados en el brief pero son endpoints nuevos por crear):
```
GET /metrics/system
GET /metrics/cycles
GET /metrics/errors
GET /metrics/champion-history
GET /metrics/equity-curve?run_id=X
GET /metrics/research
```

Si los necesitas, avisame y los creo en el backend. Mientras tanto, construi el MVP con los 6 endpoints que ya existen. No hagas fetch a endpoints que no existen — vas a tener 404s silenciosos.

---

## 3. Formato de respuesta — lo que realmente devuelven

**`GET /status`** devuelve algo como:
```json
{
  "champion": {
    "strategy": "vwap_pullback",
    "capital_final": 338.30,
    "sharpe_ratio": 1.593,
    "win_rate": 66.67,
    "total_trades": 19,
    "max_drawdown": -12.5,
    "params_json": "{...}"
  },
  "best_oos": {
    "strategy": "vwap_pullback",
    "sharpe_ratio": 1.678,
    "win_rate": 66.67,
    "capital_final": 338.30
  },
  "benchmark": {
    "fitness": 1.193,
    "label": "V5 Portfolio"
  },
  "queue": {
    "pending": 0,
    "running": 0,
    "done": 8145,
    "failed": 21
  }
}
```

**`GET /context?top_n=10`** devuelve:
```json
{
  "top_runs": [...],
  "learnings": [...],
  "opus_insights": [...]
}
```

**`GET /learnings`** devuelve un array de:
```json
{
  "category": "parameter_insight",
  "content": "...",
  "confidence": 0.85,
  "superseded": false,
  "created_at": "2026-04-07T..."
}
```

Los schemas no estan documentados formalmente. Si necesitas el schema exacto, hace `curl` a cada endpoint y usa la respuesta como tipo. La API no tiene OpenAPI docs expuestas (no hay `/docs`).

---

## 4. Trampas conocidas

### Datos que pueden ser null o ausentes
- `champion` en `/status` puede ser `null` si nunca hubo un champion
- `opus_insights` en `/context` puede ser array vacio
- `postgresql` en `/health` puede ser `false` temporalmente (1-2 min despues de un redeploy, el cron reconecta la red Docker)

### Filtros ya aplicados en el backend
- Runs con `win_rate >= 95%` ya estan filtrados de `/status` y `/context`. No vas a ver WR=100% — eso era un artefacto resuelto. No necesitas filtrar en el frontend.
- Ghost params ya se stripean en `/hypothesize`. Los params que ves en la DB son reales.

### El ciclo corre cada 30 minutos
- No hagas polling mas seguido que cada 30-60 segundos
- Los datos cambian en bloques (cuando termina un ciclo), no gradualmente
- Si `/health` devuelve `postgresql: false`, no es una emergencia — reintenta en 60s

### SQLite no es accesible directamente
- El archivo `coco_lab.db` esta dentro del container en el servidor
- Todo acceso a datos de backtesting es via la API
- No intentes conectarte a SQLite desde el frontend

---

## 5. Deploy en Vercel

- **Framework:** Vite (Vercel lo autodetecta)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build` (default)
- **Output Directory:** `dist` (default de Vite)
- **Environment Variable:** `VITE_API_URL=https://autolab-api.dantelujan.online`
- **Node version:** 20 (default)

No necesitas Dockerfile, nginx, ni nada custom. Vercel se encarga.

---

## 6. Estrategias del sistema (para labels/UI)

Hay 3 estrategias activas:
- `breakout` (a.k.a. V4) — breakout de estructura con filtros ADX/EMA
- `vwap_pullback` — pullback al VWAP con confirmacion de volumen
- `mean_reversion` — reversion a la media (recien habilitada, pocos datos aun)

El champion actual es `vwap_pullback`. En la UI, podes usar estos 3 como categorias fijas para filtros, colores, etc.

---

## 7. Que NO hacer

- No crees endpoints mock o fake data para desarrollar. Usa la API real — esta arriba 24/7.
- No agregues WebSockets, SSE, ni nada reactivo. Polling simple es suficiente.
- No implementes auth en el frontend. Cuando el backend tenga `X-API-Key`, lo agrego aca.
- No asumas que los endpoints `/metrics/*` existen. Solo usa los 6 listados arriba.
- No hardcodees la URL de la API. Usa `import.meta.env.VITE_API_URL`.

---

*Ultima actualizacion: 2026-04-08*
*Si necesitas un endpoint nuevo o un cambio en el formato de respuesta, coordinalo con el backend antes de implementar workarounds en el frontend.*
