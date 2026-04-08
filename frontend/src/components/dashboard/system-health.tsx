"use client";

import { useHealth } from "@/hooks/use-api";
import { MetricCard } from "./metric-card";
import { timeAgo } from "@/lib/formatters";
import { cn } from "@/lib/utils";

interface StatusDotProps {
  ok: boolean;
  label: string;
  detail?: string;
}

function StatusDot({ ok, label, detail }: StatusDotProps) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "h-2 w-2 rounded-full shrink-0",
            ok ? "bg-[var(--color-success)]" : "bg-[var(--color-danger)] animate-pulse-opacity"
          )}
        />
        <span className="text-sm text-[var(--color-text-primary)]">{label}</span>
      </div>
      {detail && (
        <span className="text-xs text-[var(--color-text-muted)]">{detail}</span>
      )}
    </div>
  );
}

export function SystemHealth() {
  const { data, isLoading, error } = useHealth();

  if (isLoading && !data) {
    return <MetricCard title="Estado del sistema" loading />;
  }

  if (error && !data) {
    return (
      <MetricCard title="Estado del sistema" variant="danger">
        <p className="text-sm text-[var(--color-danger)] mt-2">
          No se pudo conectar con la API
        </p>
      </MetricCard>
    );
  }

  return (
    <MetricCard title="Estado del sistema">
      <div className="mt-2 space-y-1 divide-y divide-[var(--color-border)]">
        <StatusDot
          ok={data?.status === "ok"}
          label="API AutoLab"
          detail={data ? (data.status === "ok" ? "Operativa" : "Degradada") : "—"}
        />
        <StatusDot
          ok={data?.sqlite === true}
          label="SQLite (backtesting)"
          detail={data?.sqlite ? "Conectada" : "Error"}
        />
        <StatusDot
          ok={data?.postgresql === true}
          label="PostgreSQL (IA)"
          detail={
            data?.postgresql === false
              ? "Reconectando..."
              : data?.postgresql
              ? "Conectada"
              : "—"
          }
        />
      </div>
      {data && (
        <p className="mt-3 text-xs text-[var(--color-text-muted)]">
          Verificado {timeAgo(data.timestamp)}
        </p>
      )}
    </MetricCard>
  );
}
