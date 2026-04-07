# Workflow: Correr un ciclo de experimentos manual

**Objetivo:** Ejecutar un ciclo completo de backtesting fuera del loop autónomo — útil para probar hipótesis específicas o desbloquear el sistema.
**Cuándo usarlo:** Cuando querés testear configs concretas sin esperar el ciclo de 30min.

---

## Inputs requeridos
- Lista de configuraciones a testear (strategy + params)
- `data/coco_lab.db` disponible en el servidor o localmente

## Pasos

### 1. Encolar los experimentos
```bash
# Via API (recomendado)
curl -X POST https://autolab-api.dantelujan.online/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "experiments": [
      {
        "strategy": "breakout",
        "symbol": "BTCUSDT",
        "timeframe": "4h",
        "params": {
          "lookback": 20, "vol_ratio_min": 1.5,
          "sl_atr_mult": 2.5, "trail_atr_mult": 3.0,
          "adx_filter": 22, "adx_period": 14,
          "use_daily_trend_filter": true, "ema_trend_daily_period": 30,
          "atr_period": 14, "ema_trend_period": 50, "vol_period": 20,
          "max_hold_bars": 30, "breakeven_after_r": 0.5
        },
        "dataset": "both",
        "notes": "descripción del experimento"
      }
    ],
    "session_id": "manual-test",
    "cycle_num": 0
  }'
```

### 2. Correr el pipeline
```bash
curl -X POST https://autolab-api.dantelujan.online/run-pipeline
```
Esperar respuesta con `batch_id`. El pipeline corre de forma sincrónica — puede tardar varios minutos según la cantidad de jobs.

### 3. Ver resultados del ciclo
```bash
# Con el batch_id del paso anterior
curl "https://autolab-api.dantelujan.online/results/cycle?batch_id=BATCH_XXXXXXXX"
```

### 4. Extraer learnings
```bash
curl -X POST https://autolab-api.dantelujan.online/learn
```

### 5. Verificar el campeón
```bash
curl https://autolab-api.dantelujan.online/status
# Ver si el campo "champion" cambió
```

## Outputs esperados
- Runs guardados en `coco_lab.db` tabla `runs`
- Learnings nuevos en PostgreSQL `autolab_learnings`
- Campeón actualizado si algún run superó el capital_final record
- Notificación en Telegram con resumen del ciclo

## Edge cases
- **Pipeline timeout (>10min):** reducir cantidad de jobs con `--limit N` en el body
- **Deduplicación rechaza todos:** los params ya fueron testeados — variar más parámetros
- **Sharpe OOS = 0 en todos:** verificar que los datos de candles estén cargados (`/health`)

## Parámetros válidos por estrategia

### breakout
```json
{
  "lookback": [10-30], "vol_ratio_min": [1.0-3.0],
  "sl_atr_mult": [1.5-4.0], "trail_atr_mult": [1.5-4.0],
  "adx_filter": [18-30], "breakeven_after_r": [0.5-2.0],
  "ema_trend_daily_period": [20-50]
}
```

### vwap_pullback
```json
{
  "atr_period": [10-20], "sl_atr_mult": [1.5-3.5],
  "trail_atr_mult": [1.5-3.5], "adx_filter": [18-28],
  "breakeven_after_r": [0.5-2.0], "ema_trend_period": [30-70]
}
```
