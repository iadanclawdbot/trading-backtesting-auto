import { OpusInsightsPanel } from "@/components/dashboard/opus-insights-panel";
import { Header } from "@/components/layout/header";

export default function InsightsPage() {
  return (
    <>
      <Header title="Insights" />

      <div className="p-4 lg:p-6 space-y-6">
        <div className="hidden lg:block">
          <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Insights estratégicos
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            Directivas de alto nivel generadas por el agente Opus para guiar la exploración
          </p>
        </div>

        <OpusInsightsPanel />
      </div>
    </>
  );
}
