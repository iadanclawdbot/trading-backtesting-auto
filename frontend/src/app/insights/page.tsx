import { OpusInsightsPanel } from "@/components/dashboard/opus-insights-panel";
import { Header } from "@/components/layout/header";

export default function InsightsPage() {
  return (
    <>
      <Header title="Insights" />

      <div className="p-4 lg:p-6 space-y-5">
        <div className="hidden lg:block animate-in">
          <h1 className="text-sm font-semibold text-[var(--color-text-0)] tracking-wide">
            Insights estratégicos
          </h1>
          <p className="text-[11px] text-[var(--color-text-2)] mt-0.5">
            Directivas de alto nivel generadas por el agente Opus para guiar la exploración
          </p>
        </div>

        <div className="animate-in" style={{ animationDelay: "0.05s" }}>
          <OpusInsightsPanel />
        </div>
      </div>
    </>
  );
}
