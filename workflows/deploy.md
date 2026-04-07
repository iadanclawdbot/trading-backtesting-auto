# Workflow: Deploy en Coolify

**Objetivo:** Deployar cambios del backend o frontend en producción sin romper el ciclo autónomo.
**Cuándo usarlo:** Cada vez que se pushea código que debe llegar al servidor.

---

## Inputs requeridos
- Cambios commiteados y pusheados a `main`
- Acceso a Coolify UI: `https://coolify.dantelujan.online` (o desde el servidor)

## Pasos

### 1. Verificar que el código funciona localmente
```bash
cd backend/
docker build -f deploy/Dockerfile -t autolab-test .
docker run --env-file .env -p 8000:8000 autolab-test
curl http://localhost:8000/health
# Esperado: {"status":"ok","sqlite":"connected","postgresql":"connected"}
```
**Si falla aquí → no pushear. Resolver primero.**

### 2. Push a GitHub
```bash
git push origin main
```
Coolify detecta el push automáticamente y inicia el build.

### 3. Monitorear el build en Coolify
- Ir al servicio `autolab-api` en Coolify UI
- Ver logs del build en tiempo real
- Errores comunes:
  - `ModuleNotFoundError` → falta dependencia en `requirements.txt`
  - `Cannot connect to database` → verificar `SUPABASE_DB_URL` en env vars
  - Puerto ocupado → el container anterior no terminó

### 4. Verificar post-deploy
```bash
curl https://autolab-api.dantelujan.online/health
curl https://autolab-api.dantelujan.online/status
```

### 5. Verificar red Docker de Supabase
Coolify fuerza los containers a su propia red. Hay un cron en el servidor que reconecta el container a la red de Supabase cada minuto. Si el `/health` muestra `postgresql: disconnected`:
```bash
ssh oracle-vps
crontab -l  # verificar que el cron existe y el UUID del container es correcto
```

## Outputs esperados
- `/health` responde `{"status":"ok","sqlite":"connected","postgresql":"connected"}`
- El ciclo n8n sigue corriendo (verificar en n8n UI que el último workflow no falló)

## Edge cases
- **Build falla por timeout:** uvicorn tarda en arrancar — aumentar `start-period` en HEALTHCHECK
- **Container nuevo con UUID diferente:** actualizar el filtro del cron en el servidor
- **n8n perdió conexión a la API:** los workflows se recuperan solos en el próximo trigger

## Configuración actual en Coolify
- Repository: `iadanclawdbot/trading-backtesting-auto`
- Base Directory: `backend/`
- Dockerfile: `deploy/Dockerfile`
- Env vars clave: `SCRIPTS_PATH=/app/backtesting`, `SQLITE_DB_PATH=/app/data/coco_lab.db`
