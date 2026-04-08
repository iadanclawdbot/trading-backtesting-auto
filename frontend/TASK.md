# AutoLab Dashboard — TASK.md

## Estado del proyecto (2026-04-08)

Dashboard funcional con build exitoso. Todos los componentes conectados a la API real.

---

## FASE 1 — Setup ✅ COMPLETA

- [x] 1.1 Inicializar Next.js 16.2.2 con TypeScript, Tailwind, App Router
- [x] 1.2 Instalar dependencias (recharts, lightweight-charts, motion, swr, radix-ui)
- [x] 1.3 Configurar shadcn/ui (components.json, Radix UI primitives)
- [x] 1.4 Design tokens en globals.css (colores, fuentes, scrollbar, animaciones)
- [x] 1.5 Fonts IBM Plex Mono/Sans via next/font/google
- [x] 1.6 Variables de entorno (.env.local, .env.example)
- [x] 1.7 CLAUDE.md y TASK.md

## FASE 2 — Capa de datos ✅ COMPLETA

- [x] 2.1 Tipos TypeScript (src/types/api.ts) — verificados contra API real
- [x] 2.2 Cliente API (src/lib/api.ts) — fetcher base con error handling
- [x] 2.3 Hooks SWR (src/hooks/use-api.ts) — useHealth, useStatus, useContext, useLearnings, useOpusInsights
- [x] 2.4 Constantes (src/lib/constants.ts) — estrategias, categorias, tooltips en español
- [x] 2.5 Formatters (src/lib/formatters.ts) — currency, percent, sharpe, dates

## FASE 3 — Componentes ✅ COMPLETA

### Layout shell
- [x] 3.1 ThemeProvider + ThemeToggle (dark/light con localStorage)
- [x] 3.2 Root layout con SWRProvider, fonts, estructura
- [x] 3.3 Sidebar desktop (colapsable, con indicador de health)
- [x] 3.4 Mobile nav (bottom tabs)
- [x] 3.5 Header mobile

### Primitivos
- [x] 3.6 TooltipHelp — icono (?) con explicaciones en lenguaje simple
- [x] 3.7 MetricCard — card genérica con skeleton, tooltip, variantes

### Cards del dashboard
- [x] 3.8 SystemHealth — 3 indicadores (API, SQLite, PG)
- [x] 3.9 ChampionCard — campeón actual, null-safe
- [x] 3.10 QueueStatus — done/failed con barra de exito
- [x] 3.11 BestOOSCard — mejor Sharpe OOS
- [x] 3.12 FitnessGauge — SVG gauge vs benchmark

### Charts
- [x] 3.13 AutoresearchChart — Karpathy style (Recharts ComposedChart)
- [x] 3.14 TradesDonut — WIN/LOSS PieChart
- [x] 3.15 LearningsBars — barras por categoria
- [x] 3.16 RunsTable — tabla sortable con expand de params

### Paneles
- [x] 3.17 LearningsFeed — feed colapsable con filtros
- [x] 3.18 OpusInsightsPanel — insights estratégicos

### Ensamblaje
- [x] 3.19 Dashboard page — grid responsive
- [x] 3.20 Learnings page
- [x] 3.21 Insights page

## FASE 4 — Polish y deploy ⏳ EN PROGRESO

- [ ] 4.1 Error boundaries por sección
- [ ] 4.2 Animaciones con Motion (fade-in cards, spring numbers)
- [ ] 4.3 Responsive testing en 6 breakpoints
- [ ] 4.4 `npm run build` ✅ exitoso
- [ ] 4.5 Deploy en Vercel
  - [ ] Configurar Root Directory: `frontend/`
  - [ ] Agregar NEXT_PUBLIC_API_URL en Vercel Dashboard
  - [ ] Verificar preview deploy

## FASE EXTRA — Pendiente

- [ ] E1 Candlestick chart (requiere endpoint /metrics/equity-curve del backend)
- [ ] E2 Market metrics (CoinGecko API: precio BTC, market cap, dominancia)
- [ ] E3 Fear & Greed Index (Alternative.me API)
- [ ] E4 Onboarding tour (react-joyride)
- [ ] E5 Browser notifications al cambiar campeón

---

## Endpoints pendientes del backend

Para implementar estas features extra, el backend necesita crear:
- `GET /metrics/equity-curve?run_id=X` → equity curve para candlestick/line chart
- `GET /metrics/cycles` → historial de ciclos por hora
- `GET /metrics/champion-history` → timeline de champions

Coordinar con el backend antes de implementar componentes que los consuman.
