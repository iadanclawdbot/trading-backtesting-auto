# =============================================================================
# FASE 1 — PASO 2: MOTOR DE BACKTESTING
# fase1_motor.py
#
# Lee las velas de candles_train (2024), corre la estrategia de Coco Stonks
# vela por vela, y genera el registro completo de trades y un resumen.
#
# Ejecutar: python fase1_motor.py
# =============================================================================

import sqlite3
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import (
    UNIFIED_DB,
    RESULTS_DIR,
    STRATEGY,
    STRATEGY_BREAKOUT,
    RULES,
    COSTS,
    INITIAL_CAPITAL,
    SANITY,
)
import json
import sys

# Importar motor base refactorizado
from motor_base import (
    calcular_indicadores,
    correr_backtest_base,
    calcular_metricas as calcular_metricas_base,
    calcular_indicadores_breakout,
    correr_backtest_breakout,
)


# -----------------------------------------------------------------------------
# CARGA DE DATOS
# -----------------------------------------------------------------------------


# Mapa de nombres de tablas legacy → (symbol, timeframe, dataset)
_TABLA_MAP = {
    "candles_train":         ("BTCUSDT", "1h",  "train"),
    "candles_valid":         ("BTCUSDT", "1h",  "valid"),
    "candles_train_4h":      ("BTCUSDT", "4h",  "train"),
    "candles_valid_4h":      ("BTCUSDT", "4h",  "valid"),
    "candles_train_eth_4h":  ("ETHUSDT", "4h",  "train"),
    "candles_valid_eth_4h":  ("ETHUSDT", "4h",  "valid"),
}


def cargar_velas(tabla=None, symbol="BTCUSDT", timeframe="4h", dataset="train"):
    """
    Carga las velas desde coco_lab.db.

    Acepta el nombre de tabla legacy para backward-compatibility:
        cargar_velas(tabla="candles_train_4h")  → BTCUSDT/4h/train
        cargar_velas(symbol="ETHUSDT", timeframe="4h", dataset="valid")
    """
    if tabla is not None:
        symbol, timeframe, dataset = _TABLA_MAP.get(tabla, (symbol, timeframe, dataset))

    conn = sqlite3.connect(UNIFIED_DB)
    df = pd.read_sql(
        """SELECT timestamp,
                  datetime  AS datetime_ar,
                  open, high, low, close,
                  volume    AS volume_usdt,
                  volume_base AS volume_btc
           FROM candles
           WHERE symbol=? AND timeframe=? AND dataset=?
           ORDER BY timestamp""",
        conn, params=(symbol, timeframe, dataset), index_col="timestamp"
    )
    conn.close()
    if not df.empty:
        label = tabla or f"{symbol}/{timeframe}/{dataset}"
        print(
            f"✅ {len(df):,} velas cargadas desde {label} ({df['datetime_ar'].iloc[0]} → {df['datetime_ar'].iloc[-1]})"
        )
    return df


# -----------------------------------------------------------------------------
# WRAPPER DE MÉTRICAS (para compatibilidad con código existente)
# -----------------------------------------------------------------------------


def calcular_metricas(trades, capital_final):
    """
    Wrapper que llama a motor_base.calcular_metricas.
    El Sharpe ahora usa 365 días (crypto) y retornos diarios.
    """
    return calcular_metricas_base(trades, capital_final)


# -----------------------------------------------------------------------------
# MOTOR PRINCIPAL — DELEGADO A MOTOR_BASE
# -----------------------------------------------------------------------------


def correr_backtest(df):
    """
    Delega el backtest al motor base refactorizado.
    """
    trades, capital, candle_states = correr_backtest_base(df, STRATEGY)
    return trades, capital, candle_states


# -----------------------------------------------------------------------------
# VERIFICACIÓN DE SANIDAD
# -----------------------------------------------------------------------------


def verificar_sanidad(metricas):
    """Alerta si los resultados están fuera de rangos razonables."""
    alertas = []
    wr = metricas["win_rate"] / 100
    sh = metricas["sharpe_ratio"]
    tot = metricas["total_trades"]

    if wr < SANITY["min_win_rate"]:
        alertas.append(
            f"⚠️  Win rate muy bajo ({wr:.0%}) — puede haber un bug en el motor"
        )
    if wr > SANITY["max_win_rate"]:
        alertas.append(
            f"🚨 Win rate sospechosamente alto ({wr:.0%}) — revisar lookahead bias"
        )
    if tot < SANITY["min_trades"]:
        alertas.append(
            f"⚠️  Pocos trades ({tot}) — los filtros pueden estar demasiado restrictivos"
        )
    if sh > SANITY["max_sharpe"]:
        alertas.append(
            f"🚨 Sharpe muy alto ({sh:.2f}) — posible overfitting o lookahead bias"
        )
    if not alertas:
        alertas.append("✅ Resultados dentro de rangos razonables")

    return alertas


# -----------------------------------------------------------------------------
# BASE DE DATOS DE RESULTADOS — SCHEMA Y FUNCIONES (coco_lab.db)
# -----------------------------------------------------------------------------


def generar_run_id(params=None):
    """Genera un ID único para este run."""
    p = params or STRATEGY
    sig_type = p.get("signal_type", "ema")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sig_type.upper()}_{ts}"


def guardar_en_db(run_id, trades, metricas, candle_states=None, params=None,
                  dataset="train", symbol="BTCUSDT", timeframe="4h",
                  experiment_id=None, batch_id=None):
    """
    Guarda el run, sus trades y los candle_states en coco_lab.db.

    Args:
        run_id: ID único del run
        trades: lista de dicts del motor
        metricas: dict de calcular_metricas
        candle_states: lista de dicts del CandleLogger (opcional)
        params: dict de parámetros de la estrategia
        dataset: 'train' o 'valid'
        symbol: 'BTCUSDT', 'ETHUSDT', etc.
        timeframe: '1h', '4h'
        experiment_id: FK a experiments.id (None para runs conversacionales)
        batch_id: FK a batches.batch_id (None para runs conversacionales)
    """
    p = params or STRATEGY
    strategy = p.get("signal_type", "ema_crossover")
    conn = sqlite3.connect(UNIFIED_DB)
    conn.execute("PRAGMA foreign_keys=ON")

    # Insertar resumen del run
    conn.execute(
        """INSERT OR REPLACE INTO runs
           (run_id, experiment_id, batch_id, strategy, symbol, timeframe, dataset,
            params_json, total_trades, wins, losses, win_rate,
            capital_inicial, capital_final, pnl_total, pnl_pct,
            profit_factor, sharpe_ratio, max_drawdown, avg_velas, stops_diarios)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, experiment_id, batch_id, strategy, symbol, timeframe, dataset,
         json.dumps(p),
         metricas.get("total_trades"),
         metricas.get("wins"),
         metricas.get("losses"),
         metricas.get("win_rate"),
         metricas.get("capital_inicial"),
         metricas.get("capital_final"),
         metricas.get("pnl_total_usdt"),
         metricas.get("pnl_pct"),
         metricas.get("profit_factor"),
         metricas.get("sharpe_ratio"),
         metricas.get("max_drawdown_pct"),
         metricas.get("avg_velas"),
         metricas.get("stops_diarios"))
    )

    # Insertar trades
    if trades:
        for t in trades:
            # Construir indicators_json desde columnas legacy
            indicators = {}
            for key in ("rsi_entrada", "ema_fast_entrada", "ema_slow_entrada",
                        "vol_ratio_entrada", "atr_entrada"):
                if key in t and t[key]:
                    short = key.replace("_entrada", "").replace("rsi", "rsi")
                    indicators[short] = t[key]

            direction = t.get("direction", "LONG")
            conn.execute(
                """INSERT INTO trades
                   (run_id, trade_num, direction, entrada_fecha, salida_fecha,
                    precio_entrada, precio_salida, sl_price, tp_price, qty,
                    rr_ratio, capital_antes, risk_amount, velas_abierto,
                    resultado, pnl_bruto, pnl_neto, capital_despues,
                    pnl_dia_pct, stop_diario, indicators_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, t.get("trade_num"), direction,
                 t.get("entrada_fecha"), t.get("salida_fecha"),
                 t.get("precio_entrada"), t.get("precio_salida"),
                 t.get("sl_price"), t.get("tp_price"),
                 t.get("qty_btc", t.get("qty")),
                 t.get("rr_ratio"), t.get("capital_antes"), t.get("risk_amount"),
                 t.get("velas_abierto"), t.get("resultado"),
                 t.get("pnl_bruto"), t.get("pnl_neto"), t.get("capital_despues"),
                 t.get("pnl_dia_pct"), int(t.get("stop_diario", 0)),
                 json.dumps(indicators) if indicators else None)
            )

    # Insertar candle_states
    if candle_states:
        conn.executemany(
            """INSERT INTO candle_states
               (run_id, bar_index, timestamp, equity, in_position, trade_num,
                trailing_stop, unrealized_pnl, signal, signal_passed, signal_filtered,
                filter_reason, indicators_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [(run_id, s["bar_index"], s["timestamp"], s["equity"],
              s["in_position"], s["trade_num"], s["trailing_stop"],
              s["unrealized_pnl"], s["signal"], s["signal_passed"],
              s["signal_filtered"], s["filter_reason"], s["indicators_json"])
             for s in candle_states]
        )

    conn.commit()
    conn.close()
    n_states = len(candle_states) if candle_states else 0
    print(f"📊 Guardado en DB: {run_id} ({metricas.get('total_trades')} trades, {n_states} candle_states)")
    return run_id




# -----------------------------------------------------------------------------
# REPORTE EN PANTALLA
# -----------------------------------------------------------------------------


def mostrar_reporte(metricas, alertas):
    print("\n" + "=" * 60)
    print("RESULTADOS FASE 1 — ESTRATEGIA ACTUAL DE COCO STONKS")
    print("=" * 60)
    print(f"  Período analizado    : 2024 completo (in-sample)")
    print(f"  Capital inicial      : ${metricas['capital_inicial']:,.2f}")
    print(f"  Capital final        : ${metricas['capital_final']:,.2f}")
    print(
        f"  PnL total            : ${metricas['pnl_total_usdt']:+,.2f} ({metricas['pnl_pct']:+.2f}%)"
    )
    print(f"\n  Total trades         : {metricas['total_trades']}")
    print(f"  Wins / Losses        : {metricas['wins']} / {metricas['losses']}")
    print(f"  Win rate             : {metricas['win_rate']}%")
    print(f"  Ganancia prom. (WIN) : ${metricas['avg_win_usdt']:+.4f}")
    print(f"  Pérdida prom. (LOSS) : ${metricas['avg_loss_usdt']:+.4f}")
    print(f"  Profit Factor        : {metricas['profit_factor']}")
    print(
        f"\n  Sharpe Ratio         : {metricas['sharpe_ratio']} (365 días, retornos diarios)"
    )
    print(f"  Max Drawdown         : {metricas['max_drawdown_pct']}%")
    print(f"  Duración prom. trade : {metricas['avg_velas']} velas")
    print(f"  Stops diarios activ. : {metricas['stops_diarios']}")
    print("\n  VERIFICACIÓN DE SANIDAD")
    print("  " + "-" * 40)
    for alerta in alertas:
        print(f"  {alerta}")
    print("=" * 60)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Seleccionar estrategia por argumento: --strategy breakout
    use_breakout = "--strategy" in sys.argv and "breakout" in sys.argv

    print("=" * 60)
    print("COCO STONKS — LABORATORIO DE BACKTESTING")
    print("Fase 1 · Paso 2: Motor de backtesting")
    print("=" * 60)

    if use_breakout:
        # ====================================================================
        # ESTRATEGIA BREAKOUT 4H + ATR TRAILING STOP
        # ====================================================================
        params = STRATEGY_BREAKOUT
        tabla = "candles_train_4h"

        print(f"\n📊 Estrategia: BREAKOUT 4H + ATR Trailing Stop")
        print(f"   Tabla: {tabla}")
        print(f"   Lookback: {params['lookback']} | Vol: {params['vol_ratio_min']}x")
        print(f"   SL: {params['sl_atr_mult']}x ATR | Trail: {params['trail_atr_mult']}x ATR")

        # 1. Cargar datos 4H
        df = cargar_velas(tabla)

        # 2. Calcular indicadores breakout
        df = calcular_indicadores_breakout(df, params)
        print(f"✅ Indicadores breakout calculados. Velas utilizables: {len(df):,}")

        # 3. Correr backtest breakout
        print(f"\n🚀 Corriendo backtest breakout sobre {len(df):,} velas 4H...")
        print(f"   Capital inicial: ${INITIAL_CAPITAL:,.2f} USDT\n")

        trades, capital_final, candle_states = correr_backtest_breakout(df, params)

    else:
        # ====================================================================
        # ESTRATEGIA ORIGINAL EMA CROSSOVER (default)
        # ====================================================================
        # 1. Cargar datos
        df = cargar_velas()

        # 2. Calcular indicadores técnicos
        df = calcular_indicadores(df, STRATEGY)
        print(f"✅ Indicadores calculados. Velas utilizables: {len(df):,}")

        # 3. Correr el backtest
        print(f"\n🚀 Corriendo backtest sobre {len(df):,} velas...")
        print(f"   Capital inicial: ${INITIAL_CAPITAL:,.2f} USDT")
        print(
            f"   Estrategia: RSI{STRATEGY['rsi_period']} | EMA{STRATEGY['ema_fast']}/{STRATEGY['ema_slow']} | Vol {STRATEGY['vol_ratio_min']}x\n"
        )

        trades, capital_final, candle_states = correr_backtest(df)

    if not trades:
        print("⚠️  Sin trades ejecutados. Revisá los parámetros en config.py")
    else:
        # 4. Calcular métricas
        metricas = calcular_metricas(trades, capital_final)

        # 5. Verificar sanidad
        alertas = verificar_sanidad(metricas)

        # 6. Mostrar reporte
        mostrar_reporte(metricas, alertas)

        # 7. Guardar en base de datos
        run_id = generar_run_id(params if use_breakout else None)
        guardar_en_db(run_id, trades, metricas, candle_states,
                      params=params if use_breakout else None,
                      dataset="train", timeframe="4h" if use_breakout else "1h")

        print(f"\n✅ FASE 1 COMPLETA — Run ID: {run_id}")
        mode_label = "breakout 4H" if use_breakout else "EMA crossover"
        print(f"   Estrategia: {mode_label}")
        print(
            "   Si los resultados son razonables → siguiente: python scripts/fase2_grid_search.py"
        )
        print("   Si hay alertas → revisá los parámetros en scripts/config.py")
