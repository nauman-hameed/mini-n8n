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

export function loadFacebookSdk(appId, graphVersion) {
  const version = graphVersion || "v23.0";

  if (window.FB) {
    window.FB.init({
      appId,
      autoLogAppEvents: true,
      xfbml: true,
      version,
    });
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    window.fbAsyncInit = function fbAsyncInit() {
      window.FB.init({
        appId,
        autoLogAppEvents: true,
        xfbml: true,
        version,
      });
      resolve();
    };

    const existing = document.getElementById("facebook-jssdk");
    if (existing) {
      return;
    }

    const script = document.createElement("script");
    script.id = "facebook-jssdk";
    script.async = true;
    script.defer = true;
    script.crossOrigin = "anonymous";
    script.src = "https://connect.facebook.net/en_US/sdk.js";
    script.onerror = () => reject(new Error("Could not load WhatsApp connection."));
    document.head.appendChild(script);
  });
}

export function launchEmbeddedSignup({ appId, configId, graphVersion, onComplete, onCancel, onError }) {
  let session = null;
  let authorizationCode = null;
  let finished = false;

  const cleanup = () => {
    window.removeEventListener("message", handleMessage);
  };

  const settle = (callback) => {
    if (finished) {
      return;
    }
    finished = true;
    cleanup();
    callback();
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
      settle(() => onCancel());
    }
  };

  window.addEventListener("message", handleMessage);

  return loadFacebookSdk(appId, graphVersion)
    .then(() => {
      window.FB.login(
        (response) => {
          const nextCode = response?.authResponse?.code;
          if (!nextCode) {
            settle(() => onCancel());
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
}

export { originIsFacebook, parseSignupEvent };
