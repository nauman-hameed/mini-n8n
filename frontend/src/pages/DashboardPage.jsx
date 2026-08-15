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

import BusinessSettingsCard from "../components/saas/BusinessSettingsCard";
import DashboardShell from "../components/saas/DashboardShell";
import OrdersSection from "../components/saas/OrdersSection";
import { useAuth } from "../context/AuthContext";
import { fetchBusiness, fetchBusinessOrder, fetchBusinessOrders } from "../utils/authApi";

export default function DashboardPage() {
  const { user } = useAuth();

  const [business, setBusiness] = useState(null);
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [ordersError, setOrdersError] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);

  const loadDashboard = async () => {
    setIsLoading(true);
    setOrdersLoading(true);
    setLoadError("");
    setOrdersError("");

    try {
      const nextBusiness = await fetchBusiness();
      setBusiness(nextBusiness);
    } catch (error) {
      setLoadError(error.message || "Could not load business details.");
    } finally {
      setIsLoading(false);
    }

    try {
      const nextOrders = await fetchBusinessOrders();
      setOrders(nextOrders);
    } catch (error) {
      setOrdersError(error.message || "Could not load orders.");
    } finally {
      setOrdersLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || "there";
  const whatsappConnected = Boolean(business?.whatsapp_phone_number_id);

  const openOrder = async (order) => {
    setSelectedOrder(order);

    try {
      const detail = await fetchBusinessOrder(order.id);
      setSelectedOrder(detail);
    } catch {
      setSelectedOrder(order);
    }
  };

  return (
    <DashboardShell>
      <section className="dashboard-welcome saas-animate-in">
        <p className="saas-eyebrow">
          <Sparkles size={14} aria-hidden="true" />
          Business assistant
        </p>
        <h1>Welcome, {firstName}</h1>
        <p>
          Track WhatsApp orders and keep your business details up to date.
          Automation continues to run in the background.
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
                <span className={whatsappConnected ? "badge badge--success" : "badge badge--pending"}>
                  <Phone size={14} aria-hidden="true" />
                  WhatsApp · {whatsappConnected ? "Connected" : "Not Connected"}
                </span>
              </li>
              <li>
                <span className={whatsappConnected ? "badge badge--success" : "badge badge--pending"}>
                  {whatsappConnected ? (
                    <CheckCircle2 size={14} aria-hidden="true" />
                  ) : (
                    <Clock size={14} aria-hidden="true" />
                  )}
                  Assistant · {whatsappConnected ? "Active" : "Pending"}
                </span>
              </li>
            </ul>
          </article>

          <OrdersSection
            orders={orders}
            isLoading={ordersLoading}
            error={ordersError}
            selectedOrder={selectedOrder}
            onSelectOrder={openOrder}
            onCloseDetail={() => setSelectedOrder(null)}
          />

          <BusinessSettingsCard
            business={business}
            onSaved={(updated) => {
              setBusiness(updated);
            }}
          />
        </div>
      )}
    </DashboardShell>
  );
}
