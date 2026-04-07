# Workflow: Agregar una nueva estrategia al pipeline autónomo

**Objetivo:** Incorporar una estrategia nueva para que el ciclo autónomo pueda testarla.
**Cuándo usarlo:** Cuando el espacio paramétrico de las estrategias existentes está agotado.

---

## Inputs requeridos
- Nombre de la estrategia y su motor en `backend/backtesting/motor_base.py`
- Definición de sus parámetros y rangos válidos

## Pasos

### 1. Verificar que el motor existe
```bash
grep "def correr_backtest_" backend/backtesting/motor_base.py
```
Si no existe → hay que implementarlo primero en `motor_base.py` (ver `trading-backtesting/scripts/motor_base.py` como referencia).

### 2. Verificar que pipeline_runner.py la conoce
```bash
grep "MOTORES" backend/backtesting/pipeline_runner.py
```
La estrategia debe estar mapeada en el dict `MOTORES`. Si no → agregarla.

### 3. Agregar a autolab_fitness.py

Abrir `backend/src/autolab_fitness.py` y agregar en tres lugares:

**a) ENABLED_STRATEGIES:**
```python
ENABLED_STRATEGIES = ["breakout", "vwap_pullback", "nueva_estrategia"]
```

**b) PARAMETER_SPACE:**
```python
"nueva_estrategia": {
    "param_1": [valor1, valor2, valor3],
    "param_2": [valor1, valor2],
}
```

**c) REQUIRED_PARAMS:**
```python
"nueva_estrategia": ["param_1", "param_2", "param_3_obligatorio"]
```

**d) VALID_RANGES (opcional pero recomendado):**
```python
"nueva_estrategia": {
    "param_1": (min, max),
    "param_2": (min, max),
}
```

### 4. Testear que el pipeline la acepta

Encolar un job manual y correrlo (ver `workflows/experiment_cycle.md`):
```json
{"strategy": "nueva_estrategia", "params": {...}}
```

Verificar que el run aparece en los resultados y tiene métricas válidas (no 0 trades, no error).

### 5. Hacer deploy

Seguir `workflows/deploy.md`.

### 6. Actualizar TASK.md

Marcar el ítem correspondiente como completado y agregar observaciones.

## Outputs esperados
- La nueva estrategia aparece en `/status` como opción disponible
- El ciclo autónomo empieza a generar hipótesis para ella
- Los primeros runs aparecen en `coco_lab.db`

## Edge cases
- **Motor no implementado:** implementarlo en `motor_base.py` primero, copiando el patrón de `correr_backtest_breakout`
- **Parámetros inválidos rechazados por /hypothesize:** revisar `VALID_RANGES` — los rangos deben ser coherentes
- **0 trades en todos los runs:** los filtros son demasiado restrictivos — relajar parámetros base

## Estrategias disponibles en motor_base.py
```
correr_backtest_base          → ema_crossover (legacy)
correr_backtest_breakout      → breakout (activa)
correr_backtest_breakdown     → breakdown_short (descartada)
correr_backtest_mr            → mean_reversion (disponible, no activa)
correr_backtest_retest        → retest (descartada)
correr_backtest_hibrido       → hibrido (descartada)
correr_backtest_funding_reversion → funding_reversion (descartada)
correr_backtest_vwap          → vwap_pullback (activa)
```
