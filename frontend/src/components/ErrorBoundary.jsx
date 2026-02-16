import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    if (typeof this.props.onError === "function") {
      this.props.onError(error, errorInfo);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="min-h-screen w-full p-6 md:p-10 flex items-center justify-center">
        <div className="glass-panel w-full max-w-3xl p-6 md:p-8 animate-fade-in">
          <p className="badge badge-pink mb-4">System Fault</p>
          <h1 className="text-2xl md:text-3xl font-bold hologram-text mb-3">
            HoloLearn encountered an error
          </h1>
          <p className="text-slate-300 mb-6">
            A component crashed unexpectedly. You can reload the app, and use
            the details below for debugging.
          </p>

          <div className="card mb-5 overflow-auto">
            <h2 className="text-sm font-semibold text-cyan-300 mb-2">
              Error Message
            </h2>
            <pre className="text-xs sm:text-sm text-red-200 whitespace-pre-wrap wrap-break-word">
              {this.state.error?.toString() || "Unknown error"}
            </pre>
          </div>

          {this.state.errorInfo?.componentStack ? (
            <div className="card mb-6 overflow-auto">
              <h2 className="text-sm font-semibold text-purple-300 mb-2">
                Component Stack
              </h2>
              <pre className="text-xs text-slate-300 whitespace-pre-wrap wrap-break-word">
                {this.state.errorInfo.componentStack}
              </pre>
            </div>
          ) : null}

          <button
            type="button"
            className="btn-primary"
            onClick={this.handleReload}
          >
            Reload Application
          </button>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
