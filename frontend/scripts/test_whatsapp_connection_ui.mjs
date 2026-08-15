import {
  EMBEDDED_SIGNUP_TIMEOUT_MS,
  abortEmbeddedSignup,
  launchEmbeddedSignup,
  originIsFacebook,
  parseSignupEvent,
} from "../src/utils/embeddedSignup.js";
import { getWhatsAppConnectionView } from "../src/utils/whatsappConnectionState.js";

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function ok(message) {
  console.log(`OK: ${message}`);
}

function createHost() {
  const listeners = new Map();
  const timers = new Map();
  let nextTimer = 1;
  const host = {
    FB: {
      init() {},
      login(callback) {
        host._popup = host.open("https://www.facebook.com/login.php");
        host._loginCallback = callback;
      },
    },
    document: {
      getElementById() {
        return null;
      },
      createElement() {
        return { id: "", async: true, defer: true, crossOrigin: "", src: "", onerror: null };
      },
      head: {
        appendChild() {},
      },
    },
    addEventListener(type, handler) {
      if (!listeners.has(type)) {
        listeners.set(type, new Set());
      }
      listeners.get(type).add(handler);
    },
    removeEventListener(type, handler) {
      listeners.get(type)?.delete(handler);
    },
    dispatchMessage(origin, data) {
      for (const handler of listeners.get("message") || []) {
        handler({ origin, data });
      }
    },
    open() {
      host._popup = { closed: false };
      return host._popup;
    },
    setTimeout(fn) {
      const id = nextTimer++;
      timers.set(id, { type: "timeout", fn });
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    setInterval(fn) {
      const id = nextTimer++;
      timers.set(id, { type: "interval", fn });
      return id;
    },
    clearInterval(id) {
      timers.delete(id);
    },
    runTimeouts() {
      for (const timer of [...timers.values()]) {
        if (timer.type === "timeout") {
          timer.fn();
        }
      }
    },
    runIntervals() {
      for (const timer of [...timers.values()]) {
        if (timer.type === "interval") {
          timer.fn();
        }
      }
    },
    listenerCount(type) {
      return listeners.get(type)?.size || 0;
    },
    pendingTimerCount() {
      return timers.size;
    },
  };
  return host;
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
if (connecting.state !== "connecting" || !connecting.canConnect || !connecting.canCancel) {
  fail("connecting state should remain retryable with Cancel");
}
ok("connecting state renders Connecting to WhatsApp with Try Again/Cancel");

const leftoverConnecting = getWhatsAppConnectionView(
  { whatsapp_connection_status: "connecting" },
  { enabled: true }
);
if (leftoverConnecting.state === "connecting" || !leftoverConnecting.canConnect) {
  fail("persisted connecting must not trap the dashboard after refresh");
}
ok("DB connecting leftover is treated as retryable, not an infinite spinner");

const incomplete = getWhatsAppConnectionView({ whatsapp_connection_status: "disconnected" }, { enabled: true }, "incomplete");
if (incomplete.state !== "incomplete" || incomplete.title !== "Not connected" || !incomplete.canConnect) {
  fail("incomplete state should be retryable Not connected");
}
if (!incomplete.detail.includes("not completed")) {
  fail("incomplete state missing not-completed message");
}
ok("cancelled/closed/timed-out state is retryable Not connected");

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
  }, { enabled: true }, "connecting");
if (legacy.state !== "legacy_connected" || legacy.canReconnect || legacy.canDisconnect || !legacy.detail.includes("23071055454")) {
  fail(`legacy view mismatch: ${JSON.stringify(legacy)}`);
}
ok("legacy connected tenant hides Reconnect/Disconnect even during UI connecting");

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

if (EMBEDDED_SIGNUP_TIMEOUT_MS !== 120000) {
  fail(`unexpected timeout ${EMBEDDED_SIGNUP_TIMEOUT_MS}`);
}
ok("Embedded Signup timeout is 120 seconds");

function runSignup(host, handlers = {}, timeoutMs = 120000) {
  return launchEmbeddedSignup({
    appId: "app",
    configId: "config",
    graphVersion: "v23.0",
    timeoutMs,
    hostWindow: host,
    onComplete: handlers.onComplete || (() => {}),
    onCancel: handlers.onCancel || (() => {}),
    onError: handlers.onError || (() => {}),
  });
}

function flush() {
  return Promise.resolve();
}

await (async () => {
  const host = createHost();
  let cancelled = null;
  runSignup(host, { onCancel: (info) => { cancelled = info; } });
  host.dispatchMessage("https://www.facebook.com", {
    type: "WA_EMBEDDED_SIGNUP",
    event: "CANCEL",
  });
  if (cancelled?.reason !== "cancel") {
    fail("CANCEL should be retryable incomplete, not hang");
  }
  if (host.listenerCount("message") !== 0 || host.pendingTimerCount() !== 0) {
    fail("CANCEL left listeners or timers behind");
  }
  ok("Meta CANCEL returns to retryable Not connected");

  {
    const nextHost = createHost();
    cancelled = null;
    runSignup(nextHost, { onCancel: (info) => { cancelled = info; } });
    await flush();
    nextHost._loginCallback?.({});
    if (cancelled?.reason !== "no_code") {
      fail("FB.login without code should cancel");
    }
    ok("FB.login with no code returns to retryable state");
  }

  {
    const nextHost = createHost();
    cancelled = null;
    runSignup(nextHost, { onCancel: (info) => { cancelled = info; } }, 1);
    await flush();
    nextHost.runTimeouts();
    if (cancelled?.reason !== "timeout") {
      fail("timeout should cancel without calling complete");
    }
    ok("timeout returns to retryable state");
  }

  {
    const nextHost = createHost();
    cancelled = null;
    let completed = 0;
    runSignup(nextHost, {
      onCancel: (info) => { cancelled = info; },
      onComplete: () => { completed += 1; },
    });
    await flush();
    if (!nextHost._popup) {
      fail("FB.login should open a popup we can observe");
    }
    nextHost._popup.closed = true;
    nextHost.runIntervals();
    if (cancelled?.reason !== "popup_closed" || completed !== 0) {
      fail("closed popup should cancel without complete");
    }
    ok("closed Meta popup returns to retryable state");
  }

  {
    const nextHost = createHost();
    let errored = null;
    runSignup(nextHost, { onError: (error) => { errored = error; } });
    nextHost.dispatchMessage("https://www.facebook.com", {
      type: "WA_EMBEDDED_SIGNUP",
      event: "ERROR",
      data: { error_message: "denied" },
    });
    if (!errored?.message) {
      fail("Meta ERROR event should surface a safe failure");
    }
    ok("Meta ERROR event becomes Connection failed + Try Again");
  }

  {
    const nextHost = createHost();
    const completes = [];
    runSignup(nextHost, { onComplete: (payload) => completes.push(payload) });
    await flush();
    nextHost.dispatchMessage("https://www.facebook.com", {
      type: "WA_EMBEDDED_SIGNUP",
      event: "FINISH",
      data: { waba_id: "109876543210", phone_number_id: "200300400500" },
    });
    if (completes.length !== 0) {
      fail("complete must not run before auth code exists");
    }
    nextHost._loginCallback?.({ authResponse: { code: "short-lived-auth-code" } });
    if (completes.length !== 1) {
      fail(`expected one complete call, got ${completes.length}`);
    }
    if (completes[0].wabaId !== "109876543210" || completes[0].phoneNumberId !== "200300400500") {
      fail("complete payload missing verified IDs");
    }
    if (Object.keys(completes[0]).join(",") !== "code,wabaId,phoneNumberId") {
      fail("complete payload should only include code and IDs");
    }
    ok("successful FINISH + code calls complete once");
  }

  {
    const nextHost = createHost();
    const completes = [];
    runSignup(nextHost, { onComplete: (payload) => completes.push(payload) });
    await flush();
    runSignup(nextHost, { onComplete: (payload) => completes.push(payload) });
    await flush();
    if (nextHost.listenerCount("message") !== 1) {
      fail(`repeated attempts duplicated listeners: ${nextHost.listenerCount("message")}`);
    }
    nextHost.dispatchMessage("https://www.facebook.com", {
      type: "WA_EMBEDDED_SIGNUP",
      event: "FINISH",
      data: { waba_id: "109876543210", phone_number_id: "200300400500" },
    });
    nextHost._loginCallback?.({ authResponse: { code: "short-lived-auth-code" } });
    if (completes.length !== 1) {
      fail(`repeated attempts should complete once, got ${completes.length}`);
    }
    abortEmbeddedSignup();
    ok("repeated attempts do not duplicate listeners or complete calls");
  }
})();

console.log("\nAll WhatsApp connection UI checks passed.");
