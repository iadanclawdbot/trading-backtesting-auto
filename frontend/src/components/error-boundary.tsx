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
        <div className="panel p-4 !border-[var(--color-red-dim)]">
          <div className="flex items-start gap-3">
            <span className="text-[var(--color-red)] text-lg">&#9888;</span>
            <div className="flex-1 min-w-0">
              <p className="text-[12px] font-medium text-[var(--color-text-0)]">
                {this.props.fallbackTitle ?? "Error al cargar esta sección"}
              </p>
              <p className="text-[11px] text-[var(--color-text-2)] mt-1 truncate">
                {this.state.errorMsg}
              </p>
            </div>
            <button
              onClick={() => this.setState({ hasError: false, errorMsg: "" })}
              className="flex items-center gap-1.5 text-[11px] text-[var(--color-text-2)] hover:text-[var(--color-text-0)] transition-colors shrink-0"
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
