const backendUrl =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export function getBackendUrl(path = "") {
  return `${backendUrl}${path}`;
}

export async function syncWorkflow(nodes, edges) {
  const response = await fetch(getBackendUrl("/workflow"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ nodes, edges }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Could not save workflow.");
  }

  return data;
}

export async function fetchWebhookUrl() {
  const response = await fetch(getBackendUrl("/workflow"));
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Could not load webhook URL.");
  }

  return data.webhook_url || "";
}
