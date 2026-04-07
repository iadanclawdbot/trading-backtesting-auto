# export_to_json.py
# Reads coco_lab.db and exports JSON files to ../dashboard-lab/public/data/
# Run this after every backtesting phase: python export_to_json.py

import sqlite3
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import UNIFIED_DB

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "dashboard-lab", "public", "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(UNIFIED_DB)
conn.row_factory = sqlite3.Row

def table_exists(conn, name):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0

# Export trades
trades = []
if table_exists(conn, "trades"):
    trades = [dict(r) for r in conn.execute(
        "SELECT * FROM trades ORDER BY run_id, trade_num"
    ).fetchall()]

# Export runs
runs = []
if table_exists(conn, "runs"):
    runs = [dict(r) for r in conn.execute(
        "SELECT * FROM runs ORDER BY created_at DESC"
    ).fetchall()]

# Build summary from latest valid run
summary = {}
if runs:
    latest = runs[0]
    summary = {
        "capital_inicial": 250.0,
        "capital_actual":  latest.get("capital_final", 250.0),
        "pnl_total_usdt":  latest.get("pnl_total", 0),
        "pnl_pct":         latest.get("pnl_pct", 0),
        "win_rate":        latest.get("win_rate", 0),
        "sharpe_ratio":    latest.get("sharpe_ratio", 0),
        "max_drawdown":    latest.get("max_drawdown", 0),
        "profit_factor":   latest.get("profit_factor", 0),
        "total_trades":    latest.get("total_trades", 0),
        "total_runs":      len(runs),
        "last_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

# Export batches — agrupa runs por batch_id para evolución histórica
batches = []
if table_exists(conn, "batches") and table_exists(conn, "runs"):
    batches = [dict(r) for r in conn.execute("""
        SELECT
            b.batch_id,
            b.created_at,
            b.notes,
            COUNT(r.id)                                                        AS total_runs,
            SUM(CASE WHEN r.dataset = 'valid' THEN 1 ELSE 0 END)              AS valid_runs,
            MAX(CASE WHEN r.dataset = 'valid' THEN r.sharpe_ratio  END)       AS best_sharpe_oos,
            AVG(CASE WHEN r.dataset = 'valid' THEN r.sharpe_ratio  END)       AS avg_sharpe_oos,
            MAX(CASE WHEN r.dataset = 'valid' THEN r.win_rate      END)       AS best_wr_oos,
            MAX(CASE WHEN r.dataset = 'valid' THEN r.total_trades  END)       AS max_trades_oos
        FROM batches b
        LEFT JOIN runs r ON r.batch_id = b.batch_id
        GROUP BY b.batch_id
        ORDER BY b.created_at DESC
    """).fetchall()]

json.dump(trades,  open(os.path.join(OUTPUT_DIR, "trades.json"),  "w"), indent=2, default=str)
json.dump(runs,    open(os.path.join(OUTPUT_DIR, "runs.json"),    "w"), indent=2, default=str)
json.dump(summary, open(os.path.join(OUTPUT_DIR, "summary.json"), "w"), indent=2, default=str)
json.dump(batches, open(os.path.join(OUTPUT_DIR, "batches.json"), "w"), indent=2, default=str)

conn.close()

print(f"✅ Exportado a {OUTPUT_DIR}/")
print(f"   trades.json  : {len(trades)} trades")
print(f"   runs.json    : {len(runs)} runs")
print(f"   batches.json : {len(batches)} batches")
print(f"   summary.json : capital ${summary.get('capital_actual', 250):.2f} | win rate {summary.get('win_rate', 0):.1f}%")
