# =============================================================================
# FASE 1 — PASO 1: DESCARGA DE DATOS DESDE BINANCE VISION
# fase1_datos.py
#
# Descarga archivos ZIP mensuales desde data.binance.vision (sin API key,
# sin límites, sin registro), los descomprime y los consolida en SQLite.
#
# Fuente oficial: https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/
# Formato de cada ZIP: BTCUSDT-1h-YYYY-MM.zip → CSV con 12 columnas OHLCV
#
# Ejecutar: python fase1_datos.py
# =============================================================================

import sqlite3
import pandas as pd
import requests
import zipfile
import io
import os
from datetime import datetime, timezone
from config import UNIFIED_DB, DATA_DIR, TRAIN_START, TRAIN_END, VALID_START, VALID_END

# Columnas del CSV de Binance Vision (12 columnas, solo usamos las primeras 6)
COLUMNAS = [
    "timestamp", "open", "high", "low", "close", "volume_btc",
    "close_time", "volume_usdt", "n_trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
]


# -----------------------------------------------------------------------------
# BASE DE DATOS
# -----------------------------------------------------------------------------

def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(UNIFIED_DB)
    return conn


def crear_tablas(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT NOT NULL,
            timeframe   TEXT NOT NULL,
            dataset     TEXT NOT NULL,
            timestamp   INTEGER NOT NULL,
            datetime    TEXT NOT NULL,
            open        REAL NOT NULL,
            high        REAL NOT NULL,
            low         REAL NOT NULL,
            close       REAL NOT NULL,
            volume      REAL NOT NULL,
            volume_base REAL NOT NULL,
            UNIQUE(symbol, timeframe, dataset, timestamp)
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_candles_lookup ON candles(symbol, timeframe, dataset, timestamp)"
    )
    conn.commit()
    print("✅ Tabla candles verificada.")


# -----------------------------------------------------------------------------
# GENERAR LISTA DE MESES A DESCARGAR
# -----------------------------------------------------------------------------

def generar_meses(fecha_inicio, fecha_fin):
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin    = datetime.strptime(fecha_fin,    "%Y-%m-%d")
    meses  = []
    year, month = inicio.year, inicio.month
    while (year, month) <= (fin.year, fin.month):
        meses.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return meses


# -----------------------------------------------------------------------------
# DESCARGA Y PROCESAMIENTO DE UN MES
# -----------------------------------------------------------------------------

def descargar_mes(year, month, timeframe="1h", symbol="BTCUSDT"):
    filename = f"{symbol}-{timeframe}-{year}-{month:02d}.zip"
    base_url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{timeframe}"
    url      = f"{base_url}/{filename}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 404:
            print(f"omitido (no disponible)")
            return None
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"error: {e}")
        return None

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            csv_name = zf.namelist()[0]
            with zf.open(csv_name) as f:
                df = pd.read_csv(f, header=None, names=COLUMNAS)
    except Exception as e:
        print(f"error descomprimiendo: {e}")
        return None

    df = df[["timestamp", "open", "high", "low", "close", "volume_btc", "volume_usdt"]].copy()
    df = df.astype({
        "timestamp"  : "int64",
        "open"       : "float64",
        "high"       : "float64",
        "low"        : "float64",
        "close"      : "float64",
        "volume_btc" : "float64",
        "volume_usdt": "float64",
    })

    # Auto-detectar microsegundos vs milisegundos
    # Binance Vision cambió de ms (13 dígitos) en 2024 a μs (16 dígitos) en 2025+
    if df["timestamp"].iloc[0] > 1e15:
        df["timestamp"] = df["timestamp"] // 1000  # μs → ms

    # Agregar datetime legible en AR (GMT-3)
    df["datetime"] = (
        pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        .dt.tz_convert("America/Argentina/Buenos_Aires")
        .dt.strftime("%Y-%m-%d %H:%M")
    )
    df = df[["timestamp", "datetime", "open", "high", "low", "close", "volume_usdt", "volume_btc"]]

    return df


# -----------------------------------------------------------------------------
# DESCARGA DE UN RANGO COMPLETO
# -----------------------------------------------------------------------------

def descargar_rango(fecha_inicio, fecha_fin, symbol, dataset, conn, timeframe="1h"):
    meses       = generar_meses(fecha_inicio, fecha_fin)
    total_velas = 0
    meses_ok    = 0

    print(f"\n📥 Descargando {len(meses)} meses → {symbol}/{timeframe}/{dataset}")
    print(f"   Rango : {fecha_inicio} → {fecha_fin}")
    print(f"   Fuente: https://data.binance.vision/data/spot/monthly/klines/{symbol}/{timeframe}\n")

    for year, month in meses:
        print(f"   [{meses_ok+1:02d}/{len(meses)}] {year}-{month:02d} ... ", end="", flush=True)

        df = descargar_mes(year, month, timeframe, symbol)
        if df is None:
            continue

        # Filtrar velas dentro del rango exacto
        ts_inicio = int(datetime.strptime(fecha_inicio, "%Y-%m-%d")
                        .replace(tzinfo=timezone.utc).timestamp() * 1000)
        ts_fin    = int(datetime.strptime(fecha_fin, "%Y-%m-%d")
                        .replace(tzinfo=timezone.utc).timestamp() * 1000) + 86_400_000
        df = df[(df["timestamp"] >= ts_inicio) & (df["timestamp"] <= ts_fin)]

        if df.empty:
            print("sin datos en rango")
            continue

        # Insertar en la tabla unificada con symbol/timeframe/dataset
        rows = [
            (symbol, timeframe, dataset, r.timestamp, r.datetime,
             r.open, r.high, r.low, r.close, r.volume_usdt, r.volume_btc)
            for r in df.itertuples(index=False)
        ]
        conn.executemany(
            """INSERT OR IGNORE INTO candles
               (symbol, timeframe, dataset, timestamp, datetime,
                open, high, low, close, volume, volume_base)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows
        )
        conn.commit()

        total_velas += len(df)
        meses_ok    += 1
        print(f"{len(df):,} velas ✅")

    print(f"\n   Total: {total_velas:,} velas en {meses_ok} meses descargados")
    return total_velas


# -----------------------------------------------------------------------------
# VERIFICACIÓN DE GAPS
# -----------------------------------------------------------------------------

def verificar_gaps(symbol, dataset, conn, timeframe="1h"):
    label = f"{symbol}/{timeframe}/{dataset}"
    print(f"\n🔍 Verificando gaps en '{label}'...")
    df = pd.read_sql(
        "SELECT timestamp, datetime FROM candles WHERE symbol=? AND timeframe=? AND dataset=? ORDER BY timestamp",
        conn, params=(symbol, timeframe, dataset)
    )

    if df.empty:
        print("   ⚠️  Sin datos.")
        return

    diffs   = df["timestamp"].diff().dropna()
    hora_ms = 3_600_000
    tf_hours = int(timeframe.replace("h", ""))
    gap_threshold = hora_ms * tf_hours * 1.5
    gaps    = diffs[diffs > gap_threshold]

    if gaps.empty:
        print(f"   ✅ Sin gaps. {len(df):,} velas continuas.")
    else:
        print(f"   ⚠️  {len(gaps)} gap(s) detectado(s):")
        for idx in gaps.index[:5]:
            ant = df.loc[idx - 1, "datetime"]
            sig = df.loc[idx, "datetime"]
            hs  = int(diffs[idx] / hora_ms)
            print(f"      → {ant} → {sig} ({hs}h de diferencia)")
        if len(gaps) > 5:
            print(f"      ... y {len(gaps) - 5} más")

    print(f"   📅 Desde : {df['datetime'].iloc[0]}")
    print(f"   📅 Hasta : {df['datetime'].iloc[-1]}")
    print(f"   📊 Total : {len(df):,} velas")


# -----------------------------------------------------------------------------
# RESUMEN FINAL
# -----------------------------------------------------------------------------

def mostrar_resumen(conn):
    print("\n" + "=" * 60)
    print("RESUMEN DE LA BASE DE DATOS")
    print("=" * 60)
    grupos = conn.execute(
        "SELECT symbol, timeframe, dataset, COUNT(*), MIN(datetime), MAX(datetime) FROM candles GROUP BY symbol, timeframe, dataset ORDER BY symbol, timeframe, dataset"
    ).fetchall()
    for symbol, tf, dataset, count, primera, ultima in grupos:
        label = "in-sample" if dataset == "train" else "out-of-sample"
        print(f"\n  {symbol}/{tf}/{dataset} ({label})")
        print(f"  Velas : {count:,}")
        print(f"  Desde : {primera}")
        print(f"  Hasta : {ultima}")
    print(f"\n  DB    : {UNIFIED_DB}")
    print("=" * 60)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("COCO STONKS — LABORATORIO DE BACKTESTING")
    print("Fase 1 · Datos desde Binance Vision")
    print("=" * 60)
    print(f"\n  Fuente : data.binance.vision (sin API key, sin límites)")
    print(f"  Train  : {TRAIN_START} → {TRAIN_END}")
    print(f"  Valid  : {VALID_START} → {VALID_END}")

    conn = get_connection()
    crear_tablas(conn)

    # ---- BTC 1H ----
    descargar_rango(TRAIN_START, TRAIN_END, "BTCUSDT", "train", conn, "1h")
    verificar_gaps("BTCUSDT", "train", conn, "1h")

    print(f"\n⚠️  Descargando validación 2025 — se guarda bloqueado hasta Fase 2.")
    descargar_rango(VALID_START, VALID_END, "BTCUSDT", "valid", conn, "1h")
    verificar_gaps("BTCUSDT", "valid", conn, "1h")

    # ---- BTC 4H ----
    print(f"\n📦 Descargando velas 4H nativas de Binance Vision...")
    descargar_rango(TRAIN_START, TRAIN_END, "BTCUSDT", "train", conn, "4h")
    verificar_gaps("BTCUSDT", "train", conn, "4h")

    descargar_rango(VALID_START, VALID_END, "BTCUSDT", "valid", conn, "4h")
    verificar_gaps("BTCUSDT", "valid", conn, "4h")

    # ---- ETH 4H ----
    print(f"\n📦 Descargando velas ETH 4H...")
    descargar_rango(TRAIN_START, TRAIN_END, "ETHUSDT", "train", conn, "4h")
    verificar_gaps("ETHUSDT", "train", conn, "4h")

    descargar_rango(VALID_START, VALID_END, "ETHUSDT", "valid", conn, "4h")
    verificar_gaps("ETHUSDT", "valid", conn, "4h")

    mostrar_resumen(conn)
    conn.close()

    print("\n✅ FASE 1 DATOS COMPLETO (1h + 4h)")
    print("   Siguiente: python fase1_motor.py")
