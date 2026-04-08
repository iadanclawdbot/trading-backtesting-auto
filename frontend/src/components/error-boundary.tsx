"use client";

import { Component, ReactNode } from "react";
import { RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  errorMsg: string;
}

// Error boundary de clase — necesario para capturar errores de render en React
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorMsg: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMsg: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-[var(--color-danger)]/20 bg-[var(--color-surface)] p-4">
          <div className="flex items-start gap-3">
            <span className="text-[var(--color-danger)] text-lg">⚠</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {this.props.fallbackTitle ?? "Error al cargar esta sección"}
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1 truncate">
                {this.state.errorMsg}
              </p>
            </div>
            <button
              onClick={() => this.setState({ hasError: false, errorMsg: "" })}
              className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors shrink-0"
            >
              <RefreshCw className="h-3 w-3" />
              Reintentar
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
