# AutoLab Dashboard — Requisitos extra para el agente developer

> Este documento complementa el brief técnico principal.
> El objetivo es darle libertad creativa al developer para que diseñe algo que se vea y sienta como una herramienta de trading profesional, no un dashboard genérico.

---

## Filosofía de diseño

No hay una estructura rígida de layout a seguir. Lo que importa es que la información sea legible de un vistazo y que el dashboard transmita que es una herramienta seria, técnica y personalizada. Se valora la creatividad por encima de la convención. Si hay una forma más clara, más elegante o más informativa de mostrar algo, usarla.

El único requisito estético fijo es el **tema oscuro** y la tipografía monoespaciada para números y código. Todo lo demás es abierto.

---

## Gráficos que me gustan y quiero que estén

### 1. Equity curve
Line chart del capital bar-a-bar del run actual. Simple, limpio, sin ruido. Me gusta que sea fill con baja opacidad y sin puntos visibles. Si el developer quiere expandirlo (por ejemplo, mostrando múltiples runs superpuestos o un rango histórico), bienvenido.

### 2. Autoresearch progress (estilo Karpathy)
Este es el gráfico más importante del dashboard. Combina tres capas:
- Puntos grises dispersos = experimentos descartados
- Línea escalonada verde = running best (capital acumulado)
- Puntos verdes con etiqueta = mejoras retenidas, cada una anotada con el cambio que introdujo

El eje X es el número de experimento, el eje Y es el capital en USDT. Las etiquetas de los puntos retenidos van rotadas para no solaparse. El tooltip muestra el detalle del experimento al hacer hover.

### 3. Ciclos completados por hora (bar chart)
Barras por hora de las últimas 24h. Simple, informativo. Muestra si el sistema está corriendo a la frecuencia esperada (~48 ciclos/día).

### 4. Distribución de trades (donut)
WIN vs LOSS con porcentaje. Al lado: split LONG/SHORT y avg win/loss como barras de progreso.

### 5. Learnings por categoría (progress bars)
Cinco categorías con barra horizontal y conteo. Categorías: `parameter_insight`, `promising_dir`, `dead_end`, `strategy_ranking`, `external_research`.

---

## Cosas que me parecen interesantes para agregar (libertad total)

El developer puede incorporar estas ideas si le parecen viables, o proponer alternativas mejores:

- **Heatmap de rendimiento por día de la semana / hora del día** — para ver si el sistema performa mejor en ciertos momentos del mercado. Datos disponibles en `SQLite: trades.entrada_fecha + pnl_neto`.

- **Timeline de eventos del sistema** — un feed cronológico vertical que mezcle: nuevo champion coronado, ciclo fallido, learning guardado, Brave search ejecutada. Que se pueda filtrar por tipo de evento.

- **Gauge o indicador visual del fitness score** — algo más expresivo que un número solo. Que muestre visualmente qué tan lejos o cerca está del benchmark (1.193) y del mejor histórico.

- **Comparación train vs OOS en una sola vista** — dos líneas superpuestas o un indicador de divergencia. El objetivo es detectar overfitting de un vistazo sin tener que interpretar dos números por separado.

- **Mini sparklines por estrategia** — en el historial de champions o en una sección aparte, una mini línea de tendencia de capital para cada estrategia (breakout, vwap, mean_rev).

- **Indicador de "temperatura" del sistema** — algo visual que represente si el sistema está explorando activamente (muchos experimentos nuevos, learnings variados) o convergiendo (pocos cambios, runs similares). Puede ser tan simple como un color de fondo en una card o tan elaborado como un viz custom.

- **Budget tracker de Brave Search** — una barra de progreso circular o lineal del uso mensual (X / 2000 queries). Con estimación de días restantes al ritmo actual.

- **Tabla de últimos N runs** — los últimos 10-20 runs con columnas: estrategia, Sharpe OOS, WR, capital final, fitness, beat benchmark (bool). Ordenable por columna. Highlight en verde para los que batieron benchmark.

---

## Notas de UX

- El dashboard es para uso personal en desktop, no necesita ser responsive para mobile.
- No hay autenticación. Se puede agregar una clave hardcodeada en un `.env` si se quiere algo mínimo, pero no es prioridad.
- El polling puede ser cada 30 segundos con `fetch` simple. No hace falta websockets.
- Si un endpoint falla, mantener el último valor conocido y mostrar cuándo fue la última actualización exitosa.
- Las secciones más importantes (fitness, equity curve, autoresearch progress) deberían estar visibles sin hacer scroll, o al menos ser lo primero que se ve.
- Los números que cambian entre polls pueden tener una transición visual suave (fade o highlight breve) para que sea fácil notar qué cambió.

---

## Referencia visual de lo que se construyó hasta ahora

El mockup previo usó:
- Fondo base `#0d0f0e`, superficies `#131614` y `#181c1a`
- Bordes `rgba(255,255,255,0.07)`
- Verde principal `#4ade80`, amber `#fbbf24`, rojo `#f87171`, azul `#60a5fa`
- IBM Plex Mono para números, IBM Plex Sans para texto
- Tags/pills con fondo semitransparente y borde del mismo color al 20%

Esto es una referencia, no una restricción. Si el developer tiene una dirección visual más fuerte, que la use.

---

## Datos disponibles (resumen)

| Fuente | Qué tiene |
|--------|-----------|
| `GET /health` | Estado API, SQLite conectado, PG conectado |
| `GET /status` | Champion actual, cola de jobs, best Sharpe OOS |
| `GET /context` | Top runs, learnings activos, opus insights |
| `GET /learnings` | Tabla completa de learnings con categoría y confianza |
| `GET /metrics/system` | SQLite size, contadores de tablas *(endpoint nuevo)* |
| `GET /metrics/cycles` | Historial de ciclos con timing y success rate *(nuevo)* |
| `GET /metrics/errors` | Errores recientes, sanity alerts, LLM failures *(nuevo)* |
| `GET /metrics/champion-history` | Timeline de champions *(nuevo)* |
| `GET /metrics/equity-curve?run_id=X` | candle_states para equity curve *(nuevo)* |
| `SQLite: runs` | Sharpe, WR, PnL, DD, capital, profit_factor por run |
| `SQLite: trades` | PnL por trade, R:R, duración, dirección, fecha |
| `SQLite: champions` | Historial de cambios de champion con métricas |
| `PG: autolab_cycles` | Ciclos completos con fases, LLM tokens, beat_benchmark |
| `PG: autolab_learnings` | Insights con categoría, confianza, superseded |
| `PG: topic_rotation_state` | Topics de research con productividad y outcome |
| `PG: search_history` | Brave Search queries ejecutadas este mes |
| `n8n API` | Estado de workflows activos |

---

*Este brief es un punto de partida. Si el developer ve algo que no tiene sentido, que lo cambie. Si ve algo que falta y tiene valor, que lo agregue.*
