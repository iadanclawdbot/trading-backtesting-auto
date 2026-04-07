# =============================================================================
# COCO STONKS — LABORATORIO DE BACKTESTING
# config.py — Todos los parámetros en un solo lugar.
# Modificá acá antes de correr cualquier script.
# =============================================================================

import os

# -----------------------------------------------------------------------------
# RUTAS
# -----------------------------------------------------------------------------
SCRIPTS_DIR   = os.path.dirname(os.path.abspath(__file__))
BASE_DIR      = os.path.dirname(SCRIPTS_DIR)          # raíz del proyecto
DATA_DIR      = os.path.join(BASE_DIR, "data")
RESULTS_DIR   = os.path.join(BASE_DIR, "resultados")
DB_PATH       = os.path.join(DATA_DIR, "candles_raw.db")   # legacy — se eliminará tras migración
RESULTS_DB    = os.path.join(DATA_DIR, "resultados.db")   # legacy — se eliminará tras migración
EXPERIMENTS_DB = os.path.join(DATA_DIR, "experiments.db") # legacy — se eliminará tras migración
UNIFIED_DB    = os.path.join(DATA_DIR, "coco_lab.db")     # nueva DB unificada

# -----------------------------------------------------------------------------
# DATOS HISTÓRICOS
# -----------------------------------------------------------------------------
SYMBOL        = "BTC/USDT"
TIMEFRAME     = "1h"

# 2024 = datos de entrenamiento (in-sample)
TRAIN_START   = "2024-01-01"
TRAIN_END     = "2024-12-31"

# 2025 = datos de validación (out-of-sample).
VALID_START   = "2025-01-01"
VALID_END     = "2026-03-20"

# -----------------------------------------------------------------------------
# ✅ ESTRATEGIA OFICIAL — BREAKOUT_V3 (BENCHMARK FINAL 2026-03-23)
#
# Validada en 110+ runs de backtesting sobre BTC/USDT 4H.
# OOS 2025: Sharpe 0.864 | WR 50% | DD -4.6% | Trades 16
# Única diferencia vs V2: ema_trend_daily_period 20 → 30
# Robustez confirmada: EMA diaria 28-35 produce resultados idénticos.
# Estado: LISTA PARA PAPER TRADING en Binance Testnet.
# NO modificar parámetros hasta acumular 30 trades reales.
# -----------------------------------------------------------------------------
STRATEGY_BREAKOUT_V3 = {
    "signal_type"            : "breakout",
    "lookback"               : 20,
    "vol_ratio_min"          : 1.5,
    "vol_period"             : 20,
    "atr_period"             : 14,
    "sl_atr_mult"            : 2.5,
    "trail_atr_mult"         : 2.5,
    "ema_trend_period"       : 50,
    "max_hold_bars"          : 30,
    "adx_filter"             : 24,
    "adx_period"             : 14,
    "use_daily_trend_filter" : True,
    "ema_trend_daily_period" : 30,     # ← único cambio vs V2 (era 20)
}

# Alias conveniente — usar este en producción
STRATEGY_OFICIAL = STRATEGY_BREAKOUT_V3

# -----------------------------------------------------------------------------
# ESTRATEGIA — PARÁMETROS ORIGINALES (LEGACY)
# -----------------------------------------------------------------------------
STRATEGY = {
    "rsi_period"     : 14,
    "rsi_min"        : 50,
    "rsi_max"        : 75,
    "ema_fast"       : 20,
    "ema_slow"       : 50,
    "vol_period"     : 20,
    "vol_ratio_min"  : 0.5,
    "stop_loss_pct"  : 0.01,
    "take_profit_pct": 0.02,
}

TIMEFRAME_4H = "4h"

# -----------------------------------------------------------------------------
# ESTRATEGIAS HISTÓRICAS (REFERENCIA — NO USAR EN PRODUCCIÓN)
# Documentadas para referencia del historial de experimentos.
# -----------------------------------------------------------------------------

STRATEGY_BREAKOUT = {
    "signal_type"      : "breakout",
    "lookback"         : 20,
    "vol_ratio_min"    : 1.5,
    "vol_period"       : 20,
    "atr_period"       : 14,
    "sl_atr_mult"      : 2.5,
    "trail_atr_mult"   : 0.8,
    "ema_trend_period" : 50,
    "max_hold_bars"    : 30,
}

# V1: Breakout + ADX. Sharpe OOS 0.399, WR 45%, 18 trades.
STRATEGY_BREAKOUT_V1 = {
    "signal_type"      : "breakout",
    "lookback"         : 20,
    "vol_ratio_min"    : 1.5,
    "vol_period"       : 20,
    "atr_period"       : 14,
    "sl_atr_mult"      : 2.5,
    "trail_atr_mult"   : 2.5,
    "ema_trend_period" : 50,
    "max_hold_bars"    : 30,
    "adx_filter"       : 24,
    "adx_period"       : 14,
}

# V2: Breakout + ADX + EMA20 diaria. Sharpe OOS 0.581, WR 44.4%, 18 trades.
STRATEGY_BREAKOUT_V2 = STRATEGY_BREAKOUT_V1.copy()
STRATEGY_BREAKOUT_V2.update({
    "use_daily_trend_filter" : True,
    "ema_trend_daily_period" : 20,
})

# V3: Breakout + ADX + EMA30 diaria. Sharpe OOS 0.864, WR 50%, 16 trades. ← OFICIAL
# (ya definida arriba como STRATEGY_BREAKOUT_V3)

# Variantes experimentales descartadas
STRATEGY_BREAKOUT_V3_adx_zona = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_BREAKOUT_V3_adx_zona.update({"adx_zone_low": 18, "adx_zone_body_min": 0.70})

STRATEGY_BREAKOUT_V4A = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_BREAKOUT_V4A.update({"lookback": 15})

STRATEGY_BREAKOUT_V4B = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_BREAKOUT_V4B.update({"lookback": 10})

STRATEGY_BREAKDOWN_SHORT = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_BREAKDOWN_SHORT.update({"signal_type": "breakdown_short"})

STRATEGY_MR = {
    "signal_type"      : "mean_reversion",
    "rsi_period"       : 14,
    "rsi_oversold"     : 30,
    "bb_period"        : 20,
    "bb_std"           : 2.0,
    "atr_period"       : 14,
    "sl_atr_mult"      : 2.0,
    "tp_atr_mult"      : 4.0,
    "ema_trend_period" : 200,
}

STRATEGY_RETEST_V1 = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_RETEST_V1.update({"signal_type": "retest", "max_retest_bars": 5})

STRATEGY_HIBRIDO_V1 = STRATEGY_BREAKOUT_V2.copy()
STRATEGY_HIBRIDO_V1.update({"signal_type": "hibrido", "max_retest_bars": 5})

# V5: V3 + ADX Slope (solo entrar si ADX está subiendo)
STRATEGY_BREAKOUT_V5 = STRATEGY_BREAKOUT_V3.copy()
STRATEGY_BREAKOUT_V5.update({"adx_slope_filter": True})

# V6: V3 + Breakeven Stop (mover SL a entrada tras ganar 1R)
STRATEGY_BREAKOUT_V6 = STRATEGY_BREAKOUT_V3.copy()
STRATEGY_BREAKOUT_V6.update({"breakeven_after_r": 1.0})

# V7: V3 + Trailing Dinámico (trail más ajustado en baja vol, más ancho en alta vol)
STRATEGY_BREAKOUT_V7 = STRATEGY_BREAKOUT_V3.copy()
STRATEGY_BREAKOUT_V7.update({"trail_dynamic": True})

# -----------------------------------------------------------------------------
# REGLAS INVIOLABLES DE COCO STONKS
# El motor las verifica antes de cada trade. Si alguna falla, no opera.
# -----------------------------------------------------------------------------
RULES = {
    "max_risk_pct"   : 0.02,   # Regla 1: riesgo máximo 2% del capital actual
    "min_rr_ratio"   : 2.0,    # Regla 2: R:R mínimo 1:2 (TP debe ser 2x el SL)
    "daily_stop_pct" : 0.06,   # Regla 3: stop diario 6% — para hasta mañana
    "max_daily_ops"  : 5,      # máximo de operaciones por día calendario
}

# -----------------------------------------------------------------------------
# CAPITAL INICIAL
# -----------------------------------------------------------------------------
INITIAL_CAPITAL = 250.0        # USDT — igual que Coco en Binance Testnet

# -----------------------------------------------------------------------------
# COSTOS DE TRADING (comisiones + slippage)
# -----------------------------------------------------------------------------
COSTS = {
    "commission_pct" : 0.001,  # 0.1% por lado (maker fee Binance estándar)
    "slippage_pct"   : 0.0005, # 0.05% estimado de slippage en mercado
    # Total round-trip: (commission + slippage) × 2 = ~0.3%
}

# -----------------------------------------------------------------------------
# ALERTAS DE SANIDAD (para detectar bugs o overfitting)
# -----------------------------------------------------------------------------
SANITY = {
    "min_win_rate"   : 0.35,
    "max_win_rate"   : 0.70,
    "min_trades"     : 30,
    "max_sharpe"     : 3.0,
}
