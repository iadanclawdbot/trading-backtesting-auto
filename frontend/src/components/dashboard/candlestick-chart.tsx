"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type ISeriesApi, ColorType, type CandlestickData, type Time, CandlestickSeries } from "lightweight-charts";
import { TooltipHelp } from "./tooltip-help";

interface OHLCPoint {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
}

async function fetchOHLC(days: number = 30): Promise<OHLCPoint[]> {
  const res = await fetch(
    `https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=${days}`
  );
  if (!res.ok) return [];
  const data: number[][] = await res.json();
  // CoinGecko OHLC: [timestamp, open, high, low, close]
  return data.map(([ts, o, h, l, c]) => ({
    time: (ts / 1000) as Time,
    open: o,
    high: h,
    low: l,
    close: c,
  }));
}

export function CandlestickChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [lastPrice, setLastPrice] = useState<number | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const isDark = document.documentElement.classList.contains("dark") ||
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

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchOHLC(days).then((points) => {
      if (cancelled || !seriesRef.current) return;
      seriesRef.current.setData(points as CandlestickData[]);
      chartRef.current?.timeScale().fitContent();
      if (points.length > 0) {
        setLastPrice(points[points.length - 1].close);
      }
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [days]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchOHLC(days).then((points) => {
        if (!seriesRef.current) return;
        seriesRef.current.setData(points as CandlestickData[]);
        if (points.length > 0) {
          setLastPrice(points[points.length - 1].close);
        }
      });
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [days]);

  return (
    <div className="panel">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="lbl">BTC/USD</span>
          <TooltipHelp term="BTC/USD" text="Velas OHLC de Bitcoin via CoinGecko. El sistema hace backtesting sobre datos historicos BTC/USDT 4H." />
          {lastPrice && (
            <span className="num text-[13px] text-[var(--color-text-0)] ml-1">
              ${lastPrice.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          )}
        </div>
        <div className="flex gap-1">
          {[7, 30, 90, 180].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-2 py-0.5 text-[10px] num rounded transition-colors ${
                days === d
                  ? "bg-[var(--color-green-dim)] text-[var(--color-green)] border border-[rgba(74,222,128,0.2)]"
                  : "text-[var(--color-text-2)] hover:text-[var(--color-text-1)]"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>
      <div className="relative" style={{ height: 220 }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <span className="text-[var(--color-text-2)] text-[11px] num animate-pulse-soft">cargando velas...</span>
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}
