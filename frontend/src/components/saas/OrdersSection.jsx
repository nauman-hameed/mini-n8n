import { ClipboardList, Loader2, Package, X } from "lucide-react";

const STATUS_LABELS = {
  PENDING: "Pending",
  CONFIRMED: "Confirmed",
  CANCELLED: "Cancelled",
  SHIPPED: "Shipped",
};

function statusClass(status) {
  if (status === "CONFIRMED" || status === "SHIPPED") {
    return "badge badge--success";
  }

  if (status === "CANCELLED") {
    return "badge badge--cancelled";
  }

  return "badge badge--pending";
}

function formatItems(items = []) {
  if (!items.length) {
    return "—";
  }

  return items
    .map((item) => `${item.quantity}× ${item.name}`)
    .join(", ");
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export default function OrdersSection({
  orders,
  isLoading,
  error,
  selectedOrder,
  onSelectOrder,
  onCloseDetail,
}) {
  const counts = {
    total: orders.length,
    PENDING: orders.filter((order) => order.status === "PENDING").length,
    CONFIRMED: orders.filter((order) => order.status === "CONFIRMED").length,
    CANCELLED: orders.filter((order) => order.status === "CANCELLED").length,
    SHIPPED: orders.filter((order) => order.status === "SHIPPED").length,
  };

  return (
    <section className="orders-section">
      <div className="order-stats">
        <article className="order-stat">
          <span>Total Orders</span>
          <strong>{counts.total}</strong>
        </article>
        <article className="order-stat order-stat--pending">
          <span>Pending</span>
          <strong>{counts.PENDING}</strong>
        </article>
        <article className="order-stat order-stat--confirmed">
          <span>Confirmed</span>
          <strong>{counts.CONFIRMED}</strong>
        </article>
        <article className="order-stat order-stat--cancelled">
          <span>Cancelled</span>
          <strong>{counts.CANCELLED}</strong>
        </article>
        <article className="order-stat order-stat--shipped">
          <span>Shipped</span>
          <strong>{counts.SHIPPED}</strong>
        </article>
      </div>

      <article className="dash-card dash-card--wide">
        <div className="dash-card__head">
          <div className="dash-card__icon dash-card__icon--indigo">
            <ClipboardList size={20} aria-hidden="true" />
          </div>
          <h2>Recent Orders</h2>
        </div>

        {isLoading ? (
          <div className="dashboard-loading dashboard-loading--inline">
            <Loader2 size={20} className="saas-spinner" aria-hidden="true" />
            <span>Loading orders…</span>
          </div>
        ) : error ? (
          <div className="dashboard-alert dashboard-alert--error" role="alert">
            {error}
          </div>
        ) : orders.length === 0 ? (
          <div className="orders-empty">
            <Package size={22} aria-hidden="true" />
            <p>No orders yet. New WhatsApp orders will appear here after refresh.</p>
          </div>
        ) : (
          <div className="orders-table-wrap">
            <table className="orders-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th>Phone</th>
                  <th>Items</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <button
                        type="button"
                        className="order-link"
                        onClick={() => onSelectOrder(order)}
                      >
                        {order.orderNumber || `ORD-${order.id}`}
                      </button>
                    </td>
                    <td>{order.customerName}</td>
                    <td>{order.customerPhone}</td>
                    <td>{formatItems(order.items)}</td>
                    <td>
                      <span className={statusClass(order.status)}>
                        {STATUS_LABELS[order.status] || order.status}
                      </span>
                    </td>
                    <td>{formatDate(order.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      {selectedOrder ? (
        <div
          className="order-modal-backdrop"
          role="presentation"
          onClick={onCloseDetail}
        >
          <div
            className="order-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="order-detail-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="order-modal__head">
              <h3 id="order-detail-title">
                Order {selectedOrder.orderNumber || selectedOrder.id}
              </h3>
              <button
                type="button"
                className="saas-btn saas-btn-ghost saas-btn-sm"
                onClick={onCloseDetail}
                aria-label="Close order details"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>

            <dl className="dash-card__list">
              <div>
                <dt>Order Number</dt>
                <dd>{selectedOrder.orderNumber}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <span className={statusClass(selectedOrder.status)}>
                    {STATUS_LABELS[selectedOrder.status] || selectedOrder.status}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Customer Name</dt>
                <dd>{selectedOrder.customerName}</dd>
              </div>
              <div>
                <dt>Phone</dt>
                <dd>{selectedOrder.customerPhone}</dd>
              </div>
              <div>
                <dt>Address / Notes</dt>
                <dd>{selectedOrder.notes || "—"}</dd>
              </div>
              <div>
                <dt>Created At</dt>
                <dd>{formatDate(selectedOrder.createdAt)}</dd>
              </div>
              <div>
                <dt>Courier</dt>
                <dd>{selectedOrder.courier || "—"}</dd>
              </div>
              <div>
                <dt>Tracking Number</dt>
                <dd>{selectedOrder.trackingNumber || "—"}</dd>
              </div>
              <div>
                <dt>Shipment Date</dt>
                <dd>{formatDate(selectedOrder.shipmentDate)}</dd>
              </div>
            </dl>

            <h4 className="order-modal__items-title">Items</h4>
            <ul className="order-items">
              {(selectedOrder.items || []).map((item) => (
                <li key={item.id || `${item.name}-${item.quantity}`}>
                  <span>{item.name}</span>
                  <span>Qty {item.quantity}</span>
                  <span>
                    {item.unitPrice != null ? `Rs ${item.unitPrice}` : "—"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}
