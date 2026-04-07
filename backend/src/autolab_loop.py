"""
autolab_loop.py — Orquestador Autónomo (CLI local)
====================================================
Coco Stonks Lab — Fase 2: AutoLab

Loop de mejora continua que puede correr desde la terminal o
ser invocado por n8n via Execute Command.

Uso:
  python3 autolab_loop.py                       # 50 ciclos, 10 jobs/ciclo
  python3 autolab_loop.py --cycles 100 --jobs 5
  python3 autolab_loop.py --dry-run             # LLM calls pero sin backtests
  python3 autolab_loop.py --resume AUTO_20260325_220000
  python3 autolab_loop.py --status
  python3 autolab_loop.py --report

Este script es el equivalente de "program.md" en karpathy/autoresearch:
define el comportamiento del agente autónomo.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import httpx

# Base URL del autolab_api.py
API_BASE = os.environ.get("AUTOLAB_API_URL", "http://localhost:8000")


# ==============================================================================
# CLIENTE HTTP SIMPLE (para comunicarse con autolab_api.py)
# ==============================================================================

class AutoLabClient:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.client = httpx.Client(timeout=700)  # timeout largo para /run-pipeline

    def get(self, path: str, **params) -> dict:
        r = self.client.get(f"{self.base}{path}", params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, body: dict) -> dict:
        r = self.client.post(f"{self.base}{path}", json=body)
        r.raise_for_status()
        return r.json()

    def close(self):
        self.client.close()


# ==============================================================================
# UTILIDADES
# ==============================================================================

def log(msg: str, level: str = "INFO"):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    prefix = {"INFO": "  ", "STAR": "★ ", "WARN": "⚠ ", "ERR": "✗ "}.get(level, "  ")
    print(f"[{ts}] {prefix}{msg}", flush=True)


def compute_fitness_simple(r: dict) -> float:
    """Versión simplificada del fitness para el loop (sin importar autolab_fitness)."""
    import math
    sharpe = r.get("sharpe_oos", r.get("sharpe_ratio", 0))
    trades = r.get("trades_oos", r.get("total_trades", 0))
    wr = r.get("wr_oos", r.get("win_rate", 0))
    sharpe_t = r.get("sharpe_train", 0)
    dd = r.get("dd_oos", r.get("max_drawdown", 0))

    if trades < 15: return 0.0
    if wr < 0.30 or wr > 0.75: return 0.0
    if dd < -20.0: return 0.0

    sharpe_c = sharpe * 0.70
    trade_b = min(0.25, max(0.0, math.log(max(trades, 15) / 15) * 0.2))
    cons = min(sharpe / sharpe_t, 1.0) * 0.10 if sharpe_t > 0 and sharpe > 0 else 0.0
    dd_b = max(0.0, (10.0 + dd) / 10.0) * 0.05
    return max(0.0, sharpe_c + trade_b + cons + dd_b)


BENCHMARK_FITNESS = 1.193  # V5 Portfolio — actualizar manualmente con cada nuevo campeón


# ==============================================================================
# LOOP PRINCIPAL
# ==============================================================================

def run_loop(
    session_id: str,
    cycles: int,
    jobs_per_cycle: int,
    dry_run: bool,
    starting_cycle: int = 1,
):
    """
    Ejecuta el loop autónomo de mejora continua.

    Cada ciclo:
    1. Obtiene contexto de la DB
    2. LLM analiza resultados
    3. LLM genera hipótesis
    4. Encola experimentos
    5. Ejecuta backtests
    6. Evalúa resultados
    7. LLM extrae learnings
    """
    from autolab_brain import AutoLabBrain, extract_dead_ends

    api = AutoLabClient(API_BASE)
    brain = AutoLabBrain()

    current_benchmark = BENCHMARK_FITNESS
    last_batch_id = None
    all_learnings = []
    session_best = {"fitness": 0.0, "cycle": 0, "config": None}
    total_jobs_run = 0

    print(f"\n{'='*65}")
    print(f"  AutoLab — Session {session_id}")
    print(f"  Ciclos: {starting_cycle} → {cycles} | Jobs/ciclo: {jobs_per_cycle}")
    print(f"  Benchmark: {current_benchmark:.3f} {'[DRY RUN]' if dry_run else ''}")
    print(f"{'='*65}\n")

    for cycle in range(starting_cycle, cycles + 1):
        cycle_start = time.time()
        log(f"=== CICLO {cycle}/{cycles} ===")

        try:
            # ------------------------------------------------------------------
            # FASE 1: CONTEXTO
            # ------------------------------------------------------------------
            log("Obteniendo contexto...")
            ctx = api.get(
                "/context",
                top_n=20,
                last_cycle_batch=last_batch_id or "",
            )
            top_results = ctx.get("top_results", [])
            last_cycle_results = ctx.get("last_cycle_results", [])
            opus_insights = ctx.get("opus_insights", [])
            all_learnings = ctx.get("learnings", [])
            dead_ends = extract_dead_ends(all_learnings)

            # ------------------------------------------------------------------
            # FASE 2: ANALIZAR
            # ------------------------------------------------------------------
            log("Analizando con Nemotron...")
            analysis = brain.analyze(
                last_cycle_results=last_cycle_results,
                all_time_top=top_results,
                learnings=all_learnings,
                opus_insights=opus_insights,
                cycle_num=cycle,
            )
            direction = analysis.get("suggested_direction", "")
            log(f"Dirección: {direction[:80]}...")

            # ------------------------------------------------------------------
            # FASE 3: HIPOTETIZAR
            # ------------------------------------------------------------------
            log("Generando hipótesis con GLM-5...")
            configs = brain.hypothesize(
                analysis=analysis,
                dead_ends=dead_ends,
                n_experiments=jobs_per_cycle,
                cycle_num=cycle,
            )
            log(f"{len(configs)} configs válidas generadas")

            if not configs:
                log("Sin configs válidas, saltando ciclo", "WARN")
                continue

            # ------------------------------------------------------------------
            # FASE 4: ENCOLAR
            # ------------------------------------------------------------------
            log(f"Encolando {len(configs)} experimentos...")
            queue_resp = api.post("/experiments", {
                "experiments": configs,
                "session_id": session_id,
                "cycle_num": cycle,
            })
            log(f"Encolados: {queue_resp.get('queued', 0)}")

            # ------------------------------------------------------------------
            # FASE 5: EJECUTAR
            # ------------------------------------------------------------------
            if dry_run:
                log("[DRY RUN] Saltando ejecución de backtests", "WARN")
                last_batch_id = None
                cycle_results = []
            else:
                log(f"Ejecutando {len(configs)} backtests...")
                run_resp = api.post("/run-pipeline", {
                    "limit": len(configs),
                    "session_id": session_id,
                    "cycle_num": cycle,
                })
                last_batch_id = run_resp.get("batch_id")
                duration = run_resp.get("duration_seconds", 0)
                log(f"Pipeline completado en {duration:.0f}s | batch_id: {last_batch_id}")

                # Obtener resultados del ciclo
                cycle_results = []
                if last_batch_id:
                    res = api.get("/results/cycle", batch_id=last_batch_id)
                    cycle_results = res.get("results", [])

                total_jobs_run += len(configs)

            # ------------------------------------------------------------------
            # FASE 6: EVALUAR
            # ------------------------------------------------------------------
            if cycle_results:
                # Separar train y valid, calcular fitness para cada valid run
                valid_results = [r for r in cycle_results if r.get("dataset") == "valid"]
                train_map = {r.get("experiment_id"): r for r in cycle_results
                             if r.get("dataset") == "train"}

                best_fitness = 0.0
                best_result = None

                for r in valid_results:
                    train = train_map.get(r.get("experiment_id"), {})
                    r["sharpe_train"] = train.get("sharpe_ratio", 0)
                    r["sharpe_oos"] = r.get("sharpe_ratio", 0)
                    r["trades_oos"] = r.get("total_trades", 0)
                    r["wr_oos"] = r.get("win_rate", 0)
                    r["dd_oos"] = r.get("max_drawdown", 0)

                    fit = compute_fitness_simple(r)
                    r["fitness"] = fit

                    if fit > best_fitness:
                        best_fitness = fit
                        best_result = r

                log(f"Mejor fitness ciclo: {best_fitness:.3f} (benchmark: {current_benchmark:.3f})")

                if best_fitness > current_benchmark:
                    current_benchmark = best_fitness
                    log(
                        f"NUEVO CAMPEÓN — fitness={best_fitness:.3f} | "
                        f"strategy={best_result.get('strategy')} | "
                        f"sharpe_oos={best_result.get('sharpe_oos', 0):.3f} | "
                        f"trades={best_result.get('trades_oos', 0)}",
                        "STAR"
                    )
                    if best_fitness > session_best["fitness"]:
                        session_best = {
                            "fitness": best_fitness,
                            "cycle": cycle,
                            "config": best_result,
                        }
            else:
                valid_results = []
                best_result = None

            # ------------------------------------------------------------------
            # FASE 7: APRENDER
            # ------------------------------------------------------------------
            log("Extrayendo learnings con Kimi K2.5...")
            new_learnings = brain.learn(
                cycle_results=valid_results if not dry_run else [],
                best_of_cycle=best_result,
                cycle_num=cycle,
                existing_learnings=all_learnings,
            )

            if new_learnings:
                save_resp = api.post("/learnings", {
                    "learnings": new_learnings,
                    "session_id": session_id,
                    "cycle_num": cycle,
                })
                log(f"{save_resp.get('saved', 0)} learnings guardados en DB")

            # ------------------------------------------------------------------
            # RESUMEN DEL CICLO
            # ------------------------------------------------------------------
            elapsed = time.time() - cycle_start
            stats = brain.get_stats()
            log(
                f"Ciclo {cycle} completado en {elapsed:.0f}s | "
                f"LLM calls: {stats['total_calls']} | "
                f"Tokens: {stats['total_tokens_in']+stats['total_tokens_out']:,}"
            )

        except KeyboardInterrupt:
            log("Interrumpido por usuario", "WARN")
            break
        except Exception as e:
            log(f"Error en ciclo {cycle}: {e}", "ERR")
            import traceback
            traceback.print_exc()
            # El loop nunca se rompe por un error — continúa al siguiente ciclo
            time.sleep(10)
            continue

    # ==========================================================================
    # RESUMEN FINAL DE SESIÓN
    # ==========================================================================
    stats = brain.get_stats()
    print(f"\n{'='*65}")
    print(f"  SESSION COMPLETE — {session_id}")
    print(f"  Ciclos: {cycles} | Jobs ejecutados: {total_jobs_run}")
    print(f"  LLM calls: {stats['total_calls']} | Tokens: {stats['total_tokens']:,}")
    if session_best["fitness"] > BENCHMARK_FITNESS:
        print(f"  ★ Nuevo campeón en ciclo {session_best['cycle']}: "
              f"fitness={session_best['fitness']:.3f}")
    else:
        print(f"  Sin nuevo campeón (mejor: {session_best['fitness']:.3f})")
    print(f"{'='*65}\n")

    brain.close()
    api.close()


# ==============================================================================
# COMANDOS DE UTILIDAD
# ==============================================================================

def show_status():
    """Muestra el estado actual de la cola y últimos resultados."""
    api = AutoLabClient(API_BASE)
    try:
        status = api.get("/status")
        print(f"\nEstado del sistema:")
        print(f"  Queue: {json.dumps(status.get('queue', {}), indent=4)}")
        best = status.get("best_oos")
        if best:
            print(f"  Mejor OOS: Sharpe={best.get('sharpe_ratio', 0):.3f} | "
                  f"Trades={best.get('total_trades', 0)} | "
                  f"Strategy={best.get('strategy', '?')}")
        health = api.get("/health")
        print(f"  SQLite: {'OK' if health['sqlite'] else 'ERROR'}")
        print(f"  PostgreSQL: {'OK' if health['postgresql'] else 'NO DISPONIBLE'}")
    finally:
        api.close()


def show_report():
    """Genera un reporte de la sesión actual."""
    api = AutoLabClient(API_BASE)
    try:
        ctx = api.get("/context", top_n=10)
        print(f"\n## Reporte AutoLab — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"\n### Top 10 Resultados OOS (All-Time)")
        for i, r in enumerate(ctx.get("top_results", [])[:10], 1):
            print(f"  {i}. {r.get('strategy','?')} | "
                  f"Sharpe={r.get('sharpe_oos',0):.3f} | "
                  f"Trades={r.get('trades_oos',0)} | "
                  f"WR={r.get('wr_oos',0)*100:.0f}%")

        learnings = ctx.get("learnings", [])
        if learnings:
            print(f"\n### Últimos Learnings ({len(learnings)} total)")
            for l in learnings[:10]:
                print(f"  [{l.get('category','?')}] {l.get('content','')}")

        opus = ctx.get("opus_insights", [])
        if opus:
            print(f"\n### Directivas Opus ({len(opus)} activas)")
            for ins in opus:
                print(f"  [P{ins.get('priority',1)}] {ins.get('title','')}")
    finally:
        api.close()


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AutoLab — Loop de mejora continua de estrategias de trading"
    )
    parser.add_argument("--cycles",   type=int, default=50,
                        help="Número de ciclos a ejecutar (default: 50)")
    parser.add_argument("--jobs",     type=int, default=10,
                        help="Experimentos por ciclo (default: 10)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Hace calls LLM pero no ejecuta backtests")
    parser.add_argument("--resume",   type=str,
                        help="Resumir sesión existente (SESSION_ID)")
    parser.add_argument("--status",   action="store_true",
                        help="Mostrar estado del sistema y salir")
    parser.add_argument("--report",   action="store_true",
                        help="Mostrar reporte de resultados y salir")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.report:
        show_report()
        return

    session_id = args.resume or f"AUTO_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    starting_cycle = 1

    if args.resume:
        print(f"Resumiendo sesión: {session_id}")
        # TODO: recuperar el ciclo donde se quedó desde autolab_cycles en PostgreSQL

    run_loop(
        session_id=session_id,
        cycles=args.cycles,
        jobs_per_cycle=args.jobs,
        dry_run=args.dry_run,
        starting_cycle=starting_cycle,
    )


if __name__ == "__main__":
    main()
