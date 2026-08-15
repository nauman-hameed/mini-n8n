import { useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, Loader2, Phone } from "lucide-react";

import {
  completeWhatsAppConnection,
  disconnectWhatsAppConnection,
  fetchWhatsAppConnectConfig,
} from "../../utils/authApi";
import {
  INCOMPLETE_CONNECTION_MESSAGE,
  abortEmbeddedSignup,
  launchEmbeddedSignup,
} from "../../utils/embeddedSignup";
import { getWhatsAppConnectionView } from "../../utils/whatsappConnectionState";

export default function WhatsAppConnectCard({ business, onChanged }) {
  const [connectConfig, setConnectConfig] = useState({ enabled: false });
  const [uiStatus, setUiStatus] = useState("");
  const [actionError, setActionError] = useState("");
  const [isWorking, setIsWorking] = useState(false);
  const attemptRef = useRef(null);

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
      abortEmbeddedSignup();
    };
  }, []);

  const view = useMemo(
    () => getWhatsAppConnectionView(business, connectConfig, uiStatus),
    [business, connectConfig, uiStatus]
  );

  const markIncomplete = () => {
    attemptRef.current = null;
    setUiStatus("incomplete");
    setActionError(INCOMPLETE_CONNECTION_MESSAGE);
    setIsWorking(false);
  };

  const cancelAttempt = () => {
    attemptRef.current?.abort();
    abortEmbeddedSignup();
    markIncomplete();
  };

  const runSignup = () => {
    if (!connectConfig.enabled) {
      return;
    }

    abortEmbeddedSignup();
    setActionError("");
    setUiStatus("connecting");
    setIsWorking(true);

    const attempt = launchEmbeddedSignup({
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
          setActionError("");
          onChanged?.(updated);
        } catch (error) {
          setUiStatus("error");
          setActionError(error.message || "Could not complete WhatsApp connection.");
        } finally {
          attemptRef.current = null;
          setIsWorking(false);
        }
      },
      onCancel: () => {
        markIncomplete();
      },
      onError: (error) => {
        attemptRef.current = null;
        setUiStatus("error");
        setActionError(error.message || "Could not start WhatsApp connection.");
        setIsWorking(false);
      },
    });

    attemptRef.current = attempt;
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
  const primaryLabel =
    view.state === "error" || view.state === "incomplete" || view.state === "connecting"
      ? "Try Again"
      : "Connect WhatsApp";

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
            {view.state === "connecting" ? (
              <>
                <Loader2 size={14} className="saas-spinner" aria-hidden="true" />
                {view.title}
              </>
            ) : (
              view.title
            )}
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
          {view.canConnect ? (
            <button
              type="button"
              className="saas-btn saas-btn-primary"
              onClick={runSignup}
            >
              {primaryLabel}
            </button>
          ) : null}

          {view.canCancel ? (
            <button
              type="button"
              className="saas-btn saas-btn-ghost"
              onClick={cancelAttempt}
            >
              Cancel
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
