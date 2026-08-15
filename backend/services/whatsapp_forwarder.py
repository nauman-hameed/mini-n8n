"""Forward normalized WhatsApp events to the shared n8n HTTP webhook.

In-process BackgroundTasks mean a process crash after Meta's 200 can drop
a delivery, and there is no durable retry queue. That is acceptable until
a later worker/queue cutover; Meta already received a fast ack.
"""

from __future__ import annotations

import requests

from config import (
    N8N_WHATSAPP_FORWARD_TIMEOUT_SECONDS,
    N8N_WHATSAPP_WEBHOOK_SECRET,
    N8N_WHATSAPP_WEBHOOK_URL,
)


def forwarding_enabled() -> bool:
    return bool(N8N_WHATSAPP_WEBHOOK_URL and N8N_WHATSAPP_WEBHOOK_SECRET)


def forward_whatsapp_event(event: dict) -> dict:
    if not N8N_WHATSAPP_WEBHOOK_URL:
        print(
            "WhatsApp n8n forward skipped: N8N_WHATSAPP_WEBHOOK_URL is unset."
        )
        return {"ok": False, "reason": "disabled"}

    if not N8N_WHATSAPP_WEBHOOK_SECRET:
        print(
            "WhatsApp n8n forward skipped: forward secret is unset."
        )
        return {"ok": False, "reason": "missing_secret"}

    timeout = max(1, N8N_WHATSAPP_FORWARD_TIMEOUT_SECONDS)
    business_id = event.get("businessId")
    message_type = event.get("messageType")

    try:
        response = requests.post(
            N8N_WHATSAPP_WEBHOOK_URL,
            json=event,
            headers={
                "Content-Type": "application/json",
                "x-n8n-secret": N8N_WHATSAPP_WEBHOOK_SECRET,
            },
            timeout=timeout,
        )
    except requests.Timeout:
        print(
            f"WhatsApp n8n forward timeout business_id={business_id} "
            f"type={message_type}"
        )
        return {"ok": False, "reason": "timeout"}
    except requests.RequestException:
        print(
            f"WhatsApp n8n forward error business_id={business_id} "
            f"type={message_type}"
        )
        return {"ok": False, "reason": "request_error"}

    if response.ok:
        print(
            f"WhatsApp n8n forward ok business_id={business_id} "
            f"type={message_type} status={response.status_code}"
        )
        return {"ok": True, "status": response.status_code}

    print(
        f"WhatsApp n8n forward rejected business_id={business_id} "
        f"type={message_type} status={response.status_code}"
    )
    return {"ok": False, "reason": "http_error", "status": response.status_code}
