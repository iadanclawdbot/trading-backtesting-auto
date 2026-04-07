# Changelog — AutoLab: Historial de Evolución

> Registro cronológico de cambios importantes, bugs descubiertos, y aprendizajes de la implementación del sistema AutoLab. Cada entrada documenta qué se cambió, por qué, y qué se aprendió.

---

## 2026-03-25 — Día 1 de operación autónoma (continuación)

### v4.2 — Tables conectadas (champions, search_history, autolab_cycles, topic_rotation_state)

**Contexto:** Auditoría de tablas PostgreSQL/SQLite. Se detectó que 3 tablas del schema estaban vacías por falta de código que las populara, y que `topic_rotation_state` existía pero era ignorada.

**Bugs encontrados y fixeados:**

- **`champions` vacía (SQLite)**: La tabla se creó en v4.0, pero el campeón ema_crossover $308.91 fue generado ANTES. `_maybe_crown_champion` solo inserta cuando supera el record — nunca seedeó el estado inicial. Fix: `_get_champion()` ahora inserta automáticamente en `champions` cuando usa el fallback (tabla vacía).

- **`search_history` vacía (PostgreSQL)**: `/daily-research` guardaba ideas en `external_research` pero no registraba el historial de búsquedas. Fix: ahora inserta en `search_history` con query, hash SHA256, topic, resultados raw y ideas generadas. ON CONFLICT incrementa `used_in_cycles`.

- **`autolab_cycles` vacía (PostgreSQL)**: La tabla existía en el schema pero ningún endpoint escribía en ella. Fix: `/learn` inserta una fila al final de cada ciclo con `jobs_completed`, `best_sharpe_oos`, `beat_benchmark` y `cycle_summary`.

- **`topic_rotation_state` ignorada (PostgreSQL)**: Tenía 12 temas seed pero `/daily-research` usaba 4 queries hardcodeadas (rotación por hash del día). Fix: ahora lee el topic con `last_searched` más antiguo (NULL first), mapea slug → query legible, y después actualiza `last_searched`, `search_count` e `ideas_generated`.

**Aprendizaje:** Un schema bien diseñado no garantiza que el código lo use. Verificar que cada tabla tenga al menos 1 endpoint que escriba en ella desde el inicio.

---

### v4.1 — Telegram enriquecido + Fix ciclo stale

**Contexto:** Tercera sesión del día. El usuario reportó que los últimos 3 mensajes del ciclo 30min mostraban exactamente los mismos valores ($291.04 capital, 0.983 Sharpe). Investigación reveló que `/learn` leía los últimos 20 runs globales sin filtrar por ciclo.

**Bugs encontrados y fixeados:**

- **Telegram mostraba datos stale**: `/learn` usaba `SELECT ... ORDER BY created_at DESC LIMIT 20` sin filtrar por batch_id del ciclo actual. El max de esos 20 runs era siempre el mismo run viejo. Fix: `/run-pipeline` guarda `batch_id` en `session_state`; `/learn` lee ese batch y filtra resultados del ciclo.
- **`_save_session`/`_load_session` solo aceptaban dicts**: batch_id es string → `json.dumps("BATCH_...")` generaba un string JSON válido pero innecesario. Fix: detectar tipo y manejar strings directamente.
- **`cycle_results` no inicializado en except**: si SQLite fallaba, `cycle_results` no existía → crash en el bloque de telegram. Fix: inicializar en except.

**Nuevas features:**

1. **Telegram enriquecido** — Cada notificación de ciclo 30min incluye:
   - Lista numerada de cada run: estrategia, WR%, Sharpe, capital inicio→fin (+PnL%)
   - Mejor run resaltado
   - `cycle_summary` generado por LLM: 1 frase con sugerencia para el próximo ciclo
   - Batch ID para tracking
   - Cuando no hay runs nuevos, dice "Sin runs nuevos" en vez de mostrar datos viejos

2. **Diagrama excalidraw reconstruido** — 105 elementos en 5 columnas (n8n, API, SQLite, PostgreSQL, Telegram) con flechas correctamente conectadas.

**Aprendizaje:** Cuando un reporte dice "este ciclo" pero lee datos globales sin filtro temporal, el resultado parece un loop. Siempre filtrar reportes por el scope que dicen representar (batch_id, timestamp, etc).

---

### v4.0 — Sistema de Campeón + Telegram + Chat Interactivo

**Contexto:** Segunda sesión del día. El sistema ya corría con v3.0. Se agregó tracking del mejor resultado, alertas proactivas y chat interactivo vía Telegram.

**Nuevas features:**

1. **Sistema de Campeón** — Tabla `champions` en SQLite. `_get_champion()` busca primero en la tabla, con fallback a `MAX(capital_final)` de `runs`. `_maybe_crown_champion()` se llama al final de `/learn`: si el mejor run del batch supera el capital_final del campeón actual, inserta nuevo registro. `/analyze` y `/hypothesize` reciben el campeón como contexto y generan variaciones + competidores.

2. **Notificaciones Telegram** — Bot `@dante_ia_bot` (token via Coolify env var). 3 tipos:
   - **Ciclo 30min** (`/learn`): estrategias testeadas, mejor capital del ciclo, learnings nuevos, campeón vigente
   - **Nuevo campeón** (`/learn`): mensaje especial cuando se supera el capital_final máximo
   - **Daily Research** (`/daily-research`): query ejecutado + ideas nuevas generadas

3. **`POST /chat`** — Endpoint de chat interactivo. Carga contexto completo (campeón, top 5 capital, runs por estrategia, learnings, opus insights) y llama a `nvidia/nemotron-super-49b-v1` (fallback: kimi-k2). Responde en el mismo idioma de la pregunta. Retorna `telegram_msg` listo para n8n.

4. **n8n workflow "AutoLab Chat — Telegram Interactivo"** (ID: `hANSvWyqiH6KpYxi`) — Telegram Trigger → POST /chat → Telegram Responder. Activado y operativo.

5. **Credencial Telegram en n8n** — `Telegram Autoevolucion-API-AI` (ID: `Xj52PYgRoPbfUJC7`) configurada via n8n API. Usada tanto en el Chat workflow como en los nodos de notificación del Main Loop.

**Bugs encontrados y fixeados:**

- **`last_cycle_batch=None` explícito**: `get_context()` usa `Query()` como default de FastAPI. Al llamarla directamente sin ese param, SQLite recibía un objeto `Query(None)` → "type 'Query' is not supported". Fix: pasar `last_cycle_batch=None` explícitamente.
- **URL interna Docker**: El workflow de chat usaba `http://autolab-api:8000` — Coolify no resuelve hostnames internos. Fix: cambiar a `https://autolab-api.dantelujan.online/chat`.
- **Telegram parse_mode**: El LLM responde con markdown (`**bold**`) que Telegram no puede parsear si está malformado → "can't parse entities". Fix: deshabilitar parse_mode en el nodo Telegram Responder (texto plano).
- **`conn.close()` duplicado**: Al agregar `_get_champion()` en `/status`, había doble `conn.close()`.

**Aprendizaje:** El flujo Telegram → n8n → API → LLM → Telegram requiere: (1) URL pública no hostname interno, (2) body como keypair no JSON.stringify, (3) Telegram en plain text o con markdown bien formado, (4) timeout generoso (90s) para LLMs lentos.

---

## 2026-03-25 — Día 1 de operación autónoma

### v3.0 — Auditoría completa del sistema (8 fixes)
**Contexto:** Auditoría de calidad completa del sistema AutoLab después de 1 día de operación. Se encontraron 8 problemas que afectaban la convergencia del sistema.

**Fixes implementados:**

1. **P1: Deduplicación de experiments** — `/hypothesize` ahora verifica si `params_json` (normalizado con `sort_keys=True`) ya existe en la tabla `experiments` antes de insertar. Evita desperdiciar cómputo re-testeando params idénticos.

2. **P2: Validación de rangos** — Se agregó diccionario `VALID_RANGES` con límites por param y estrategia. Params fuera de rango se rechazan silenciosamente con log.

3. **P3: Guard division-by-zero en breakout** — `motor_base.py` línea 898: `if sl_distance <= 0: continue`. Otros motores ya tenían este guard, breakout no.

4. **P4: Benchmark dinámico** — `/analyze` y `/learn` ahora leen `MAX(sharpe_ratio)` de la DB en vez del hardcoded "1.166". El sistema sabe si mejoró.

5. **P5: Contexto ampliado** — `/analyze` pasa de top 5 → top 20 resultados, y de 10 → 30 learnings. El LLM tiene más datos para encontrar patrones.

6. **P6: Dedup de learnings** — `/learn` verifica si ya existe un learning con misma categoría y contenido exacto antes de insertar.

7. **P7: Log de DataFrame vacío** — `pipeline_runner.py` ahora loguea cuando un DataFrame queda vacío después de calcular indicadores (antes era silent skip).

8. **P8: Ciclo de maduración de ideas externas** — Las ideas de Daily Research ahora pasan por: `pending → testing → promising/dead_end`. `/hypothesize` lee ideas pending + testing. `/learn` evalúa resultados y actualiza `external_research` con feedback real (test_sharpe_oos, test_trades_oos).

**Aprendizaje:** Un sistema autónomo necesita: (1) no repetir trabajo, (2) recordar sus errores, (3) saber cuándo mejoró, (4) dar tiempo a las ideas nuevas para madurar. Sin estos 4 pilares, el loop degenera en exploración aleatoria.

---

### v2.1 — Fix breakeven_after_r=0 (WR=100% artifact)
**Problema:** Runs de breakout mostraban WR=100%, DD=-0.01% con 30-62 trades — estadísticamente imposible en BTC real.

**Root cause:** En `motor_base.py`, `buscar_salida_trailing()` evaluaba:
```python
if unrealized >= breakeven_after_r * initial_risk  # 0 * risk = 0
```
Con `breakeven_after_r=0`, el SL se movía a breakeven (+0.3% comisiones) en la primera vela con cualquier uptick. Los trades nunca podían perder.

**Fix:** `breakeven_after_r=0` ahora se trata como "desactivado" (igual que None). Rango válido: 0.5-1.5.

**Aprendizaje:** Parámetros con valor 0 que significan "no aplicar" son peligrosos cuando se multiplican (0 × algo = siempre true). Mejor usar None/null para "desactivado" o validar explícitamente.

---

### v2.0 — Endpoints LLM self-contained (fix definitivo n8n)
**Problema:** n8n HTTP Request node (v2.13.2) tiene un bug: al enviar body JSON via POST, o envía body vacío (Content-Length:0) o lo prepende con null byte `\x00`. Probamos:
1. `specifyBody:json` → envía body vacío a nuestra API
2. `specifyBody:string` + `JSON.stringify()` → envía `\x00{...}`

**Lo que se probó y NO funcionó:**
- Middleware Starlette `BaseHTTPMiddleware` para stripear null byte → no intercepta body antes de FastAPI
- Endpoint wrapper con `request.body()` manual → FastAPI ya consumió el body
- Body como string + JSON.parse server-side → n8n alternaba entre vacío y null byte

**Solución final (arquitectura v2):**
Reescribimos la arquitectura completa. Cada endpoint LLM (`/analyze`, `/hypothesize`, `/learn`) es ahora **self-contained**:
- n8n solo dispara POST vacíos (sin body)
- Cada endpoint lee su contexto internamente desde SQLite/PostgreSQL
- Cada endpoint llama al LLM directamente via httpx
- Cada endpoint guarda sus resultados directamente

El workflow n8n pasó de 16 nodos complejos (con expresiones JS) a 5 nodos simples (Cron → 4 POSTs).

**Aprendizaje:** Cuando una herramienta de integración tiene bugs fundamentales en features core (envío de body HTTP), no pelear contra el bug — rediseñar la arquitectura para no depender de esa feature.

---

### v1.9 — ASGI middleware para null bytes
**Problema:** `BaseHTTPMiddleware` de Starlette no permite modificar el body antes de que FastAPI lo parsee (por buffering interno).

**Fix:** Reescribimos como raw ASGI middleware:
```python
class StripNullByteMiddleware:
    async def __call__(self, scope, receive, send):
        async def patched_receive():
            message = await receive()
            if message.get("body", b"") and message["body"][0] == 0:
                message = {**message, "body": message["body"].lstrip(b"\x00")}
            return message
        await self.app(scope, patched_receive, send)
```

**Aprendizaje:** En ASGI, para modificar el body hay que interceptar `receive`, no `request.body()`. Los middleware de Starlette abstraen esto pero pierden control.

---

### v1.8 — Fix estrategia incorrecta (todo era "ema_crossover")
**Problema:** Los 50 top results en la DB eran `ema_crossover`, aunque `/hypothesize` generaba `breakout` y `vwap_pullback`.

**Root cause:** `guardar_en_db()` en `fase1_motor.py` (línea 179):
```python
strategy = p.get("signal_type", "ema_crossover")
```
Los params generados por el LLM no incluían `signal_type`, así que todo se guardaba como `ema_crossover`.

**Fix:** `pipeline_runner.py` ahora inyecta `params["signal_type"] = strategy` antes de correr el experimento.

**Aprendizaje:** Cuando una función determina un campo clave (nombre de estrategia) buscándolo en un dict con default, y ese dict viene de fuentes externas (LLM), el default siempre va a ganar. Mejor pasar el valor explícitamente como argumento.

---

### v1.7 — Fix learnings no se guardaban en Supabase
**Problema:** `/learn` retornaba `{"saved": 1}` pero Supabase estaba vacío.

**Root cause (doble):**
1. El LLM generaba categorías como `strategy_insight`, `risk_management` que no existen en el CHECK constraint de PostgreSQL (solo acepta: `parameter_insight`, `dead_end`, `promising_direction`, `strategy_ranking`, `external_research`)
2. El INSERT fallaba con constraint violation, pero `saved` ya se había incrementado antes del `commit()`. El commit fallaba silenciosamente y el transaction se rollbackeaba.

**Fix:**
- Prompt actualizado con las categorías exactas del schema
- Sanitizador que mapea categorías inválidas a `parameter_insight`
- Commit por fila (no por batch) para que un error no pierda todo

**Aprendizaje:** Cuando usás `try/except` alrededor de un bloque con loop + commit al final, el counter dentro del loop miente si el commit falla. Siempre commitear por fila o mover el counter después del commit.

---

### v1.6 — Fix JSON parsing (truncamiento por max_tokens)
**Problema:** `/analyze` fallaba intermitentemente con "Expecting ',' delimiter" o "No se pudo parsear JSON".

**Evolución de fixes:**
1. **Regex greedy** (`\{[\s\S]*\}`) → capturaba de primer `{` a último `}`, incluyendo texto extra
2. **Bracket-counter** → fallaba con `}` dentro de strings JSON (ej: `"value con } adentro"`)
3. **`json.JSONDecoder.raw_decode()`** → parsea correctamente respetando strings, PERO el JSON estaba truncado

**Root cause final:** `max_tokens=1024` no alcanzaba para la respuesta de análisis (patterns con arrays largos). El LLM cortaba el JSON a mitad.

**Fix:** `max_tokens=2048` + prompt que pide "JSON COMPACTO (máx 5 items por lista, strings cortos de 1 línea)".

**Aprendizaje:** Cuando el LLM devuelve JSON malformado, antes de mejorar el parser verificar si el JSON está completo. `raw_decode` es la mejor opción para parsear JSON embebido en texto, pero no puede arreglar JSON truncado.

---

### v1.5 — Cambio de modelo LLM: nemotron → llama → minimax → kimi-k2
**Problema:** `nvidia/nemotron-3-super-120b-a12b` tardaba >120s → Cloudflare 504 (timeout 100s).

**Modelos probados:**
| Modelo | Resultado |
|--------|-----------|
| `nvidia/nemotron-3-super-120b-a12b` | ❌ 504 timeout (120s) |
| `meta/llama-3.3-70b-instruct` | ⚠️ Funciona pero lento (~60s) |
| `minimaxai/minimax-m2.5` | ⚠️ Rápido pero JSON malformado frecuente |
| `moonshotai/kimi-k2-instruct` | ✅ Rápido (~10-15s) + JSON limpio |

**Arquitectura dual-model:**
- `LLM_MODEL` = kimi-k2 → para /hypothesize y /learn (necesitan JSON limpio)
- `LLM_MODEL_ANALYSIS` = kimi-k2 (overridable a nemotron-120B via env var para análisis profundo)

**Aprendizaje:** Para tareas que requieren output estructurado (JSON), la velocidad y la adherencia al formato importan más que el tamaño del modelo. MoE models (kimi-k2, deepseek-v3) son ideales: rápidos y precisos.

---

### v1.4 — Workflow n8n simplificado (16 → 5 nodos)
**Antes (v1, 16 nodos):**
```
Cron → GET /context → NVIDIA Analizar → Parsear → Hipotetizar → Parsear →
Validar Params → POST /experiments → POST /run-pipeline → GET /results →
NVIDIA Aprender → Parsear → POST /learnings → ...
```

**Después (v2, 5 nodos):**
```
Cron → POST /analyze → POST /hypothesize → POST /run-pipeline → POST /learn
```

Toda la lógica de parseo, validación y llamadas LLM se movió a los endpoints Python. n8n es solo un scheduler.

**Aprendizaje:** n8n es excelente como scheduler/orquestador pero frágil para lógica de procesamiento (parsing JSON, validación, transformación de datos). Mejor mantener la lógica en código (Python) y usar n8n solo para triggers y secuenciamiento.

---

### v1.3 — Primera ejecución exitosa end-to-end
**Hito:** Ejecución 401 — primer ciclo completo (Cron → analyze → hypothesize → run-pipeline → learn) en 49 segundos.

**Resultado:** /analyze usó fallback (parse error), pero /hypothesize generó 6 experiments y el pipeline los corrió. Demostró que la arquitectura funciona aunque los datos no eran óptimos.

---

### v1.2 — Deploy en Coolify + Supabase
**Stack deployado:**
- autolab-api en Coolify (Oracle Cloud 144.22.43.204)
- n8n en Coolify (same server)
- Supabase self-hosted en Coolify
- Cloudflare como proxy/DNS

**Problema descubierto:** Coolify ignora `networks:` en docker-compose. autolab-api no podía conectar a Supabase PostgreSQL.

**Solución:** Cron job en el servidor que reconecta el container a la red de Supabase cada minuto.

---

### v1.1 — Diseño inicial del sistema
**Decisiones de arquitectura:**
- SQLite para backtesting (ya existente, ~863MB de datos históricos)
- PostgreSQL (Supabase) para la capa de inteligencia (learnings, insights)
- n8n como orquestador (ya desplegado en el servidor del usuario)
- NVIDIA Build API como LLM provider (API keys gratuitas)
- FastAPI como bridge entre todo

**Inspiración:** karpathy/autoresearch — loop autónomo de investigación científica aplicado a trading cuantitativo.

---

## Resumen de Aprendizajes Clave

### Infraestructura
1. **n8n HTTP body bug:** No confiar en que n8n envíe body correctamente. Hacer endpoints self-contained.
2. **Coolify networking:** Docker networks del compose son ignoradas. Usar cron de reconexión.
3. **Cloudflare timeout:** 100s hard limit. Modelos >100s de respuesta causan 504.

### LLM
4. **JSON de LLMs:** Siempre usar `json.JSONDecoder.raw_decode()`, nunca regex greedy.
5. **max_tokens:** Calcular cuánto espacio necesita el output esperado. JSON con arrays necesita más tokens.
6. **Categorías/enums:** El prompt debe listar los valores exactos que el schema acepta.
7. **Modelo selection:** Para JSON estructurado, MoE models > modelos grandes lentos.

### Motor de Backtesting
8. **signal_type default:** Nunca confiar en defaults cuando el dict viene de fuentes externas.
9. **breakeven_after_r=0:** Parámetros multiplicativos con 0 = "siempre true". Usar None para "desactivado".
10. **Commit por fila:** En PostgreSQL con CHECK constraints, commitear por fila para no perder todo el batch.

---

*Changelog iniciado 2026-03-25 — AutoLab Fase 2*
