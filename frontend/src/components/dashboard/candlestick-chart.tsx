"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  type CandlestickData,
  type Time,
  CandlestickSeries,
  createSeriesMarkers,
} from "lightweight-charts";
import { useCandles } from "@/hooks/use-api";
import { useCoin } from "@/context/coin-context";
import { TooltipHelp } from "./tooltip-help";

type TF = "4h" | "1h";
type DS = "train" | "valid";
export function CandlestickChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markersRef = useRef<any>(null);
  const [timeframe, setTimeframe] = useState<TF>("4h");
  const [dataset, setDataset] = useState<DS>("valid");
  const { coin, coinLabel } = useCoin();

  const { data, isLoading } = useCandles(timeframe, dataset, 3000, coin);

  // Create chart once
  useEffect(() => {
    if (!containerRef.current) return;

    const isDark =
      document.documentElement.classList.contains("dark") ||
      !document.documentElement.classList.contains("light");

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: isDark ? "#6b7280" : "#9ca3af",
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: isDark ? "#1a1f1c" : "#f3f4f6" },
        horzLines: { color: isDark ? "#1a1f1c" : "#f3f4f6" },
      },
      crosshair: {
        vertLine: { color: isDark ? "#4ade80" : "#22c55e", width: 1, style: 3 },
        horzLine: { color: isDark ? "#4ade80" : "#22c55e", width: 1, style: 3 },
      },
      timeScale: {
        borderColor: isDark ? "#1e2321" : "#e5e7eb",
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: isDark ? "#1e2321" : "#e5e7eb",
      },
      handleScroll: { vertTouchDrag: false },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#4ade80",
      downColor: "#f87171",
      borderUpColor: "#4ade80",
      borderDownColor: "#f87171",
      wickUpColor: "#4ade8080",
      wickDownColor: "#f8717180",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Update data when it changes
  useEffect(() => {
    if (!seriesRef.current || !data?.candles?.length) return;

    const candles: CandlestickData[] = data.candles.map((c) => ({
      time: (c.ts / 1000) as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    seriesRef.current.setData(candles);

    // Overlay champion trades as markers
    if (data.champion_trades?.length && seriesRef.current) {
      const markerData = [];
      for (const t of data.champion_trades) {
        const entryTs = findNearestTs(data.candles.map((c) => c.ts), t.entrada_fecha);
        const exitTs = findNearestTs(data.candles.map((c) => c.ts), t.salida_fecha);

        if (entryTs) {
          markerData.push({
            time: (entryTs / 1000) as Time,
            position: "belowBar" as const,
            color: "#4ade80",
            shape: "arrowUp" as const,
            text: "BUY",
          });
        }
        if (exitTs) {
          markerData.push({
            time: (exitTs / 1000) as Time,
            position: "aboveBar" as const,
            color: t.resultado === "WIN" ? "#4ade80" : "#f87171",
            shape: "arrowDown" as const,
            text: `${t.resultado === "WIN" ? "+" : ""}${t.pnl_pct.toFixed(1)}%`,
          });
        }
      }
      markerData.sort((a, b) => (a.time as number) - (b.time as number));

      // Clean up previous markers primitive
      if (markersRef.current) {
        seriesRef.current.detachPrimitive(markersRef.current);
      }
      markersRef.current = createSeriesMarkers(seriesRef.current, markerData);
    }

    chartRef.current?.timeScale().fitContent();
  }, [data]);

  const lastCandle = data?.candles?.[data.candles.length - 1];
  const firstCandle = data?.candles?.[0];
  const tradesCount = data?.champion_trades?.length ?? 0;

  const toggleClass = (active: boolean) =>
    `px-2 py-0.5 text-[10px] num rounded transition-colors ${
      active
        ? "bg-[var(--color-green-dim)] text-[var(--color-green)] border border-[rgba(74,222,128,0.2)]"
        : "text-[var(--color-text-2)] hover:text-[var(--color-text-1)]"
    }`;

  return (
    <div className="panel">
      {/* Row 1: title + price */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <span className="lbl">{coinLabel}/USDT</span>
          <TooltipHelp
            term="Candles"
            text="Velas OHLCV reales de la DB de backtesting. Las flechas marcan entradas (verde) y salidas (verde=WIN, rojo=LOSS) del campeon actual."
          />
        </div>
        <div className="flex items-center gap-2">
          {lastCandle && (
            <span className="num text-[12px] text-[var(--color-text-2)]">
              ${lastCandle.close.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          )}
          {tradesCount > 0 && (
            <span className="pill" style={{ background: "var(--color-green-dim)", borderColor: "rgba(74,222,128,0.2)", color: "var(--color-green)" }}>
              {tradesCount} trades
            </span>
          )}
        </div>
      </div>
      {/* Row 2: toggles */}
      <div className="flex items-center gap-1 mb-2 flex-wrap">
        {(["valid", "train"] as DS[]).map((d) => (
          <button key={d} onClick={() => setDataset(d)} className={toggleClass(dataset === d)}>
            {d}
          </button>
        ))}
        <span className="text-[var(--color-text-2)] text-[10px] mx-0.5">|</span>
        {(["4h", "1h"] as TF[]).map((tf) => (
          <button key={tf} onClick={() => setTimeframe(tf)} className={toggleClass(timeframe === tf)}>
            {tf}
          </button>
        ))}
      </div>
      <div className="relative" style={{ height: 260 }}>
        {isLoading && !data && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <span className="text-[var(--color-text-2)] text-[11px] num animate-pulse-soft">
              cargando velas...
            </span>
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      </div>
      {firstCandle && lastCandle && (
        <div className="flex justify-between mt-1 text-[10px] text-[var(--color-text-2)] num">
          <span>{new Date(firstCandle.ts).toLocaleDateString()}</span>
          <span>{data?.count} velas {timeframe} ({dataset})</span>
          <span>{new Date(lastCandle.ts).toLocaleDateString()}</span>
        </div>
      )}
    </div>
  );
}

/** Find nearest candle timestamp for a datetime string */
function findNearestTs(timestamps: number[], dateStr: string): number | null {
  if (!dateStr || timestamps.length === 0) return null;
  // dateStr format: "2025-06-15 12:00:00" (Argentina time)
  const target = new Date(dateStr.replace(" ", "T") + "-03:00").getTime();
  let best = timestamps[0];
  let bestDiff = Math.abs(timestamps[0] - target);
  for (const ts of timestamps) {
    const diff = Math.abs(ts - target);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = ts;
    }
  }
  return bestDiff < 24 * 60 * 60 * 1000 ? best : null; // within 24h
}
