"""
autolab_brain.py — LLM Multi-Provider con Fallback + Prompts
=============================================================
Coco Stonks Lab — Fase 2: AutoLab

Abstracción de los 3 proveedores NVIDIA Build (free tier).
Todos usan el mismo endpoint OpenAI-compatible en integrate.api.nvidia.com/v1.

Modelos disponibles (free developer tier — 45 RPM):
  - Nemotron Super 120B:  1M ctx, ideal para ANALIZAR (contexto largo)
  - GLM-5 744B MoE:       32K ctx, ideal para HIPOTETIZAR (reasoning)
  - Kimi K2.5 1T MoE:     32K ctx, ideal para APRENDER (síntesis)
"""

import json
import os
import time
import hashlib
import re
from typing import Optional
from datetime import datetime

import httpx  # pip install httpx

from autolab_fitness import (
    BENCHMARK, PARAMETER_SPACE, REQUIRED_PARAMS, ENABLED_STRATEGIES,
    validate_experiment_config, get_parameter_space_summary,
)


# ==============================================================================
# CONFIGURACIÓN DE PROVIDERS
# ==============================================================================

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

MODELS = {
    "analyze": {
        "id": "nvidia/nemotron-3-super-120b-a12b",
        "ctx_window": 1_000_000,
        "best_for": "Analizar historial completo (contexto 1M tokens)",
        "max_tokens": 2048,
    },
    "hypothesize": {
        "id": "z-ai/glm5",
        "ctx_window": 32_768,
        "best_for": "Generar hipótesis complejas (modelo de reasoning)",
        "max_tokens": 4096,
    },
    "learn": {
        "id": "moonshotai/kimi-k2.5",
        "ctx_window": 32_768,
        "best_for": "Sintetizar learnings (multimodal, síntesis eficiente)",
        "max_tokens": 2048,
    },
}

# Rate limit conservador: 45 RPM = 1 request cada 1.33s
# Usamos 2s de delay entre calls para margen de seguridad
INTER_CALL_DELAY_S = 2.0
MAX_RETRIES = 2
RETRY_WAIT_S = 60.0  # wait si 429


# ==============================================================================
# CLIENTE LLM
# ==============================================================================

class AutoLabBrain:
    """
    Orquesta las 3 fases de razonamiento LLM:
      A. analyze()     — Analiza resultados recientes + historial
      B. hypothesize() — Genera N configs de experimento como JSON
      C. learn()       — Extrae learnings estructurados del ciclo

    Maneja rate limits, retries y logging de tokens.
    """

    def __init__(self):
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("Falta NVIDIA_API_KEY en las variables de entorno")

        self.client = httpx.Client(timeout=60.0)
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.call_count = 0
        self._last_call_time = 0.0

    def _wait_for_rate_limit(self):
        """Asegura el mínimo delay entre calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < INTER_CALL_DELAY_S:
            time.sleep(INTER_CALL_DELAY_S - elapsed)

    def _call_llm(self, phase: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Llama al modelo asignado para esta fase. Con retry en 429.

        Returns:
            El contenido del mensaje del asistente, o None si falla.
        """
        model = MODELS[phase]
        payload = {
            "model": model["id"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens": model["max_tokens"],
            "temperature": 0.7,
            "stream": False,
        }

        for attempt in range(MAX_RETRIES + 1):
            self._wait_for_rate_limit()

            try:
                response = self.client.post(
                    f"{NVIDIA_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                self._last_call_time = time.time()
                self.call_count += 1

                if response.status_code == 429:
                    wait = RETRY_WAIT_S * (attempt + 1)
                    print(f"  [brain] Rate limit (429). Esperando {wait:.0f}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                # Tracking de tokens
                usage = data.get("usage", {})
                self.total_tokens_in  += usage.get("prompt_tokens", 0)
                self.total_tokens_out += usage.get("completion_tokens", 0)

                return data["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                print(f"  [brain] HTTP error {e.response.status_code}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT_S)
                    continue
                return None
            except Exception as e:
                print(f"  [brain] Error inesperado: {e}")
                return None

        return None

    def _extract_json(self, text: str) -> Optional[dict | list]:
        """
        Extrae JSON de la respuesta del LLM.
        Maneja JSON embebido en texto libre o markdown code blocks.
        """
        if not text:
            return None

        # Intentar parsear directamente
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Buscar JSON en code block ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Buscar primer objeto/array JSON en el texto
        for pattern in [r"(\{[\s\S]*\})", r"(\[[\s\S]*\])"]:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

        print(f"  [brain] No se pudo extraer JSON de: {text[:200]}...")
        return None

    # --------------------------------------------------------------------------
    # FASE A: ANALIZAR
    # --------------------------------------------------------------------------

    def analyze(
        self,
        last_cycle_results: list[dict],
        all_time_top: list[dict],
        learnings: list[dict],
        opus_insights: list[dict],
        cycle_num: int,
    ) -> Optional[dict]:
        """
        Analiza los resultados recientes e identifica patrones.

        Args:
            last_cycle_results: Resultados del ciclo anterior [{strategy, params, sharpe_oos, ...}]
            all_time_top:       Top 20 resultados de todos los tiempos
            learnings:          Learnings acumulados de la sesión
            opus_insights:      Directivas del Director Senior (Opus 4.6)
            cycle_num:          Número de ciclo actual

        Returns:
            dict con {patterns_positive, patterns_negative, parameter_insights, suggested_direction}
        """
        system = (
            "Sos un analista cuantitativo senior especializado en backtesting de estrategias "
            "de trading BTC/USDT. Analizás resultados de experimentos con criterio estadístico "
            "riguroso. Respondé SIEMPRE en JSON válido, sin texto adicional."
        )

        # Construir user prompt (puede ser largo — Nemotron tiene 1M ctx)
        benchmark_str = (
            f"Benchmark actual: {BENCHMARK['strategy']} | "
            f"Fitness: {BENCHMARK['fitness']:.3f} | "
            f"Sharpe OOS: {BENCHMARK['sharpe_oos']} | "
            f"Trades: {BENCHMARK['trades_oos']} | "
            f"WR: {BENCHMARK['wr_oos']*100:.0f}% | "
            f"DD: {BENCHMARK['dd_oos']}%"
        )

        opus_str = ""
        if opus_insights:
            opus_str = "\n## Directivas del Director Senior (Opus 4.6)\n"
            for ins in opus_insights[:5]:
                opus_str += f"[P{ins.get('priority',1)}] {ins.get('title','')}: {ins.get('content','')[:200]}\n"

        last_results_str = ""
        if last_cycle_results:
            last_results_str = "\n## Resultados Ciclo Anterior\n"
            last_results_str += "strategy | sharpe_train | sharpe_oos | trades | wr | dd | fitness\n"
            for r in last_cycle_results[:15]:
                last_results_str += (
                    f"{r.get('strategy','?')} | "
                    f"{r.get('sharpe_train', 0):.3f} | "
                    f"{r.get('sharpe_oos', 0):.3f} | "
                    f"{r.get('trades_oos', 0)} | "
                    f"{r.get('wr_oos', 0)*100:.0f}% | "
                    f"{r.get('dd_oos', 0):.1f}% | "
                    f"{r.get('fitness', 0):.3f}\n"
                )

        top_str = "\n## Top 20 All-Time\n"
        top_str += "# | strategy | sharpe_oos | trades | wr | fitness\n"
        for i, r in enumerate(all_time_top[:20], 1):
            top_str += (
                f"{i}. {r.get('strategy','?')} | "
                f"{r.get('sharpe_oos', 0):.3f} | "
                f"{r.get('trades_oos', 0)} | "
                f"{r.get('wr_oos', 0)*100:.0f}% | "
                f"{r.get('fitness', 0):.3f}\n"
            )

        learnings_str = ""
        if learnings:
            learnings_str = "\n## Learnings Acumulados\n"
            for l in learnings[-20:]:
                learnings_str += f"[{l.get('category','?')}] {l.get('content','')}\n"

        user = f"""
{benchmark_str}

Ciclo actual: {cycle_num}
{opus_str}
{last_results_str}
{top_str}
{learnings_str}

## Tarea
Analizá los patrones en los resultados. Respondé con este JSON exacto:
{{
  "patterns_positive": ["qué funcionó y por qué"],
  "patterns_negative": ["qué no funcionó y por qué"],
  "parameter_insights": ["relaciones param → resultado observadas"],
  "suggested_direction": "hacia dónde explorar en el próximo ciclo (1-2 oraciones)",
  "strategies_to_prioritize": ["lista de estrategias a priorizar"],
  "params_to_avoid": {{"param_name": "razón"}}
}}
"""
        print(f"  [brain:analyze] Llamando Nemotron (1M ctx)...")
        raw = self._call_llm("analyze", system, user)
        result = self._extract_json(raw)

        if not isinstance(result, dict):
            print(f"  [brain:analyze] Output inválido, usando defaults")
            return {
                "patterns_positive": [],
                "patterns_negative": [],
                "parameter_insights": [],
                "suggested_direction": "Explorar variaciones de los mejores configs",
                "strategies_to_prioritize": ENABLED_STRATEGIES,
                "params_to_avoid": {},
            }

        return result

    # --------------------------------------------------------------------------
    # FASE B: HIPOTETIZAR
    # --------------------------------------------------------------------------

    def hypothesize(
        self,
        analysis: dict,
        dead_ends: list[str],
        n_experiments: int,
        cycle_num: int,
    ) -> list[dict]:
        """
        Genera N configs de experimento basadas en el análisis.

        Returns:
            Lista de configs válidas [{strategy, params, notes}]
        """
        system = (
            "Sos un ingeniero cuantitativo. Tu trabajo es proponer configuraciones "
            "de experimentos de backtesting para BTC/USDT. "
            "Respondé SIEMPRE con un JSON array válido, sin texto adicional. "
            "NUNCA propongas valores fuera de los rangos indicados."
        )

        benchmark_str = (
            f"Benchmark a superar — Fitness: {BENCHMARK['fitness']:.3f} | "
            f"Sharpe OOS: {BENCHMARK['sharpe_oos']}"
        )

        dead_ends_str = ""
        if dead_ends:
            dead_ends_str = "\n## Dead Ends — NO Explorar\n"
            for de in dead_ends[:15]:
                dead_ends_str += f"- {de}\n"

        analysis_str = json.dumps(analysis, ensure_ascii=False, indent=2)

        user = f"""
{benchmark_str}

## Análisis del Ciclo Anterior
{analysis_str}

{get_parameter_space_summary()}
{dead_ends_str}

## Reglas de las Estrategias (INVIOLABLES)
- Riesgo 2% por trade
- Stop diario 6%
- Sin lookahead bias
- Mínimo 30 trades para validez estadística

## Tarea
Generá exactamente {n_experiments} configs de experimento.

Distribución recomendada:
- Priorizar: {analysis.get('strategies_to_prioritize', ENABLED_STRATEGIES)}
- Incluir al menos 1 config de cada estrategia habilitada
- 30% de configs deben ser variaciones de los mejores resultados históricos
- 30% deben explorar combinaciones nuevas no probadas
- 40% deben explorar la dirección sugerida: {analysis.get('suggested_direction', '')}

Respondé con este formato JSON array (SIN texto adicional):
[
  {{
    "strategy": "breakout",
    "params": {{
      "lookback": 20,
      "vol_ratio_min": 1.5,
      "atr_period": 14,
      "sl_atr_mult": 2.5,
      "trail_atr_mult": 2.5,
      "ema_trend_period": 50,
      "ema_trend_daily_period": 30,
      "adx_filter": 22,
      "breakeven_after_r": 0.5
    }},
    "notes": "Hipótesis: descripción breve de por qué esta config podría superar el benchmark"
  }},
  ...
]
"""
        print(f"  [brain:hypothesize] Llamando GLM-5 (reasoning)...")
        raw = self._call_llm("hypothesize", system, user)
        configs = self._extract_json(raw)

        if not isinstance(configs, list):
            print(f"  [brain:hypothesize] Output inválido, retornando lista vacía")
            return []

        # Validar y filtrar configs
        valid_configs = []
        for config in configs:
            if not isinstance(config, dict):
                continue
            ok, reason = validate_experiment_config(config)
            if ok:
                valid_configs.append(config)
            else:
                print(f"  [brain:hypothesize] Config rechazada: {reason}")

        print(f"  [brain:hypothesize] {len(valid_configs)}/{len(configs)} configs válidas")
        return valid_configs

    # --------------------------------------------------------------------------
    # FASE C: APRENDER
    # --------------------------------------------------------------------------

    def learn(
        self,
        cycle_results: list[dict],
        best_of_cycle: Optional[dict],
        cycle_num: int,
        existing_learnings: list[dict],
    ) -> list[dict]:
        """
        Extrae 2-5 learnings estructurados del ciclo.

        Returns:
            Lista de learnings [{category, content, confidence}]
        """
        system = (
            "Sos un analista cuantitativo. Extraés aprendizajes reutilizables "
            "de resultados de backtesting. Solo aprendizajes con valor predictivo real. "
            "Respondé SIEMPRE con un JSON array válido."
        )

        results_str = "strategy | params_key | sharpe_train | sharpe_oos | trades | wr | dd\n"
        for r in cycle_results[:20]:
            params = r.get("params", {})
            key_params = {k: v for k, v in params.items()
                         if k in ["adx_filter", "breakeven_after_r", "ema_trend_daily_period"]}
            results_str += (
                f"{r.get('strategy','?')} | "
                f"{json.dumps(key_params)} | "
                f"{r.get('sharpe_train',0):.3f} | "
                f"{r.get('sharpe_oos',0):.3f} | "
                f"{r.get('trades_oos',0)} | "
                f"{r.get('wr_oos',0)*100:.0f}% | "
                f"{r.get('dd_oos',0):.1f}%\n"
            )

        best_str = ""
        if best_of_cycle:
            best_str = (
                f"\nMejor resultado del ciclo:\n"
                f"  {json.dumps(best_of_cycle, ensure_ascii=False)}"
            )

        existing_str = ""
        if existing_learnings:
            existing_str = "\n## Learnings Ya Existentes (no duplicar)\n"
            for l in existing_learnings[-10:]:
                existing_str += f"- [{l.get('category')}] {l.get('content','')}\n"

        user = f"""
## Resultados del Ciclo {cycle_num}
{results_str}
{best_str}
{existing_str}

## Benchmark Actual
Fitness: {BENCHMARK['fitness']:.3f} | Sharpe OOS: {BENCHMARK['sharpe_oos']}

## Categorías Válidas de Learnings
- parameter_insight: relación concreta entre parámetro y resultado
- dead_end: combinación que consistentemente falla (con datos que lo respaldan)
- promising_direction: área que merece más exploración (con razón específica)
- strategy_ranking: comparación entre estrategias basada en este ciclo

## Reglas
1. Solo learnings con datos que los respalden (mínimo 3 experimentos)
2. Learnings concretos y accionables, no generales
3. No duplicar los ya existentes
4. Confidence entre 0.4 (hipótesis) y 0.9 (fuertemente respaldado)

Respondé con 2-5 learnings en este formato JSON array:
[
  {{
    "category": "parameter_insight",
    "content": "descripción concreta y accionable",
    "confidence": 0.7
  }}
]
"""
        print(f"  [brain:learn] Llamando Kimi K2.5...")
        raw = self._call_llm("learn", system, user)
        learnings = self._extract_json(raw)

        if not isinstance(learnings, list):
            print(f"  [brain:learn] Output inválido, retornando lista vacía")
            return []

        # Filtrar y limpiar
        valid_learnings = []
        valid_categories = {"parameter_insight", "dead_end", "promising_direction", "strategy_ranking"}
        for l in learnings:
            if not isinstance(l, dict):
                continue
            if l.get("category") not in valid_categories:
                continue
            if not l.get("content"):
                continue
            confidence = float(l.get("confidence", 0.5))
            l["confidence"] = max(0.1, min(0.95, confidence))
            valid_learnings.append(l)

        print(f"  [brain:learn] {len(valid_learnings)} learnings extraídos")
        return valid_learnings

    def get_stats(self) -> dict:
        """Retorna estadísticas de uso del brain."""
        return {
            "total_calls": self.call_count,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_tokens": self.total_tokens_in + self.total_tokens_out,
        }

    def close(self):
        self.client.close()


# ==============================================================================
# GENERACIÓN DE DEAD ENDS desde learnings
# ==============================================================================

def extract_dead_ends(learnings: list[dict]) -> list[str]:
    """Filtra y retorna solo los learnings de tipo dead_end."""
    return [
        l["content"] for l in learnings
        if l.get("category") == "dead_end" and not l.get("superseded", False)
    ]


if __name__ == "__main__":
    # Test básico — requiere NVIDIA_API_KEY en el environment
    brain = AutoLabBrain()

    print("Testing brain.analyze() con datos dummy...")
    analysis = brain.analyze(
        last_cycle_results=[],
        all_time_top=[],
        learnings=[],
        opus_insights=[],
        cycle_num=1,
    )
    print(f"Analysis: {json.dumps(analysis, indent=2, ensure_ascii=False)}")

    stats = brain.get_stats()
    print(f"\nStats: {stats}")
    brain.close()
