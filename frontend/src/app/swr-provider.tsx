"use client";

import { SWRConfig } from "swr";
import { fetcher } from "@/lib/api";

export function SWRProvider({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        keepPreviousData: true,
        revalidateOnFocus: false,
        errorRetryInterval: 60_000,
        shouldRetryOnError: true,
      }}
    >
      {children}
    </SWRConfig>
  );
}
