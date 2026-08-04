function ExecutionOverlay({ executedSteps = [], currentStep = 0 }) {
  const defaultSteps = [
    "WhatsApp Trigger",
    "AI Order Extractor",
    "Google Sheets",
    "WhatsApp Reply",
  ];

  const steps = executedSteps.length > 0 ? executedSteps : defaultSteps;

  return (
    <div className="execution-overlay" role="status" aria-live="polite">
      <div className="execution-overlay-card">
        <div className="execution-spinner" aria-hidden="true" />
        <h3 className="execution-title">Executing workflow…</h3>
        <p className="execution-subtitle">
          Please wait while your nodes run in sequence.
        </p>

        <ul className="execution-steps">
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isDone = index < currentStep;

            return (
              <li
                key={`${step}-${index}`}
                className={`execution-step${
                  isActive ? " execution-step--active" : ""
                }${isDone ? " execution-step--done" : ""}`}
              >
                <span className="execution-step-icon">
                  {isDone ? "✓" : isActive ? "●" : "○"}
                </span>
                <span className="execution-step-label">{formatStepLabel(step)}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function formatStepLabel(step) {
  const labels = {
    start: "Start",
    whatsappTrigger: "WhatsApp Trigger",
    aiExtractor: "AI Order Extractor",
    googleSheets: "Google Sheets",
    whatsappReply: "WhatsApp Reply",
    api: "HTTP Request",
    llm: "LLM",
    condition: "If / Else",
    stop: "Stop",
  };

  return labels[step] || step;
}

export default ExecutionOverlay;
