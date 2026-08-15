import { getWhatsAppConnectionView } from "../src/utils/whatsappConnectionState.js";
import { originIsFacebook, parseSignupEvent } from "../src/utils/embeddedSignup.js";

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function ok(message) {
  console.log(`OK: ${message}`);
}

const disabled = getWhatsAppConnectionView({ whatsapp_connection_status: "disconnected" }, { enabled: false });
if (disabled.state !== "disconnected" || disabled.canConnect) {
  fail("disconnected + disabled config should not show Connect");
}
ok("disconnected + missing Meta config is a safe disabled state");

const ready = getWhatsAppConnectionView({ whatsapp_connection_status: "disconnected" }, { enabled: true });
if (!ready.canConnect || ready.state !== "disconnected") {
  fail("disconnected + enabled config should show Connect");
}
ok("disconnected + enabled config shows Connect WhatsApp");

const connecting = getWhatsAppConnectionView({ whatsapp_connection_status: "disconnected" }, { enabled: true }, "connecting");
if (connecting.state !== "connecting" || connecting.canConnect) {
  fail("connecting state mismatch");
}
ok("connecting state renders Connecting to WhatsApp");

const connected = getWhatsAppConnectionView({
    whatsapp_connection_status: "connected",
    whatsapp_connection_type: "embedded_signup",
    whatsapp_connected: true,
    whatsapp_display_phone_number: "+923009991111",
  }, { enabled: true });
if (connected.state !== "connected" || !connected.canReconnect || !connected.canDisconnect) {
  fail("connected ES tenant should allow reconnect/disconnect");
}
ok("connected Embedded Signup tenant can reconnect and disconnect");

const legacy = getWhatsAppConnectionView({
    whatsapp_connection_status: "connected",
    whatsapp_connection_type: "legacy",
    whatsapp_connected: true,
    whatsapp_display_phone_number: "+923071055454",
  }, { enabled: true });
if (legacy.state !== "legacy_connected" || legacy.canReconnect || legacy.canDisconnect || !legacy.detail.includes("23071055454")) {
  fail(`legacy view mismatch: ${JSON.stringify(legacy)}`);
}
ok("legacy connected tenant hides Reconnect/Disconnect");

const errored = getWhatsAppConnectionView({
    whatsapp_connection_status: "error",
    whatsapp_connection_error: "Could not complete WhatsApp connection. Please try again.",
  }, { enabled: true });
if (errored.state !== "error" || !errored.canConnect) {
  fail("error state should offer Try Again");
}
ok("error state renders Try Again");

if (!originIsFacebook("https://www.facebook.com") || originIsFacebook("https://evil.example")) {
  fail("origin check failed");
}
ok("Embedded Signup listener accepts facebook.com origins only");

const event = parseSignupEvent({
  type: "WA_EMBEDDED_SIGNUP",
  event: "FINISH",
  data: { waba_id: "1", phone_number_id: "2" },
});
if (event?.data?.waba_id !== "1") {
  fail("FINISH event parse failed");
}
ok("Embedded Signup FINISH event parses WABA and phone IDs");

console.log("\nAll WhatsApp connection UI checks passed.");
