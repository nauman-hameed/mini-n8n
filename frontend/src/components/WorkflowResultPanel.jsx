function WorkflowResultPanel({ result, executedNodes, onClose }) {
  const googleSheets = result?.google_sheets;

  return (
    <div className="panel result-panel">
      <div className="panel-header">
        <h3 className="panel-title">✅ Workflow Completed</h3>
        <button
          className="btn btn-icon btn-ghost"
          onClick={onClose}
          aria-label="Close result"
        >
          ✕
        </button>
      </div>

      <div className="panel-body">
        {executedNodes?.length > 0 && (
          <>
            <p className="form-label">Executed Nodes</p>
            <ul className="executed-nodes-list">
              {executedNodes.map((node, index) => (
                <li key={`${node}-${index}`}>{formatNodeLabel(node)}</li>
              ))}
            </ul>
          </>
        )}

        {googleSheets && (
          <div className="result-highlight result-highlight--success">
            <strong>Google Sheets updated</strong>
            <p>
              {googleSheets.updated_rows || 0} row(s) added
              {googleSheets.updated_range
                ? ` → ${googleSheets.updated_range}`
                : ""}
            </p>
          </div>
        )}

        {result?.whatsapp_send?.success && (
          <div className="result-highlight result-highlight--success">
            <strong>WhatsApp message sent</strong>
            <p>
              Delivered to {result.whatsapp_send.to}
              {result.whatsapp_send.message_id
                ? ` · ID: ${result.whatsapp_send.message_id}`
                : ""}
            </p>
          </div>
        )}

        {result?.reply_message && !result?.whatsapp_send?.success && (
          <div className="result-highlight">
            <strong>Reply prepared only</strong>
            <p>
              Add a Test Phone on the WhatsApp Trigger node to send
              during manual runs, or trigger via the Meta webhook.
            </p>
          </div>
        )}

        <p className="form-label" style={{ marginTop: 16 }}>
          Extracted Order
        </p>

        <div className="result-field">
          <span className="result-field-label">Name</span>
          <span className="result-field-value">{result.name || "—"}</span>
        </div>
        <div className="result-field">
          <span className="result-field-label">Phone</span>
          <span className="result-field-value">{result.phone || "—"}</span>
        </div>
        <div className="result-field">
          <span className="result-field-label">Address</span>
          <span className="result-field-value">{result.address || "—"}</span>
        </div>
        <div className="result-field">
          <span className="result-field-label">Items</span>
          <span className="result-field-value">{result.items || "—"}</span>
        </div>

        <p className="form-label" style={{ marginTop: 16 }}>
          WhatsApp Reply
        </p>
        <div className="result-reply">
          {result.reply_message || "No reply generated."}
        </div>
      </div>
    </div>
  );
}

function formatNodeLabel(nodeType) {
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

  return labels[nodeType] || nodeType;
}

export default WorkflowResultPanel;
