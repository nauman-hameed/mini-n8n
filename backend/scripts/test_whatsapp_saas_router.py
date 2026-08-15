#!/usr/bin/env python3
"""P2 WhatsApp SaaS router, signature, send/media proxy tests."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

APP_SECRET = "test-meta-app-secret"
VERIFY_TOKEN = "test-meta-verify-token"
INTERNAL_TOKEN = "test-n8n-internal-token"
CALLBACK_SECRET = "test-n8n-callback-secret"
FORWARD_URL = "https://n8n.example.invalid/webhook/whatsapp-saas"
LEGACY_TOKEN = "legacy-meta-access-token"
TENANT_TOKEN = "embedded-tenant-access-token"
LEGACY_PHONE_ID = "1160990267106849"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def sign_body(raw: bytes) -> str:
    digest = hmac.new(APP_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def meta_payload(*, phone_id: str, messages: list[dict], waba_id: str = "waba-1") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": waba_id,
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "923071055454",
                                "phone_number_id": phone_id,
                            },
                            "messages": messages,
                        },
                    }
                ],
            }
        ],
    }


def post_webhook(client, payload: dict, signature: str | None):
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Hub-Signature-256"] = signature
    return client.post("/webhook/whatsapp", content=raw, headers=headers), raw


def bootstrap():
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    os.environ["JWT_SECRET_KEY"] = "local-test-secret"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["CREDENTIAL_ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
    os.environ["N8N_CALLBACK_SECRET"] = CALLBACK_SECRET
    os.environ["N8N_INTERNAL_TOKEN"] = INTERNAL_TOKEN
    os.environ["N8N_WHATSAPP_WEBHOOK_URL"] = FORWARD_URL
    os.environ["N8N_WHATSAPP_WEBHOOK_SECRET"] = CALLBACK_SECRET
    os.environ["META_APP_SECRET"] = APP_SECRET
    os.environ["META_VERIFY_TOKEN"] = VERIFY_TOKEN
    os.environ["META_ACCESS_TOKEN"] = LEGACY_TOKEN
    os.environ["META_API_VERSION"] = "v23.0"

    for module_name in list(sys.modules):
        if (
            module_name in {"config", "database", "main"}
            or module_name.startswith("models")
            or module_name.startswith("routes.")
            or module_name.startswith("services.")
            or module_name.startswith("dependencies.")
            or module_name.startswith("schemas.")
        ):
            del sys.modules[module_name]

    from fastapi.testclient import TestClient

    from database import SessionLocal, init_db
    from main import app
    from models.business import (
        WHATSAPP_CONNECTION_CONNECTED,
        WHATSAPP_CONNECTION_DISCONNECTED,
        WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP,
        WHATSAPP_CONNECTION_TYPE_LEGACY,
        Business,
    )
    from models.user import User
    from services.auth_service import hash_password
    from services.whatsapp_credential_service import store_whatsapp_secrets

    init_db()
    db = SessionLocal()

    legacy_user = User(
        id=5,
        full_name="Khizar",
        email="legacy-owner@example.com",
        password_hash=hash_password("password12345"),
    )
    disconnected_user = User(
        full_name="Other",
        email="disconnected@example.com",
        password_hash=hash_password("password12345"),
    )
    embedded_user = User(
        full_name="Embedded",
        email="embedded@example.com",
        password_hash=hash_password("password12345"),
    )
    db.add_all([legacy_user, disconnected_user, embedded_user])
    db.flush()

    legacy = Business(
        id=2,
        user_id=5,
        business_name="NH",
        whatsapp_number="+923071055454",
        whatsapp_phone_number_id=LEGACY_PHONE_ID,
        whatsapp_display_phone_number="+923071055454",
        whatsapp_connection_status=WHATSAPP_CONNECTION_CONNECTED,
        whatsapp_connection_type=WHATSAPP_CONNECTION_TYPE_LEGACY,
        whatsapp_connected_at=datetime.utcnow(),
        onboarding_completed=True,
    )
    disconnected = Business(
        user_id=disconnected_user.id,
        business_name="Idle Shop",
        whatsapp_number="+923001111111",
        whatsapp_phone_number_id="555000111",
        whatsapp_connection_status=WHATSAPP_CONNECTION_DISCONNECTED,
        onboarding_completed=True,
    )
    embedded = Business(
        user_id=embedded_user.id,
        business_name="ES Shop",
        whatsapp_number="+923002222222",
        whatsapp_phone_number_id="777888999",
        whatsapp_connection_status=WHATSAPP_CONNECTION_CONNECTED,
        whatsapp_connection_type=WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP,
        onboarding_completed=True,
    )
    db.add_all([legacy, disconnected, embedded])
    db.commit()
    embedded_id = embedded.id
    disconnected_id = disconnected.id
    store_whatsapp_secrets(
        db,
        business_id=embedded_id,
        access_token=TENANT_TOKEN,
        two_step_pin="123456",
    )
    db.close()

    return TestClient(app), embedded_id, disconnected_id


def main() -> None:
    client, embedded_id, disconnected_id = bootstrap()
    auth = {"Authorization": f"Bearer {INTERNAL_TOKEN}"}

    from services.whatsapp_events import normalize_whatsapp_events
    from services.whatsapp_forwarder import forward_whatsapp_event
    from services.whatsapp_graph import _build_graph_message

    verify = client.get(
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "challenge-token",
        },
    )
    if verify.status_code != 200 or verify.text != "challenge-token":
        fail(f"GET verify failed: {verify.status_code} {verify.text}")
    ok("GET /webhook/whatsapp verification preserved")

    text_payload = meta_payload(
        phone_id=LEGACY_PHONE_ID,
        messages=[
            {
                "from": "923001112233",
                "id": "wamid.text1",
                "timestamp": "1710000000",
                "type": "text",
                "text": {"body": "I want 2 kurtas"},
            }
        ],
    )

    missing, _ = post_webhook(client, text_payload, None)
    if missing.status_code != 403:
        fail(f"missing signature expected 403, got {missing.status_code}")
    ok("missing X-Hub-Signature-256 → 403")

    invalid, raw = post_webhook(client, text_payload, "sha256=deadbeef")
    if invalid.status_code != 403:
        fail(f"invalid signature expected 403, got {invalid.status_code}")
    ok("invalid signature → 403")

    forwarded = []

    def capture_forward(event):
        forwarded.append(event)
        return {"ok": True}

    with patch("routes.whatsapp_webhook.forward_whatsapp_event", side_effect=capture_forward):
        with patch("services.workflow_runner.run_workflow") as editor_runner:
            valid, raw_valid = post_webhook(
                client,
                text_payload,
                sign_body(json.dumps(text_payload, separators=(",", ":")).encode()),
            )
            if valid.status_code != 200:
                fail(f"valid signature expected 200, got {valid.status_code} {valid.text}")
            if valid.json().get("forwarded") != 1:
                fail(f"expected forwarded 1, got {valid.json()}")
            if editor_runner.called:
                fail("SaaS webhook must not run the editor workflow")
    if len(forwarded) != 1 or forwarded[0]["businessId"] != "2":
        fail(f"text event routed incorrectly: {forwarded}")
    if forwarded[0]["text"] != "I want 2 kurtas":
        fail("text body was not normalized")
    ok("valid signature accepted and connected phone routes to business 2")

    forwarded.clear()
    unknown = meta_payload(
        phone_id="0000000000",
        messages=[{"from": "92300", "id": "wamid.x", "type": "text", "text": {"body": "hi"}}],
    )
    with patch("routes.whatsapp_webhook.forward_whatsapp_event", side_effect=capture_forward):
        unknown_raw = json.dumps(unknown, separators=(",", ":")).encode()
        response, _ = post_webhook(client, unknown, sign_body(unknown_raw))
    if response.status_code != 200 or response.json().get("forwarded") != 0:
        fail(f"unknown phone should skip forward: {response.status_code} {response.text}")
    if forwarded:
        fail("unknown phone_id must not forward")
    ok("unknown phone_number_id → 200, no forward")

    disconnected_payload = meta_payload(
        phone_id="555000111",
        messages=[{"from": "92300", "id": "wamid.d", "type": "text", "text": {"body": "hi"}}],
    )
    with patch("routes.whatsapp_webhook.forward_whatsapp_event", side_effect=capture_forward):
        disconnected_raw = json.dumps(disconnected_payload, separators=(",", ":")).encode()
        response, _ = post_webhook(
            client,
            disconnected_payload,
            sign_body(disconnected_raw),
        )
    if response.status_code != 200 or forwarded:
        fail("disconnected tenant must not forward")
    ok("disconnected phone_id → 200, no forward")

    interactive = {
        "from": "923001112233",
        "id": "wamid.btn",
        "timestamp": "1710000001",
        "type": "interactive",
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": "confirm_42", "title": "Confirm Order"},
        },
    }
    image = {
        "from": "923001112233",
        "id": "wamid.img",
        "timestamp": "1710000002",
        "type": "image",
        "image": {"id": "MEDIA99", "mime_type": "image/jpeg", "caption": "label"},
    }
    events = normalize_whatsapp_events(
        meta_payload(phone_id=LEGACY_PHONE_ID, messages=[interactive, image], waba_id="waba-9"),
        business_id=2,
        phone_number_id=LEGACY_PHONE_ID,
        waba_id="waba-9",
    )
    if events[0]["interactive"]["buttonId"] != "confirm_42":
        fail(f"interactive normalize failed: {events[0]}")
    if events[1]["media"]["id"] != "MEDIA99" or events[1]["text"] != "label":
        fail(f"image normalize failed: {events[1]}")
    ok("normalization covers text, interactive confirm/cancel, and image media")

    mixed = meta_payload(phone_id=LEGACY_PHONE_ID, messages=[interactive, image])
    forwarded.clear()
    with patch("routes.whatsapp_webhook.forward_whatsapp_event", side_effect=capture_forward):
        mixed_raw = json.dumps(mixed, separators=(",", ":")).encode()
        response, _ = post_webhook(client, mixed, sign_body(mixed_raw))
    if response.json().get("forwarded") != 2:
        fail(f"expected 2 forwarded events, got {response.json()}")
    ok("interactive and image events queued for the mapped business")

    with patch("services.whatsapp_forwarder.requests.post") as mocked_post:
        mocked_post.return_value.ok = True
        mocked_post.return_value.status_code = 200
        result = forward_whatsapp_event(
            {"businessId": "2", "messageType": "text", "text": "hi"}
        )
        if not result.get("ok"):
            fail(f"forward should succeed: {result}")
        args, kwargs = mocked_post.call_args
        if args[0] != FORWARD_URL:
            fail("forward URL mismatch")
        headers = kwargs["headers"]
        if headers.get("x-n8n-secret") != CALLBACK_SECRET:
            fail("forward missing x-n8n-secret")
        if kwargs["json"]["businessId"] != "2":
            fail("forward payload missing businessId")
    ok("n8n forward sends businessId and internal secret header")

    with patch("services.whatsapp_forwarder.requests.post", side_effect=requests.Timeout):
        result = forward_whatsapp_event(
            {"businessId": "2", "messageType": "text", "text": TENANT_TOKEN}
        )
        dumped = json.dumps(result)
        if TENANT_TOKEN in dumped or CALLBACK_SECRET in dumped or FORWARD_URL in dumped:
            fail("timeout result leaked a secret")
        if result.get("reason") != "timeout":
            fail(f"expected timeout reason, got {result}")
    ok("forward timeout does not leak secrets")

    unauth = client.post(
        "/api/internal/whatsapp/send",
        json={"businessId": 2, "to": "923001234567", "message": {"type": "text", "text": {"body": "x"}}},
    )
    if unauth.status_code != 401:
        fail(f"send unauthenticated expected 401, got {unauth.status_code}")
    ok("send proxy unauthenticated → 401")

    wrong = client.post(
        "/api/internal/whatsapp/send",
        headers={"Authorization": "Bearer wrong-token"},
        json={"businessId": 2, "to": "923001234567", "message": {"type": "text", "text": {"body": "x"}}},
    )
    if wrong.status_code != 401:
        fail(f"send wrong bearer expected 401, got {wrong.status_code}")
    ok("send proxy wrong bearer → 401")

    captured = {}

    def fake_post(url, access_token, payload):
        captured["url"] = url
        captured["token"] = access_token
        captured["payload"] = payload
        return {"messages": [{"id": "wamid.out"}]}, 200

    with patch("services.whatsapp_graph._post_graph_json", side_effect=fake_post):
        sent = client.post(
            "/api/internal/whatsapp/send",
            headers=auth,
            json={
                "businessId": 2,
                "to": "+923001234567",
                "message": {
                    "type": "text",
                    "phone_number_id": "spoofed-sender",
                    "to": "999",
                    "text": {"body": "hello"},
                },
            },
        )
    if sent.status_code != 200:
        fail(f"legacy send failed: {sent.status_code} {sent.text}")
    if captured["token"] != LEGACY_TOKEN:
        fail("legacy send did not use env META_ACCESS_TOKEN")
    if LEGACY_PHONE_ID not in captured["url"]:
        fail("legacy send URL must use database Phone Number ID")
    if "spoofed-sender" in captured["url"] or captured["payload"].get("phone_number_id"):
        fail("n8n was able to spoof sender Phone Number ID")
    if captured["payload"]["to"] != "923001234567":
        fail(f"recipient not forced: {captured['payload']}")
    if captured["payload"]["messaging_product"] != "whatsapp":
        fail("messaging_product was not forced")
    ok("legacy send uses env token and database sender id; spoofed sender rejected")

    captured.clear()
    with patch("services.whatsapp_graph._post_graph_json", side_effect=fake_post):
        sent = client.post(
            "/api/internal/whatsapp/send",
            headers=auth,
            json={
                "businessId": embedded_id,
                "to": "923009998887",
                "message": {"type": "text", "text": {"body": "tenant"}},
            },
        )
    if sent.status_code != 200:
        fail(f"embedded send failed: {sent.status_code} {sent.text}")
    if captured["token"] != TENANT_TOKEN:
        fail("embedded send did not use decrypted tenant token")
    if captured["token"] == LEGACY_TOKEN:
        fail("embedded send leaked onto the legacy token")
    if "777888999" not in captured["url"]:
        fail("embedded send used the wrong Phone Number ID")
    ok("embedded tenant send uses decrypted business token")

    disconnected_send = client.post(
        "/api/internal/whatsapp/send",
        headers=auth,
        json={
            "businessId": disconnected_id,
            "to": "923001234567",
            "message": {"type": "text", "text": {"body": "nope"}},
        },
    )
    if disconnected_send.status_code != 409:
        fail(f"disconnected send expected 409, got {disconnected_send.status_code}")
    ok("disconnected tenant send rejected")

    graph_body = _build_graph_message(
        {"type": "interactive", "phone_number_id": "nope", "interactive": {"type": "button"}},
        "92300",
    )
    if "phone_number_id" in graph_body:
        fail("graph builder kept spoofed phone_number_id")
    ok("send payload cannot set sender Phone Number ID")

    media_unauth = client.get("/api/internal/whatsapp/media/MEDIA99", params={"businessId": 2})
    if media_unauth.status_code != 401:
        fail(f"media unauthenticated expected 401, got {media_unauth.status_code}")
    ok("media proxy unauthenticated → 401")

    def fake_meta(url, access_token):
        if "MEDIA99" in url and "messages" not in url:
            return {"url": "https://lookaside.fbsbx.com/media/MEDIA99", "mime_type": "image/jpeg"}, 200
        fail(f"unexpected metadata url {url}")
        return {}, 500

    with patch("services.whatsapp_graph._get_graph_json", side_effect=fake_meta):
        with patch(
            "services.whatsapp_graph._download_media_bytes",
            return_value=b"jpeg-bytes",
        ) as download:
            media = client.get(
                "/api/internal/whatsapp/media/MEDIA99",
                params={"businessId": 2},
                headers=auth,
            )
            if download.call_args[0][1] != LEGACY_TOKEN:
                fail("legacy media download used the wrong token")
    if media.status_code != 200 or media.content != b"jpeg-bytes":
        fail(f"legacy media download failed: {media.status_code}")
    if media.headers.get("content-type") != "image/jpeg":
        fail("media content-type mismatch")
    ok("legacy media proxy uses env token and returns binary")

    with patch("services.whatsapp_graph._get_graph_json", side_effect=fake_meta):
        with patch(
            "services.whatsapp_graph._download_media_bytes",
            return_value=b"tenant-bytes",
        ) as download:
            media = client.get(
                f"/api/internal/whatsapp/media/MEDIA99",
                params={"businessId": embedded_id},
                headers=auth,
            )
            if download.call_args[0][1] != TENANT_TOKEN:
                fail("embedded media download used the wrong token")
    if media.content != b"tenant-bytes":
        fail("embedded media proxy isolation failed")
    ok("embedded media proxy uses decrypted tenant token")

    disconnected_media = client.get(
        "/api/internal/whatsapp/media/MEDIA99",
        params={"businessId": disconnected_id},
        headers=auth,
    )
    if disconnected_media.status_code != 409:
        fail(f"disconnected media expected 409, got {disconnected_media.status_code}")
    ok("disconnected tenant media rejected")

    # Cross-tenant: embedded businessId must not be able to send as legacy phone id
    captured.clear()
    with patch("services.whatsapp_graph._post_graph_json", side_effect=fake_post):
        client.post(
            "/api/internal/whatsapp/send",
            headers=auth,
            json={
                "businessId": embedded_id,
                "to": "92300",
                "message": {"type": "text", "text": {"body": "x"}},
            },
        )
    if LEGACY_PHONE_ID in captured.get("url", ""):
        fail("embedded business sent using legacy Phone Number ID")
    ok("businessId cannot cause cross-tenant sender leakage")

    print("\nAll WhatsApp SaaS router and proxy checks passed.")


if __name__ == "__main__":
    main()
