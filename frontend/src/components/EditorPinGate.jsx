import { useEffect, useState } from "react";
import { getBackendUrl } from "../utils/api";

const AUTH_SESSION_KEY = "mini-n8n-editor-unlocked";

export function isEditorUnlocked() {
  return sessionStorage.getItem(AUTH_SESSION_KEY) === "true";
}

export function unlockEditor() {
  sessionStorage.setItem(AUTH_SESSION_KEY, "true");
}

export function lockEditor() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}

function EditorPinGate({ onClose, onSuccess }) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkPinRequired = async () => {
      try {
        const response = await fetch(getBackendUrl("/auth/pin-required"));
        const data = await response.json();

        if (response.ok && !data.pin_required) {
          unlockEditor();
          onSuccess();
          return;
        }
      } catch (verifyError) {
        console.error("Could not check PIN requirement:", verifyError);
        setError("Could not reach the server. Try again.");
      } finally {
        setIsChecking(false);
      }
    };

    checkPinRequired();
  }, [onSuccess]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await fetch(getBackendUrl("/auth/verify-pin"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pin }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.message || "Incorrect PIN.");
        return;
      }

      unlockEditor();
      onSuccess();
    } catch (submitError) {
      console.error("PIN verification failed:", submitError);
      setError("Could not reach the server. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isChecking) {
    return (
      <div className="modal-overlay">
        <div className="modal">
          <p className="modal-loading">Checking access…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-labelledby="pin-gate-title"
      >
        <div className="modal-header">
          <h2 className="modal-title" id="pin-gate-title">
            Enter editor PIN
          </h2>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <p style={{ color: "var(--color-text-muted)", marginBottom: 16 }}>
            Enter the PIN to open the workflow editor and credentials.
          </p>

          <label className="form-label" htmlFor="editor-pin">
            PIN
          </label>
          <input
            id="editor-pin"
            className="form-input"
            type="password"
            inputMode="numeric"
            autoComplete="current-password"
            value={pin}
            onChange={(event) => setPin(event.target.value)}
            placeholder="Enter PIN"
            autoFocus
          />

          {error && (
            <p style={{ color: "#ff6b6b", marginTop: 12, fontSize: 13 }}>
              {error}
            </p>
          )}

          <div
            style={{
              display: "flex",
              gap: 10,
              justifyContent: "flex-end",
              marginTop: 20,
            }}
          >
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || !pin.trim()}
            >
              {isSubmitting ? "Checking…" : "Unlock Editor"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditorPinGate;
