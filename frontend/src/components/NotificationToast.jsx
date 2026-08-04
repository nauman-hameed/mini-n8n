function NotificationToast({ notifications, onDismiss }) {
  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="toast-container" aria-live="polite">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`toast toast--${notification.type}`}
          role="alert"
        >
          <span className="toast-icon">{getIcon(notification.type)}</span>
          <div className="toast-content">
            <p className="toast-title">{notification.title}</p>
            {notification.message && (
              <p className="toast-message">{notification.message}</p>
            )}
          </div>
          <button
            className="toast-close"
            onClick={() => onDismiss(notification.id)}
            aria-label="Dismiss notification"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

function getIcon(type) {
  if (type === "success") return "✅";
  if (type === "error") return "❌";
  if (type === "warning") return "⚠️";
  return "ℹ️";
}

export default NotificationToast;
