#!/usr/bin/env python3
# =============================================================================
# GENERAR BATCH REPORT — Coco Stonks Lab
# scripts/generar_batch_report.py
#
# Lee los resultados del último batch en experiments.db y genera un reporte
# Markdown compacto para que el modelo analice sin leer miles de líneas.
#
# Uso:
#   python3 scripts/generar_batch_report.py              # último batch
#   python3 scripts/generar_batch_report.py --top 30     # top 30 en vez de 20
#   python3 scripts/generar_batch_report.py --all        # todos los jobs done
# =============================================================================

import sqlite3
import json
import sys
import os
import argparse
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import UNIFIED_DB, SANITY

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "resultados")

# Benchmark actual — actualizar si cambia el benchmark en historico_aprendizajes.md
BENCHMARK = {
    "sharpe": 1.593,
    "wr":     63.2,
    "dd":     -4.96,
    "trades": 19,
    "nombre": "vwap_pullback campeón ($338.30)",
}


def cargar_jobs_done(solo_recientes=True):
    """Carga todos los jobs con status=done, con métricas via JOIN a runs."""
    conn = sqlite3.connect(UNIFIED_DB)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT
            e.id, e.strategy, e.params_json, e.notes, e.finished_at,
            r_train.sharpe_ratio  AS sharpe_train,
            r_train.win_rate      AS wr_train,
            r_train.total_trades  AS trades_train,
            r_train.max_drawdown  AS dd_train,
            r_train.capital_inicial    AS capital_inicial,
            r_train.capital_final      AS capital_final_train,
            r_valid.sharpe_ratio  AS sharpe_valid,
            r_valid.win_rate      AS wr_valid,
            r_valid.total_trades  AS trades_valid,
            r_valid.max_drawdown  AS dd_valid,
            r_valid.capital_final      AS capital_final_valid
        FROM experiments e
        LEFT JOIN runs r_train ON r_train.experiment_id = e.id AND r_train.dataset = 'train'
        LEFT JOIN runs r_valid ON r_valid.experiment_id = e.id AND r_valid.dataset = 'valid'
        WHERE e.status = 'done'
        ORDER BY e.finished_at DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def capital_str(j):
    """Genera la línea de progresión de capital para un job."""
    ci   = j.get("capital_inicial") or 250.0
    ct   = j.get("capital_final_train")
    cv   = j.get("capital_final_valid")
    if ct is None or cv is None:
        return "N/A"
    pct_t = (ct - ci) / ci * 100
    pct_v = (cv - ci) / ci * 100
    # Encadenado: capital tras train se usa como base del valid
    cv_enc = ct * (1 + pct_v / 100)
    pct_enc = (cv_enc - ci) / ci * 100
    return (f"${ci:.0f}→${ct:.2f} 2024 ({pct_t:+.2f}%) | "
            f"${ci:.0f}→${cv:.2f} 2025 ({pct_v:+.2f}%) | "
            f"encadenado→${cv_enc:.2f} ({pct_enc:+.2f}%)")


def detectar_patrones(jobs_top):
    """
    Analiza los parámetros del top de jobs y detecta valores dominantes.
    Retorna un dict con el parámetro y el valor más frecuente.
    """
    all_params = []
    for job in jobs_top:
        try:
            p = json.loads(job["params_json"])
            all_params.append(p)
        except Exception:
            continue

    if not all_params:
        return {}

    claves = set()
    for p in all_params:
        claves.update(p.keys())

    patrones = {}
    for clave in sorted(claves):
        valores = [str(p.get(clave, "N/A")) for p in all_params]
        counter = Counter(valores)
        top_val, top_n = counter.most_common(1)[0]
        pct = top_n / len(all_params) * 100
        if pct >= 40:  # solo reportar si domina en ≥40%
            patrones[clave] = {"valor": top_val, "pct": round(pct, 0), "n": top_n}

    return patrones


def generar_reporte(top_n=20, solo_recientes=True):
    jobs = cargar_jobs_done(solo_recientes)

    if not jobs:
        print("⚠️  No hay jobs completados en la cola.")
        return

    total_done    = len(jobs)
    superan_bench = [j for j in jobs if (j["sharpe_valid"] or -99) > BENCHMARK["sharpe"]]
    sharpe_pos    = [j for j in jobs if (j["sharpe_valid"] or -99) > 0]
    validos       = [j for j in jobs if (j["trades_valid"] or 0) >= SANITY["min_trades"]]

    # Ordenar por sharpe_valid descendente
    jobs_sorted = sorted(jobs, key=lambda j: j["sharpe_valid"] or -99, reverse=True)
    top_jobs    = jobs_sorted[:top_n]

    # Detectar patrones en el top
    patrones = detectar_patrones(top_jobs)

    # =========================================================================
    # CONSTRUIR EL REPORTE
    # =========================================================================
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")
    lineas = []

    lineas.append(f"# Batch Report — Coco Stonks Lab")
    lineas.append(f"Generado: {now} | Total jobs completados: {total_done}")
    lineas.append("")

    # --- Resumen ejecutivo ---
    lineas.append("## Resumen Ejecutivo")
    lineas.append("")
    lineas.append(f"| Métrica | Valor |")
    lineas.append(f"|---------|-------|")
    lineas.append(f"| Jobs completados | {total_done} |")
    lineas.append(f"| Con ≥{SANITY['min_trades']} trades válidos (OOS) | {len(validos)} |")
    lineas.append(f"| Con Sharpe OOS > 0 | {len(sharpe_pos)} |")
    lineas.append(f"| **Superan benchmark ({BENCHMARK['sharpe']})** | **{len(superan_bench)}** |")
    lineas.append("")

    # --- Benchmark de referencia ---
    lineas.append("## Benchmark Actual (V2)")
    lineas.append("")
    lineas.append(f"| Métrica | Valor |")
    lineas.append(f"|---------|-------|")
    lineas.append(f"| Estrategia | {BENCHMARK['nombre']} |")
    lineas.append(f"| Sharpe OOS | {BENCHMARK['sharpe']} |")
    lineas.append(f"| Win Rate OOS | {BENCHMARK['wr']}% |")
    lineas.append(f"| Max DD OOS | {BENCHMARK['dd']}% |")
    lineas.append(f"| Trades OOS | {BENCHMARK['trades']} |")
    lineas.append("")

    # --- Top N resultados ---
    lineas.append(f"## Top {top_n} Configuraciones (por Sharpe OOS)")
    lineas.append("")
    lineas.append("| # | Strategy | Sharpe Train | Sharpe OOS | WR OOS | Trades OOS | DD OOS | Supera Bench | Parámetros clave |")
    lineas.append("|---|----------|-------------|------------|--------|------------|--------|--------------|-----------------|")

    for rank, j in enumerate(top_jobs, 1):
        sh_t  = f"{j['sharpe_train']:.3f}"  if j["sharpe_train"]  is not None else "N/A"
        sh_v  = f"{j['sharpe_valid']:.3f}"  if j["sharpe_valid"]  is not None else "N/A"
        wr_v  = f"{j['wr_valid']:.1f}%"     if j["wr_valid"]      is not None else "N/A"
        tr_v  = str(j["trades_valid"] or 0)
        dd_v  = f"{j['dd_valid']:.1f}%"     if j["dd_valid"]      is not None else "N/A"
        bench = "⭐ SÍ" if (j["sharpe_valid"] or -99) > BENCHMARK["sharpe"] else "No"

        # Resumir params
        try:
            p = json.loads(j["params_json"])
            param_str = " ".join(f"{k}={v}" for k, v in list(p.items())[:4])
        except Exception:
            param_str = "N/A"

        lineas.append(
            f"| {rank} | {j['strategy']} | {sh_t} | {sh_v} | {wr_v} | {tr_v} | {dd_v} | {bench} | `{param_str}` |"
        )

    lineas.append("")

    # --- Patrones detectados ---
    if patrones:
        lineas.append("## Patrones en el Top")
        lineas.append("")
        lineas.append("Parámetros que dominan consistentemente en las mejores configuraciones:")
        lineas.append("")
        for param, info in patrones.items():
            lineas.append(f"- **{param}={info['valor']}** aparece en {info['n']}/{top_n} configs del top ({info['pct']}%)")
        lineas.append("")

    # --- Configs que superan benchmark ---
    if superan_bench:
        lineas.append(f"## Configs que Superan el Benchmark (Sharpe OOS > {BENCHMARK['sharpe']})")
        lineas.append("")
        for j in sorted(superan_bench, key=lambda x: x["sharpe_valid"] or 0, reverse=True):
            try:
                p = json.loads(j["params_json"])
                params_full = json.dumps(p, indent=2)
            except Exception:
                params_full = j["params_json"]
            lineas.append(f"### Job #{j['id']} — {j['strategy']}")
            lineas.append(f"- Sharpe: train={j['sharpe_train']:.3f} | OOS={j['sharpe_valid']:.3f}")
            lineas.append(f"- WR OOS: {j['wr_valid']:.1f}% | Trades: {j['trades_valid']} | DD: {j['dd_valid']:.1f}%")
            lineas.append(f"- Capital: {capital_str(j)}")
            lineas.append(f"- Parámetros completos:")
            lineas.append(f"```json")
            lineas.append(params_full)
            lineas.append(f"```")
            lineas.append("")

    # --- Análisis adicional ---
    lineas.append("## Distribución de Resultados")
    lineas.append("")

    rangos = {
        "Sharpe OOS > 0.5": sum(1 for j in jobs if (j["sharpe_valid"] or -99) > 0.5),
        "Sharpe OOS 0-0.5": sum(1 for j in jobs if 0 < (j["sharpe_valid"] or -99) <= 0.5),
        "Sharpe OOS < 0": sum(1 for j in jobs if (j["sharpe_valid"] or -99) < 0),
        f"Trades OOS < {SANITY['min_trades']} (inválidos)": sum(1 for j in jobs if (j["trades_valid"] or 0) < SANITY["min_trades"]),
    }
    for desc, n in rangos.items():
        lineas.append(f"- {desc}: **{n}** ({n/total_done*100:.0f}%)")

    lineas.append("")
    lineas.append("---")
    lineas.append(f"*Generado por generar_batch_report.py · {now}*")

    # Guardar archivo — nombre fijo, se sobreescribe cada vez.
    # El dato completo está en coco_lab.db; el .md es una vista temporal.
    os.makedirs(RESULTS_DIR, exist_ok=True)
    nombre = "batch_report_latest.md"
    ruta = os.path.join(RESULTS_DIR, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    print(f"\n✅ Reporte generado: {ruta}")
    print(f"   {total_done} jobs | {len(superan_bench)} superan benchmark | {len(validos)} estadísticamente válidos")
    print(f"\n   Pasá este archivo al modelo para análisis:")
    print(f"   resultados/{nombre}\n")
    return ruta


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera batch report para el modelo")
    parser.add_argument("--top",  type=int, default=20, help="Cuántos resultados incluir en el top (default: 20)")
    parser.add_argument("--all",  action="store_true",  help="Incluir todos los jobs (no solo recientes)")
    args = parser.parse_args()

    generar_reporte(top_n=args.top, solo_recientes=not args.all)
