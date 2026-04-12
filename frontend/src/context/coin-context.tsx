"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type CoinSymbol = "BTCUSDT" | "ETHUSDT" | "SOLUSDT";

export const COINS: { symbol: CoinSymbol; label: string; color: string }[] = [
  { symbol: "BTCUSDT", label: "BTC", color: "#f7931a" },
  { symbol: "ETHUSDT", label: "ETH", color: "#627eea" },
  { symbol: "SOLUSDT", label: "SOL", color: "#9945ff" },
];

interface CoinContextType {
  coin: CoinSymbol;
  setCoin: (coin: CoinSymbol) => void;
  coinLabel: string;
}

const CoinContext = createContext<CoinContextType>({
  coin: "BTCUSDT",
  setCoin: () => {},
  coinLabel: "BTC",
});

export function CoinProvider({ children }: { children: ReactNode }) {
  const [coin, setCoinState] = useState<CoinSymbol>("BTCUSDT");

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("autolab-coin") as CoinSymbol | null;
    if (saved && COINS.some((c) => c.symbol === saved)) {
      setCoinState(saved);
    }
  }, []);

  const setCoin = (c: CoinSymbol) => {
    setCoinState(c);
    localStorage.setItem("autolab-coin", c);
  };

  const coinLabel = COINS.find((c) => c.symbol === coin)?.label ?? "BTC";

  return (
    <CoinContext.Provider value={{ coin, setCoin, coinLabel }}>
      {children}
    </CoinContext.Provider>
  );
}

export function useCoin() {
  return useContext(CoinContext);
}
