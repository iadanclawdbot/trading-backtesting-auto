import { LearningCategory } from "@/types/api";

// ─── Estrategias ────────────────────────────────────────────────────────────
export const STRATEGIES: Record<string, { label: string; color: string }> = {
  vwap_pullback: { label: "VWAP Pullback", color: "var(--color-vwap)" },
  breakout: { label: "Breakout V4", color: "var(--color-breakout)" },
  mean_reversion: { label: "Mean Reversion", color: "var(--color-mr)" },
  ema_crossover: { label: "EMA Crossover", color: "var(--color-ema)" },
};

export function getStrategy(name: string) {
  return STRATEGIES[name] ?? { label: name, color: "var(--color-text-1)" };
}

// ─── Categorias de learnings ────────────────────────────────────────────────
export const LEARNING_CATEGORIES: Record<
  LearningCategory,
  { label: string; color: string; emoji: string }
> = {
  parameter_insight: {
    label: "Parametros",
    color: "var(--color-cat-parameter)",
    emoji: "⚙️",
  },
  promising_direction: {
    label: "Direccion prometedora",
    color: "var(--color-cat-promising)",
    emoji: "✅",
  },
  dead_end: {
    label: "Callejon sin salida",
    color: "var(--color-cat-dead-end)",
    emoji: "🚫",
  },
  strategy_ranking: {
    label: "Ranking estrategias",
    color: "var(--color-cat-ranking)",
    emoji: "📊",
  },
  external_research: {
    label: "Investigacion",
    color: "var(--color-cat-research)",
    emoji: "🔬",
  },
};

// ─── Tooltips — explicaciones en lenguaje simple ───────────────────────────
export const TOOLTIPS: Record<string, string> = {
  sharpe_ratio:
    "Mide cuanto ganás por cada unidad de riesgo que asumís. Un Sharpe mayor a 1.0 es bueno; mayor a 1.5 es excelente. El sistema busca maximizar este número.",
  win_rate:
    "Porcentaje de trades (operaciones) que terminaron en ganancia. Un 60% ya es muy bueno en trading profesional — la mayoría pierde.",
  max_drawdown:
    "La caida máxima desde el punto más alto del capital. Por ejemplo, -5% significa que en algún momento el capital bajó 5% desde su pico. Cuanto más cercano a 0%, mejor.",
  capital_final:
    "Capital al final del backtest (simulación), empezando siempre de $250 USDT. Si muestra $338, el sistema 'ganó' $88 en la simulación.",
  pnl_pct:
    "Ganancia o pérdida porcentual total sobre el capital inicial ($250). Un +35% significa que el capital creció un 35% durante la simulación.",
  fitness_score:
    "Score compuesto que combina Sharpe, consistencia y drawdown en un solo número. El benchmark a superar es 1.193 (V5 Portfolio). Cuanto más alto, mejor.",
  benchmark:
    "Referencia de rendimiento del sistema anterior. El objetivo del agente IA es encontrar estrategias que superen este número (1.193).",
  total_trades:
    "Cantidad de operaciones realizadas en el backtest. Muy pocas (<30) puede indicar filtros demasiado restrictivos que pierden oportunidades.",
  confidence:
    "Qué tan seguro está el agente IA de este aprendizaje. 0.9+ es alta confianza, 0.6 es dudoso. Se basa en cuántos experimentos confirman la misma conclusión.",
  consistency_ratio:
    "Compara rendimiento en datos de entrenamiento (2024) vs validación (2025). Cerca de 1.0 = no hay sobreajuste (overfitting). Alejarse de 1.0 es señal de problema.",
  queue_done:
    "Total de experimentos completados exitosamente desde el inicio del sistema. Cada experimento es una estrategia con parámetros específicos probada en datos históricos.",
  queue_failed:
    "Experimentos que fallaron durante la ejecución (errores de datos, parámetros inválidos, etc.). Un número pequeño es normal.",
  profit_factor:
    "Ratio entre ganancias totales y pérdidas totales. Mayor a 1.0 es rentable. Ejemplo: 2.0 significa que ganás el doble de lo que perdés.",
  sharpe_train:
    "Sharpe calculado en datos de entrenamiento (2024). Si es mucho mayor que el Sharpe OOS, hay sobreajuste — la estrategia funciona en datos viejos pero no en nuevos.",
  sharpe_oos:
    "Sharpe calculado en datos out-of-sample (2025) — datos que el modelo nunca vio durante el entrenamiento. Es la métrica más honesta del rendimiento real.",
  autoresearch:
    "Gráfico del progreso de la investigación autónoma. Cada punto es un experimento. La línea verde muestra cómo mejoró el mejor resultado a lo largo del tiempo.",
  learnings_feed:
    "Aprendizajes acumulados por el agente IA a lo largo de miles de experimentos. Cada insight representa un patrón estadísticamente confirmado sobre qué funciona y qué no.",
};

// ─── Benchmark fijo ─────────────────────────────────────────────────────────
export const BENCHMARK_FITNESS = 1.193;
export const BENCHMARK_LABEL = "V5 Portfolio";
