"""
migrate_sqlite_to_pg.py — Migración de datos SQLite → PostgreSQL
================================================================
Coco Stonks Lab — Fase 2: AutoLab

Migra las tablas de autolab del coco_lab.db (SQLite) a autolab_db (PostgreSQL).
Solo migra autolab_cycles y autolab_learnings si existen en SQLite.
Las tablas de backtesting (runs, trades, etc.) permanecen en SQLite.

Uso:
  python3 migrate_sqlite_to_pg.py --check     # ver qué hay en SQLite
  python3 migrate_sqlite_to_pg.py --migrate   # migrar datos
  python3 migrate_sqlite_to_pg.py --verify    # verificar migración
"""

import argparse
import json
import os
import sqlite3
import sys

import psycopg2
import psycopg2.extras

SQLITE_PATH = os.environ.get("SQLITE_DB_PATH", "../../data/coco_lab.db")
PG_DSN = os.environ.get("SUPABASE_DB_URL") or os.environ.get("PG_DSN")


def get_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_postgres():
    if not PG_DSN:
        raise ValueError("Falta SUPABASE_DB_URL o PG_DSN en variables de entorno")
    return psycopg2.connect(PG_DSN, cursor_factory=psycopg2.extras.RealDictCursor)


def check_sqlite():
    """Verifica qué tablas de autolab existen en SQLite."""
    conn = get_sqlite()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'autolab%'")
    tables = [row[0] for row in cur.fetchall()]

    print(f"\nTablas autolab en SQLite ({SQLITE_PATH}):")
    if not tables:
        print("  (ninguna — SQLite solo tiene datos de backtesting)")
    else:
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            print(f"  {t}: {count} filas")

    print(f"\nTablas de backtesting (permanecen en SQLite):")
    for table in ["experiments", "runs", "trades", "batches", "candles", "candle_states"]:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE 1=1")
        try:
            count = cur.fetchone()[0]
            print(f"  {table}: {count} filas")
        except Exception:
            print(f"  {table}: no existe")

    conn.close()


def migrate():
    """Migra datos de autolab desde SQLite a PostgreSQL."""
    if not PG_DSN:
        print("ERROR: Falta PG_DSN / SUPABASE_DB_URL. No se puede conectar a PostgreSQL.")
        sys.exit(1)

    sqlite = get_sqlite()
    pg = get_postgres()
    pg_cur = pg.cursor()

    print(f"\nMigrando autolab_cycles...")
    try:
        sqlite_cur = sqlite.cursor()
        sqlite_cur.execute("SELECT * FROM autolab_cycles")
        rows = sqlite_cur.fetchall()
        print(f"  {len(rows)} registros encontrados en SQLite")

        for row in rows:
            d = dict(row)
            pg_cur.execute("""
                INSERT INTO autolab_cycles
                    (cycle_num, session_id, phase, started_at, finished_at,
                     llm_provider, llm_tokens_in, llm_tokens_out,
                     jobs_queued, jobs_completed, best_fitness, best_sharpe_oos,
                     beat_benchmark, notes, error_msg)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (
                d.get("cycle_num"), d.get("session_id"), d.get("phase"),
                d.get("started_at"), d.get("finished_at"),
                d.get("llm_provider"), d.get("llm_tokens_in", 0), d.get("llm_tokens_out", 0),
                d.get("jobs_queued", 0), d.get("jobs_completed", 0),
                d.get("best_fitness"), d.get("best_sharpe"),
                bool(d.get("beat_benchmark", 0)),
                d.get("notes"), d.get("error_msg"),
            ))
        print(f"  OK — {len(rows)} ciclos migrados")
    except sqlite3.OperationalError:
        print("  autolab_cycles no existe en SQLite (OK — se crea desde cero en PG)")

    print(f"\nMigrando autolab_learnings...")
    try:
        sqlite_cur = sqlite.cursor()
        sqlite_cur.execute("SELECT * FROM autolab_learnings")
        rows = sqlite_cur.fetchall()
        print(f"  {len(rows)} registros encontrados en SQLite")

        for row in rows:
            d = dict(row)
            pg_cur.execute("""
                INSERT INTO autolab_learnings
                    (cycle_num, session_id, category, content, confidence, superseded)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (
                d.get("cycle_num"), d.get("session_id"),
                d.get("category"), d.get("content"),
                d.get("confidence", 0.5), bool(d.get("superseded", 0)),
            ))
        print(f"  OK — {len(rows)} learnings migrados")
    except sqlite3.OperationalError:
        print("  autolab_learnings no existe en SQLite (OK — se crea desde cero en PG)")

    pg.commit()
    pg.close()
    sqlite.close()
    print("\nMigración completada.")


def verify():
    """Verifica que la migración fue exitosa."""
    pg = get_postgres()
    cur = pg.cursor()

    print("\nEstado de autolab_db (PostgreSQL):")
    for table in ["autolab_cycles", "autolab_learnings", "opus_insights",
                  "search_history", "external_research", "topic_rotation_state"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()["count"]
            print(f"  {table}: {count} filas")
        except Exception as e:
            print(f"  {table}: ERROR — {e}")

    # Verificar tópicos de rotación
    cur.execute("SELECT topic, last_searched, search_count FROM topic_rotation_state ORDER BY topic")
    topics = cur.fetchall()
    print(f"\nTópicos de rotación: {len(topics)}")
    for t in topics:
        status = f"(buscado {t['search_count']}x)" if t['search_count'] > 0 else "(nunca buscado)"
        print(f"  {t['topic']} {status}")

    pg.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migración SQLite → PostgreSQL para AutoLab")
    parser.add_argument("--check",   action="store_true", help="Ver qué hay en SQLite")
    parser.add_argument("--migrate", action="store_true", help="Migrar datos")
    parser.add_argument("--verify",  action="store_true", help="Verificar estado de PostgreSQL")
    args = parser.parse_args()

    if args.check:
        check_sqlite()
    elif args.migrate:
        migrate()
    elif args.verify:
        verify()
    else:
        parser.print_help()
