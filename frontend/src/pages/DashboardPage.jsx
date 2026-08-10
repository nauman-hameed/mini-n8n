import { useEffect, useState } from "react";
import {
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  Loader2,
  Phone,
  Sparkles,
} from "lucide-react";

import DashboardShell from "../components/saas/DashboardShell";
import { useAuth } from "../context/AuthContext";
import { fetchBusiness } from "../utils/authApi";

export default function DashboardPage() {
  const { user } = useAuth();
  const [business, setBusiness] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    fetchBusiness()
      .then(setBusiness)
      .catch((error) => {
        setLoadError(error.message || "Could not load business details.");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || "there";

  return (
    <DashboardShell>
      <section className="dashboard-welcome saas-animate-in">
        <p className="saas-eyebrow">
          <Sparkles size={14} aria-hidden="true" />
          Setup Complete
        </p>
        <h1>Welcome, {firstName}</h1>
        <p>
          Your business assistant setup is ready for the next step. Connect
          WhatsApp to activate automation behind the scenes.
        </p>
      </section>

      {isLoading ? (
        <div className="dashboard-loading">
          <Loader2 size={24} className="saas-spinner" aria-hidden="true" />
          <span>Loading business details…</span>
        </div>
      ) : loadError ? (
        <div className="dashboard-alert dashboard-alert--error" role="alert">
          {loadError}
        </div>
      ) : (
        <div className="dashboard-grid saas-animate-in saas-animate-delay-1">
          <article className="dash-card">
            <div className="dash-card__head">
              <div className="dash-card__icon dash-card__icon--blue">
                <Building2 size={20} aria-hidden="true" />
              </div>
              <h2>Business</h2>
            </div>
            <dl className="dash-card__list">
              <div>
                <dt>Name</dt>
                <dd>{business?.business_name || "—"}</dd>
              </div>
              <div>
                <dt>WhatsApp Number</dt>
                <dd>{business?.whatsapp_number || "—"}</dd>
              </div>
            </dl>
          </article>

          <article className="dash-card">
            <div className="dash-card__head">
              <div className="dash-card__icon dash-card__icon--green">
                <Bot size={20} aria-hidden="true" />
              </div>
              <h2>Assistant Status</h2>
            </div>
            <ul className="status-list">
              <li>
                <span className="badge badge--success">
                  <CheckCircle2 size={14} aria-hidden="true" />
                  Setup Complete
                </span>
              </li>
              <li>
                <span className="badge badge--pending">
                  <Phone size={14} aria-hidden="true" />
                  WhatsApp Connection · Pending
                </span>
              </li>
              <li>
                <span className="badge badge--pending">
                  <Clock size={14} aria-hidden="true" />
                  Assistant Activation · Pending
                </span>
              </li>
            </ul>
          </article>

          <article className="dash-card dash-card--wide">
            <div className="dash-card__head">
              <div className="dash-card__icon dash-card__icon--indigo">
                <Sparkles size={20} aria-hidden="true" />
              </div>
              <h2>What&apos;s Next</h2>
            </div>
            <ol className="next-steps">
              <li>Connect your WhatsApp Business account</li>
              <li>Configure assistant behavior for your business</li>
              <li>Start handling customer conversations automatically</li>
            </ol>
          </article>
        </div>
      )}
    </DashboardShell>
  );
}
