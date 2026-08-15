function originIsFacebook(origin) {
  return typeof origin === "string" && origin.endsWith("facebook.com");
}

function parseSignupEvent(data) {
  if (!data) {
    return null;
  }

  let parsed = data;

  if (typeof data === "string") {
    try {
      parsed = JSON.parse(data);
    } catch {
      return null;
    }
  }

  if (parsed?.type !== "WA_EMBEDDED_SIGNUP") {
    return null;
  }

  return parsed;
}

export const EMBEDDED_SIGNUP_TIMEOUT_MS = 120000;
export const INCOMPLETE_CONNECTION_MESSAGE =
  "WhatsApp connection was not completed.";

const POPUP_POLL_MS = 700;

let activeSignup = null;

function resolveWindow(hostWindow) {
  if (hostWindow) {
    return hostWindow;
  }

  if (typeof window !== "undefined") {
    return window;
  }

  throw new Error("WhatsApp connection requires a browser window.");
}

export function loadFacebookSdk(appId, graphVersion, hostWindow) {
  const win = resolveWindow(hostWindow);
  const version = graphVersion || "v23.0";
  const doc = win.document;

  if (win.FB) {
    win.FB.init({
      appId,
      autoLogAppEvents: true,
      xfbml: true,
      version,
    });
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const previousInit = win.fbAsyncInit;
    win.fbAsyncInit = function fbAsyncInit() {
      if (typeof previousInit === "function") {
        previousInit();
      }
      win.FB.init({
        appId,
        autoLogAppEvents: true,
        xfbml: true,
        version,
      });
      resolve();
    };

    const existing = doc.getElementById("facebook-jssdk");
    if (existing) {
      return;
    }

    const script = doc.createElement("script");
    script.id = "facebook-jssdk";
    script.async = true;
    script.defer = true;
    script.crossOrigin = "anonymous";
    script.src = "https://connect.facebook.net/en_US/sdk.js";
    script.onerror = () => reject(new Error("Could not load WhatsApp connection."));
    doc.head.appendChild(script);
  });
}

function capturePopup(win) {
  const originalOpen = win.open;
  let popup = null;

  if (typeof originalOpen !== "function") {
    return {
      getPopup: () => popup,
      restore: () => {},
    };
  }

  win.open = function openProxy(...args) {
    popup = originalOpen.apply(win, args);
    win.open = originalOpen;
    return popup;
  };

  return {
    getPopup: () => popup,
    restore: () => {
      win.open = originalOpen;
    },
  };
}

export function abortEmbeddedSignup() {
  if (activeSignup) {
    activeSignup.abort();
  }
}

export function launchEmbeddedSignup({
  appId,
  configId,
  graphVersion,
  onComplete,
  onCancel,
  onError,
  timeoutMs = EMBEDDED_SIGNUP_TIMEOUT_MS,
  hostWindow,
} = {}) {
  abortEmbeddedSignup();

  const win = resolveWindow(hostWindow);
  let session = null;
  let authorizationCode = null;
  let finished = false;
  let timeoutId = null;
  let pollId = null;
  const popupCapture = capturePopup(win);

  const cleanup = () => {
    win.removeEventListener("message", handleMessage);
    if (timeoutId) {
      win.clearTimeout(timeoutId);
      timeoutId = null;
    }
    if (pollId) {
      win.clearInterval(pollId);
      pollId = null;
    }
    popupCapture.restore();
    if (activeSignup && activeSignup.abort === abort) {
      activeSignup = null;
    }
  };

  const settle = (callback) => {
    if (finished) {
      return;
    }
    finished = true;
    cleanup();
    callback();
  };

  const abort = () => {
    settle(() => onCancel?.({ reason: "aborted" }));
  };

  const tryComplete = () => {
    if (!session || !authorizationCode) {
      return;
    }

    const payload = {
      code: authorizationCode,
      wabaId: session.waba_id,
      phoneNumberId: session.phone_number_id,
    };
    authorizationCode = null;
    settle(() => onComplete(payload));
  };

  const handleMessage = (event) => {
    if (!originIsFacebook(event.origin)) {
      return;
    }

    const parsed = parseSignupEvent(event.data);
    if (!parsed) {
      return;
    }

    if (parsed.event === "FINISH" || parsed.event === "FINISH_ONLY_WABA") {
      const wabaId = String(parsed.data?.waba_id || "").trim();
      const phoneNumberId = String(parsed.data?.phone_number_id || "").trim();
      if (!wabaId || !phoneNumberId) {
        settle(() => onError(new Error("WhatsApp did not return connection details.")));
        return;
      }
      session = { waba_id: wabaId, phone_number_id: phoneNumberId };
      tryComplete();
      return;
    }

    if (parsed.event === "CANCEL") {
      settle(() => onCancel?.({ reason: "cancel" }));
      return;
    }

    if (parsed.event === "ERROR") {
      settle(() =>
        onError(new Error("WhatsApp could not complete Embedded Signup. Please try again."))
      );
    }
  };

  activeSignup = { abort };
  win.addEventListener("message", handleMessage);

  timeoutId = win.setTimeout(() => {
    settle(() => onCancel?.({ reason: "timeout" }));
  }, timeoutMs);

  pollId = win.setInterval(() => {
    const popup = popupCapture.getPopup();
    if (popup && popup.closed) {
      settle(() => onCancel?.({ reason: "popup_closed" }));
    }
  }, POPUP_POLL_MS);

  loadFacebookSdk(appId, graphVersion, win)
    .then(() => {
      if (finished) {
        return;
      }

      if (!win.FB || typeof win.FB.login !== "function") {
        settle(() => onError(new Error("Could not start WhatsApp connection.")));
        return;
      }

      win.FB.login(
        (response) => {
          const nextCode = response?.authResponse?.code;
          if (!nextCode) {
            settle(() => onCancel?.({ reason: "no_code" }));
            return;
          }
          authorizationCode = nextCode;
          tryComplete();
        },
        {
          config_id: configId,
          response_type: "code",
          override_default_response_type: true,
          extras: {
            setup: {},
            sessionInfoVersion: "3",
          },
        }
      );
    })
    .catch((error) => {
      settle(() => onError(error));
    });

  return { abort };
}

export { originIsFacebook, parseSignupEvent };
