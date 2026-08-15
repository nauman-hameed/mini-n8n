"""Resolve per-business Graph credentials and call WhatsApp Cloud API."""

from __future__ import annotations

from datetime import datetime

import requests
from sqlalchemy.orm import Session

from config import META_ACCESS_TOKEN, META_API_VERSION
from models.business import (
    LEGACY_CONNECTED_BUSINESS_ID,
    LEGACY_CONNECTED_PHONE_NUMBER_ID,
    WHATSAPP_CONNECTION_CONNECTED,
    WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP,
    WHATSAPP_CONNECTION_TYPE_LEGACY,
    Business,
)
from services.whatsapp_credential_service import (
    get_whatsapp_credential,
    load_whatsapp_access_token,
)
from services.whatsapp_service import extract_meta_error, normalize_phone_number


GRAPH_TIMEOUT_SECONDS = 20
MAX_MEDIA_BYTES = 15 * 1024 * 1024
ALLOWED_MESSAGE_KEYS = {
    "type",
    "text",
    "interactive",
    "image",
    "audio",
    "document",
    "video",
    "sticker",
    "template",
    "context",
    "preview_url",
}


class WhatsAppGraphError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "whatsapp_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def get_business_by_id(db: Session, business_id: int) -> Business | None:
    return db.query(Business).filter(Business.id == business_id).first()


def parse_business_id(raw_business_id) -> int:
    if raw_business_id is None:
        raise WhatsAppGraphError("businessId is required.", status_code=400)

    cleaned = str(raw_business_id).strip()
    if not cleaned.isdigit():
        raise WhatsAppGraphError("businessId must be a numeric id.", status_code=400)

    return int(cleaned)


def require_connected_business(business: Business | None) -> Business:
    if not business:
        raise WhatsAppGraphError("Business not found.", status_code=404)

    if business.whatsapp_connection_status != WHATSAPP_CONNECTION_CONNECTED:
        raise WhatsAppGraphError(
            "WhatsApp is not connected for this business.",
            status_code=409,
            code="disconnected",
        )

    if not (business.whatsapp_phone_number_id or "").strip():
        raise WhatsAppGraphError(
            "WhatsApp Phone Number ID is missing for this business.",
            status_code=409,
            code="missing_phone_id",
        )

    return business


def resolve_graph_access_token(db: Session, business: Business) -> str:
    connection_type = (business.whatsapp_connection_type or "").strip()

    if connection_type == WHATSAPP_CONNECTION_TYPE_LEGACY:
        return _legacy_access_token(business)

    if connection_type == WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP:
        return _embedded_access_token(db, business)

    raise WhatsAppGraphError(
        "WhatsApp connection type is not supported.",
        status_code=409,
        code="unsupported_connection",
    )


def send_whatsapp_message(
    db: Session,
    *,
    business_id: int,
    to: str,
    message: dict,
) -> dict:
    business = require_connected_business(get_business_by_id(db, business_id))
    access_token = resolve_graph_access_token(db, business)
    recipient = normalize_phone_number(to)

    if not recipient:
        raise WhatsAppGraphError("Recipient phone number is required.")

    graph_body = _build_graph_message(message, recipient)
    phone_number_id = business.whatsapp_phone_number_id.strip()
    url = _graph_url(phone_number_id, "messages")

    response_data, status_code = _post_graph_json(url, access_token, graph_body)
    _touch_credential_last_used(db, business)

    if status_code >= 400:
        raise WhatsAppGraphError(
            sanitize_meta_error_message(response_data),
            status_code=502,
            code="meta_error",
        )

    message_id = ""
    messages = response_data.get("messages") if isinstance(response_data, dict) else None
    if isinstance(messages, list) and messages:
        message_id = str((messages[0] or {}).get("id") or "")

    return {
        "success": True,
        "messageId": message_id or None,
        "to": recipient,
        "phoneNumberId": phone_number_id,
        "businessId": str(business.id),
    }


def download_whatsapp_media(
    db: Session,
    *,
    business_id: int,
    media_id: str,
) -> tuple[bytes, str]:
    cleaned_media_id = (media_id or "").strip()
    if not cleaned_media_id.isalnum():
        raise WhatsAppGraphError("media_id is invalid.", status_code=400)

    business = require_connected_business(get_business_by_id(db, business_id))
    access_token = resolve_graph_access_token(db, business)
    metadata_url = _graph_url(cleaned_media_id)
    metadata, status_code = _get_graph_json(metadata_url, access_token)

    if status_code >= 400 or not isinstance(metadata, dict):
        raise WhatsAppGraphError(
            sanitize_meta_error_message(metadata if isinstance(metadata, dict) else {}),
            status_code=502,
            code="meta_error",
        )

    media_url = str(metadata.get("url") or "").strip()
    mime_type = str(metadata.get("mime_type") or "application/octet-stream").strip()
    if not media_url:
        raise WhatsAppGraphError("Media download URL was missing.", status_code=502)

    content = _download_media_bytes(media_url, access_token)
    _touch_credential_last_used(db, business)
    return content, mime_type or "application/octet-stream"


def sanitize_meta_error_message(response_data: dict | None) -> str:
    if not isinstance(response_data, dict):
        return "Meta API request failed."

    message = extract_meta_error(response_data)
    cleaned = " ".join(str(message).split())
    return cleaned[:300] or "Meta API request failed."


def _legacy_access_token(business: Business) -> str:
    if (
        business.id != LEGACY_CONNECTED_BUSINESS_ID
        or (business.whatsapp_phone_number_id or "").strip()
        != LEGACY_CONNECTED_PHONE_NUMBER_ID
    ):
        raise WhatsAppGraphError(
            "Legacy WhatsApp credentials are not available for this business.",
            status_code=403,
            code="legacy_forbidden",
        )

    token = str(META_ACCESS_TOKEN or "").strip()
    if not token:
        raise WhatsAppGraphError(
            "Legacy WhatsApp access token is not configured.",
            status_code=503,
            code="missing_legacy_token",
        )

    return token


def _embedded_access_token(db: Session, business: Business) -> str:
    token = load_whatsapp_access_token(db, business.id)
    if not token:
        raise WhatsAppGraphError(
            "WhatsApp credentials are not available for this business.",
            status_code=503,
            code="missing_tenant_token",
        )
    return token


def _build_graph_message(message: dict, recipient: str) -> dict:
    if not isinstance(message, dict) or not message:
        raise WhatsAppGraphError("message payload is required.")

    message_type = str(message.get("type") or "").strip()
    if not message_type:
        raise WhatsAppGraphError("message.type is required.")

    graph_body = {
        key: value
        for key, value in message.items()
        if key in ALLOWED_MESSAGE_KEYS
    }
    graph_body["messaging_product"] = "whatsapp"
    graph_body["recipient_type"] = "individual"
    graph_body["to"] = recipient
    graph_body["type"] = message_type
    return graph_body


def _graph_url(*parts: str) -> str:
    version = (META_API_VERSION or "v23.0").strip()
    joined = "/".join(part.strip("/") for part in parts if part)
    return f"https://graph.facebook.com/{version}/{joined}"


def _post_graph_json(url: str, access_token: str, payload: dict) -> tuple[dict, int]:
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=GRAPH_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise WhatsAppGraphError(
            "Could not reach WhatsApp Cloud API.",
            status_code=502,
        ) from error

    return _safe_json(response), response.status_code


def _get_graph_json(url: str, access_token: str) -> tuple[dict, int]:
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=GRAPH_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise WhatsAppGraphError(
            "Could not reach WhatsApp Cloud API.",
            status_code=502,
        ) from error

    return _safe_json(response), response.status_code


def _download_media_bytes(url: str, access_token: str) -> bytes:
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=GRAPH_TIMEOUT_SECONDS,
            stream=True,
        )
    except requests.RequestException as error:
        raise WhatsAppGraphError(
            "Could not download WhatsApp media.",
            status_code=502,
        ) from error

    if not response.ok:
        raise WhatsAppGraphError(
            "WhatsApp media download failed.",
            status_code=502,
        )

    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_MEDIA_BYTES:
            raise WhatsAppGraphError(
                "WhatsApp media exceeds the allowed size.",
                status_code=413,
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _safe_json(response) -> dict:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _touch_credential_last_used(db: Session, business: Business) -> None:
    if business.whatsapp_connection_type != WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP:
        return

    row = get_whatsapp_credential(db, business.id)
    if not row:
        return

    row.last_used_at = datetime.utcnow()
    db.commit()
