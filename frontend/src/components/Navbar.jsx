import { Link } from "react-router-dom";

import Logo from "./Logo";

function Navbar({
  runWorkflow,
  stopWorkflow,
  openCredentials,
  onGoHome,
  homeTo,
  executionState,
}) {
  const { status, message } = executionState;

  const statusClass =
    status === "running"
      ? "navbar-status--running"
      : status === "success"
        ? "navbar-status--success"
        : status === "error"
          ? "navbar-status--error"
          : "";

  const statusLabel =
    message ||
    (status === "running"
      ? "Executing…"
      : status === "success"
        ? "Completed"
        : status === "error"
          ? "Failed"
          : "Ready");

  const brandInner = (
    <>
      <Logo />
      <div>
        <div className="navbar-title">mini-n8n</div>
        <div className="navbar-subtitle">Internal Editor</div>
      </div>
    </>
  );

  return (
    <header className="navbar">
      {homeTo ? (
        <Link to={homeTo} className="navbar-brand navbar-brand-link">
          {brandInner}
        </Link>
      ) : (
        <div
          className="navbar-brand"
          onClick={onGoHome}
          role="button"
          tabIndex={0}
        >
          {brandInner}
        </div>
      )}

      <div className="navbar-actions">
        <div className={`navbar-status ${statusClass}`}>
          <span
            className={`status-dot${
              status === "running" ? " status-dot--running" : ""
            }`}
          />
          {statusLabel}
        </div>

        <button className="btn btn-ghost" onClick={openCredentials}>
          🔑 Credentials
        </button>

        <button
          className="btn btn-execute"
          onClick={runWorkflow}
          disabled={status === "running"}
        >
          {status === "running" ? "⏳ Running…" : "▶ Execute Workflow"}
        </button>

        <button className="btn btn-ghost" onClick={stopWorkflow}>
          Clear
        </button>
      </div>
    </header>
  );
}

export default Navbar;
