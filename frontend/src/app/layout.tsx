import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";
import { SWRProvider } from "./swr-provider";
import { ThemeProvider } from "@/components/layout/theme-provider";
import { CoinProvider } from "@/context/coin-context";
import { Sidebar } from "@/components/layout/sidebar";
import { MobileNav } from "@/components/layout/mobile-nav";

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AutoLab Dashboard",
  description:
    "Monitoreo en tiempo real del sistema autónomo de mejora de estrategias de trading BTC/USDT",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${plexMono.variable} ${plexSans.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="h-full overflow-hidden">
        <SWRProvider>
          <ThemeProvider>
          <CoinProvider>
            <div className="flex h-full">
              {/* Sidebar desktop */}
              <Sidebar />

              {/* Contenido principal */}
              <main className="flex-1 overflow-y-auto overflow-x-hidden pb-20 lg:pb-0">
                {children}
              </main>
            </div>

            {/* Nav mobile — bottom */}
            <MobileNav />
          </CoinProvider>
          </ThemeProvider>
        </SWRProvider>
      </body>
    </html>
  );
}
