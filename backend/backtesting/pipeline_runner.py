#!/usr/bin/env python3
# =============================================================================
# PIPELINE RUNNER — Coco Stonks Lab
# scripts/pipeline_runner.py
#
# Ejecuta experimentos en cola desde data/coco_lab.db de forma autónoma.
# SIN modelo de IA. Consume jobs pendientes y guarda resultados en coco_lab.db
#
# Uso:
#   python3 scripts/pipeline_runner.py              # corre todos los pending
#   python3 scripts/pipeline_runner.py --limit 50   # solo los primeros 50
#   python3 scripts/pipeline_runner.py --status      # ver estado de la cola
# =============================================================================

import sqlite3
import json
import sys
import os
import argparse
import subprocess
from datetime import datetime

# Asegurar que scripts/ está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import UNIFIED_DB, RESULTS_DIR, INITIAL_CAPITAL, RULES, COSTS, SANITY
from motor_base import (
    calcular_indicadores_breakout,
    correr_backtest_breakout,
    calcular_indicadores_breakdown,
    correr_backtest_breakdown,
    calcular_indicadores,
    correr_backtest_base,
    calcular_indicadores_mr,
    correr_backtest_mr,
    correr_backtest_retest,
    correr_backtest_hibrido,
    calcular_indicadores_funding,
    correr_backtest_funding_reversion,
    calcular_indicadores_vwap,
    correr_backtest_vwap,
    calcular_metricas,
)
from fase1_motor import guardar_en_db, cargar_velas


# =============================================================================
# FUNCIONES DE COLA — tabla experiments en UNIFIED_DB
# =============================================================================

def get_pending_jobs(limit=None):
    """Obtiene jobs pendientes ordenados por prioridad."""
    conn = sqlite3.connect(UNIFIED_DB)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT id, strategy, params_json, dataset, symbol, timeframe, notes
        FROM experiments
        WHERE status = 'pending'
        ORDER BY priority DESC, id ASC
    """
    if limit:
        query += f" LIMIT {limit}"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_running(job_id):
    conn = sqlite3.connect(UNIFIED_DB)
    conn.execute(
        "UPDATE experiments SET status='running', started_at=? WHERE id=?",
        (datetime.now().isoformat(), job_id)
    )
    conn.commit()
    conn.close()


def mark_done(job_id):
    conn = sqlite3.connect(UNIFIED_DB)
    conn.execute(
        "UPDATE experiments SET status='done', finished_at=? WHERE id=?",
        (datetime.now().isoformat(), job_id)
    )
    conn.commit()
    conn.close()


def mark_failed(job_id, error_msg):
    conn = sqlite3.connect(UNIFIED_DB)
    conn.execute(
        "UPDATE experiments SET status='failed', finished_at=?, error_msg=? WHERE id=?",
        (datetime.now().isoformat(), str(error_msg)[:500], job_id)
    )
    conn.commit()
    conn.close()


def get_queue_status():
    conn = sqlite3.connect(UNIFIED_DB)
    rows = conn.execute("""
        SELECT status, COUNT(*) as n
        FROM experiments
        GROUP BY status
        ORDER BY status
    """).fetchall()
    conn.close()
    return dict(rows)


# =============================================================================
# MOTOR: CARGA DE DATOS Y EJECUCIÓN
# =============================================================================

# Cache de datos para no recargar en cada job
_data_cache = {}

def get_data(symbol, timeframe, dataset):
    key = (symbol, timeframe, dataset)
    if key not in _data_cache:
        print(f"   📂 Cargando {symbol}/{timeframe}/{dataset}...")
        _data_cache[key] = cargar_velas(symbol=symbol, timeframe=timeframe, dataset=dataset)
    return _data_cache[key]


# Mapa de estrategias → funciones y defaults de symbol/timeframe
MOTORES = {
    "breakout": {
        "indicadores": calcular_indicadores_breakout,
        "backtest":    correr_backtest_breakout,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "breakdown_short": {
        "indicadores": calcular_indicadores_breakdown,
        "backtest":    correr_backtest_breakdown,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    # Alias legacy
    "breakdown": {
        "indicadores": calcular_indicadores_breakdown,
        "backtest":    correr_backtest_breakdown,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "mean_reversion": {
        "indicadores": calcular_indicadores_mr,
        "backtest":    correr_backtest_mr,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "ema_crossover": {
        "indicadores": calcular_indicadores,
        "backtest":    correr_backtest_base,
        "symbol":      "BTCUSDT",
        "timeframe":   "1h",
    },
    "retest": {
        "indicadores": calcular_indicadores_breakout,
        "backtest":    correr_backtest_retest,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "hibrido": {
        "indicadores": calcular_indicadores_breakout,
        "backtest":    correr_backtest_hibrido,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "funding_reversion": {
        "indicadores": calcular_indicadores_funding,
        "backtest":    correr_backtest_funding_reversion,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
    "vwap_pullback": {
        "indicadores": calcular_indicadores_vwap,
        "backtest":    correr_backtest_vwap,
        "symbol":      "BTCUSDT",
        "timeframe":   "4h",
    },
}


def correr_experimento(strategy, params, dataset,
                       symbol_override=None, timeframe_override=None):
    """
    Corre un experimento completo según la estrategia.
    Retorna dict con resultados por split y metadatos symbol/timeframe.
    """
    if strategy not in MOTORES:
        raise ValueError(f"Estrategia desconocida: {strategy}")

    motor     = MOTORES[strategy]
    fn_ind    = motor["indicadores"]
    fn_bt     = motor["backtest"]
    symbol    = symbol_override    or motor["symbol"]
    timeframe = timeframe_override or motor["timeframe"]

    results = {
        "train": {"trades": None, "metricas": None, "states": None},
        "valid": {"trades": None, "metricas": None, "states": None},
        "symbol":    symbol,
        "timeframe": timeframe,
    }

    for split in (["train", "valid"] if dataset == "both" else [dataset]):
        df_raw = get_data(symbol, timeframe, split)
        df = fn_ind(df_raw.copy(), params)

        if df.empty:
            print(f"    ⚠️  DataFrame vacío después de indicadores ({split}) — params pueden ser extremos")
            continue

        trades, capital, states = fn_bt(df, params)
        metricas = calcular_metricas(trades, capital) if trades else {}
        results[split] = {"trades": trades, "metricas": metricas, "states": states}

    return results


# =============================================================================
# RUNNER PRINCIPAL
# =============================================================================

def run_pipeline(limit=None, verbose=True):
    if not os.path.exists(UNIFIED_DB):
        print(f"❌ No se encontró {UNIFIED_DB}")
        print(f"   Ejecutar primero: python3 scripts/migrate_to_unified_db.py")
        return

    jobs = get_pending_jobs(limit)
    total = len(jobs)

    if total == 0:
        print("✅ No hay jobs pendientes en la cola.")
        return

    # Crear batch record en UNIFIED_DB
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn = sqlite3.connect(UNIFIED_DB)
    conn.execute(
        "INSERT OR IGNORE INTO batches (batch_id, notes) VALUES (?, ?)",
        (batch_id, f"Pipeline automático — {total} jobs")
    )
    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"🚀 PIPELINE RUNNER — Coco Stonks Lab")
    print(f"   Batch ID:        {batch_id}")
    print(f"   Jobs a procesar: {total}")
    print(f"   Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    exitosos  = 0
    fallidos  = 0
    sin_trades = 0

    for i, job in enumerate(jobs, 1):
        job_id   = job["id"]
        strategy = job["strategy"]
        dataset  = job["dataset"]
        # Overrides opcionales (None → usa default del motor)
        sym_ov = job.get("symbol")   or None
        tf_ov  = job.get("timeframe") or None

        try:
            params = json.loads(job["params_json"])
            # Asegurar que signal_type esté en params para guardar_en_db
            if "signal_type" not in params:
                params["signal_type"] = strategy
            mark_running(job_id)

            if verbose:
                print(f"[{i:>4}/{total}] Job #{job_id} | {strategy} | {job.get('notes') or ''}")

            result = correr_experimento(
                strategy, params, dataset,
                symbol_override=sym_ov,
                timeframe_override=tf_ov,
            )

            symbol    = result["symbol"]
            timeframe = result["timeframe"]
            m_train   = result["train"]["metricas"]
            m_valid   = result["valid"]["metricas"]
            t_train   = result["train"]["trades"]
            t_valid   = result["valid"]["trades"]
            s_train   = result["train"]["states"]
            s_valid   = result["valid"]["states"]

            run_id_train = run_id_valid = None

            if t_train is not None and m_train:
                run_id_train = f"JOB{job_id}_TRAIN_{datetime.now().strftime('%H%M%S')}"
                guardar_en_db(
                    run_id_train, t_train, m_train, s_train,
                    params=params, dataset="train",
                    symbol=symbol, timeframe=timeframe,
                    experiment_id=job_id, batch_id=batch_id,
                )

            if t_valid is not None and m_valid:
                run_id_valid = f"JOB{job_id}_VALID_{datetime.now().strftime('%H%M%S')}"
                guardar_en_db(
                    run_id_valid, t_valid, m_valid, s_valid,
                    params=params, dataset="valid",
                    symbol=symbol, timeframe=timeframe,
                    experiment_id=job_id, batch_id=batch_id,
                )

            mark_done(job_id)

            # Resumen por línea
            sh_t = m_train.get("sharpe_ratio", 0) if m_train else 0
            sh_v = m_valid.get("sharpe_ratio", 0) if m_valid else 0
            tr_v = m_valid.get("total_trades",  0) if m_valid else 0
            wr_v = m_valid.get("win_rate",       0) if m_valid else 0

            flag = "⭐" if sh_v > 0.581 else ("✅" if sh_v > 0 else "  ")
            if verbose:
                print(f"         {flag} Sharpe train={sh_t:.3f} valid={sh_v:.3f} | WR={wr_v:.1f}% | Trades valid={tr_v}")

            if tr_v < SANITY["min_trades"]:
                sin_trades += 1
            exitosos += 1

        except Exception as e:
            mark_failed(job_id, e)
            fallidos += 1
            if verbose:
                print(f"         ❌ Error: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Pipeline terminado — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Batch ID:        {batch_id}")
    print(f"   Exitosos:        {exitosos}")
    print(f"   Con pocos trades: {sin_trades} (incluidos en exitosos)")
    print(f"   Fallidos:        {fallidos}")

    # Exportar al dashboard automáticamente
    print(f"\n   📤 Exportando al dashboard...")
    try:
        script_dir  = os.path.dirname(os.path.abspath(__file__))
        export_script = os.path.join(script_dir, "export_to_json.py")
        result = subprocess.run(
            [sys.executable, export_script],
            capture_output=True, text=True,
            cwd=os.path.dirname(script_dir)
        )
        if result.returncode == 0:
            print(f"   ✅ Dashboard actualizado")
        else:
            print(f"   ⚠️  Export falló: {result.stderr.strip()}")
    except Exception as e:
        print(f"   ⚠️  Export falló: {e}")

    print(f"\n   Siguiente paso:")
    print(f"   python3 scripts/generar_batch_report.py")
    print(f"{'='*60}\n")


def show_status():
    if not os.path.exists(UNIFIED_DB):
        print(f"❌ No se encontró {UNIFIED_DB}. Ejecutar migrate_to_unified_db.py primero.")
        return
    status = get_queue_status()
    total = sum(status.values())
    print(f"\n📊 Estado de la cola ({total} jobs total):")
    for s, n in sorted(status.items()):
        icon = {"pending": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}.get(s, "❓")
        print(f"   {icon} {s:<10} {n:>5}")
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Runner — Coco Stonks Lab")
    parser.add_argument("--limit",  type=int, help="Máximo de jobs a procesar")
    parser.add_argument("--status", action="store_true", help="Ver estado de la cola")
    parser.add_argument("--quiet",  action="store_true", help="Menos output")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        run_pipeline(limit=args.limit, verbose=not args.quiet)
