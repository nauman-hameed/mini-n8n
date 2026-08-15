"""Parse Meta Cloud API webhooks into a tenant-safe n8n event."""

from __future__ import annotations


SUPPORTED_MESSAGE_TYPES = {"text", "interactive", "image"}


def normalize_whatsapp_events(
    body: dict,
    *,
    business_id: int,
    phone_number_id: str,
    waba_id: str | None,
) -> list[dict]:
    if not isinstance(body, dict) or body.get("object") != "whatsapp_business_account":
        return []

    events: list[dict] = []

    for entry in body.get("entry") or []:
        if not isinstance(entry, dict):
            continue

        entry_waba_id = str(entry.get("id") or "").strip() or waba_id

        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            if change.get("field") != "messages":
                continue

            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue

            for message in value.get("messages") or []:
                event = normalize_message(
                    message,
                    business_id=business_id,
                    phone_number_id=phone_number_id,
                    waba_id=entry_waba_id,
                )
                if event:
                    events.append(event)

    return events


def extract_phone_number_id(body: dict) -> str:
    if not isinstance(body, dict):
        return ""

    for entry in body.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue
            metadata = value.get("metadata") or {}
            if not isinstance(metadata, dict):
                continue
            phone_number_id = str(metadata.get("phone_number_id") or "").strip()
            if phone_number_id:
                return phone_number_id

    return ""


def extract_waba_id(body: dict) -> str:
    if not isinstance(body, dict):
        return ""

    for entry in body.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        waba_id = str(entry.get("id") or "").strip()
        if waba_id:
            return waba_id

    return ""


def normalize_message(
    message: dict,
    *,
    business_id: int,
    phone_number_id: str,
    waba_id: str | None,
) -> dict | None:
    if not isinstance(message, dict):
        return None

    message_type = str(message.get("type") or "").strip().lower()
    if message_type not in SUPPORTED_MESSAGE_TYPES:
        return None

    customer_phone = str(message.get("from") or "").strip()
    wa_message_id = str(message.get("id") or "").strip()
    if not customer_phone or not wa_message_id:
        return None

    event = {
        "businessId": str(business_id),
        "phoneNumberId": phone_number_id,
        "wabaId": waba_id or None,
        "messageType": message_type,
        "customerPhone": customer_phone,
        "waMessageId": wa_message_id,
        "timestamp": str(message.get("timestamp") or "").strip() or None,
        "text": None,
        "interactive": None,
        "media": None,
        "rawEventSubset": {
            "id": wa_message_id,
            "type": message_type,
            "from": customer_phone,
        },
    }

    if message_type == "text":
        text_body = str((message.get("text") or {}).get("body") or "").strip()
        if not text_body:
            return None
        event["text"] = text_body
        return event

    if message_type == "interactive":
        interactive = message.get("interactive") or {}
        if not isinstance(interactive, dict):
            return None

        button = interactive.get("button_reply") or {}
        list_reply = interactive.get("list_reply") or {}
        source = button if isinstance(button, dict) and button.get("id") else list_reply
        if not isinstance(source, dict):
            return None

        button_id = str(source.get("id") or "").strip()
        title = str(source.get("title") or "").strip()
        if not button_id:
            return None

        event["interactive"] = {
            "buttonId": button_id,
            "title": title or None,
            "type": str(interactive.get("type") or "").strip() or None,
        }
        return event

    image = message.get("image") or {}
    if not isinstance(image, dict):
        return None

    media_id = str(image.get("id") or "").strip()
    if not media_id:
        return None

    caption = str(image.get("caption") or "").strip() or None
    event["media"] = {
        "id": media_id,
        "mimeType": str(image.get("mime_type") or "").strip() or None,
        "kind": "image",
    }
    event["text"] = caption
    return event
