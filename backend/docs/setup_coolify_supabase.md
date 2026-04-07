# Setup Guide — Coolify + Supabase + n8n + AutoLab API

> Guía paso a paso para levantar todo el stack de la Fase 2.
> Tiempo estimado: 2-3 horas (primera vez)

---

## Prereqs

- Server con Coolify instalado y accesible
- Dominio o IP pública (para n8n HTTPS)
- API keys: NVIDIA Build, Brave Search

---

## Paso 1 — Instalar Supabase en Coolify

Supabase self-hosted incluye PostgreSQL + Auth + API + Studio (UI).

1. En Coolify: **New Resource → One-Click Apps → Supabase**
2. Configurar:
   - `POSTGRES_PASSWORD`: generar con `openssl rand -hex 32`
   - `JWT_SECRET`: generar con `openssl rand -hex 32`
   - Puerto: 8000 (interno), mapear al 8080 externo o similar
3. Deploy → esperar ~3 minutos
4. Abrir Supabase Studio: `http://TU_SERVER:8080`
5. En SQL Editor, pegar y ejecutar el contenido de `database/schema_postgresql.sql`
6. Copiar la DATABASE_URL desde Supabase Settings → Database

```
DATABASE_URL = postgresql://postgres:TU_PASSWORD@localhost:5432/postgres
```

> **Tip**: Si Supabase está en el mismo server que AutoLab, usar `localhost`.
> Si está en container separado, usar el nombre del servicio en la red de Docker.

---

## Paso 2 — Levantar AutoLab API + n8n

1. En tu repo, asegurarte de que estos archivos están presentes:
   ```
   actualizacion/autoevolucion/deploy/docker-compose.yml
   actualizacion/autoevolucion/deploy/Dockerfile.autolab-api
   actualizacion/autoevolucion/deploy/requirements.txt
   actualizacion/autoevolucion/scripts/*.py
   ```

2. En Coolify: **New Resource → Docker Compose**
   - Source: tu repositorio
   - Branch: main
   - Compose file path: `actualizacion/autoevolucion/deploy/docker-compose.yml`

3. Agregar variables de entorno (desde `.env.example`):
   - `NVIDIA_API_KEY`
   - `BRAVE_SEARCH_API_KEY`
   - `SUPABASE_DB_URL`
   - `N8N_BASIC_AUTH_PASSWORD`
   - `N8N_ENCRYPTION_KEY` (generar con `openssl rand -hex 32`)
   - `SQLITE_DATA_PATH` (path al directorio con coco_lab.db)
   - `BACKTESTING_CODE_PATH` (path al directorio scripts/)

4. Deploy

5. Verificar:
   ```bash
   curl http://TU_SERVER:8000/health
   # → {"status":"ok","sqlite":true,"postgresql":true,...}
   ```

---

## Paso 3 — Configurar n8n

1. Abrir n8n: `http://TU_SERVER:5678` (usuario/contraseña del .env)

2. Importar el workflow:
   - **Settings → Import** → subir `n8n/workflow_autolab.json`

3. Configurar credenciales en n8n:
   - **Credentials → New**: HTTP Bearer Auth
     - Name: `NVIDIA API`
     - Token: tu NVIDIA_API_KEY
   - **Credentials → New**: PostgreSQL
     - Host: (host de Supabase, ej: `localhost` o IP)
     - Port: 5432
     - Database: postgres
     - User: postgres
     - Password: tu POSTGRES_PASSWORD

4. En el workflow:
   - Nodo "Brave Search": asegurarse que usa el Brave API key
   - Nodo "Guardar External Research": seleccionar la credencial PostgreSQL creada
   - Nodo "NVIDIA — *": seleccionar credencial "NVIDIA API"

5. Variables de environment en n8n:
   - En la UI de n8n: **Settings → Variables → New**
   - `AUTOLAB_API_URL` = `http://autolab-api:8000` (nombre del container en Docker)
   - `BRAVE_SEARCH_API_KEY` = tu clave

6. Activar el workflow (toggle en la esquina superior derecha)

---

## Paso 4 — Copiar coco_lab.db al Server

El SQLite con todos los datos históricos de backtesting necesita estar accesible desde el container de AutoLab API.

```bash
# Desde tu Mac local, copiar la DB al server
scp /Users/mac/Documents/IA/Antigravity/trading-backtesting/data/coco_lab.db \
    usuario@TU_SERVER:/ruta/a/data/coco_lab.db
```

O si el repo está clonado en el server:
```bash
# En el server
cd /ruta/al/repo
python3 scripts/fase1_datos.py  # re-descargar datos si es necesario
```

---

## Paso 5 — Verificar el Sistema Completo

```bash
# 1. Health check de la API
curl http://TU_SERVER:8000/health

# 2. Estado de la cola
curl http://TU_SERVER:8000/status

# 3. Contexto (debería traer datos históricos)
curl "http://TU_SERVER:8000/context?top_n=5"

# 4. Test manual del workflow en n8n
# En n8n UI: abrir workflow → "Test workflow" (botón naranja)
# Verificar que cada nodo pase sin errores

# 5. Verificar PostgreSQL
curl http://TU_SERVER:8000/learnings
# → {"learnings": [], "count": 0}  (vacío al inicio — correcto)
```

---

## Paso 6 — Configurar Claude Code MCP (para Opus Analyst)

Para que Claude Code pueda acceder a la DB de PostgreSQL al ejecutar `/opus-analyst`:

1. En tu Mac, editar `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest", "--access-token", "TU_SUPABASE_ACCESS_TOKEN"]
    }
  }
}
```

2. O usar el MCP de PostgreSQL genérico:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://postgres:PASSWORD@TU_SERVER:5432/postgres"]
    }
  }
}
```

3. Reiniciar Claude Code y verificar que `postgres` aparece como MCP disponible.

---

## Troubleshooting

### autolab-api no puede conectar a SQLite
- Verificar que `SQLITE_DATA_PATH` apunta al directorio correcto en el host
- Verificar que el volume mount en docker-compose.yml es correcto
- `docker exec autolab-api ls /app/data/` — debe mostrar coco_lab.db

### n8n no puede llamar a autolab-api
- Verificar que ambos containers están en la misma red Docker (`autolab-net`)
- URL interna: `http://autolab-api:8000` (nombre del container, no localhost)
- `docker exec n8n curl http://autolab-api:8000/health`

### PostgreSQL connection error
- Verificar que SUPABASE_DB_URL tiene el formato correcto
- Si Supabase está en container separado, usar nombre del servicio o IP del container
- `docker exec autolab-api python3 -c "import psycopg2; psycopg2.connect('$SUPABASE_DB_URL')"`

### n8n workflow no activa el cron
- Verificar que el workflow está activo (toggle verde)
- Verificar timezone: `GENERIC_TIMEZONE=America/Argentina/Mendoza`
- Probar manualmente: "Test workflow" en la UI

---

## Checklist Final

- [ ] Supabase corriendo y schema creado (`schema_postgresql.sql`)
- [ ] AutoLab API respondiendo en `:8000/health` con sqlite=true y postgresql=true
- [ ] n8n respondiendo en `:5678`
- [ ] Workflow importado y activo
- [ ] Credenciales NVIDIA y PostgreSQL configuradas en n8n
- [ ] Variables de entorno configuradas en n8n (AUTOLAB_API_URL, BRAVE_SEARCH_API_KEY)
- [ ] coco_lab.db accesible desde el container de AutoLab API
- [ ] Test manual del workflow sin errores
- [ ] Claude Code MCP configurado (para /opus-analyst)

---

*Setup Guide v1.0 — 2026-03-24*
