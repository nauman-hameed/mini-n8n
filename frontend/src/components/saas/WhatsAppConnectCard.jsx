import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, Phone } from "lucide-react";

import {
  completeWhatsAppConnection,
  disconnectWhatsAppConnection,
  fetchWhatsAppConnectConfig,
} from "../../utils/authApi";
import { launchEmbeddedSignup } from "../../utils/embeddedSignup";
import { getWhatsAppConnectionView } from "../../utils/whatsappConnectionState";

export default function WhatsAppConnectCard({ business, onChanged }) {
  const [connectConfig, setConnectConfig] = useState({ enabled: false });
  const [uiStatus, setUiStatus] = useState("");
  const [actionError, setActionError] = useState("");
  const [isWorking, setIsWorking] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetchWhatsAppConnectConfig()
      .then((config) => {
        if (!cancelled) {
          setConnectConfig(config);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setConnectConfig({ enabled: false });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const view = useMemo(
    () => getWhatsAppConnectionView(business, connectConfig, uiStatus),
    [business, connectConfig, uiStatus]
  );

  const runSignup = async () => {
    if (!connectConfig.enabled || isWorking) {
      return;
    }

    setActionError("");
    setUiStatus("connecting");
    setIsWorking(true);

    await launchEmbeddedSignup({
      appId: connectConfig.appId,
      configId: connectConfig.configId,
      graphVersion: connectConfig.graphVersion,
      onComplete: async ({ code, wabaId, phoneNumberId }) => {
        try {
          const updated = await completeWhatsAppConnection({
            code,
            wabaId,
            phoneNumberId,
          });
          setUiStatus("");
          onChanged?.(updated);
        } catch (error) {
          setUiStatus("error");
          setActionError(error.message || "Could not complete WhatsApp connection.");
        } finally {
          setIsWorking(false);
        }
      },
      onCancel: () => {
        setUiStatus("");
        setIsWorking(false);
      },
      onError: (error) => {
        setUiStatus("error");
        setActionError(error.message || "Could not start WhatsApp connection.");
        setIsWorking(false);
      },
    });
  };

  const handleDisconnect = async () => {
    if (isWorking) {
      return;
    }

    setIsWorking(true);
    setActionError("");

    try {
      const updated = await disconnectWhatsAppConnection();
      setUiStatus("");
      onChanged?.(updated);
    } catch (error) {
      setActionError(error.message || "Could not disconnect WhatsApp.");
    } finally {
      setIsWorking(false);
    }
  };

  const connected = view.state === "connected" || view.state === "legacy_connected";

  return (
    <article className="dash-card dash-card--wide">
      <div className="dash-card__head">
        <div className="dash-card__icon dash-card__icon--green">
          <Phone size={20} aria-hidden="true" />
        </div>
        <h2>WhatsApp Connection</h2>
      </div>

      <div className="whatsapp-connect">
        <div className="whatsapp-connect__status">
          <span className={connected ? "badge badge--success" : view.state === "error" ? "badge badge--cancelled" : "badge badge--pending"}>
            {connected ? <CheckCircle2 size={14} aria-hidden="true" /> : null}
            {view.title}
          </span>
          {view.detail ? <p className="whatsapp-connect__detail">{view.detail}</p> : null}
          {actionError ? (
            <p className="field-error" role="alert">
              {actionError}
            </p>
          ) : null}
          {view.state === "legacy_connected" ? (
            <p className="field-hint">
              This number is already connected through the original setup.
              Embedded Signup migration is not available yet.
            </p>
          ) : null}
        </div>

        <div className="whatsapp-connect__actions">
          {view.state === "connecting" ? (
            <button type="button" className="saas-btn saas-btn-primary" disabled>
              <Loader2 size={16} className="saas-spinner" aria-hidden="true" />
              Connecting to WhatsApp...
            </button>
          ) : null}

          {view.state !== "connecting" && view.canConnect ? (
            <button
              type="button"
              className="saas-btn saas-btn-primary"
              onClick={runSignup}
              disabled={isWorking}
            >
              {view.state === "error" ? "Try Again" : "Connect WhatsApp"}
            </button>
          ) : null}

          {view.canReconnect ? (
            <button
              type="button"
              className="saas-btn saas-btn-secondary"
              onClick={runSignup}
              disabled={isWorking}
            >
              Reconnect
            </button>
          ) : null}

          {view.canDisconnect ? (
            <button
              type="button"
              className="saas-btn saas-btn-ghost"
              onClick={handleDisconnect}
              disabled={isWorking}
            >
              Disconnect
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
