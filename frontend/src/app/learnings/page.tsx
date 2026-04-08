import { LearningsFeed } from "@/components/dashboard/learnings-feed";
import { LearningsBars } from "@/components/dashboard/learnings-bars";
import { Header } from "@/components/layout/header";

export default function LearningsPage() {
  return (
    <>
      <Header title="Learnings" />

      <div className="p-4 lg:p-6 space-y-6">
        <div className="hidden lg:block">
          <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Learnings
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            Aprendizajes acumulados por el agente IA a lo largo de los experimentos
          </p>
        </div>

        <LearningsBars />
        <LearningsFeed />
      </div>
    </>
  );
}
