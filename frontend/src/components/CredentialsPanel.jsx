import { useEffect, useState } from "react";
import { fetchWebhookUrl, getBackendUrl } from "../utils/api";

const EMPTY_FORM = {
  googleClientId: "",
  googleClientSecret: "",
  googleSpreadsheetId: "",
  metaAccessToken: "",
  metaPhoneNumberId: "",
  metaVerifyToken: "",
  aiProvider: "gemini",
  geminiApiKey: "",
};

function CredentialsPanel({ onClose }) {
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");

  useEffect(() => {
    fetchWebhookUrl()
      .then(setWebhookUrl)
      .catch((error) => {
        console.error("Could not load webhook URL:", error);
      });
  }, []);

  const updateField = (field, value) => {
    setFormData((currentData) => ({
      ...currentData,
      [field]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setIsSaving(true);

      const response = await fetch(getBackendUrl("/credentials"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        setSaveMessage("");
        alert(data.message || "Could not save credentials.");
        return;
      }

      setSaveMessage("Credentials saved securely.");
    } catch (error) {
      console.error("Credentials error:", error);
      alert("Backend connection failed.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-labelledby="credentials-title"
      >
        <div className="modal-header">
          <h2 className="modal-title" id="credentials-title">
            🔑 Credentials
          </h2>
          <button
            className="btn btn-icon btn-ghost"
            onClick={onClose}
            disabled={isSaving}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <p className="field-hint" style={{ marginBottom: 16 }}>
            Paste your API keys below, then click Save Credentials. Fields
            start empty each time you open this panel.
          </p>

            {saveMessage && (
              <p
                className="field-hint"
                style={{ color: "#4ade80", marginBottom: 16 }}
              >
                {saveMessage}
              </p>
            )}

            <h3 className="form-section-title">Google Sheets</h3>

            <label className="form-label">Google Client ID</label>
            <input
              className="form-input"
              type="text"
              value={formData.googleClientId}
              onChange={(event) =>
                updateField("googleClientId", event.target.value)
              }
            />

            <label className="form-label">Google Client Secret</label>
            <input
              className="form-input"
              type="password"
              value={formData.googleClientSecret}
              onChange={(event) =>
                updateField("googleClientSecret", event.target.value)
              }
            />

            <label className="form-label">Spreadsheet ID</label>
            <input
              className="form-input"
              type="text"
              value={formData.googleSpreadsheetId}
              onChange={(event) =>
                updateField("googleSpreadsheetId", event.target.value)
              }
            />

            <hr className="form-divider" />

            <h3 className="form-section-title">Meta WhatsApp</h3>

            <label className="form-label">Access Token</label>
            <input
              className="form-input"
              type="password"
              value={formData.metaAccessToken}
              onChange={(event) =>
                updateField("metaAccessToken", event.target.value)
              }
            />

            <label className="form-label">Phone Number ID</label>
            <input
              className="form-input"
              type="text"
              value={formData.metaPhoneNumberId}
              onChange={(event) =>
                updateField("metaPhoneNumberId", event.target.value)
              }
            />

            <label className="form-label">Verify Token</label>
            <input
              className="form-input"
              type="password"
              value={formData.metaVerifyToken}
              onChange={(event) =>
                updateField("metaVerifyToken", event.target.value)
              }
            />

            {webhookUrl && (
              <>
                <label className="form-label" style={{ marginTop: 12 }}>
                  Webhook Callback URL
                </label>
                <input
                  className="form-input"
                  type="text"
                  value={webhookUrl}
                  readOnly
                />
                <p className="field-hint">
                  Paste this URL in Meta Developer Console → WhatsApp →
                  Configuration → Webhook. Use the same Verify Token above.
                  Subscribe to the <strong>messages</strong> field.
                </p>
              </>
            )}

            <hr className="form-divider" />

            <h3 className="form-section-title">AI Provider</h3>

            <label className="form-label">Provider</label>
            <select
              className="form-select"
              value={formData.aiProvider}
              onChange={(event) =>
                updateField("aiProvider", event.target.value)
              }
            >
              <option value="ollama">Ollama</option>
              <option value="gemini">Gemini</option>
            </select>

            {formData.aiProvider === "gemini" && (
              <>
                <label className="form-label" style={{ marginTop: 12 }}>
                  Gemini API Key
                </label>
                <input
                  className="form-input"
                  type="password"
                  value={formData.geminiApiKey}
                  onChange={(event) =>
                    updateField("geminiApiKey", event.target.value)
                  }
                />
              </>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSaving}
              style={{ width: "100%", marginTop: 20 }}
            >
            {isSaving ? "Saving…" : "Save Credentials"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default CredentialsPanel;
