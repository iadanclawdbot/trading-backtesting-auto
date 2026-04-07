#!/usr/bin/env python3
# =============================================================================
# DESCARGAR FUNDING RATES — Binance Perpetual Futures
# descargar_funding_rates.py
#
# Descarga el historial de funding rates de BTCUSDT desde Binance Futures API
# y lo almacena en la tabla funding_rates de coco_lab.db.
#
# Binance funding rate: cada 8H (00:00, 08:00, 16:00 UTC)
# API pública: https://fapi.binance.com/fapi/v1/fundingRate
#
# Ejecutar: python3 scripts/descargar_funding_rates.py
# =============================================================================

import sqlite3
import requests
import time
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import UNIFIED_DB

BINANCE_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
SYMBOL = "BTCUSDT"
# Desde inicio de 2024 para cubrir train + valid
START_TS = int(datetime(2023, 12, 1, tzinfo=timezone.utc).timestamp() * 1000)
LIMIT = 1000  # máximo por request


def crear_tabla(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS funding_rates (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol    TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            datetime  TEXT NOT NULL,
            rate      REAL NOT NULL,
            UNIQUE(symbol, timestamp)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_funding_lookup ON funding_rates(symbol, timestamp)"
    )
    conn.commit()
    print("✅ Tabla funding_rates verificada.")


def descargar_batch(symbol, start_ms, end_ms=None):
    params = {
        "symbol": symbol,
        "startTime": start_ms,
        "limit": LIMIT,
    }
    if end_ms:
        params["endTime"] = end_ms
    resp = requests.get(BINANCE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def insertar_registros(conn, registros):
    insertados = 0
    for r in registros:
        ts = int(r["fundingTime"])
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rate = float(r["fundingRate"])
        try:
            conn.execute(
                "INSERT OR IGNORE INTO funding_rates (symbol, timestamp, datetime, rate) VALUES (?, ?, ?, ?)",
                (r["symbol"], ts, dt, rate)
            )
            insertados += 1
        except Exception:
            pass
    conn.commit()
    return insertados


def main():
    conn = sqlite3.connect(UNIFIED_DB)
    crear_tabla(conn)

    # Verificar qué tenemos ya
    existing = conn.execute(
        "SELECT COUNT(*), MAX(timestamp) FROM funding_rates WHERE symbol=?",
        (SYMBOL,)
    ).fetchone()
    count_existing, last_ts = existing
    print(f"📊 Registros existentes: {count_existing}")

    # Empezar desde el último registro + 1ms (o desde START_TS)
    start_ms = (last_ts + 1) if last_ts else START_TS
    end_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    total_insertados = 0
    batch = 0

    while start_ms < end_ms:
        batch += 1
        data = descargar_batch(SYMBOL, start_ms)

        if not data:
            print("   ✅ Sin más datos.")
            break

        insertados = insertar_registros(conn, data)
        total_insertados += insertados

        ultimo = data[-1]
        ultimo_ts = int(ultimo["fundingTime"])
        ultimo_dt = datetime.fromtimestamp(ultimo_ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

        print(f"   Batch {batch:3d}: {len(data)} registros → hasta {ultimo_dt} ({insertados} nuevos)")

        if len(data) < LIMIT:
            break

        start_ms = ultimo_ts + 1
        time.sleep(0.3)  # rate limiting

    # Resumen final
    final_count = conn.execute(
        "SELECT COUNT(*), MIN(datetime), MAX(datetime) FROM funding_rates WHERE symbol=?",
        (SYMBOL,)
    ).fetchone()
    conn.close()

    print(f"\n✅ Descarga completa. {total_insertados} nuevos registros.")
    print(f"   Total en DB: {final_count[0]} registros")
    print(f"   Período: {final_count[1]} → {final_count[2]}")


if __name__ == "__main__":
    main()
