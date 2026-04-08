# AutoLab Dashboard — Frontend

Dashboard de monitoreo del sistema AutoLab: mejora continua autónoma de estrategias BTC/USDT.

## Stack

| Tecnología | Versión | Notas |
|------------|---------|-------|
| Next.js | 16.2.2 | App Router, Turbopack default |
| React | 19.2.4 | Server Components disponibles |
| Tailwind CSS | 4.1 | CSS-first (`@import "tailwindcss"` + `@theme {}`) |
| Recharts | 3.8.1 | Charts estándar |
| lightweight-charts | 5.x | Candlestick TradingView (instalado, pendiente endpoint) |
| Motion | 12.38.0 | `import from "motion/react"` (NO framer-motion) |
| SWR | latest | Polling, keepPreviousData |
| Lucide React | latest | Iconos |

## API

URL: `https://autolab-api.dantelujan.online` (en `NEXT_PUBLIC_API_URL`)

**Endpoints disponibles:**
- `GET /health` → `{ status, sqlite, postgresql, timestamp }`
- `GET /status` → `{ champion | null, queue: { done, failed }, best_oos, benchmark? }`
- `GET /context?top_n=N` → `{ top_results[] (incluye capital_final), last_cycle_results[], learnings[], opus_insights[] }`
- `GET /learnings` → `{ learnings: [], count }` (NO es array plano)
- `GET /opus-insights` → `{ insights: [], count }` (actualmente vacío)
- `GET /metrics/equity-curve?run_id=X` → `{ run_id, strategy, points: [{bar, ts, equity, in_pos}] }` (sin run_id usa campeón)
- `GET /metrics/champion-history` → `{ champions: [{promoted_at, strategy, capital_final, ...}], count }`
- `GET /metrics/cycles?limit=N` → `{ cycles: [{finished_at, jobs_completed, best_sharpe_oos, beat_benchmark}], count }`
- `GET /metrics/system` → `{ db_size_mb, total_runs, total_trades, total_experiments, strategies_tested }`

## Deploy

- Plataforma: **Vercel**
- Root Directory: `frontend/`
- Framework: Next.js (auto-detectado)
- Build Command: `next build`
- Variable de entorno: `NEXT_PUBLIC_API_URL`

## Estructura

```
src/
  app/                    # Rutas: / /learnings /insights
  components/
    layout/               # Sidebar, MobileNav, Header, ThemeProvider, ThemeToggle
    dashboard/            # 18 componentes del dashboard:
      autoresearch-chart  # Scatter+step capital por experimento (Recharts)
      best-oos-card       # Mejor resultado OOS
      champion-card       # Campeón actual con métricas
      champion-timeline   # Timeline visual de evolución del campeón
      cycles-chart        # Barras de ciclos autónomos (beat benchmark)
      equity-curve        # Equity curve real del campeón (AreaChart)
      fitness-gauge       # SVG gauge Sharpe vs benchmark
      learnings-bars      # Barras por categoría de learning
      learnings-feed      # Feed colapsable de learnings
      market-context      # BTC price + Fear & Greed (APIs externas)
      metric-card         # Card genérica reutilizable
      opus-insights-panel # Panel de insights estratégicos
      queue-status        # Jobs done/failed
      runs-table          # Top runs sortable con params expandibles
      system-health       # Dots: API, SQLite, PG
      system-stats        # Métricas infra (DB size, runs, trades)
      tooltip-help        # Icono (?) con tooltip explicativo
      trades-donut        # Win/Loss pie chart
  hooks/                  # use-api.ts — 9 SWR hooks
  lib/                    # api.ts, constants.ts, formatters.ts, utils.ts
  types/                  # api.ts — interfaces TS para todos los endpoints
```

## APIs externas

- **CoinGecko** (free, sin key): BTC price, 24h change, market cap, volumen — polling 5 min
- **Alternative.me**: Fear & Greed Index — polling 5 min

## Convenciones

- Texto de UI en **español**; nombres de variables/funciones en **inglés**
- Fuente monoespaciada (`font-mono`) para todos los números y métricas
- Colores semánticos via CSS variables (`var(--color-green)`, `var(--color-red)`, etc.)
- Cada componente de dashboard tiene su propio hook SWR (polling 30-60s)
- `keepPreviousData: true` en todos los hooks — sin pantallas en blanco
- Componentes del dashboard son todos Client Components (`"use client"`)
- Páginas en `app/` pueden ser Server Components (no usan hooks directamente)
- Error boundaries por sección — un componente falla, el resto sigue funcionando
