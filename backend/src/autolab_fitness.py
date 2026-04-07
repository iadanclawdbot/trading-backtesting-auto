"""
autolab_fitness.py — Función de Fitness + Espacio de Parámetros
================================================================
Coco Stonks Lab — Fase 2: AutoLab

INMUTABLE: Este archivo define el harness de evaluación.
No modificar sin revisión humana explícita.

El fitness score es la métrica única que el sistema de hill-climbing
maximiza. Equivalente a val_bpb en karpathy/autoresearch.
"""

import math
from typing import Optional


# ==============================================================================
# BENCHMARK ACTUAL (se actualiza manualmente cuando hay nuevo campeón)
# ==============================================================================

BENCHMARK = {
    "strategy": "V5 Portfolio (V4 Breakout 50% + VWAP Pullback 50%)",
    "sharpe_oos": 1.166,
    "trades_oos": 53,
    "wr_oos": 0.68,
    "sharpe_train": 1.042,
    "dd_oos": -4.6,
    "fitness": 1.193,  # compute_fitness() del benchmark actual
    "updated_at": "2026-03-24",
}


# ==============================================================================
# FUNCIÓN DE FITNESS COMPUESTA
# ==============================================================================

def compute_fitness(
    sharpe_oos: float,
    trades_oos: int,
    wr_oos: float,
    sharpe_train: float,
    dd_oos: float,
) -> float:
    """
    Fitness compuesto. Retorna float >= 0. Maximizar.

    Principios de diseño:
    - Sharpe OOS es la señal PRIMARIA (70% del peso)
    - Gates binarias: si no pasa → fitness = 0 (descarte inmediato)
    - Trade count bonus: más trades = más confianza estadística
    - Consistency train/valid: penaliza overfitting
    - Drawdown bonus: menos DD = mejor

    Calibración vs Benchmark V5 (2026-03-24):
      sharpe=1.166, trades=53, wr=0.68, train=1.042, dd=-4.6
      → fitness = 1.193

    Args:
        sharpe_oos:   Sharpe ratio en out-of-sample (validación 2025)
        trades_oos:   Número de trades en out-of-sample
        wr_oos:       Win rate en out-of-sample (0.0 a 1.0)
        sharpe_train: Sharpe ratio en in-sample (entrenamiento 2024)
        dd_oos:       Max drawdown en OOS (negativo, ej: -4.6)

    Returns:
        float: fitness score >= 0. Superar BENCHMARK["fitness"] para ganar.
    """

    # === GATES BINARIAS ===
    # Eliminar resultados inválidos antes de calcular

    if trades_oos < 15:
        # Muestra insuficiente para cualquier conclusión estadística
        return 0.0

    if wr_oos < 0.30 or wr_oos > 0.75:
        # WR fuera del rango realista para crypto trading con filtros de calidad
        # <30%: destruye capital sistemáticamente
        # >75%: casi siempre indica overfitting o lookahead bias
        return 0.0

    if dd_oos < -20.0:
        # Drawdown inaceptable para producción
        return 0.0

    if sharpe_oos < -2.0:
        # Sharpe extremadamente negativo = estrategia destruye capital
        return 0.0

    # === COMPONENTES DEL FITNESS ===

    # 1. Sharpe OOS — señal primaria (70%)
    # Puede ser negativo pero las gates lo limitan a >= -2.0
    sharpe_component = sharpe_oos * 0.70

    # 2. Trade volume bonus (hasta 25%)
    # Log scale: 15 trades=0.0, 30 trades≈0.14, 53 trades≈0.24, 100 trades≈0.25
    # Incentiva estrategias estadísticamente robustas sin over-reward por volumen
    trade_bonus = min(0.25, max(0.0, math.log(max(trades_oos, 15) / 15) * 0.2))

    # 3. Consistency train/valid (10%)
    # Si ambos Sharpes son positivos: penaliza cuando train >> valid (overfitting)
    # Si train negativo + valid positivo: sospechoso, consistencia = 0
    if sharpe_train > 0 and sharpe_oos > 0:
        ratio = min(sharpe_oos / sharpe_train, 1.0)
        consistency_component = ratio * 0.10
    elif sharpe_train <= 0 and sharpe_oos > 0:
        # Train negativo + valid positivo = inversión de signo → ruido estadístico
        consistency_component = 0.0
    else:
        consistency_component = 0.0

    # 4. Drawdown bonus (5%)
    # DD=0% → 0.05, DD=-10% → 0.0, DD<-10% → 0.0
    # Solo premia drawdowns controlados, no penaliza los malos (la gate lo hace)
    dd_component = max(0.0, (10.0 + dd_oos) / 10.0) * 0.05

    raw_fitness = sharpe_component + trade_bonus + consistency_component + dd_component
    return max(0.0, raw_fitness)


def beats_benchmark(fitness: float) -> bool:
    """¿Supera el benchmark actual?"""
    return fitness > BENCHMARK["fitness"]


def fitness_delta(fitness: float) -> float:
    """Diferencia vs benchmark. Positivo = mejor."""
    return fitness - BENCHMARK["fitness"]


# ==============================================================================
# ESPACIO DE PARÁMETROS (PARAMETER_SPACE)
# ==============================================================================
# Define los rangos válidos para cada parámetro por estrategia.
# El brain LLM recibe este dict y SOLO puede proponer valores dentro de estos rangos.
# El validador en autolab_brain.py rechaza cualquier valor fuera de bounds.

PARAMETER_SPACE = {

    "breakout": {
        # Ventana de lookback para detectar máximos históricos
        "lookback": {
            "min": 10, "max": 40, "step": 5, "default": 20,
            "note": "Probados 10-30. EL V3 usa 20. No cambiar sin razón."
        },
        # Ratio de volumen mínimo para confirmar breakout
        "vol_ratio_min": {
            "min": 1.0, "max": 3.0, "step": 0.25, "default": 1.5,
            "note": "1.5 aparece en 98% del top 20 histórico. Invariante."
        },
        # Período para calcular volumen promedio
        "vol_period": {
            "min": 10, "max": 40, "step": 5, "default": 20,
            "note": "Explorado poco. Potencial."
        },
        # Período ATR para stops
        "atr_period": {
            "min": 7, "max": 21, "step": 7, "default": 14,
            "note": "Solo 3 valores: 7, 14, 21."
        },
        # Multiplicador ATR para stop loss inicial
        "sl_atr_mult": {
            "min": 1.5, "max": 4.0, "step": 0.5, "default": 2.5,
            "note": "Espacio agotado. 2.5 confirmado como óptimo."
        },
        # Multiplicador ATR para trailing stop
        "trail_atr_mult": {
            "min": 1.5, "max": 4.0, "step": 0.5, "default": 2.5,
            "note": "Espacio agotado. 2.5 confirmado como óptimo."
        },
        # Período EMA de tendencia en 4H
        "ema_trend_period": {
            "min": 20, "max": 200, "step": 10, "default": 50,
            "note": "EMA50 es invariante. Combinaciones con >100 no exploradas."
        },
        # Período EMA de tendencia diaria
        "ema_trend_daily_period": {
            "min": 15, "max": 60, "step": 5, "default": 30,
            "note": "EMA28-35 produce resultados idénticos. El hallazgo más importante."
        },
        # Períodos máximos para mantener una posición abierta
        "max_hold_bars": {
            "min": 15, "max": 60, "step": 5, "default": 30,
            "note": "Poco explorado. Potencial con estrategias de alta frecuencia."
        },
        # Umbral mínimo ADX para entrar
        "adx_filter": {
            "min": 18, "max": 32, "step": 2, "default": 22,
            "note": "ADX 20-22 supera 24+. V4 usa 22. NO probar >28 (dead end)."
        },
        # Período del ADX
        "adx_period": {
            "min": 7, "max": 21, "step": 7, "default": 14,
            "note": "Solo 3 valores válidos."
        },
        # R ganado antes de mover SL a breakeven (0 = desactivado)
        "breakeven_after_r": {
            "min": 0.0, "max": 1.5, "step": 0.25, "default": 0.5,
            "note": "0.5 es el catalizador clave. >1.0 con adx=24 → nunca dispara."
        },
    },

    "vwap_pullback": {
        "sl_atr_mult": {
            "min": 0.75, "max": 2.5, "step": 0.25, "default": 1.25,
            "note": "VWAP necesita SL más ajustado que breakout."
        },
        "trail_atr_mult": {
            "min": 1.5, "max": 3.5, "step": 0.5, "default": 2.5,
            "note": "2.5 confirmado como óptimo también para VWAP."
        },
        "adx_filter": {
            "min": 0, "max": 30, "step": 5, "default": 20,
            "note": "adx=20 + vol=1.0 aparece en 100% del top 10."
        },
        "adx_period": {
            "min": 7, "max": 21, "step": 7, "default": 14,
        },
        "vol_ratio_min": {
            "min": 0.8, "max": 2.0, "step": 0.2, "default": 1.0,
            "note": "vol=1.0 (sin filtro extra) funciona mejor para VWAP."
        },
        "breakeven_after_r": {
            "min": 0.0, "max": 1.0, "step": 0.25, "default": 0.5,
            "note": "be=0.5 es decisivo: sin él Sharpe cae de 0.905 a 0.47."
        },
        "ema_trend_period": {
            "min": 20, "max": 100, "step": 10, "default": 50,
        },
        "ema_trend_daily_period": {
            "min": 15, "max": 60, "step": 5, "default": 30,
        },
        "max_hold_bars": {
            "min": 15, "max": 60, "step": 5, "default": 30,
        },
    },

    "mean_reversion": {
        "rsi_period": {
            "min": 7, "max": 21, "step": 7, "default": 14,
        },
        "rsi_oversold": {
            "min": 25, "max": 40, "step": 5, "default": 30,
            "note": "DEAD END: rsi_oversold < 25 produce 0 trades en train."
        },
        "bb_period": {
            "min": 14, "max": 30, "step": 2, "default": 20,
        },
        "bb_std": {
            "min": 1.5, "max": 3.0, "step": 0.5, "default": 2.0,
        },
        "atr_period": {
            "min": 7, "max": 21, "step": 7, "default": 14,
        },
        "sl_atr_mult": {
            "min": 1.5, "max": 3.0, "step": 0.5, "default": 2.0,
        },
        "ema_trend_period": {
            "min": 20, "max": 200, "step": 20, "default": 50,
        },
        "breakeven_after_r": {
            "min": 0.0, "max": 1.0, "step": 0.25, "default": 0.5,
        },
        "max_hold_bars": {
            "min": 10, "max": 40, "step": 5, "default": 20,
        },
    },

}

# Parámetros requeridos por estrategia (para validación de configs del LLM)
REQUIRED_PARAMS = {
    "breakout": [
        "lookback", "vol_ratio_min", "atr_period", "sl_atr_mult",
        "trail_atr_mult", "ema_trend_period", "ema_trend_daily_period",
        "adx_filter", "breakeven_after_r",
    ],
    "vwap_pullback": [
        "sl_atr_mult", "trail_atr_mult", "adx_filter", "vol_ratio_min",
        "breakeven_after_r", "ema_trend_period", "ema_trend_daily_period",
    ],
    "mean_reversion": [
        "rsi_period", "rsi_oversold", "bb_period", "bb_std",
        "atr_period", "sl_atr_mult", "ema_trend_period",
    ],
}

# Estrategias habilitadas para exploración autónoma
ENABLED_STRATEGIES = ["breakout", "vwap_pullback", "mean_reversion"]


# ==============================================================================
# VALIDACIÓN DE CONFIGS GENERADAS POR EL LLM
# ==============================================================================

def validate_experiment_config(config: dict) -> tuple[bool, str]:
    """
    Valida una config de experimento generada por el LLM.

    Returns:
        (True, "") si es válida
        (False, "razón del rechazo") si es inválida
    """
    strategy = config.get("strategy")
    params = config.get("params", {})

    if not strategy:
        return False, "Falta el campo 'strategy'"

    if strategy not in ENABLED_STRATEGIES:
        return False, f"Estrategia '{strategy}' no habilitada. Usar: {ENABLED_STRATEGIES}"

    space = PARAMETER_SPACE.get(strategy, {})
    required = REQUIRED_PARAMS.get(strategy, [])

    # Verificar parámetros requeridos
    for param in required:
        if param not in params:
            return False, f"Falta parámetro requerido: '{param}' para {strategy}"

    # Verificar rangos de cada parámetro presente
    for param, value in params.items():
        if param not in space:
            continue  # Parámetros no definidos en PARAMETER_SPACE se ignoran

        bounds = space[param]
        if value < bounds["min"] or value > bounds["max"]:
            return False, (
                f"Parámetro '{param}' = {value} fuera de rango "
                f"[{bounds['min']}, {bounds['max']}]"
            )

    return True, ""


def get_parameter_space_summary() -> str:
    """
    Retorna un resumen legible del PARAMETER_SPACE para incluir en prompts LLM.
    """
    lines = ["## Espacio de Parámetros Permitido\n"]
    for strategy, params in PARAMETER_SPACE.items():
        lines.append(f"### {strategy}")
        for param, bounds in params.items():
            note = f" — {bounds['note']}" if "note" in bounds else ""
            lines.append(
                f"  {param}: [{bounds['min']} → {bounds['max']}] "
                f"step={bounds['step']} default={bounds['default']}{note}"
            )
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # Test rápido
    fitness = compute_fitness(
        sharpe_oos=1.166, trades_oos=53, wr_oos=0.68,
        sharpe_train=1.042, dd_oos=-4.6
    )
    print(f"Fitness V5 Portfolio: {fitness:.3f}")
    print(f"Benchmark almacenado: {BENCHMARK['fitness']:.3f}")
    print(f"¿Supera benchmark? {beats_benchmark(fitness)}")

    # Test validación
    config_ok = {
        "strategy": "breakout",
        "params": {
            "lookback": 20, "vol_ratio_min": 1.5, "atr_period": 14,
            "sl_atr_mult": 2.5, "trail_atr_mult": 2.5, "ema_trend_period": 50,
            "ema_trend_daily_period": 30, "adx_filter": 22, "breakeven_after_r": 0.5,
        }
    }
    valid, reason = validate_experiment_config(config_ok)
    print(f"\nConfig válida: {valid} — {reason or 'OK'}")

    config_bad = {"strategy": "breakout", "params": {"lookback": 100}}
    valid, reason = validate_experiment_config(config_bad)
    print(f"Config inválida: {valid} — {reason}")
