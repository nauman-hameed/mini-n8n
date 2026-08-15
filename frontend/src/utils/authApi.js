import { getBackendUrl } from "./api";

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let message = data.detail || data.message || "Request failed.";

    if (Array.isArray(message)) {
      message = message[0]?.msg || message[0]?.message || "Request failed.";
    }

    throw new Error(typeof message === "string" ? message : "Request failed.");
  }

  return data;
}

async function authRequest(path, options = {}) {
  const response = await fetch(getBackendUrl(path), {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  return parseJsonResponse(response);
}

export async function signupUser(payload) {
  const data = await authRequest("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return data.user;
}

export async function loginUser(payload) {
  const data = await authRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return data.user;
}

export async function logoutUser() {
  await authRequest("/auth/logout", {
    method: "POST",
  });
}

export async function fetchCurrentUser() {
  const data = await authRequest("/auth/me");
  return data.user;
}

export async function saveBusinessOnboarding(payload) {
  const data = await authRequest("/business/onboarding", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return data.business;
}

export async function fetchBusiness() {
  const data = await authRequest("/business");
  return data.business;
}

export async function updateBusiness(payload) {
  const data = await authRequest("/business", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  return data.business;
}

export async function fetchBusinessOrders() {
  const data = await authRequest("/business/orders");
  return data.orders || [];
}

export async function fetchBusinessOrder(orderId) {
  const data = await authRequest(`/business/orders/${orderId}`);
  return data.order;
}

export async function fetchWhatsAppConnectConfig() {
  const data = await authRequest("/business/whatsapp/connect-config");
  return {
    enabled: Boolean(data.enabled),
    appId: data.appId || "",
    configId: data.configId || "",
    graphVersion: data.graphVersion || "",
  };
}

export async function completeWhatsAppConnection(payload) {
  const data = await authRequest("/business/whatsapp/connect/complete", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return data.business;
}

export async function disconnectWhatsAppConnection() {
  const data = await authRequest("/business/whatsapp/disconnect", {
    method: "POST",
  });

  return data.business;
}

export function validateMetaPhoneNumberId(value) {
  const cleaned = value.trim();

  if (!cleaned) {
    return "";
  }

  if (!/^\d{5,64}$/.test(cleaned)) {
    return "Meta Phone Number ID must be digits only.";
  }

  return "";
}

export function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function validatePassword(value) {
  if (value.length < 8) {
    return "Password must be at least 8 characters.";
  }

  return "";
}

export function validateWhatsAppNumber(value) {
  const cleaned = value.trim().replace(/\s+/g, "").replace(/-/g, "");

  if (!/^\+[1-9]\d{7,14}$/.test(cleaned)) {
    return "Use international format, e.g. +923001234567.";
  }

  return "";
}
