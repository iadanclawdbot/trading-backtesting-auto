"use client";

import useSWR from "swr";
import { Bitcoin, TrendingUp, TrendingDown, Gauge } from "lucide-react";

interface CoinGeckoData {
  bitcoin: {
    usd: number;
    usd_24h_change: number;
    usd_market_cap: number;
    usd_24h_vol: number;
  };
}

interface FearGreedData {
  data: Array<{
    value: string;
    value_classification: string;
    timestamp: string;
  }>;
}

const externalFetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
};

function formatLargeNumber(n: number): string {
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  return `$${n.toLocaleString()}`;
}

function getFearColor(value: number): string {
  if (value <= 25) return "var(--color-red)";
  if (value <= 45) return "var(--color-amber)";
  if (value <= 55) return "var(--color-text-1)";
  if (value <= 75) return "var(--color-green)";
  return "var(--color-green)";
}

export function MarketContext() {
  const { data: btcData } = useSWR<CoinGeckoData>(
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true",
    externalFetcher,
    { refreshInterval: 300_000, revalidateOnFocus: false, errorRetryInterval: 60_000 }
  );

  const { data: fgData } = useSWR<FearGreedData>(
    "https://api.alternative.me/fng/?limit=1",
    externalFetcher,
    { refreshInterval: 300_000, revalidateOnFocus: false, errorRetryInterval: 60_000 }
  );

  const btc = btcData?.bitcoin;
  const fg = fgData?.data?.[0];
  const fgValue = fg ? parseInt(fg.value) : null;
  const change24h = btc?.usd_24h_change ?? 0;
  const isUp = change24h >= 0;

  return (
    <div className="panel p-4">
      <div className="section-label mb-3">Contexto de mercado</div>

      {/* BTC Price */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bitcoin className="h-4 w-4 text-[var(--color-amber)]" />
          <span className="text-[11px] text-[var(--color-text-1)]">BTC/USD</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="num text-[15px] font-medium text-[var(--color-text-0)]">
            {btc ? `$${btc.usd.toLocaleString("en-US", { maximumFractionDigits: 0 })}` : "—"}
          </span>
          {btc && (
            <span className={`num text-[11px] font-medium flex items-center gap-0.5 ${isUp ? "text-[var(--color-green)]" : "text-[var(--color-red)]"}`}>
              {isUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {isUp ? "+" : ""}{change24h.toFixed(2)}%
            </span>
          )}
        </div>
      </div>

      {/* Market stats row */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="mcard">
          <div className="lbl">Market cap</div>
          <div className="val" style={{ fontSize: 12 }}>
            {btc ? formatLargeNumber(btc.usd_market_cap) : "—"}
          </div>
        </div>
        <div className="mcard">
          <div className="lbl">Vol 24h</div>
          <div className="val" style={{ fontSize: 12 }}>
            {btc ? formatLargeNumber(btc.usd_24h_vol) : "—"}
          </div>
        </div>
      </div>

      {/* Fear & Greed */}
      <div className="flex items-center justify-between p-2 rounded bg-[var(--color-surface-0)]">
        <div className="flex items-center gap-2">
          <Gauge className="h-3.5 w-3.5 text-[var(--color-text-2)]" />
          <span className="text-[11px] text-[var(--color-text-1)]">Fear & Greed</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="num text-[13px] font-semibold"
            style={{ color: fgValue !== null ? getFearColor(fgValue) : undefined }}
          >
            {fgValue ?? "—"}
          </span>
          {fg && (
            <span className="text-[10px] text-[var(--color-text-2)]">
              {fg.value_classification}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
