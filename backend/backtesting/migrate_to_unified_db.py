#!/usr/bin/env python3
# =============================================================================
# MIGRACIÓN A DB UNIFICADA — Coco Stonks Lab
# scripts/migrate_to_unified_db.py
#
# Script one-shot que:
#   1. Crea data/coco_lab.db con el schema relacional nuevo
#   2. Migra candles de candles_raw.db (6 tablas → tabla unificada con symbol/timeframe/dataset)
#   3. Migra runs de resultados.db (limpieza de legacy EMA cols → params_json, infiere strategy)
#   4. Migra trades (indicadores sueltos → indicators_json)
#   5. Migra experiments de experiments.db (sin métricas denormalizadas)
#   6. NO migra autoresearch_log
#   7. Backup de DBs viejas en data/backup_pre_migration/
#
# Uso:
#   python3 scripts/migrate_to_unified_db.py
#   python3 scripts/migrate_to_unified_db.py --dry-run   (solo imprime lo que haría)
# =============================================================================

import sqlite3
import json
import os
import sys
import shutil
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, DB_PATH, RESULTS_DB, EXPERIMENTS_DB, UNIFIED_DB

BACKUP_DIR = os.path.join(DATA_DIR, "backup_pre_migration")


# =============================================================================
# SCHEMA DDL
# =============================================================================

DDL = """
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
);
CREATE INDEX IF NOT EXISTS idx_candles_lookup ON candles(symbol, timeframe, dataset, timestamp);

CREATE TABLE IF NOT EXISTS batches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id   TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    notes      TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    status      TEXT NOT NULL DEFAULT 'pending',
    strategy    TEXT NOT NULL,
    symbol      TEXT NOT NULL DEFAULT 'BTCUSDT',
    timeframe   TEXT NOT NULL DEFAULT '4h',
    params_json TEXT NOT NULL,
    dataset     TEXT NOT NULL DEFAULT 'both',
    priority    INTEGER DEFAULT 0,
    batch_id    TEXT,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    started_at  TEXT,
    finished_at TEXT,
    error_msg   TEXT,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status, priority DESC, id ASC);

CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT UNIQUE NOT NULL,
    experiment_id   INTEGER,
    batch_id        TEXT,
    strategy        TEXT NOT NULL,
    symbol          TEXT NOT NULL DEFAULT 'BTCUSDT',
    timeframe       TEXT NOT NULL DEFAULT '4h',
    dataset         TEXT NOT NULL,
    params_json     TEXT NOT NULL,
    total_trades    INTEGER,
    wins            INTEGER,
    losses          INTEGER,
    win_rate        REAL,
    capital_inicial REAL,
    capital_final   REAL,
    pnl_total       REAL,
    pnl_pct         REAL,
    profit_factor   REAL,
    sharpe_ratio    REAL,
    max_drawdown    REAL,
    avg_velas       REAL,
    stops_diarios   INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id),
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
);
CREATE INDEX IF NOT EXISTS idx_runs_batch ON runs(batch_id);
CREATE INDEX IF NOT EXISTS idx_runs_strategy ON runs(strategy, dataset);

CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    trade_num       INTEGER NOT NULL,
    direction       TEXT NOT NULL DEFAULT 'LONG',
    entrada_fecha   TEXT NOT NULL,
    salida_fecha    TEXT NOT NULL,
    precio_entrada  REAL NOT NULL,
    precio_salida   REAL NOT NULL,
    sl_price        REAL,
    tp_price        REAL,
    qty             REAL NOT NULL,
    rr_ratio        REAL,
    capital_antes   REAL,
    risk_amount     REAL,
    velas_abierto   INTEGER,
    resultado       TEXT NOT NULL,
    pnl_bruto       REAL,
    pnl_neto        REAL,
    capital_despues REAL,
    pnl_dia_pct     REAL,
    stop_diario     INTEGER DEFAULT 0,
    indicators_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
CREATE INDEX IF NOT EXISTS idx_trades_run ON trades(run_id);

CREATE TABLE IF NOT EXISTS candle_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    bar_index       INTEGER NOT NULL,
    timestamp       INTEGER NOT NULL,
    equity          REAL NOT NULL,
    in_position     INTEGER NOT NULL DEFAULT 0,
    trade_num       INTEGER,
    trailing_stop   REAL,
    unrealized_pnl  REAL,
    signal          TEXT,
    signal_passed   INTEGER DEFAULT 0,
    signal_filtered INTEGER DEFAULT 0,
    filter_reason   TEXT,
    indicators_json TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
CREATE INDEX IF NOT EXISTS idx_candle_states_run ON candle_states(run_id);
CREATE INDEX IF NOT EXISTS idx_candle_states_lookup ON candle_states(run_id, timestamp);
"""


# =============================================================================
# HELPERS
# =============================================================================

def infer_strategy(params_json_str):
    """Infiere la estrategia real desde el params_json."""
    try:
        p = json.loads(params_json_str) if params_json_str else {}
        return p.get("signal_type", "ema_crossover")
    except Exception:
        return "ema_crossover"


def infer_dataset_and_timeframe(dataset_str):
    """
    Convierte el dataset legacy al formato nuevo.
    'train_2024' → ('train', '1h')
    'valid_2025' → ('valid', '1h')
    'train_2024_4h' → ('train', '4h')
    'valid_2025_4h' → ('valid', '4h')
    """
    if "_4h" in dataset_str:
        timeframe = "4h"
        dataset = "train" if "train" in dataset_str else "valid"
    else:
        timeframe = "1h"
        dataset = "train" if "train" in dataset_str else "valid"
    return dataset, timeframe


def infer_symbol(run_id_str, params_json_str):
    """
    Infiere el símbolo. Por ahora todos los runs históricos son BTCUSDT.
    En el futuro el run_id incluirá el símbolo.
    """
    return "BTCUSDT"


# =============================================================================
# FASE 1: CREAR SCHEMA
# =============================================================================

def crear_schema(conn):
    for statement in DDL.split(";"):
        s = statement.strip()
        if s:
            conn.execute(s + ";")
    conn.commit()
    print("  ✓ Schema creado")


# =============================================================================
# FASE 2: MIGRAR CANDLES
# =============================================================================

TABLE_MAP = {
    "candles_train":     ("BTCUSDT", "1h",  "train"),
    "candles_valid":     ("BTCUSDT", "1h",  "valid"),
    "candles_train_4h":  ("BTCUSDT", "4h",  "train"),
    "candles_valid_4h":  ("BTCUSDT", "4h",  "valid"),
    "candles_train_eth_4h": ("ETHUSDT", "4h", "train"),
    "candles_valid_eth_4h": ("ETHUSDT", "4h", "valid"),
}


def migrar_candles(src_conn, dst_conn, dry_run=False):
    total = 0
    for table, (symbol, timeframe, dataset) in TABLE_MAP.items():
        rows = src_conn.execute(
            f"SELECT timestamp, datetime_ar, open, high, low, close, volume_usdt, volume_btc FROM \"{table}\""
        ).fetchall()

        if not dry_run:
            dst_conn.executemany(
                """INSERT OR IGNORE INTO candles
                   (symbol, timeframe, dataset, timestamp, datetime, open, high, low, close, volume, volume_base)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [(symbol, timeframe, dataset, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in rows]
            )
            dst_conn.commit()

        total += len(rows)
        print(f"  ✓ {table} → {symbol}/{timeframe}/{dataset}: {len(rows)} velas")

    print(f"  Total candles migradas: {total}")
    return total


# =============================================================================
# FASE 3: MIGRAR RUNS
# =============================================================================

def migrar_runs(src_conn, dst_conn, dry_run=False):
    rows = src_conn.execute(
        """SELECT run_id, created_at, params_json, dataset, batch_id,
                  total_trades, wins, losses, win_rate,
                  capital_inicial, capital_final, pnl_total, pnl_pct,
                  profit_factor, sharpe_ratio, max_drawdown, avg_velas, stops_diarios
           FROM backtest_runs"""
    ).fetchall()

    migrated = 0
    for r in rows:
        (run_id, created_at, params_json_str, dataset_legacy, batch_id,
         total_trades, wins, losses, win_rate,
         capital_inicial, capital_final, pnl_total, pnl_pct,
         profit_factor, sharpe_ratio, max_drawdown, avg_velas, stops_diarios) = r

        strategy = infer_strategy(params_json_str)
        dataset, timeframe = infer_dataset_and_timeframe(dataset_legacy or "")
        symbol = infer_symbol(run_id, params_json_str)

        if not dry_run:
            dst_conn.execute(
                """INSERT OR IGNORE INTO runs
                   (run_id, experiment_id, batch_id, strategy, symbol, timeframe, dataset,
                    params_json, total_trades, wins, losses, win_rate,
                    capital_inicial, capital_final, pnl_total, pnl_pct,
                    profit_factor, sharpe_ratio, max_drawdown, avg_velas, stops_diarios, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, None, batch_id, strategy, symbol, timeframe, dataset,
                 params_json_str, total_trades, wins, losses, win_rate,
                 capital_inicial, capital_final, pnl_total, pnl_pct,
                 profit_factor, sharpe_ratio, max_drawdown, avg_velas, stops_diarios, created_at)
            )
        migrated += 1

    if not dry_run:
        dst_conn.commit()

    print(f"  ✓ Runs migrados: {migrated}")
    return migrated


# =============================================================================
# FASE 4: MIGRAR TRADES
# =============================================================================

def migrar_trades(src_conn, dst_conn, dry_run=False):
    rows = src_conn.execute(
        """SELECT run_id, trade_num, entrada_fecha, salida_fecha,
                  precio_entrada, precio_salida, sl_price, tp_price, qty_btc,
                  rr_ratio, capital_antes, risk_amount, velas_abierto,
                  resultado, pnl_bruto, pnl_neto, capital_despues, pnl_dia_pct, stop_diario,
                  rsi_entrada, ema_fast_entrada, ema_slow_entrada, vol_ratio_entrada, atr_entrada
           FROM backtest_trades"""
    ).fetchall()

    migrated = 0
    for r in rows:
        (run_id, trade_num, entrada_fecha, salida_fecha,
         precio_entrada, precio_salida, sl_price, tp_price, qty_btc,
         rr_ratio, capital_antes, risk_amount, velas_abierto,
         resultado, pnl_bruto, pnl_neto, capital_despues, pnl_dia_pct, stop_diario,
         rsi_entrada, ema_fast_entrada, ema_slow_entrada, vol_ratio_entrada, atr_entrada) = r

        # Consolidar indicadores legacy en indicators_json
        indicators = {}
        if rsi_entrada is not None:        indicators["rsi"] = rsi_entrada
        if ema_fast_entrada is not None:   indicators["ema_fast"] = ema_fast_entrada
        if ema_slow_entrada is not None:   indicators["ema_slow"] = ema_slow_entrada
        if vol_ratio_entrada is not None:  indicators["vol_ratio"] = vol_ratio_entrada
        if atr_entrada is not None:        indicators["atr"] = atr_entrada
        indicators_json = json.dumps(indicators) if indicators else None

        if not dry_run:
            dst_conn.execute(
                """INSERT INTO trades
                   (run_id, trade_num, direction, entrada_fecha, salida_fecha,
                    precio_entrada, precio_salida, sl_price, tp_price, qty,
                    rr_ratio, capital_antes, risk_amount, velas_abierto,
                    resultado, pnl_bruto, pnl_neto, capital_despues, pnl_dia_pct, stop_diario,
                    indicators_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, trade_num, "LONG", entrada_fecha, salida_fecha,
                 precio_entrada, precio_salida, sl_price, tp_price, qty_btc,
                 rr_ratio, capital_antes, risk_amount, velas_abierto,
                 resultado, pnl_bruto, pnl_neto, capital_despues, pnl_dia_pct, stop_diario,
                 indicators_json)
            )
        migrated += 1

    if not dry_run:
        dst_conn.commit()

    print(f"  ✓ Trades migrados: {migrated}")
    return migrated


# =============================================================================
# FASE 5: MIGRAR EXPERIMENTS
# =============================================================================

def migrar_experiments(src_conn, dst_conn, dry_run=False):
    rows = src_conn.execute(
        """SELECT id, status, strategy, params_json, dataset, priority, notes,
                  created_at, started_at, finished_at, error_msg
           FROM experiment_queue"""
    ).fetchall()

    migrated = 0
    for r in rows:
        (exp_id, status, strategy, params_json, dataset_raw, priority, notes,
         created_at, started_at, finished_at, error_msg) = r

        # Normalizar dataset
        if dataset_raw in ("both", "train", "valid"):
            dataset = dataset_raw
        else:
            dataset, _ = infer_dataset_and_timeframe(dataset_raw or "both")

        if not dry_run:
            dst_conn.execute(
                """INSERT OR IGNORE INTO experiments
                   (id, status, strategy, symbol, timeframe, params_json, dataset,
                    priority, batch_id, notes, created_at, started_at, finished_at, error_msg)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (exp_id, status, strategy, "BTCUSDT", "4h", params_json, dataset,
                 priority or 0, None, notes, created_at, started_at, finished_at, error_msg)
            )
        migrated += 1

    if not dry_run:
        dst_conn.commit()

    print(f"  ✓ Experiments migrados: {migrated}")
    return migrated


# =============================================================================
# BACKUP
# =============================================================================

def hacer_backup(dry_run=False):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = []
    for src in [DB_PATH, RESULTS_DB, EXPERIMENTS_DB]:
        if os.path.exists(src):
            dst = os.path.join(BACKUP_DIR, f"{os.path.basename(src)}.{ts}.bak")
            if not dry_run:
                shutil.copy2(src, dst)
            backups.append(dst)
            print(f"  ✓ Backup: {os.path.basename(src)} → {os.path.basename(dst)}")
    return backups


# =============================================================================
# VERIFICACIÓN
# =============================================================================

def verificar(dst_conn):
    checks = {
        "candles":     28440,
        "runs":        110,
        "trades":      5579,
        "experiments": 5,
    }
    ok = True
    for table, expected in checks.items():
        count = dst_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        status = "✓" if count == expected else "⚠"
        if count != expected:
            ok = False
        print(f"  {status} {table}: {count} (esperado: {expected})")

    # Verifica que candle_states está vacío (se llena en backtests futuros)
    cs_count = dst_conn.execute("SELECT COUNT(*) FROM candle_states").fetchone()[0]
    print(f"  ✓ candle_states: {cs_count} (vacía — se poblará en nuevos backtests)")

    # Verifica distribución de candles por símbolo/timeframe
    dist = dst_conn.execute(
        "SELECT symbol, timeframe, dataset, COUNT(*) FROM candles GROUP BY symbol, timeframe, dataset ORDER BY symbol, timeframe, dataset"
    ).fetchall()
    print("\n  Distribución de candles:")
    for row in dist:
        print(f"    {row[0]}/{row[1]}/{row[2]}: {row[3]} velas")

    return ok


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Migra a coco_lab.db unificada")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir nada")
    args = parser.parse_args()

    dry_run = args.dry_run
    if dry_run:
        print("🔍 DRY RUN — no se escribe nada\n")

    # Verificar que las DBs fuente existen
    for src in [DB_PATH, RESULTS_DB, EXPERIMENTS_DB]:
        if not os.path.exists(src):
            print(f"❌ DB fuente no encontrada: {src}")
            sys.exit(1)

    # Si la DB destino ya existe, preguntar
    if os.path.exists(UNIFIED_DB) and not dry_run:
        resp = input(f"\n⚠️  {UNIFIED_DB} ya existe. ¿Sobreescribir? [s/N] ").strip().lower()
        if resp != "s":
            print("Cancelado.")
            sys.exit(0)
        os.remove(UNIFIED_DB)

    print("\n📦 Fase 0 — Backup de DBs originales")
    hacer_backup(dry_run)

    print("\n🏗  Fase 1 — Crear schema en coco_lab.db")
    if not dry_run:
        dst_conn = sqlite3.connect(UNIFIED_DB)
        dst_conn.execute("PRAGMA journal_mode=WAL")
        dst_conn.execute("PRAGMA foreign_keys=ON")
        crear_schema(dst_conn)
    else:
        dst_conn = None

    print("\n🗂  Fase 2 — Migrar candles (candles_raw.db → candles)")
    src_candles = sqlite3.connect(DB_PATH)
    migrar_candles(src_candles, dst_conn, dry_run)
    src_candles.close()

    print("\n📊 Fase 3 — Migrar runs (resultados.db → runs)")
    src_resultados = sqlite3.connect(RESULTS_DB)

    # Pre-crear batches referenciados por runs existentes
    if not dry_run:
        batch_ids = src_resultados.execute(
            "SELECT DISTINCT batch_id FROM backtest_runs WHERE batch_id IS NOT NULL"
        ).fetchall()
        for (bid,) in batch_ids:
            dst_conn.execute(
                "INSERT OR IGNORE INTO batches (batch_id, notes) VALUES (?, ?)",
                (bid, "Migrado desde resultados.db")
            )
        dst_conn.commit()
        if batch_ids:
            print(f"  ✓ Pre-creados {len(batch_ids)} batch(es) referenciados")

    migrar_runs(src_resultados, dst_conn, dry_run)

    print("\n💰 Fase 4 — Migrar trades (resultados.db → trades)")
    migrar_trades(src_resultados, dst_conn, dry_run)
    src_resultados.close()

    print("\n🧪 Fase 5 — Migrar experiments (experiments.db → experiments)")
    src_experiments = sqlite3.connect(EXPERIMENTS_DB)
    migrar_experiments(src_experiments, dst_conn, dry_run)
    src_experiments.close()

    if not dry_run:
        print("\n✅ Fase 6 — Verificación")
        ok = verificar(dst_conn)
        dst_conn.close()

        if ok:
            print(f"\n🎉 Migración completa → {UNIFIED_DB}")
        else:
            print(f"\n⚠️  Migración completada con diferencias en conteos — revisar antes de continuar")
    else:
        print("\n🔍 Dry run completado — ejecutá sin --dry-run para migrar")


if __name__ == "__main__":
    main()
