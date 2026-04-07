# Workflow: Diagnosticar por qué el ciclo autónomo se estancó

**Objetivo:** Identificar la causa raíz cuando el sistema deja de mejorar resultados y proponer solución.
**Cuándo usarlo:** Cuando el campeón no cambia en >3 días o los learnings son siempre los mismos.

---

## Inputs requeridos
- API en producción respondiendo (`/health` ok)
- Acceso a los endpoints de contexto

## Pasos

### 1. Leer el estado actual
```bash
curl https://autolab-api.dantelujan.online/status
curl "https://autolab-api.dantelujan.online/context?top_n=50"
curl https://autolab-api.dantelujan.online/learnings
```

Anotar:
- ¿Cuántos runs hay en total? ¿Cuántos en los últimos 7 días?
- ¿El Sharpe OOS del campeón está mejorando o estancado?
- ¿Los learnings son variados o siempre dicen lo mismo?

### 2. Identificar la causa

**Causa A — Espacio paramétrico agotado**
- Síntoma: `/hypothesize` genera configs que son rechazadas por deduplicación
- Verificar: `SELECT COUNT(*) FROM experiments WHERE status='done'` — si >500, probable
- Solución: ampliar rangos en `backend/src/autolab_fitness.py` → `PARAMETER_SPACE`

**Causa B — LLM sin diversidad**
- Síntoma: los experimentos generados siempre varían los mismos 1-2 parámetros
- Verificar: revisar los últimos 20 `params_json` en la tabla `experiments`
- Solución: agregar instrucción explícita en el prompt de `/hypothesize` para forzar diversidad

**Causa C — Benchmark demasiado alto**
- Síntoma: ningún run supera el fitness 1.193 de `autolab_fitness.py`
- Verificar: `SELECT MAX(sharpe_ratio) FROM runs WHERE dataset='valid'`
- Solución: revisar si el fitness está bien calibrado o separar benchmark de exploración

**Causa D — Estrategia nueva necesaria**
- Síntoma: breakout y vwap están en sus máximos posibles
- Verificar: distribución de Sharpe OOS — ¿hay fat tail o ya convergió?
- Solución: activar `mean_reversion` en `ENABLED_STRATEGIES` de `autolab_fitness.py`

### 3. Proponer y ejecutar solución

Según la causa identificada, seguir el workflow correspondiente:
- Causa A/D → `workflows/add_strategy.md`
- Causa B/C → modificar `backend/src/autolab_fitness.py` directamente

### 4. Documentar

Agregar en `TASK.md` → sección "NO REPETIR":
- Qué causa se encontró
- Qué se hizo
- Cómo verificar que funcionó

## Outputs esperados
- Causa identificada con evidencia (números, no suposiciones)
- Plan de acción concreto con archivo y línea a modificar
- TASK.md actualizado

## Edge cases
- **API caída:** resolver deploy primero (`workflows/deploy.md`)
- **Learnings vacíos:** ejecutar manualmente `POST /learn` y verificar logs
- **Ciclo n8n no corre:** verificar en n8n UI que los workflows están activos
