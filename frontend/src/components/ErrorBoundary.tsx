import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Unhandled UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: "2rem", maxWidth: 480, margin: "3rem auto", textAlign: "center" }}>
          <h1 style={{ marginBottom: "0.75rem" }}>Something went wrong</h1>
          <p style={{ color: "var(--color-ink-muted)", marginBottom: "1.25rem" }}>
            Please reload the page. If the problem continues, contact the Student Services Helpdesk.
          </p>
          <button type="button" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
