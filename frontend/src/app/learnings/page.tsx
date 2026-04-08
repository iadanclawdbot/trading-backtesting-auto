import { LearningsFeed } from "@/components/dashboard/learnings-feed";
import { LearningsBars } from "@/components/dashboard/learnings-bars";
import { Header } from "@/components/layout/header";

export default function LearningsPage() {
  return (
    <>
      <Header title="Learnings" />

      <div className="p-4 lg:p-6 space-y-5">
        <div className="hidden lg:block animate-in">
          <h1 className="text-sm font-semibold text-[var(--color-text-0)] tracking-wide">
            Learnings
          </h1>
          <p className="text-[11px] text-[var(--color-text-2)] mt-0.5">
            Aprendizajes acumulados por el agente IA a lo largo de los experimentos
          </p>
        </div>

        <div className="animate-in" style={{ animationDelay: "0.05s" }}>
          <LearningsBars />
        </div>
        <div className="animate-in" style={{ animationDelay: "0.1s" }}>
          <LearningsFeed />
        </div>
      </div>
    </>
  );
}
