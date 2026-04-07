# =============================================================================
# MOTOR BASE — LÓGICA COMPARTIDA DE BACKTESTING
# motor_base.py
#
# Contiene toda la lógica del motor de backtesting que es compartida entre:
# - fase1_motor.py (ejecución individual)
# - fase2_grid_search.py (optimización de parámetros)
#
# Este archivo NO debe modificarse para cambiar la estrategia.
# Los parámetros se pasan como argumentos a las funciones.
# =============================================================================

import json
import sqlite3
import pandas as pd
import numpy as np
from config import RULES, COSTS, INITIAL_CAPITAL, UNIFIED_DB


# =============================================================================
# CANDLE LOGGER — REGISTRO VELA POR VELA
# =============================================================================

class CandleLogger:
    """
    Registra el estado de cada vela durante un backtest.
    Permite reconstruir la curva de equity y el detalle de señales/filtros.
    Se inserta en candle_states de coco_lab.db al guardar el run.
    """

    __slots__ = ("enabled", "states")

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.states = []

    def log(self, bar_index, timestamp, equity,
            in_position=0, trade_num=None, trailing_stop=None, unrealized_pnl=None,
            signal=None, signal_passed=False, signal_filtered=False,
            filter_reason=None, indicators=None):
        if not self.enabled:
            return
        self.states.append({
            "bar_index":       bar_index,
            "timestamp":       int(timestamp),
            "equity":          round(float(equity), 4),
            "in_position":     in_position,
            "trade_num":       trade_num,
            "trailing_stop":   round(float(trailing_stop), 2) if trailing_stop is not None else None,
            "unrealized_pnl":  round(float(unrealized_pnl), 4) if unrealized_pnl is not None else None,
            "signal":          signal,
            "signal_passed":   1 if signal_passed else 0,
            "signal_filtered": 1 if signal_filtered else 0,
            "filter_reason":   filter_reason,
            "indicators_json": json.dumps(indicators) if indicators else None,
        })


# =============================================================================
# HELPERS — FILTER REASON
# =============================================================================

def _filter_reason_breakout(vela, params, stop_diario, ops_dia, rules):
    """Retorna la razón por la que no se abrió trade en la vela actual."""
    if stop_diario:
        return "daily_stop"
    if ops_dia >= rules["max_daily_ops"]:
        return "max_daily_ops"
    if not (vela["close"] > vela["high_max"]):
        return "no_breakout"
    if not (vela["vol_ratio"] >= params.get("vol_ratio_min", 1.5)):
        return "vol_low"
    if not (vela["close"] > vela["ema_trend"]):
        return "trend_down"
    if params.get("use_daily_trend_filter", False):
        if not (vela["close"] > vela.get("ema20_diaria", float("inf"))):
            return "daily_trend_down"
    adx_filter = params.get("adx_filter", 0)
    if adx_filter > 0 and vela.get("adx", 100) < adx_filter:
        return "adx_low"
    if params.get("adx_slope_filter", False) and "adx_prev" in vela:
        if not (vela["adx"] > vela["adx_prev"]):
            return "adx_slope_down"
    return "no_signal"


def _filter_reason_breakdown(vela, params, stop_diario, ops_dia, rules):
    if stop_diario:
        return "daily_stop"
    if ops_dia >= rules["max_daily_ops"]:
        return "max_daily_ops"
    if not (vela["close"] < vela["low_min"]):
        return "no_breakdown"
    if not (vela["vol_ratio"] >= params.get("vol_ratio_min", 1.5)):
        return "vol_low"
    if not (vela["close"] < vela["ema_trend"]):
        return "trend_up"
    if params.get("use_daily_trend_filter", False):
        if not (vela["close"] < vela.get("ema20_diaria", 0)):
            return "daily_trend_up"
    adx_filter = params.get("adx_filter", 0)
    if adx_filter > 0 and vela.get("adx", 100) < adx_filter:
        return "adx_low"
    return "no_signal"


# -----------------------------------------------------------------------------
# CÁLCULO DE INDICADORES TÉCNICOS
# -----------------------------------------------------------------------------


def calcular_indicadores(df, params):
    """
    Agrega columnas de indicadores al DataFrame según los parámetros dados.
    Todos los cálculos son hacia atrás (lookback) — nunca usa datos futuros.

    Args:
        df: DataFrame con columnas: close, volume_btc
        params: dict con rsi_period, ema_fast, ema_slow, vol_period (opcional)

    Returns:
        DataFrame con columnas adicionales: rsi, ema_fast, ema_slow, vol_sma, vol_ratio
    """
    df = df.copy()

    rsi_period = params.get("rsi_period", 14)
    ema_fast = params.get("ema_fast", 20)
    ema_slow = params.get("ema_slow", 50)
    vol_period = params.get("vol_period", 20)

    # RSI — Relative Strength Index
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
    avg_loss = loss.ewm(com=rsi_period - 1, min_periods=rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # EMAs — Medias Móviles Exponenciales
    df["ema_fast"] = df["close"].ewm(span=ema_fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=ema_slow, adjust=False).mean()

    # Ratio de volumen (volumen actual / promedio de los últimos N períodos)
    df["vol_sma"] = df["volume_btc"].rolling(window=vol_period).mean()
    df["vol_ratio"] = df["volume_btc"] / df["vol_sma"].replace(0, np.nan)

    # Eliminar filas sin indicadores válidos (las primeras N velas)
    df.dropna(subset=["rsi", "ema_fast", "ema_slow", "vol_ratio"], inplace=True)

    return df


# -----------------------------------------------------------------------------
# MOTOR DE SEÑALES — DECIDE SI ENTRAR O NO EN CADA VELA
# -----------------------------------------------------------------------------


def generar_señal(vela, params):
    """
    Evalúa la vela actual y retorna True si se cumplen todas las condiciones
    para abrir un trade.

    NUNCA usa datos de velas futuras — solo la vela actual y los indicadores
    ya calculados (que usan velas pasados).

    Args:
        vela: Series con columnas rsi, ema_fast, ema_slow, vol_ratio, close
        params: dict con rsi_min, rsi_max, vol_ratio_min, ema_gap_min

    Returns:
        bool: True si hay señal de entrada
    """
    tendencia_alcista = vela["ema_fast"] > vela["ema_slow"]
    rsi_ok = params.get("rsi_min", 50) < vela["rsi"] < params.get("rsi_max", 75)
    volumen_ok = vela["vol_ratio"] >= params.get("vol_ratio_min", 0.5)

    # Filtro de separación EMA (evitar mercados laterales)
    # Solo entrar si la distancia entre EMAs es > X% del precio
    ema_gap_min = params.get("ema_gap_min", 0.0)  # default 0 = sin filtro
    if ema_gap_min > 0:
        separacion_ema = (vela["ema_fast"] - vela["ema_slow"]) / vela["close"] * 100
        tendencia_real = separacion_ema > ema_gap_min
    else:
        tendencia_real = True  # sin filtro

    return tendencia_alcista and rsi_ok and volumen_ok and tendencia_real


# -----------------------------------------------------------------------------
# CÁLCULO DE TAMAÑO DE POSICIÓN
# -----------------------------------------------------------------------------


def calcular_posicion(capital_actual, precio_entrada, params):
    """
    Calcula cuánto BTC comprar según las 4 reglas de Coco.

    Args:
        capital_actual: capital disponible en USDT
        precio_entrada: precio de entrada
        params: dict con stop_loss_pct, take_profit_pct

    Returns:
        dict con risk_amount, qty_btc, sl_price, tp_price, rr_ratio
        o None si el R:R no cumple el mínimo
    """
    # Regla 1: riesgo máximo 2% del capital actual
    risk_amount = capital_actual * RULES["max_risk_pct"]

    # SL y TP según config
    stop_loss_pct = params.get("stop_loss_pct", 0.01)
    take_profit_pct = params.get("take_profit_pct", 0.02)

    sl_price = precio_entrada * (1 - stop_loss_pct)
    tp_price = precio_entrada * (1 + take_profit_pct)

    # Regla 2: verificar que R:R es al menos 1:2
    distancia_sl = precio_entrada - sl_price
    distancia_tp = tp_price - precio_entrada
    rr_ratio = distancia_tp / distancia_sl if distancia_sl > 0 else 0

    if rr_ratio < RULES["min_rr_ratio"]:
        return None

    # Cantidad de BTC: dividimos el riesgo en USDT por la pérdida por BTC
    qty_btc = risk_amount / distancia_sl

    return {
        "risk_amount": round(risk_amount, 4),
        "qty_btc": round(qty_btc, 8),
        "sl_price": round(sl_price, 2),
        "tp_price": round(tp_price, 2),
        "rr_ratio": round(rr_ratio, 2),
    }


# -----------------------------------------------------------------------------
# BÚSQUEDA DE SALIDA — AVANZA VELA A VELA HASTA ENCONTRAR SL O TP
# -----------------------------------------------------------------------------


def buscar_salida(df, idx_entrada, sl_price, tp_price):
    """
    A partir de la vela de entrada, avanza vela por vela buscando cuál
    toca primero el SL o el TP.

    Compara el HIGH de cada vela con el TP, y el LOW con el SL.
    Si en la misma vela se tocan ambos, se asume SL (peor caso, conservador).

    Args:
        df: DataFrame completo con todas las velas
        idx_entrada: índice (timestamp) de la vela de entrada
        sl_price: precio del stop loss
        tp_price: precio del take profit

    Returns:
        tuple: (idx_salida, precio_salida, resultado, velas_abierto)
    """
    indices = df.index.tolist()
    pos_entrada = indices.index(idx_entrada)

    for i in range(pos_entrada + 1, len(indices)):
        idx = indices[i]
        vela = df.loc[idx]

        sl_tocado = vela["low"] <= sl_price
        tp_tocado = vela["high"] >= tp_price

        if sl_tocado and tp_tocado:
            # Ambos en la misma vela → asumimos SL (conservador)
            return idx, sl_price, "LOSS", i - pos_entrada

        if tp_tocado:
            return idx, tp_price, "WIN", i - pos_entrada

        if sl_tocado:
            return idx, sl_price, "LOSS", i - pos_entrada

    # Si llegan al final de los datos sin resolverse → cierre por fin de datos
    ultimo_idx = indices[-1]
    precio_cierre = df.loc[ultimo_idx, "close"]
    resultado = "WIN" if precio_cierre >= tp_price else "LOSS"
    return ultimo_idx, precio_cierre, resultado, len(indices) - pos_entrada


# -----------------------------------------------------------------------------
# COSTO TOTAL DE UN TRADE
# -----------------------------------------------------------------------------


def aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida):
    """
    Descuenta comisiones y slippage del PnL bruto.

    Args:
        pnl_bruto: ganancia/pérdida antes de costos
        qty_btc: cantidad de BTC operada
        precio_entrada: precio de compra
        precio_salida: precio de venta

    Returns:
        float: PnL neto después de costos
    """
    # Comisión de apertura + slippage entrada
    costo_entrada = (
        precio_entrada * qty_btc * (COSTS["commission_pct"] + COSTS["slippage_pct"])
    )
    # Comisión de cierre + slippage salida
    costo_salida = (
        precio_salida * qty_btc * (COSTS["commission_pct"] + COSTS["slippage_pct"])
    )
    return round(pnl_bruto - costo_entrada - costo_salida, 4)


# -----------------------------------------------------------------------------
# MÉTRICAS DE RENDIMIENTO
# -----------------------------------------------------------------------------


def calcular_metricas(trades, capital_final):
    """
    Calcula todas las métricas relevantes del backtest.

    IMPORTANTE - Sharpe Ratio:
    - Crypto opera 365 días/año (no 252 como el mercado de acciones)
    - Usamos retornos DIARIOS (no por trade) para reducir ruido
    - Fórmula: (retorno_medio_diario / std_diaria) * sqrt(365)

    Args:
        trades: lista de dicts con datos de cada trade
        capital_final: capital al final del backtest

    Returns:
        dict con todas las métricas
    """
    if not trades:
        return {}

    df_t = pd.DataFrame(trades)
    wins = df_t[df_t["resultado"] == "WIN"]
    losses = df_t[df_t["resultado"] == "LOSS"]

    total = len(df_t)
    n_wins = len(wins)
    n_loss = len(losses)

    win_rate = n_wins / total if total > 0 else 0
    pnl_total = capital_final - INITIAL_CAPITAL
    pnl_pct = (pnl_total / INITIAL_CAPITAL) * 100

    # Ganancia promedio vs pérdida promedio
    avg_win = wins["pnl_neto"].mean() if n_wins > 0 else 0
    avg_loss = losses["pnl_neto"].mean() if n_loss > 0 else 0
    profit_factor = (
        abs(wins["pnl_neto"].sum() / losses["pnl_neto"].sum())
        if n_loss > 0 and losses["pnl_neto"].sum() != 0
        else float("inf")
    )

    # Max Drawdown
    capital_series = [INITIAL_CAPITAL] + df_t["capital_despues"].tolist()
    capital_series = pd.Series(capital_series)
    rolling_max = capital_series.cummax()
    drawdown = (capital_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()

    # Sharpe Ratio (anualizado para crypto, usando retornos DIARIOS)
    # NOTA: Crypto opera 24/7, 365 días/año (no 252 como acciones)
    # Usamos retornos diarios agrupados para reducir el ruido de trades individuales
    df_t["fecha"] = pd.to_datetime(df_t["entrada_fecha"]).dt.date
    retornos_diarios = df_t.groupby("fecha").apply(
        lambda x: x["pnl_neto"].sum() / x["capital_antes"].iloc[0]
    )

    # Llenar los días sin trades con retorno 0.0 para que la desviación estándar sea real
    if len(retornos_diarios) > 1:
        idx = pd.date_range(start=retornos_diarios.index.min(), end=retornos_diarios.index.max())
        retornos_diarios = retornos_diarios.reindex(idx.date, fill_value=0.0)

    if retornos_diarios.std() > 0:
        sharpe = (retornos_diarios.mean() / retornos_diarios.std()) * np.sqrt(365)
    else:
        sharpe = 0

    return {
        "total_trades": total,
        "wins": n_wins,
        "losses": n_loss,
        "win_rate": round(win_rate * 100, 2),
        "capital_inicial": INITIAL_CAPITAL,
        "capital_final": round(capital_final, 2),
        "pnl_total_usdt": round(pnl_total, 2),
        "pnl_pct": round(pnl_pct, 2),
        "avg_win_usdt": round(avg_win, 4),
        "avg_loss_usdt": round(avg_loss, 4),
        "profit_factor": round(profit_factor, 3),
        "max_drawdown_pct": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 3),
        "avg_velas": round(df_t["velas_abierto"].mean(), 1),
        "stops_diarios": int(df_t["stop_diario"].sum()),
    }


# -----------------------------------------------------------------------------
# MOTOR PRINCIPAL — BACKTEST BASE
# -----------------------------------------------------------------------------


def correr_backtest_base(df, params, rules=None, costs=None, initial_capital=None,
                         log_candles=True):
    """
    Motor de backtesting genérico. Recorre todas las velas en orden cronológico.
    Aplica las reglas de Coco antes de cada trade.

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    # Para logging de velas en posición abierta
    _open_trade = None  # {"price": ..., "qty": ..., "capital_antes": ..., "num": ...}

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                if _open_trade:
                    unrealized = (_open_trade["price"] - vela["close"]) if False else \
                        (vela["close"] - _open_trade["price"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if not generar_señal(vela, params):
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="no_signal",
                       indicators={"rsi": round(float(vela["rsi"]), 2),
                                   "ema_fast": round(float(vela["ema_fast"]), 2),
                                   "ema_slow": round(float(vela["ema_slow"]), 2),
                                   "vol_ratio": round(float(vela["vol_ratio"]), 3)})
            i += 1
            continue

        precio_entrada = vela["close"]
        pos = calcular_posicion(capital, precio_entrada, params)

        if pos is None:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="rr_failed")
            i += 1
            continue

        idx_salida, precio_salida, resultado, velas_abierto = buscar_salida(
            df, idx, pos["sl_price"], pos["tp_price"]
        )

        pnl_bruto = (precio_salida - precio_entrada) * pos["qty_btc"]
        pnl_neto = aplicar_costos(pnl_bruto, pos["qty_btc"], precio_entrada, precio_salida)

        capital_antes = capital
        capital += pnl_neto
        capital = round(capital, 4)

        pnl_dia += pnl_neto
        ops_dia += 1

        pnl_dia_pct = pnl_dia / capital_antes
        if pnl_dia_pct <= -rules["daily_stop_pct"]:
            stop_diario = True

        trade_num = len(trades) + 1
        trades.append({
            "trade_num": trade_num,
            "entrada_fecha": vela["datetime_ar"],
            "salida_fecha": df.loc[idx_salida, "datetime_ar"],
            "precio_entrada": precio_entrada,
            "sl_price": pos["sl_price"],
            "tp_price": pos["tp_price"],
            "precio_salida": precio_salida,
            "qty_btc": pos["qty_btc"],
            "rr_ratio": pos["rr_ratio"],
            "capital_antes": capital_antes,
            "risk_amount": pos["risk_amount"],
            "velas_abierto": velas_abierto,
            "resultado": resultado,
            "pnl_bruto": round(pnl_bruto, 4),
            "pnl_neto": pnl_neto,
            "capital_despues": capital,
            "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
            "stop_diario": stop_diario,
            "rsi_entrada": round(vela["rsi"], 2),
            "ema_fast_entrada": round(vela["ema_fast"], 2),
            "ema_slow_entrada": round(vela["ema_slow"], 2),
            "vol_ratio_entrada": round(vela["vol_ratio"], 3),
        })

        logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                   signal="buy", signal_passed=True, trade_num=trade_num,
                   indicators={"rsi": round(float(vela["rsi"]), 2),
                                "vol_ratio": round(float(vela["vol_ratio"]), 3)})

        _open_trade = {"price": precio_entrada, "qty": pos["qty_btc"],
                       "capital_antes": capital_antes, "num": trade_num}
        skip_hasta_idx = idx_salida
        i += 1

    return trades, capital, logger.states


# =============================================================================
# BREAKOUT + ATR TRAILING STOP — NUEVA ESTRATEGIA 4H
# Las funciones de abajo NO modifican nada del motor EMA original.
# =============================================================================


# -----------------------------------------------------------------------------
# CÁLCULO DE INDICADORES PARA BREAKOUT
# -----------------------------------------------------------------------------


def calcular_indicadores_breakout(df, params):
    """
    Calcula indicadores para la estrategia de breakout.
    ATR, EMA de tendencia, volumen ratio, y máximo de N velas.

    Args:
        df: DataFrame con columnas: open, high, low, close, volume_btc
        params: dict con atr_period, ema_trend_period, vol_period, lookback

    Returns:
        DataFrame con columnas adicionales: atr, ema_trend, vol_ratio, high_max
    """
    df = df.copy()

    atr_period = params.get("atr_period", 14)
    ema_trend_period = params.get("ema_trend_period", 50)
    vol_period = params.get("vol_period", 20)
    lookback = params.get("lookback", 20)

    # ATR — Average True Range
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=atr_period, adjust=False).mean()

    # EMA de tendencia (filtro direccional)
    df["ema_trend"] = df["close"].ewm(span=ema_trend_period, adjust=False).mean()

    # Ratio de volumen
    df["vol_sma"] = df["volume_btc"].rolling(window=vol_period).mean()
    df["vol_ratio"] = df["volume_btc"] / df["vol_sma"].replace(0, np.nan)

    # Máximo de las últimas N velas (shift 1 para no incluir la actual)
    df["high_max"] = df["high"].rolling(lookback).max().shift(1)

    # NUEVO: Body Position (para filtro vela fuerte en zona gris ADX)
    df["body_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"]).replace(0, np.nan)
    df["body_position"] = df["body_position"].fillna(0.5)

    # NUEVO: Filtro de ADX (Wilder's smoothing)
    adx_period = params.get("adx_period", 14)
    if adx_period > 0:
        high = df['high']
        low = df['low']
        close = df['close']
        
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        
        plus_dm = pd.Series(plus_dm, index=df.index)
        minus_dm = pd.Series(minus_dm, index=df.index)
        
        tr_adx = tr.copy() # reutilizar True Range del ATR
        
        plus_di = 100 * (plus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / tr_adx.ewm(alpha=1/adx_period, adjust=False).mean())
        minus_di = 100 * (minus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / tr_adx.ewm(alpha=1/adx_period, adjust=False).mean())
        
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
        df['adx'] = dx.ewm(alpha=1/adx_period, adjust=False).mean()
        # ADX slope: diferencia vs vela anterior (shift 1 para evitar lookahead)
        df['adx_prev'] = df['adx'].shift(1)
    else:
        df['adx'] = 100 # Dummy value si no se usa
        df['adx_prev'] = 100

    # NUEVO: Filtro de tendencia diaria
    # Calcula la EMA sobre el close diario (el último de cada fecha)
    # y mapea el valor desplazado (ayer) a las velas de hoy.
    if params.get("use_daily_trend_filter", False):
        ema_trend_daily_period = params.get("ema_trend_daily_period", 20)
        df["date_str"] = df["datetime_ar"].astype(str).str[:10]
        daily_closes = df.groupby("date_str")["close"].last()
        daily_ema = daily_closes.ewm(span=ema_trend_daily_period, adjust=False).mean()
        # IMPORTANTE: shift(1) asegura que las velas 4H de hoy miren la EMA de AYER, evitando lookahead bias
        daily_ema_shifted = daily_ema.shift(1)
        df["ema20_diaria"] = df["date_str"].map(daily_ema_shifted)
        df.drop(columns=["date_str"], inplace=True)
        
        # Eliminar filas sin indicadores válidos incluyendo la EMA diaria
        df.dropna(subset=["atr", "ema_trend", "vol_ratio", "high_max", "ema20_diaria", "adx"], inplace=True)
    else:
        # Eliminar filas sin indicadores válidos
        df.dropna(subset=["atr", "ema_trend", "vol_ratio", "high_max", "adx"], inplace=True)

    return df


# -----------------------------------------------------------------------------
# SEÑAL DE BREAKOUT
# -----------------------------------------------------------------------------


def generar_señal_breakout(vela, params):
    """
    Evalúa si la vela actual cumple condiciones de breakout.

    Condiciones:
    1. Precio cierra por encima del máximo de las últimas N velas
    2. Volumen actual >= vol_ratio_min × promedio
    3. Precio está por encima de la EMA de tendencia
    4. OPCIONAL: Precio por encima de la EMA diaria (filtros tendencia mayor)
    5. OPCIONAL: ADX > adx_filter (filtro de régimen)

    Args:
        vela: Series con columnas close, high_max, vol_ratio, ema_trend, adx
        params: dict con varios parámetros opcionales

    Returns:
        bool: True si hay señal de breakout
    """
    breakout = vela["close"] > vela["high_max"]
    volumen_ok = vela["vol_ratio"] >= params.get("vol_ratio_min", 1.5)
    tendencia = vela["close"] > vela["ema_trend"]

    # Adición Filtro Tendencia Diaria (Opcional)
    if params.get("use_daily_trend_filter", False):
        tendencia_diaria = vela["close"] > vela["ema20_diaria"]
    else:
        tendencia_diaria = True

    # Adición Filtro de Régimen ADX (Opcional)
    if "adx" not in vela:
        adx_ok = True
    else:
        adx_val = vela["adx"]
        adx_filter = params.get("adx_filter", 0)
        adx_zone_low = params.get("adx_zone_low", adx_filter)
        
        if adx_filter > 0:
            if adx_val > adx_filter:
                adx_ok = True
            elif adx_zone_low <= adx_val <= adx_filter:
                adx_zone_body_min = params.get("adx_zone_body_min", 0.70)
                body_position = vela.get("body_position", 0.5)
                adx_ok = body_position >= adx_zone_body_min
            else:
                adx_ok = False
        else:
            adx_ok = True

    # Filtro ADX slope: exigir que ADX esté subiendo (tendencia fortaleciéndose)
    if params.get("adx_slope_filter", False) and "adx_prev" in vela:
        adx_slope_ok = vela["adx"] > vela["adx_prev"]
    else:
        adx_slope_ok = True

    return breakout and volumen_ok and tendencia and tendencia_diaria and adx_ok and adx_slope_ok


# -----------------------------------------------------------------------------
# BÚSQUEDA DE SALIDA CON TRAILING STOP
# -----------------------------------------------------------------------------


def buscar_salida_trailing(df, idx_entrada, sl_price, trail_atr_mult, max_bars=30,
                           breakeven_after_r=None, trail_dynamic=False):
    """
    Avanza vela a vela con trailing stop ATR dinámico.

    El SL sube conforme sube el precio.
    Se cierra cuando el low toca el trailing stop, o por timeout.

    Args:
        df: DataFrame completo con todas las velas
        idx_entrada: índice de la vela de entrada
        sl_price: precio inicial del stop loss (entry - sl_atr_mult × ATR)
        trail_atr_mult: multiplicador del ATR para el trailing stop
        max_bars: máximo velas antes de forzar cierre
        breakeven_after_r: si no es None, mover SL a entrada + comisión cuando
                          ganancia no realizada >= breakeven_after_r × riesgo inicial
        trail_dynamic: si True, adaptar trail_atr_mult según percentil de ATR
                      (ATR bajo → trail más ajustado, ATR alto → trail más ancho)

    Returns:
        tuple: (idx_salida, precio_salida, resultado, velas_abierto)
    """
    indices = df.index.tolist()
    pos_entrada = indices.index(idx_entrada)

    entry_price = df.loc[idx_entrada, "close"]
    initial_risk = entry_price - sl_price  # distancia SL inicial
    highest = entry_price
    current_sl = sl_price
    breakeven_triggered = False

    # Para trailing dinámico: calcular percentiles de ATR en ventana previa
    if trail_dynamic:
        lookback_window = min(pos_entrada, 100)
        if lookback_window > 20:
            atr_history = df.iloc[pos_entrada - lookback_window:pos_entrada]["atr"]
            atr_p25 = atr_history.quantile(0.25)
            atr_p75 = atr_history.quantile(0.75)
        else:
            trail_dynamic = False  # no hay suficiente historia

    for i in range(pos_entrada + 1, min(pos_entrada + max_bars + 1, len(indices))):
        idx = indices[i]
        vela = df.loc[idx]

        # ¿Tocó el trailing stop?
        if vela["low"] <= current_sl:
            resultado = "WIN" if current_sl > entry_price else "LOSS"
            return idx, current_sl, resultado, i - pos_entrada

        # Breakeven: mover SL a entrada cuando ganancia >= X × riesgo
        # breakeven_after_r=0 se trata como desactivado (evita WR=100% artificial)
        if breakeven_after_r and breakeven_after_r > 0 and not breakeven_triggered:
            unrealized = vela["high"] - entry_price
            if unrealized >= breakeven_after_r * initial_risk:
                breakeven_sl = entry_price + (entry_price * 0.003)  # cubrir comisiones RT
                if breakeven_sl > current_sl:
                    current_sl = breakeven_sl
                breakeven_triggered = True

        # Actualizar máximo y trailing
        if vela["high"] > highest:
            highest = vela["high"]
            atr_actual = vela["atr"]

            # Trailing dinámico: ajustar multiplicador según ATR actual
            if trail_dynamic:
                if atr_actual <= atr_p25:
                    effective_mult = trail_atr_mult * 0.8  # ATR bajo → trail ajustado
                elif atr_actual >= atr_p75:
                    effective_mult = trail_atr_mult * 1.2  # ATR alto → trail ancho
                else:
                    effective_mult = trail_atr_mult
            else:
                effective_mult = trail_atr_mult

            trail_distance = effective_mult * atr_actual
            new_sl = highest - trail_distance
            if new_sl > current_sl:
                current_sl = new_sl

    # Timeout: cerrar al cierre de la última vela permitida
    ultimo_i = min(pos_entrada + max_bars, len(indices) - 1)
    ultimo_idx = indices[ultimo_i]
    precio_cierre = df.loc[ultimo_idx, "close"]
    resultado = "WIN" if precio_cierre > entry_price else "LOSS"
    return ultimo_idx, precio_cierre, resultado, ultimo_i - pos_entrada


# -----------------------------------------------------------------------------
# MOTOR PRINCIPAL — BACKTEST BREAKOUT
# -----------------------------------------------------------------------------


def correr_backtest_breakout(df, params, rules=None, costs=None, initial_capital=None,
                             log_candles=True):
    """
    Motor de backtesting para la estrategia de breakout + trailing stop ATR.

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    sl_atr_mult = params.get("sl_atr_mult", 2.5)
    trail_atr_mult = params.get("trail_atr_mult", 0.8)
    max_hold_bars = params.get("max_hold_bars", 30)

    _open_trade = None

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                if _open_trade:
                    unrealized = (vela["close"] - _open_trade["price"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if not generar_señal_breakout(vela, params):
            reason = _filter_reason_breakout(vela, params, stop_diario, ops_dia, rules)
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason,
                       indicators={"atr": round(float(vela["atr"]), 2),
                                   "adx": round(float(vela.get("adx", 0)), 1),
                                   "vol_ratio": round(float(vela["vol_ratio"]), 3),
                                   "ema_trend": round(float(vela["ema_trend"]), 2)})
            i += 1
            continue

        precio_entrada = vela["close"]
        atr_actual = vela["atr"]
        sl_distance = sl_atr_mult * atr_actual

        if sl_distance <= 0:
            i += 1
            continue

        sl_price = precio_entrada - sl_distance

        risk_amount = capital * rules["max_risk_pct"]
        qty_btc = risk_amount / sl_distance

        idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing(
            df, idx, sl_price, trail_atr_mult, max_hold_bars,
            breakeven_after_r=params.get("breakeven_after_r"),
            trail_dynamic=params.get("trail_dynamic", False),
        )

        pnl_bruto = (precio_salida - precio_entrada) * qty_btc
        pnl_neto = aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida)

        capital_antes = capital
        capital += pnl_neto
        capital = round(capital, 4)

        pnl_dia += pnl_neto
        ops_dia += 1

        pnl_dia_pct = pnl_dia / capital_antes
        if pnl_dia_pct <= -rules["daily_stop_pct"]:
            stop_diario = True

        trade_num = len(trades) + 1
        trades.append({
            "trade_num": trade_num,
            "entrada_fecha": vela["datetime_ar"],
            "salida_fecha": df.loc[idx_salida, "datetime_ar"],
            "precio_entrada": precio_entrada,
            "sl_price": round(sl_price, 2),
            "tp_price": 0,
            "precio_salida": round(precio_salida, 2),
            "qty_btc": round(qty_btc, 8),
            "rr_ratio": round(
                (precio_salida - precio_entrada) / sl_distance, 2
            ) if resultado == "WIN" else round(
                (precio_entrada - precio_salida) / sl_distance * -1, 2
            ),
            "capital_antes": capital_antes,
            "risk_amount": round(risk_amount, 4),
            "velas_abierto": velas_abierto,
            "resultado": resultado,
            "pnl_bruto": round(pnl_bruto, 4),
            "pnl_neto": pnl_neto,
            "capital_despues": capital,
            "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
            "stop_diario": stop_diario,
            "rsi_entrada": 0,
            "ema_fast_entrada": 0,
            "ema_slow_entrada": round(vela["ema_trend"], 2),
            "vol_ratio_entrada": round(vela["vol_ratio"], 3),
            "atr_entrada": round(atr_actual, 2),
        })

        logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                   signal="buy", signal_passed=True, trade_num=trade_num,
                   indicators={"atr": round(float(atr_actual), 2),
                                "adx": round(float(vela.get("adx", 0)), 1),
                                "vol_ratio": round(float(vela["vol_ratio"]), 3),
                                "ema_trend": round(float(vela["ema_trend"]), 2),
                                "sl_price": round(float(sl_price), 2)})

        _open_trade = {"price": precio_entrada, "qty": qty_btc,
                       "capital_antes": capital_antes, "num": trade_num}
        skip_hasta_idx = idx_salida
        i += 1

    return trades, capital, logger.states

# =============================================================================
# MEAN REVERSION 4H — NUEVA ESTRATEGIA (CON RSI Y BOLLINGER)
# =============================================================================


# -----------------------------------------------------------------------------
# CÁLCULO DE INDICADORES PARA MEAN REVERSION
# -----------------------------------------------------------------------------


def calcular_indicadores_mr(df, params):
    """
    Calcula indicadores para la estrategia Mean Reversion.
    """
    df = df.copy()

    rsi_period = params.get("rsi_period", 14)
    bb_period = params.get("bb_period", 20)
    bb_std = params.get("bb_std", 2.0)
    atr_period = params.get("atr_period", 14)
    ema_trend_period = params.get("ema_trend_period", 200)

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['bb_mid'] = df['close'].rolling(window=bb_period).mean()
    bb_std_dev = df['close'].rolling(window=bb_period).std()
    df['bb_lower'] = df['bb_mid'] - (bb_std_dev * bb_std)
    df['bb_upper'] = df['bb_mid'] + (bb_std_dev * bb_std)

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=atr_period, adjust=False).mean()

    # EMA de tendencia
    df["ema_trend"] = df["close"].ewm(span=ema_trend_period, adjust=False).mean()

    df.dropna(subset=["rsi", "bb_lower", "atr", "ema_trend"], inplace=True)
    return df


# -----------------------------------------------------------------------------
# SEÑAL DE MEAN REVERSION
# -----------------------------------------------------------------------------


def generar_señal_mr(vela, params):
    """
    Evalúa si la vela actual cumple condiciones de Mean Reversion.
    """
    rsi_oversold = params.get("rsi_oversold", 30)

    # Condición 1: RSI en sobreventa
    cond_rsi = vela["rsi"] < rsi_oversold
    # Condición 2: El precio cerró por debajo de la banda inferior de Bollinger
    cond_bb = vela["close"] < vela["bb_lower"]
    # Condición 3: Filtro de tendencia (el precio debe estar por encima de la EMA de largo plazo para no comprar cuchillos cayendo)
    cond_trend = vela["close"] > vela["ema_trend"]

    return cond_rsi and cond_bb and cond_trend


# -----------------------------------------------------------------------------
# MOTOR PRINCIPAL — BACKTEST MEAN REVERSION
# -----------------------------------------------------------------------------


def correr_backtest_mr(df, params, rules=None, costs=None, initial_capital=None,
                       log_candles=True):
    """
    Motor de backtesting para la estrategia Mean Reversion.

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    sl_atr_mult = params.get("sl_atr_mult", 2.0)
    tp_atr_mult = params.get("tp_atr_mult", 4.0)

    _open_trade = None

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                if _open_trade:
                    unrealized = (vela["close"] - _open_trade["price"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if not generar_señal_mr(vela, params):
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="no_signal",
                       indicators={"rsi": round(float(vela["rsi"]), 2),
                                   "atr": round(float(vela["atr"]), 2),
                                   "bb_lower": round(float(vela["bb_lower"]), 2)})
            i += 1
            continue

        precio_entrada = vela["close"]
        atr_actual = vela["atr"]
        sl_distance = sl_atr_mult * atr_actual
        sl_price = precio_entrada - sl_distance
        tp_distance = tp_atr_mult * atr_actual
        tp_price = precio_entrada + tp_distance

        risk_amount = capital * rules["max_risk_pct"]
        if sl_distance == 0:
            i += 1
            continue
        qty_btc = risk_amount / sl_distance

        idx_salida, precio_salida, resultado, velas_abierto = buscar_salida(
            df, idx, sl_price, tp_price
        )

        pnl_bruto = (precio_salida - precio_entrada) * qty_btc
        pnl_neto = aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida)

        capital_antes = capital
        capital += pnl_neto
        capital = round(capital, 4)

        pnl_dia += pnl_neto
        ops_dia += 1

        pnl_dia_pct = pnl_dia / capital_antes
        if pnl_dia_pct <= -rules["daily_stop_pct"]:
            stop_diario = True

        trade_num = len(trades) + 1
        trades.append({
            "trade_num": trade_num,
            "entrada_fecha": vela["datetime_ar"],
            "salida_fecha": df.loc[idx_salida, "datetime_ar"],
            "precio_entrada": precio_entrada,
            "sl_price": round(sl_price, 2),
            "tp_price": round(tp_price, 2),
            "precio_salida": round(precio_salida, 2),
            "qty_btc": round(qty_btc, 8),
            "rr_ratio": round(tp_distance / sl_distance, 2),
            "capital_antes": capital_antes,
            "risk_amount": round(risk_amount, 4),
            "velas_abierto": velas_abierto,
            "resultado": resultado,
            "pnl_bruto": round(pnl_bruto, 4),
            "pnl_neto": pnl_neto,
            "capital_despues": capital,
            "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
            "stop_diario": stop_diario,
            "rsi_entrada": round(vela["rsi"], 2),
            "ema_fast_entrada": 0,
            "ema_slow_entrada": round(vela["ema_trend"], 2),
            "vol_ratio_entrada": 0,
            "atr_entrada": round(atr_actual, 2),
        })

        logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                   signal="buy", signal_passed=True, trade_num=trade_num,
                   indicators={"rsi": round(float(vela["rsi"]), 2),
                                "atr": round(float(atr_actual), 2),
                                "bb_lower": round(float(vela["bb_lower"]), 2)})

        _open_trade = {"price": precio_entrada, "qty": qty_btc,
                       "capital_antes": capital_antes, "num": trade_num}
        skip_hasta_idx = idx_salida
        i += 1

    return trades, capital, logger.states


# =============================================================================
# BREAKDOWN SHORT 4H — ESTRATEGIA ESPEJO PARA SHORTS
# Las funciones de abajo NO modifican nada del motor Breakout original.
# =============================================================================


def calcular_indicadores_breakdown(df, params):
    """
    Calcula indicadores para la estrategia de breakdown (short).
    Reutiliza la misma lógica que calcular_indicadores_breakout pero agrega
    low_min (mínimo de las últimas N velas) en lugar de high_max.
    """
    df = df.copy()

    atr_period = params.get("atr_period", 14)
    ema_trend_period = params.get("ema_trend_period", 50)
    vol_period = params.get("vol_period", 20)
    lookback = params.get("lookback", 20)

    # ATR — Average True Range
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=atr_period, adjust=False).mean()

    # EMA de tendencia (filtro direccional)
    df["ema_trend"] = df["close"].ewm(span=ema_trend_period, adjust=False).mean()

    # Ratio de volumen
    df["vol_sma"] = df["volume_btc"].rolling(window=vol_period).mean()
    df["vol_ratio"] = df["volume_btc"] / df["vol_sma"].replace(0, np.nan)

    # Mínimo de las últimas N velas (shift 1 para no incluir la actual)
    df["low_min"] = df["low"].rolling(lookback).min().shift(1)

    # ADX (Wilder's smoothing)
    adx_period = params.get("adx_period", 14)
    if adx_period > 0:
        high = df['high']
        low = df['low']

        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_dm = pd.Series(plus_dm, index=df.index)
        minus_dm = pd.Series(minus_dm, index=df.index)

        tr_adx = tr.copy()

        plus_di = 100 * (plus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / tr_adx.ewm(alpha=1/adx_period, adjust=False).mean())
        minus_di = 100 * (minus_dm.ewm(alpha=1/adx_period, adjust=False).mean() / tr_adx.ewm(alpha=1/adx_period, adjust=False).mean())

        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
        df['adx'] = dx.ewm(alpha=1/adx_period, adjust=False).mean()
    else:
        df['adx'] = 100

    # Filtro de tendencia diaria
    if params.get("use_daily_trend_filter", False):
        ema_trend_daily_period = params.get("ema_trend_daily_period", 20)
        df["date_str"] = df["datetime_ar"].astype(str).str[:10]
        daily_closes = df.groupby("date_str")["close"].last()
        daily_ema = daily_closes.ewm(span=ema_trend_daily_period, adjust=False).mean()
        daily_ema_shifted = daily_ema.shift(1)
        df["ema20_diaria"] = df["date_str"].map(daily_ema_shifted)
        df.drop(columns=["date_str"], inplace=True)

        df.dropna(subset=["atr", "ema_trend", "vol_ratio", "low_min", "ema20_diaria", "adx"], inplace=True)
    else:
        df.dropna(subset=["atr", "ema_trend", "vol_ratio", "low_min", "adx"], inplace=True)

    return df


def generar_señal_breakdown(vela, params):
    """
    Espejo exacto de generar_señal_breakout pero invertido para shorts.

    Condiciones:
    1. close < low_min (precio rompe el mínimo de las últimas N velas)
    2. vol_ratio >= vol_ratio_min (volumen confirma el movimiento)
    3. close < ema_trend (precio por debajo de EMA50 — tendencia bajista)
    4. adx >= adx_filter (mercado con tendencia fuerte)
    5. close < ema20_diaria (contexto macro bajista)
    """
    breakdown = vela["close"] < vela["low_min"]
    volumen_ok = vela["vol_ratio"] >= params.get("vol_ratio_min", 1.5)
    tendencia = vela["close"] < vela["ema_trend"]

    if params.get("use_daily_trend_filter", False):
        tendencia_diaria = vela["close"] < vela["ema20_diaria"]
    else:
        tendencia_diaria = True

    adx_filter = params.get("adx_filter", 0)
    if adx_filter > 0 and "adx" in vela:
        adx_ok = vela["adx"] >= adx_filter
    else:
        adx_ok = True

    return breakdown and volumen_ok and tendencia and tendencia_diaria and adx_ok


def buscar_salida_trailing_short(df, idx_entrada, sl_price, trail_atr_mult, max_bars=30):
    """
    Trailing stop ATR dinámico para posición SHORT.
    El SL baja conforme baja el precio. Se cierra cuando el high toca el SL.
    """
    indices = df.index.tolist()
    pos_entrada = indices.index(idx_entrada)

    precio_entrada = df.loc[idx_entrada, "close"]
    lowest = precio_entrada
    current_sl = sl_price

    for i in range(pos_entrada + 1, min(pos_entrada + max_bars + 1, len(indices))):
        idx = indices[i]
        vela = df.loc[idx]

        if vela["high"] >= current_sl:
            resultado = "WIN" if current_sl < precio_entrada else "LOSS"
            return idx, current_sl, resultado, i - pos_entrada

        if vela["low"] < lowest:
            lowest = vela["low"]
            atr_actual = vela["atr"]
            trail_distance = trail_atr_mult * atr_actual
            new_sl = lowest + trail_distance
            if new_sl < current_sl:
                current_sl = new_sl

    ultimo_i = min(pos_entrada + max_bars, len(indices) - 1)
    ultimo_idx = indices[ultimo_i]
    precio_cierre = df.loc[ultimo_idx, "close"]
    resultado = "WIN" if precio_cierre < precio_entrada else "LOSS"
    return ultimo_idx, precio_cierre, resultado, ultimo_i - pos_entrada


def correr_backtest_breakdown(df, params, rules=None, costs=None, initial_capital=None,
                              log_candles=True):
    """
    Motor de backtesting para breakdown (short) + trailing stop ATR.

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    sl_atr_mult = params.get("sl_atr_mult", 2.5)
    trail_atr_mult = params.get("trail_atr_mult", 2.5)
    max_hold_bars = params.get("max_hold_bars", 30)

    _open_trade = None

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                if _open_trade:
                    # SHORT: profit when price goes DOWN
                    unrealized = (_open_trade["price"] - vela["close"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=-1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if not generar_señal_breakdown(vela, params):
            reason = _filter_reason_breakdown(vela, params, stop_diario, ops_dia, rules)
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason,
                       indicators={"atr": round(float(vela["atr"]), 2),
                                   "adx": round(float(vela.get("adx", 0)), 1),
                                   "vol_ratio": round(float(vela["vol_ratio"]), 3)})
            i += 1
            continue

        precio_entrada = vela["close"]
        atr_actual = vela["atr"]
        sl_distance = sl_atr_mult * atr_actual
        sl_price = precio_entrada + sl_distance

        risk_amount = capital * rules["max_risk_pct"]
        qty_btc = risk_amount / sl_distance

        idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing_short(
            df, idx, sl_price, trail_atr_mult, max_hold_bars
        )

        pnl_bruto = (precio_entrada - precio_salida) * qty_btc
        pnl_neto = aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida)

        capital_antes = capital
        capital += pnl_neto
        capital = round(capital, 4)

        pnl_dia += pnl_neto
        ops_dia += 1

        pnl_dia_pct = pnl_dia / capital_antes
        if pnl_dia_pct <= -rules["daily_stop_pct"]:
            stop_diario = True

        trade_num = len(trades) + 1
        trades.append({
            "trade_num": trade_num,
            "entrada_fecha": vela["datetime_ar"],
            "salida_fecha": df.loc[idx_salida, "datetime_ar"],
            "precio_entrada": precio_entrada,
            "sl_price": round(sl_price, 2),
            "tp_price": 0,
            "precio_salida": round(precio_salida, 2),
            "qty_btc": round(qty_btc, 8),
            "rr_ratio": round(
                (precio_entrada - precio_salida) / sl_distance, 2
            ) if resultado == "WIN" else round(
                (precio_salida - precio_entrada) / sl_distance * -1, 2
            ),
            "capital_antes": capital_antes,
            "risk_amount": round(risk_amount, 4),
            "velas_abierto": velas_abierto,
            "resultado": resultado,
            "pnl_bruto": round(pnl_bruto, 4),
            "pnl_neto": pnl_neto,
            "capital_despues": capital,
            "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
            "stop_diario": stop_diario,
            "rsi_entrada": 0,
            "ema_fast_entrada": 0,
            "ema_slow_entrada": round(vela["ema_trend"], 2),
            "vol_ratio_entrada": round(vela["vol_ratio"], 3),
            "atr_entrada": round(atr_actual, 2),
            "direction": "SHORT",
        })

        logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                   signal="sell", signal_passed=True, trade_num=trade_num,
                   indicators={"atr": round(float(atr_actual), 2),
                                "adx": round(float(vela.get("adx", 0)), 1),
                                "vol_ratio": round(float(vela["vol_ratio"]), 3)})

        _open_trade = {"price": precio_entrada, "qty": qty_btc,
                       "capital_antes": capital_antes, "num": trade_num}
        skip_hasta_idx = idx_salida
        i += 1

    return trades, capital, logger.states


# =============================================================================
# RETEST ENTRY — PULLBACK AL NIVEL ROTO
# Las funciones de abajo NO modifican nada del motor Breakout original.
# Hipótesis: entrar en el pullback al nivel roto mejora el precio de entrada,
# reduce la distancia real al SL y sube el payout vs entrar en la vela de breakout.
# =============================================================================


def detectar_breakout_pendiente(vela, params):
    """
    Misma lógica de calidad que generar_señal_breakout() pero en lugar de
    ejecutar la entrada, marca que hay un breakout válido esperando retest.

    Retorna (True, nivel_breakout) si todos los filtros pasan.
    El nivel_breakout es el high_max que fue roto — ese es el soporte al que
    esperamos que el precio regrese.

    Args:
        vela: Series con columnas close, high_max, vol_ratio, ema_trend,
              adx, ema20_diaria (si use_daily_trend_filter)
        params: mismos parámetros que generar_señal_breakout

    Returns:
        tuple: (bool, float) — (hay_breakout_pendiente, nivel_breakout)
    """
    breakout = vela["close"] > vela["high_max"]
    volumen_ok = vela["vol_ratio"] >= params.get("vol_ratio_min", 1.5)
    tendencia = vela["close"] > vela["ema_trend"]

    if params.get("use_daily_trend_filter", False):
        tendencia_diaria = vela["close"] > vela["ema20_diaria"]
    else:
        tendencia_diaria = True

    adx_filter = params.get("adx_filter", 0)
    if adx_filter > 0 and "adx" in vela:
        adx_ok = vela["adx"] >= adx_filter
    else:
        adx_ok = True

    es_valido = breakout and volumen_ok and tendencia and tendencia_diaria and adx_ok
    nivel = float(vela["high_max"]) if es_valido else 0.0
    return es_valido, nivel


def detectar_retest(vela, nivel_breakout, params):
    """
    Confirma que la vela actual es un retest válido del nivel roto.

    Condiciones:
    1. vela["low"] <= nivel_breakout  — el precio tocó o cruzó el nivel
    2. vela["close"] > nivel_breakout — pero cerró por encima (soporte confirmado)
    3. vela["close"] > vela["ema_trend"] — sigue sobre la EMA50 (tendencia intacta)
    4. vela["close"] > vela["ema20_diaria"] — sigue sobre EMA20 diaria (si aplica)

    Args:
        vela: Series con los indicadores de la vela candidata
        nivel_breakout: float — el high_max que fue roto (nivel de soporte esperado)
        params: dict con use_daily_trend_filter

    Returns:
        bool: True si el retest está confirmado y se puede entrar
    """
    toco_nivel = vela["low"] <= nivel_breakout
    cerro_arriba = vela["close"] > nivel_breakout
    sobre_ema50 = vela["close"] > vela["ema_trend"]

    if params.get("use_daily_trend_filter", False):
        sobre_ema_diaria = vela["close"] > vela["ema20_diaria"]
    else:
        sobre_ema_diaria = True

    return toco_nivel and cerro_arriba and sobre_ema50 and sobre_ema_diaria


def correr_backtest_retest(df, params, rules=None, costs=None, initial_capital=None,
                           log_candles=True):
    """
    Motor de backtesting para la estrategia Retest Entry.

    Dos fases por iteración:
    FASE 1 — Buscar breakout válido (detectar_breakout_pendiente).
             Una vez detectado, guardar el nivel y esperar retest.
    FASE 2 — Monitorear las siguientes max_retest_bars velas buscando
             el pullback (detectar_retest).
             - Si el retest se confirma → entrar al close de esa vela con la
               lógica de posición de V2 (SL = sl_atr_mult × ATR, trailing).
             - Si pasan max_retest_bars sin retest → cancelar el setup.
             - Si el precio sube más de un ATR por encima del breakout antes
               del retest → también cancelar (el setup ya no es un pullback).

    Reglas idénticas a correr_backtest_breakout:
    - Riesgo 2% del capital actual
    - Stop diario 6%
    - No lookahead bias

    Args:
        df: DataFrame con indicadores de breakout ya calculados
            (calcular_indicadores_breakout con use_daily_trend_filter si aplica)
        params: dict con parámetros de la estrategia (debe incluir max_retest_bars)
        rules: dict con reglas de riesgo
        costs: dict con costos de trading
        initial_capital: capital inicial

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    sl_atr_mult = params.get("sl_atr_mult", 2.5)
    trail_atr_mult = params.get("trail_atr_mult", 2.5)
    max_hold_bars = params.get("max_hold_bars", 30)
    max_retest_bars = params.get("max_retest_bars", 5)

    breakout_pendiente = False
    nivel_breakout = 0.0
    velas_esperando = 0
    idx_breakout = None

    _open_trade = None

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                breakout_pendiente = False
                if _open_trade:
                    unrealized = (vela["close"] - _open_trade["price"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if breakout_pendiente:
            velas_esperando += 1
            nivel_cancelacion = nivel_breakout + vela["atr"]
            if vela["close"] > nivel_cancelacion:
                breakout_pendiente = False
                logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                           signal_filtered=True, filter_reason="retest_cancelled")
            elif velas_esperando > max_retest_bars:
                breakout_pendiente = False
                logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                           signal_filtered=True, filter_reason="retest_timeout")
            elif detectar_retest(vela, nivel_breakout, params):
                precio_entrada = vela["close"]
                atr_actual = vela["atr"]
                sl_distance = sl_atr_mult * atr_actual
                sl_price = precio_entrada - sl_distance

                risk_amount = capital * rules["max_risk_pct"]
                qty_btc = risk_amount / sl_distance

                idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing(
                    df, idx, sl_price, trail_atr_mult, max_hold_bars,
                    breakeven_after_r=params.get("breakeven_after_r"),
                    trail_dynamic=params.get("trail_dynamic", False),
                )

                pnl_bruto = (precio_salida - precio_entrada) * qty_btc
                pnl_neto = aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida)

                capital_antes = capital
                capital += pnl_neto
                capital = round(capital, 4)

                pnl_dia += pnl_neto
                ops_dia += 1

                pnl_dia_pct = pnl_dia / capital_antes
                if pnl_dia_pct <= -rules["daily_stop_pct"]:
                    stop_diario = True

                trade_num = len(trades) + 1
                trades.append({
                    "trade_num": trade_num,
                    "entrada_fecha": vela["datetime_ar"],
                    "salida_fecha": df.loc[idx_salida, "datetime_ar"],
                    "precio_entrada": precio_entrada,
                    "nivel_breakout": round(nivel_breakout, 2),
                    "sl_price": round(sl_price, 2),
                    "tp_price": 0,
                    "precio_salida": round(precio_salida, 2),
                    "qty_btc": round(qty_btc, 8),
                    "rr_ratio": round(
                        (precio_salida - precio_entrada) / sl_distance, 2
                    ) if resultado == "WIN" else round(
                        (precio_entrada - precio_salida) / sl_distance * -1, 2
                    ),
                    "capital_antes": capital_antes,
                    "risk_amount": round(risk_amount, 4),
                    "velas_abierto": velas_abierto,
                    "velas_esperando_retest": velas_esperando,
                    "resultado": resultado,
                    "pnl_bruto": round(pnl_bruto, 4),
                    "pnl_neto": pnl_neto,
                    "capital_despues": capital,
                    "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
                    "stop_diario": stop_diario,
                    "rsi_entrada": 0,
                    "ema_fast_entrada": 0,
                    "ema_slow_entrada": round(vela["ema_trend"], 2),
                    "vol_ratio_entrada": round(vela["vol_ratio"], 3),
                    "atr_entrada": round(atr_actual, 2),
                })

                logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                           signal="buy", signal_passed=True, trade_num=trade_num,
                           indicators={"atr": round(float(atr_actual), 2),
                                        "nivel_breakout": round(float(nivel_breakout), 2)})

                _open_trade = {"price": precio_entrada, "qty": qty_btc,
                               "capital_antes": capital_antes, "num": trade_num}
                breakout_pendiente = False
                skip_hasta_idx = idx_salida
                i += 1
                continue
            else:
                logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                           signal_filtered=True, filter_reason="waiting_retest")
                i += 1
                continue

        hay_breakout, nivel = detectar_breakout_pendiente(vela, params)
        if hay_breakout:
            breakout_pendiente = True
            nivel_breakout = nivel
            velas_esperando = 0
            idx_breakout = idx
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal="breakout_detected", filter_reason="waiting_retest")
        else:
            reason = _filter_reason_breakout(vela, params, stop_diario, ops_dia, rules)
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason)

        i += 1

    return trades, capital, logger.states


# =============================================================================
# ENTRADA HÍBRIDA — RETEST PREFERIDO, BREAKOUT FALLBACK
# NO modifica ninguna función existente.
# Hipótesis: mismo volumen de trades que V2 (~18), pero con precio de entrada
# mejorado en los casos donde hay retest. WR y payout suben sin perder señales.
# =============================================================================


def correr_backtest_hibrido(df, params, rules=None, costs=None, initial_capital=None,
                            log_candles=True):
    """
    Motor híbrido: detecta un breakout válido y espera max_retest_bars velas
    buscando un retest del nivel roto. Si no hay retest → fallback breakout.

    Returns:
        tuple: (lista de trades, capital_final, candle_states)
    """
    rules = rules or RULES
    costs = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual = None
    pnl_dia = 0.0
    ops_dia = 0
    stop_diario = False
    skip_hasta_idx = None

    sl_atr_mult = params.get("sl_atr_mult", 2.5)
    trail_atr_mult = params.get("trail_atr_mult", 2.5)
    max_hold_bars = params.get("max_hold_bars", 30)
    max_retest_bars = params.get("max_retest_bars", 5)

    modo_espera = False
    nivel_breakout = 0.0
    precio_breakout_close = 0.0
    idx_breakout = None
    velas_esperando = 0

    _open_trade = None

    while i < len(indices):
        idx = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual = fecha_vela
            pnl_dia = 0.0
            ops_dia = 0
            stop_diario = False

        if skip_hasta_idx is not None:
            if idx <= skip_hasta_idx:
                modo_espera = False
                if _open_trade:
                    unrealized = (vela["close"] - _open_trade["price"]) * _open_trade["qty"]
                    unrealized_net = aplicar_costos(unrealized, _open_trade["qty"],
                                                    _open_trade["price"], vela["close"])
                    logger.log(bar_index=i, timestamp=idx,
                               equity=_open_trade["capital_antes"] + unrealized_net,
                               in_position=1, trade_num=_open_trade["num"])
                i += 1
                continue
            else:
                skip_hasta_idx = None
                _open_trade = None

        if stop_diario:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        if ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="max_daily_ops")
            i += 1
            continue

        if modo_espera:
            velas_esperando += 1
            retest_confirmado = detectar_retest(vela, nivel_breakout, params)

            if retest_confirmado:
                precio_entrada = vela["close"]
                entrada_tipo = "retest"
            elif velas_esperando >= max_retest_bars:
                precio_entrada = vela["close"]
                entrada_tipo = "breakout_fallback"
            else:
                logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                           signal_filtered=True, filter_reason="waiting_retest")
                i += 1
                continue

            atr_actual = vela["atr"]
            sl_distance = sl_atr_mult * atr_actual
            sl_price = precio_entrada - sl_distance

            risk_amount = capital * rules["max_risk_pct"]
            qty_btc = risk_amount / sl_distance

            idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing(
                df, idx, sl_price, trail_atr_mult, max_hold_bars,
                breakeven_after_r=params.get("breakeven_after_r"),
                trail_dynamic=params.get("trail_dynamic", False),
            )

            pnl_bruto = (precio_salida - precio_entrada) * qty_btc
            pnl_neto = aplicar_costos(pnl_bruto, qty_btc, precio_entrada, precio_salida)

            capital_antes = capital
            capital += pnl_neto
            capital = round(capital, 4)

            pnl_dia += pnl_neto
            ops_dia += 1

            pnl_dia_pct = pnl_dia / capital_antes
            if pnl_dia_pct <= -rules["daily_stop_pct"]:
                stop_diario = True

            trade_num = len(trades) + 1
            trades.append({
                "trade_num": trade_num,
                "entrada_fecha": vela["datetime_ar"],
                "salida_fecha": df.loc[idx_salida, "datetime_ar"],
                "entrada_tipo": entrada_tipo,
                "precio_entrada": precio_entrada,
                "precio_breakout": round(precio_breakout_close, 2),
                "nivel_breakout": round(nivel_breakout, 2),
                "sl_price": round(sl_price, 2),
                "tp_price": 0,
                "precio_salida": round(precio_salida, 2),
                "qty_btc": round(qty_btc, 8),
                "rr_ratio": round(
                    (precio_salida - precio_entrada) / sl_distance, 2
                ) if resultado == "WIN" else round(
                    (precio_entrada - precio_salida) / sl_distance * -1, 2
                ),
                "capital_antes": capital_antes,
                "risk_amount": round(risk_amount, 4),
                "velas_abierto": velas_abierto,
                "velas_esperando_retest": velas_esperando,
                "resultado": resultado,
                "pnl_bruto": round(pnl_bruto, 4),
                "pnl_neto": pnl_neto,
                "capital_despues": capital,
                "pnl_dia_pct": round(pnl_dia_pct * 100, 2),
                "stop_diario": stop_diario,
                "rsi_entrada": 0,
                "ema_fast_entrada": 0,
                "ema_slow_entrada": round(vela["ema_trend"], 2),
                "vol_ratio_entrada": round(vela["vol_ratio"], 3),
                "atr_entrada": round(atr_actual, 2),
            })

            logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                       signal="buy", signal_passed=True, trade_num=trade_num,
                       indicators={"atr": round(float(atr_actual), 2),
                                    "entrada_tipo": entrada_tipo})

            _open_trade = {"price": precio_entrada, "qty": qty_btc,
                           "capital_antes": capital_antes, "num": trade_num}
            modo_espera = False
            skip_hasta_idx = idx_salida
            i += 1
            continue

        if generar_señal_breakout(vela, params):
            modo_espera = True
            nivel_breakout = float(vela["high_max"])
            precio_breakout_close = float(vela["close"])
            idx_breakout = idx
            velas_esperando = 0
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal="breakout_detected", filter_reason="waiting_retest")
        else:
            reason = _filter_reason_breakout(vela, params, stop_diario, ops_dia, rules)
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason)

        i += 1

    return trades, capital, logger.states


# =============================================================================
# MOTOR: FUNDING RATE REVERSION
# =============================================================================

def _cargar_funding_rates(symbol="BTCUSDT"):
    """Carga todos los funding rates del símbolo desde la DB."""
    conn = sqlite3.connect(UNIFIED_DB)
    df = pd.read_sql_query(
        "SELECT timestamp, rate FROM funding_rates WHERE symbol=? ORDER BY timestamp",
        conn, params=(symbol,)
    )
    conn.close()
    df["timestamp"] = df["timestamp"].astype(int)
    df = df.set_index("timestamp")
    return df


def calcular_indicadores_funding(df, params):
    """
    Indicadores para Funding Rate Reversion.
    Merge por timestamp: cada vela hereda el funding rate vigente más reciente.
    """
    df = df.copy()

    atr_period       = params.get("atr_period", 14)
    ema_macro_period = params.get("ema_macro_period", 200)
    ema_trend_period = params.get("ema_trend_period", 50)
    adx_period       = params.get("adx_period", 14)

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"]  - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.ewm(span=atr_period, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=ema_trend_period, adjust=False).mean()

    df["date_str"] = df["datetime_ar"].astype(str).str[:10]
    daily_closes = df.groupby("date_str")["close"].last()
    daily_ema    = daily_closes.ewm(span=ema_macro_period, adjust=False).mean()
    df["ema_macro_diaria"] = df["date_str"].map(daily_ema.shift(1))
    df.drop(columns=["date_str"], inplace=True)

    if adx_period > 0:
        high, low = df["high"], df["low"]
        up_move   = high - high.shift(1)
        down_move = low.shift(1) - low
        plus_dm   = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
        minus_dm  = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
        alpha     = 1 / adx_period
        plus_di   = 100 * (plus_dm.ewm(alpha=alpha, adjust=False).mean() / tr.ewm(alpha=alpha, adjust=False).mean())
        minus_di  = 100 * (minus_dm.ewm(alpha=alpha, adjust=False).mean() / tr.ewm(alpha=alpha, adjust=False).mean())
        dx        = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
        df["adx"] = dx.ewm(alpha=alpha, adjust=False).mean()
    else:
        df["adx"] = 100.0

    fr = _cargar_funding_rates()
    candle_ts      = df.index.values
    funding_ts     = fr.index.values
    funding_rates  = fr["rate"].values
    idx_match      = np.searchsorted(funding_ts, candle_ts, side="right") - 1
    idx_match      = np.clip(idx_match, 0, len(funding_rates) - 1)
    df["funding_rate"] = funding_rates[idx_match]

    threshold = params.get("neg_funding_threshold", -0.0001)
    df["funding_negative"] = (df["funding_rate"] < threshold).astype(int)

    neg = df["funding_negative"].shift(1).fillna(0)
    racha = []
    count = 0
    for v in neg:
        if v == 1:
            count += 1
        else:
            count = 0
        racha.append(count)
    df["funding_neg_streak"] = racha

    df.dropna(subset=["atr", "ema_trend", "ema_macro_diaria", "adx"], inplace=True)
    return df


def correr_backtest_funding_reversion(df, params, rules=None, costs=None,
                                       initial_capital=None, log_candles=True):
    """
    Backtest Funding Rate Reversion (sistema independiente).
    Entra long cuando: macro alcista + funding negativo N períodos + precio en corrección.
    """
    rules           = rules or RULES
    costs           = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual     = None
    pnl_dia        = 0.0
    ops_dia        = 0
    stop_diario    = False
    skip_hasta_idx = None

    sl_atr_mult    = params.get("sl_atr_mult", 2.0)
    trail_atr_mult = params.get("trail_atr_mult", 2.5)
    max_hold_bars  = params.get("max_hold_bars", 30)
    min_neg_streak = params.get("min_neg_streak", 2)
    adx_filter     = params.get("adx_filter", 0)
    breakeven_r    = params.get("breakeven_after_r", None)

    while i < len(indices):
        idx  = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual  = fecha_vela
            pnl_dia     = 0.0
            ops_dia     = 0
            stop_diario = False

        if skip_hasta_idx is not None and idx <= skip_hasta_idx:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=1)
            i += 1
            continue

        if stop_diario or ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        macro_ok  = vela["close"] > vela["ema_macro_diaria"]
        streak_ok = vela["funding_neg_streak"] >= min_neg_streak
        require_pullback = params.get("require_pullback", False)
        pullback  = (vela["close"] < vela["ema_trend"]) if require_pullback else True
        adx_ok    = (adx_filter == 0) or (vela["adx"] >= adx_filter)

        if macro_ok and streak_ok and pullback and adx_ok:
            entry_price  = float(vela["close"])
            atr_actual   = float(vela["atr"])
            sl_price     = entry_price - sl_atr_mult * atr_actual
            riesgo       = entry_price - sl_price
            if riesgo <= 0:
                i += 1
                continue

            qty_btc = (capital * rules["max_risk_pct"]) / riesgo
            costo   = entry_price * qty_btc * (costs["commission_pct"] + costs["slippage_pct"])
            capital -= costo
            trade_num = len(trades) + 1
            ops_dia  += 1

            idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing(
                df, idx, sl_price, trail_atr_mult, max_hold_bars,
                breakeven_after_r=breakeven_r
            )

            pnl_bruto    = (precio_salida - entry_price) * qty_btc
            costo_salida = precio_salida * qty_btc * (costs["commission_pct"] + costs["slippage_pct"])
            pnl_neto     = pnl_bruto - costo_salida
            capital_antes = capital
            capital      += pnl_neto
            if capital <= 0:
                capital = 0.0

            pnl_pct  = pnl_neto / capital_antes * 100
            pnl_dia += pnl_neto

            if pnl_dia / (capital_antes + abs(pnl_dia)) < -rules["daily_stop_pct"]:
                stop_diario = True

            trades.append({
                "trade_num"      : trade_num,
                "direction"      : "LONG",
                "entrada_fecha"  : vela.get("datetime_ar", str(idx)),
                "salida_fecha"   : df.loc[idx_salida, "datetime_ar"] if idx_salida in df.index else str(idx_salida),
                "precio_entrada" : entry_price,
                "precio_salida"  : precio_salida,
                "qty_btc"        : round(qty_btc, 8),
                "resultado"      : resultado,
                "pnl_neto"       : round(pnl_neto, 4),
                "pnl_pct"        : round(pnl_pct, 4),
                "capital_antes"  : round(capital_antes, 4),
                "capital_despues": round(capital, 4),
                "velas_abierto"  : velas_abierto,
                "stop_diario"    : int(stop_diario),
                "funding_rate"   : float(vela["funding_rate"]),
                "neg_streak"     : int(vela["funding_neg_streak"]),
            })

            logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                       signal="funding_reversion", signal_passed=True, trade_num=trade_num,
                       indicators={"funding_rate": round(float(vela["funding_rate"]), 6),
                                   "neg_streak": int(vela["funding_neg_streak"])})
            skip_hasta_idx = idx_salida
        else:
            reason = ("macro_down"       if not macro_ok
                      else "streak_low"  if not streak_ok
                      else "not_pullback" if not pullback
                      else "adx_low")
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason)

        i += 1

    return trades, capital, logger.states


# =============================================================================
# MOTOR: VWAP PULLBACK
# =============================================================================

def calcular_indicadores_vwap(df, params):
    """
    Indicadores para VWAP Pullback.
    VWAP diario (reset UTC 00:00) calculado sin lookahead.
    """
    df = df.copy()

    atr_period   = params.get("atr_period", 14)
    ema_period   = params.get("ema_trend_period", 50)
    ema_d_period = params.get("ema_trend_daily_period", 30)
    adx_period   = params.get("adx_period", 14)
    vol_period   = params.get("vol_period", 20)

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"]  - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"]       = tr.ewm(span=atr_period, adjust=False).mean()
    df["ema_trend"] = df["close"].ewm(span=ema_period, adjust=False).mean()
    df["vol_sma"]   = df["volume_btc"].rolling(window=vol_period).mean()
    df["vol_ratio"] = df["volume_btc"] / df["vol_sma"].replace(0, np.nan)

    df["date_str"] = df["datetime_ar"].astype(str).str[:10]
    daily_closes   = df.groupby("date_str")["close"].last()
    daily_ema      = daily_closes.ewm(span=ema_d_period, adjust=False).mean()
    df["ema20_diaria"] = df["date_str"].map(daily_ema.shift(1))

    if adx_period > 0:
        high, low = df["high"], df["low"]
        up_move   = high - high.shift(1)
        down_move = low.shift(1) - low
        plus_dm   = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index)
        minus_dm  = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index)
        alpha     = 1 / adx_period
        plus_di   = 100 * (plus_dm.ewm(alpha=alpha, adjust=False).mean() / tr.ewm(alpha=alpha, adjust=False).mean())
        minus_di  = 100 * (minus_dm.ewm(alpha=alpha, adjust=False).mean() / tr.ewm(alpha=alpha, adjust=False).mean())
        dx        = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
        df["adx"] = dx.ewm(alpha=alpha, adjust=False).mean()
    else:
        df["adx"] = 100.0

    # VWAP diario
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["tp_vol"]        = df["typical_price"] * df["volume_btc"]

    vwap_list = []
    for date, group in df.groupby("date_str", sort=False):
        cum_tpvol = group["tp_vol"].cumsum()
        cum_vol   = group["volume_btc"].cumsum()
        vwap_list.append(cum_tpvol / cum_vol.replace(0, np.nan))
    df["vwap"] = pd.concat(vwap_list).reindex(df.index)

    df["vwap_prev"]  = df["vwap"].shift(1)
    df["close_prev"] = df["close"].shift(1)

    df.drop(columns=["date_str", "tp_vol", "typical_price"], inplace=True)
    df.dropna(subset=["atr", "ema_trend", "ema20_diaria", "adx", "vwap", "vwap_prev"], inplace=True)
    return df


def correr_backtest_vwap(df, params, rules=None, costs=None,
                          initial_capital=None, log_candles=True):
    """
    Backtest VWAP Pullback.
    Señal: cruce alcista del VWAP diario + tendencia 4H + tendencia diaria + ADX.
    """
    rules           = rules or RULES
    costs           = costs or COSTS
    initial_capital = initial_capital or INITIAL_CAPITAL

    logger = CandleLogger(enabled=log_candles)
    trades = []
    capital = initial_capital
    indices = df.index.tolist()
    i = 0

    dia_actual     = None
    pnl_dia        = 0.0
    ops_dia        = 0
    stop_diario    = False
    skip_hasta_idx = None

    sl_atr_mult    = params.get("sl_atr_mult", 2.5)
    trail_atr_mult = params.get("trail_atr_mult", 2.5)
    max_hold_bars  = params.get("max_hold_bars", 30)
    adx_filter     = params.get("adx_filter", 22)
    vol_ratio_min  = params.get("vol_ratio_min", 1.2)
    breakeven_r    = params.get("breakeven_after_r", None)

    while i < len(indices):
        idx  = indices[i]
        vela = df.loc[idx]

        fecha_vela = vela["datetime_ar"][:10]
        if fecha_vela != dia_actual:
            dia_actual  = fecha_vela
            pnl_dia     = 0.0
            ops_dia     = 0
            stop_diario = False

        if skip_hasta_idx is not None and idx <= skip_hasta_idx:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=1)
            i += 1
            continue

        if stop_diario or ops_dia >= rules["max_daily_ops"]:
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason="daily_stop")
            i += 1
            continue

        tendencia_4h  = vela["close"] > vela["ema_trend"]
        tendencia_dia = vela["close"] > vela["ema20_diaria"]
        adx_ok        = (adx_filter == 0) or (vela["adx"] >= adx_filter)
        vol_ok        = vela["vol_ratio"] >= vol_ratio_min
        vwap_cross_up = (float(vela["close_prev"]) < float(vela["vwap_prev"])) and \
                        (float(vela["close"])       >= float(vela["vwap"]))

        if tendencia_4h and tendencia_dia and adx_ok and vol_ok and vwap_cross_up:
            entry_price  = float(vela["close"])
            atr_actual   = float(vela["atr"])
            sl_price     = entry_price - sl_atr_mult * atr_actual
            riesgo       = entry_price - sl_price
            if riesgo <= 0:
                i += 1
                continue

            qty_btc = (capital * rules["max_risk_pct"]) / riesgo
            costo   = entry_price * qty_btc * (costs["commission_pct"] + costs["slippage_pct"])
            capital -= costo
            trade_num = len(trades) + 1
            ops_dia  += 1

            idx_salida, precio_salida, resultado, velas_abierto = buscar_salida_trailing(
                df, idx, sl_price, trail_atr_mult, max_hold_bars,
                breakeven_after_r=breakeven_r
            )

            pnl_bruto    = (precio_salida - entry_price) * qty_btc
            costo_salida = precio_salida * qty_btc * (costs["commission_pct"] + costs["slippage_pct"])
            pnl_neto     = pnl_bruto - costo_salida
            capital_antes = capital
            capital      += pnl_neto
            if capital <= 0:
                capital = 0.0

            pnl_pct  = pnl_neto / capital_antes * 100
            pnl_dia += pnl_neto

            if pnl_dia / (capital_antes + abs(pnl_dia)) < -rules["daily_stop_pct"]:
                stop_diario = True

            trades.append({
                "trade_num"      : trade_num,
                "direction"      : "LONG",
                "entrada_fecha"  : vela.get("datetime_ar", str(idx)),
                "salida_fecha"   : df.loc[idx_salida, "datetime_ar"] if idx_salida in df.index else str(idx_salida),
                "precio_entrada" : entry_price,
                "precio_salida"  : precio_salida,
                "qty_btc"        : round(qty_btc, 8),
                "resultado"      : resultado,
                "pnl_neto"       : round(pnl_neto, 4),
                "pnl_pct"        : round(pnl_pct, 4),
                "capital_antes"  : round(capital_antes, 4),
                "capital_despues": round(capital, 4),
                "velas_abierto"  : velas_abierto,
                "stop_diario"    : int(stop_diario),
                "vwap"           : float(vela["vwap"]),
            })

            logger.log(bar_index=i, timestamp=idx, equity=capital_antes, in_position=0,
                       signal="vwap_cross", signal_passed=True, trade_num=trade_num,
                       indicators={"vwap": round(float(vela["vwap"]), 2),
                                   "adx": round(float(vela["adx"]), 2)})
            skip_hasta_idx = idx_salida
        else:
            reason = ("trend_4h_down"   if not tendencia_4h
                      else "trend_day_down" if not tendencia_dia
                      else "adx_low"        if not adx_ok
                      else "vol_low"        if not vol_ok
                      else "no_vwap_cross")
            logger.log(bar_index=i, timestamp=idx, equity=capital, in_position=0,
                       signal_filtered=True, filter_reason=reason)

        i += 1

    return trades, capital, logger.states
