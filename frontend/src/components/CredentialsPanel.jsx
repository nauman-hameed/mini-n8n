import { useEffect, useState } from "react";

const EMPTY_FORM = {
  googleClientId: "",
  googleClientSecret: "",
  googleSpreadsheetId: "",
  metaAccessToken: "",
  metaPhoneNumberId: "",
  metaVerifyToken: "",
  aiProvider: "ollama",
  geminiApiKey: "",
};

function CredentialsPanel({ onClose }) {
  const [formData, setFormData] =
    useState(EMPTY_FORM);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSaving, setIsSaving] =
    useState(false);

  useEffect(() => {
    const loadCredentials = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_BACKEND_URL}/credentials`
        );

        const data = await response.json();

        if (!response.ok) {
          console.error(
            data.message ||
              "Could not load credentials."
          );
          return;
        }

        if (data.credentials) {
          setFormData({
            ...EMPTY_FORM,
            ...data.credentials,
          });
        }
      } catch (error) {
        console.error(
          "Could not load credentials:",
          error
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadCredentials();
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

      const response = await fetch(
        `${import.meta.env.VITE_BACKEND_URL}/credentials`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(
          data.message ||
            "Could not save credentials."
        );
        return;
      }

      alert(data.message);
      onClose();
    } catch (error) {
      console.error(
        "Credentials error:",
        error
      );

      alert("Backend connection failed.");
    } finally {
      setIsSaving(false);
    }
  };

  const inputStyle = {
    boxSizing: "border-box",
    width: "100%",
    padding: "9px",
    marginTop: "5px",
    marginBottom: "12px",
  };

  const labelStyle = {
    display: "block",
    fontWeight: "600",
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.55)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: "480px",
          maxHeight: "85vh",
          overflowY: "auto",
          background: "white",
          borderRadius: "8px",
          padding: "20px",
          color: "#222",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            marginBottom: "18px",
          }}
        >
          <h2 style={{ margin: 0 }}>
            Credentials
          </h2>

          <button
            onClick={onClose}
            disabled={isSaving}
          >
            ✕
          </button>
        </div>

        {isLoading ? (
          <p>Loading credentials...</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3>Google Sheets</h3>

            <label style={labelStyle}>
              Google Client ID
            </label>

            <input
              type="text"
              value={formData.googleClientId}
              onChange={(event) =>
                updateField(
                  "googleClientId",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <label style={labelStyle}>
              Google Client Secret
            </label>

            <input
              type="password"
              value={
                formData.googleClientSecret
              }
              onChange={(event) =>
                updateField(
                  "googleClientSecret",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <label style={labelStyle}>
              Spreadsheet ID
            </label>

            <input
              type="text"
              value={
                formData.googleSpreadsheetId
              }
              onChange={(event) =>
                updateField(
                  "googleSpreadsheetId",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <hr />

            <h3>Meta WhatsApp</h3>

            <label style={labelStyle}>
              Access Token
            </label>

            <input
              type="password"
              value={formData.metaAccessToken}
              onChange={(event) =>
                updateField(
                  "metaAccessToken",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <label style={labelStyle}>
              Phone Number ID
            </label>

            <input
              type="text"
              value={
                formData.metaPhoneNumberId
              }
              onChange={(event) =>
                updateField(
                  "metaPhoneNumberId",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <label style={labelStyle}>
              Verify Token
            </label>

            <input
              type="password"
              value={formData.metaVerifyToken}
              onChange={(event) =>
                updateField(
                  "metaVerifyToken",
                  event.target.value
                )
              }
              style={inputStyle}
            />

            <hr />

            <h3>AI Provider</h3>

            <label style={labelStyle}>
              Provider
            </label>

            <select
              value={formData.aiProvider}
              onChange={(event) =>
                updateField(
                  "aiProvider",
                  event.target.value
                )
              }
              style={inputStyle}
            >
              <option value="ollama">
                Ollama
              </option>

              <option value="gemini">
                Gemini
              </option>
            </select>

            {formData.aiProvider ===
              "gemini" && (
              <>
                <label style={labelStyle}>
                  Gemini API Key
                </label>

                <input
                  type="password"
                  value={
                    formData.geminiApiKey
                  }
                  onChange={(event) =>
                    updateField(
                      "geminiApiKey",
                      event.target.value
                    )
                  }
                  style={inputStyle}
                />
              </>
            )}

            <button
              type="submit"
              disabled={isSaving}
              style={{
                width: "100%",
                padding: "10px",
                marginTop: "10px",
                cursor: isSaving
                  ? "not-allowed"
                  : "pointer",
              }}
            >
              {isSaving
                ? "Saving..."
                : "Save Credentials"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default CredentialsPanel;