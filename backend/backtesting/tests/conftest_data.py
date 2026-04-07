# =============================================================================
# FIXTURES PARA TESTS — GENERADOR DE VELAS SINTÉTICAS
# conftest_data.py
#
# Genera datos sintéticos para tests sin necesidad de datos reales.
# Las fechas NO asumen 2024 — se generan a partir de 2024-01-01 por simplicidad
# pero los tests no dependen del año específico.
# =============================================================================

import pandas as pd
import numpy as np


def make_candles(n=200, trend="alcista", seed=42, start_date="2024-01-01"):
    """
    Generate synthetic BTCUSDT 1h candles for testing.

    Args:
        n: number of candles to generate
        trend: "alcista" | "bajista" | "lateral"
        seed: random seed for reproducibility
        start_date: starting date (default 2024-01-01, but tests should not depend on year)

    Returns:
        DataFrame with columns: timestamp, datetime_ar, open, high, low, close, volume_btc, volume_usdt
    """
    np.random.seed(seed)
    base = 50000
    timestamps = pd.date_range(start_date, periods=n, freq="h")

    if trend == "alcista":
        prices = base + np.cumsum(np.random.randn(n) * 100 + 50)
    elif trend == "bajista":
        prices = base + np.cumsum(np.random.randn(n) * 100 - 50)
    else:
        prices = base + np.cumsum(np.random.randn(n) * 80)

    # Ensure positive prices
    prices = np.maximum(prices, 1000)

    df = pd.DataFrame(
        {
            "timestamp": [int(t.timestamp() * 1000) for t in timestamps],
            "datetime_ar": [t.strftime("%Y-%m-%d %H:%M") for t in timestamps],
            "open": prices,
            "high": prices + np.abs(np.random.randn(n) * 150),
            "low": prices - np.abs(np.random.randn(n) * 150),
            "close": prices + np.random.randn(n) * 50,
            "volume_btc": np.abs(np.random.randn(n) * 100 + 200),
            "volume_usdt": np.abs(np.random.randn(n) * 5000000),
        }
    )

    # Ensure high >= low and prices within range
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)

    df.index = df["timestamp"]
    return df


def make_candles_multi_day(n_days=3, trend="alcista", seed=42):
    """
    Generate candles spanning multiple days to test daily stop logic.

    Args:
        n_days: number of days
        trend: "alcista" | "bajista" | "lateral"
        seed: random seed

    Returns:
        DataFrame with 24 * n_days hourly candles
    """
    return make_candles(n=24 * n_days, trend=trend, seed=seed)
