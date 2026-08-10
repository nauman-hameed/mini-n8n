import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";
import { fetchBusiness } from "../utils/authApi";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
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

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="saas-page dashboard-page">
      <header className="dashboard-header">
        <Link to="/" className="saas-nav-brand">
          <Logo />
          <span>Hoplynk Assistant</span>
        </Link>

        <div className="dashboard-header-actions">
          <span className="dashboard-user">{user?.full_name}</span>
          <button type="button" className="saas-btn saas-btn-secondary" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <section className="dashboard-hero-card">
          <p className="saas-eyebrow">Setup Complete</p>
          <h1>Your Business Assistant account is ready</h1>
          <p>
            We&apos;ve saved your business details. The next milestone will connect
            WhatsApp and activate your assistant behind the scenes.
          </p>
        </section>

        {isLoading ? (
          <div className="dashboard-card">Loading business details…</div>
        ) : loadError ? (
          <div className="dashboard-card dashboard-card-error">{loadError}</div>
        ) : (
          <section className="dashboard-grid">
            <article className="dashboard-card">
              <h2>Business</h2>
              <dl>
                <div>
                  <dt>Name</dt>
                  <dd>{business?.business_name || "—"}</dd>
                </div>
                <div>
                  <dt>WhatsApp Number</dt>
                  <dd>{business?.whatsapp_number || "—"}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>
                    <span className="status-pill status-pill-success">
                      Onboarding saved
                    </span>
                  </dd>
                </div>
              </dl>
            </article>

            <article className="dashboard-card">
              <h2>What&apos;s next</h2>
              <ul className="dashboard-next-list">
                <li>Connect your WhatsApp Business account</li>
                <li>Configure assistant behavior for your business</li>
                <li>Start handling customer conversations automatically</li>
              </ul>
            </article>
          </section>
        )}
      </main>
    </div>
  );
}
