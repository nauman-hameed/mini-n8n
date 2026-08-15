export function getWhatsAppConnectionView(business, connectConfig = {}, uiStatus = "") {
  const isLegacy = business?.whatsapp_connection_type === "legacy";
  const persistedStatus = business?.whatsapp_connection_status || "disconnected";
  const displayNumber =
    business?.whatsapp_display_phone_number || business?.whatsapp_number || "";
  const persistedConnected =
    persistedStatus === "connected" || Boolean(business?.whatsapp_connected);

  if (isLegacy && persistedConnected) {
    return {
      state: "legacy_connected",
      title: "WhatsApp Connected",
      detail: displayNumber,
      canConnect: false,
      canReconnect: false,
      canDisconnect: false,
      canCancel: false,
    };
  }

  if (uiStatus === "connecting") {
    return {
      state: "connecting",
      title: "Connecting to WhatsApp...",
      detail: "Finish the Meta window if it is still open, or cancel to try again.",
      canConnect: Boolean(connectConfig.enabled),
      canReconnect: false,
      canDisconnect: false,
      canCancel: true,
    };
  }

  if (persistedConnected) {
    return {
      state: "connected",
      title: "WhatsApp Connected",
      detail: displayNumber,
      canConnect: false,
      canReconnect: Boolean(connectConfig.enabled),
      canDisconnect: true,
      canCancel: false,
    };
  }

  if (uiStatus === "error" || persistedStatus === "error") {
    return {
      state: "error",
      title: "Connection failed",
      detail:
        business?.whatsapp_connection_error ||
        "WhatsApp could not be connected. Please try again.",
      canConnect: Boolean(connectConfig.enabled),
      canReconnect: false,
      canDisconnect: false,
      canCancel: false,
    };
  }

  if (uiStatus === "incomplete") {
    return {
      state: "incomplete",
      title: "Not connected",
      detail: "WhatsApp connection was not completed.",
      canConnect: Boolean(connectConfig.enabled),
      canReconnect: false,
      canDisconnect: false,
      canCancel: false,
    };
  }

  return {
    state: "disconnected",
    title: "Not connected",
    detail: connectConfig.enabled
      ? "Connect your WhatsApp Business account with Meta Embedded Signup."
      : "WhatsApp connection is not available yet. Meta setup is still required.",
    canConnect: Boolean(connectConfig.enabled),
    canReconnect: false,
    canDisconnect: false,
    canCancel: false,
  };
}
