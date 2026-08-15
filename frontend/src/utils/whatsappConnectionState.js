export function getWhatsAppConnectionView(business, connectConfig = {}, uiStatus = "") {
  const isLegacy = business?.whatsapp_connection_type === "legacy";
  const status = uiStatus || business?.whatsapp_connection_status || "disconnected";
  const connected = status === "connected" || Boolean(business?.whatsapp_connected);
  const displayNumber =
    business?.whatsapp_display_phone_number || business?.whatsapp_number || "";

  if (isLegacy && connected) {
    return {
      state: "legacy_connected",
      title: "WhatsApp Connected",
      detail: displayNumber,
      canConnect: false,
      canReconnect: false,
      canDisconnect: false,
    };
  }

  if (status === "connecting" || uiStatus === "connecting") {
    return {
      state: "connecting",
      title: "Connecting to WhatsApp...",
      detail: "Please finish the Meta window if it is still open.",
      canConnect: false,
      canReconnect: false,
      canDisconnect: false,
    };
  }

  if (connected) {
    return {
      state: "connected",
      title: "WhatsApp Connected",
      detail: displayNumber,
      canConnect: false,
      canReconnect: Boolean(connectConfig.enabled),
      canDisconnect: true,
    };
  }

  if (status === "error") {
    return {
      state: "error",
      title: "Connection failed",
      detail:
        business?.whatsapp_connection_error ||
        "WhatsApp could not be connected. Please try again.",
      canConnect: Boolean(connectConfig.enabled),
      canReconnect: false,
      canDisconnect: false,
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
  };
}
