#!/usr/bin/env python3
"""P3 Embedded Signup connect-config, complete, disconnect, and legacy lock."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

APP_ID = "1234567890"
CONFIG_ID = "es-config-1"
APP_SECRET = "test-meta-app-secret"
INTERNAL = "test-n8n-internal-token"
LEGACY_PHONE = "1160990267106849"
NEW_PHONE = "200300400500"
NEW_WABA = "109876543210"
CODE = "short-lived-auth-code-value"
TENANT_TOKEN = "EAA_TEST_EMBEDDED_TOKEN"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def reload_modules() -> None:
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


def bootstrap(*, embed_enabled: bool):
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    os.environ["JWT_SECRET_KEY"] = "local-test-secret"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["CREDENTIAL_ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
    os.environ["N8N_CALLBACK_SECRET"] = "test-n8n-callback-secret"
    os.environ["N8N_INTERNAL_TOKEN"] = INTERNAL
    os.environ["META_APP_SECRET"] = APP_SECRET
    os.environ["META_APP_ID"] = APP_ID if embed_enabled else ""
    os.environ["META_EMBEDDED_SIGNUP_CONFIG_ID"] = CONFIG_ID if embed_enabled else ""
    os.environ["META_API_VERSION"] = "v23.0"

    reload_modules()

    from fastapi.testclient import TestClient

    from database import SessionLocal, init_db
    from main import app
    from models.business import (
        WHATSAPP_CONNECTION_CONNECTED,
        WHATSAPP_CONNECTION_TYPE_LEGACY,
        Business,
    )
    from models.order import ORDER_STATUS_PENDING, Order, OrderItem
    from models.user import User
    from services.auth_service import hash_password

    init_db()
    db = SessionLocal()

    legacy_user = User(
        id=5,
        full_name="Khizar",
        email="legacy@example.com",
        password_hash=hash_password("password12345"),
    )
    new_user = User(
        full_name="New Customer",
        email="new@example.com",
        password_hash=hash_password("password12345"),
    )
    other_user = User(
        full_name="Other",
        email="other@example.com",
        password_hash=hash_password("password12345"),
    )
    db.add_all([legacy_user, new_user, other_user])
    db.flush()

    db.add(
        Business(
            id=2,
            user_id=5,
            business_name="NH",
            whatsapp_number="+923071055454",
            whatsapp_phone_number_id=LEGACY_PHONE,
            whatsapp_display_phone_number="+923071055454",
            whatsapp_connection_status=WHATSAPP_CONNECTION_CONNECTED,
            whatsapp_connection_type=WHATSAPP_CONNECTION_TYPE_LEGACY,
            whatsapp_connected_at=datetime.utcnow(),
            onboarding_completed=True,
        )
    )
    db.add(
        Business(
            user_id=new_user.id,
            business_name="Fresh Shop",
            whatsapp_number="+923009991111",
            onboarding_completed=True,
        )
    )
    other_biz = Business(
        user_id=other_user.id,
        business_name="Occupied",
        whatsapp_number="+923008881111",
        whatsapp_phone_number_id="999111222",
        onboarding_completed=True,
    )
    db.add(other_biz)
    db.flush()

    for index in range(12):
        order = Order(
            order_number=f"ORD-L{index + 1}",
            business_id=2,
            customer_phone="923001000001",
            customer_name="Ali",
            notes="addr",
            status=ORDER_STATUS_PENDING,
        )
        db.add(order)
        db.flush()
        db.add(OrderItem(order_id=order.id, name="Item", quantity=1, unit_price=0))

    db.commit()
    db.close()
    return TestClient(app)


def login(client, email):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "password12345"},
    )
    if response.status_code != 200:
        fail(f"login failed for {email}: {response.status_code} {response.text}")
    return response


def assert_no_secrets(payload: dict, label: str) -> None:
    blob = str(payload)
    lowered_keys = " ".join(str(key).lower() for key in payload)
    if "token" in lowered_keys or "pin" in lowered_keys or "secret" in lowered_keys:
        fail(f"{label} leaked secret-looking key: {list(payload)}")
    if TENANT_TOKEN in blob or APP_SECRET in blob or CODE in blob or "gAAAA" in blob:
        fail(f"{label} leaked credential material")


def main() -> None:
    client = bootstrap(embed_enabled=False)

    unauth = client.get("/business/whatsapp/connect-config")
    if unauth.status_code != 401:
        fail(f"connect-config unauthenticated expected 401, got {unauth.status_code}")
    ok("connect-config requires auth")

    login(client, "new@example.com")
    disabled = client.get("/business/whatsapp/connect-config")
    if disabled.status_code != 200 or disabled.json().get("enabled") is not False:
        fail(f"missing env should disable connect: {disabled.text}")
    assert_no_secrets(disabled.json(), "disabled connect-config")
    if disabled.json().get("appId") or disabled.json().get("configId"):
        fail("disabled config should omit public ids")
    ok("connect-config disabled when Embedded Signup env is missing")

    client = bootstrap(embed_enabled=True)
    login(client, "new@example.com")
    enabled = client.get("/business/whatsapp/connect-config")
    body = enabled.json()
    if not body.get("enabled") or body.get("appId") != APP_ID or body.get("configId") != CONFIG_ID:
        fail(f"enabled connect-config mismatch: {body}")
    if body.get("graphVersion") != "v23.0":
        fail(f"unexpected graphVersion: {body}")
    assert_no_secrets(body, "enabled connect-config")
    ok("connect-config enabled and returns only public bootstrap values")

    from fastapi.testclient import TestClient
    from main import app as live_app

    complete_unauth = TestClient(live_app).post(
        "/business/whatsapp/connect/complete",
        json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
    )
    if complete_unauth.status_code != 401:
        fail(f"complete unauthenticated expected 401, got {complete_unauth.status_code}")
    ok("complete connection requires auth")

    login(client, "legacy@example.com")
    legacy_complete = client.post(
        "/business/whatsapp/connect/complete",
        json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
    )
    if legacy_complete.status_code != 409:
        fail(f"legacy complete expected 409, got {legacy_complete.status_code} {legacy_complete.text}")
    legacy_biz = client.get("/business").json()["business"]
    if legacy_biz["id"] != 2 or legacy_biz["whatsapp_connection_type"] != "legacy":
        fail(f"legacy business mutated: {legacy_biz}")
    if legacy_biz["whatsapp_phone_number_id"] != LEGACY_PHONE:
        fail("legacy Phone Number ID changed")
    ok("legacy business 2 rejects Embedded Signup and stays connected")

    from database import SessionLocal
    from models.order import Order
    from models.whatsapp_credential import WhatsAppCredential

    original_session_local = SessionLocal
    db = SessionLocal()
    if db.query(Order).filter(Order.business_id == 2).count() != 12:
        fail("legacy orders were changed")
    if db.query(WhatsAppCredential).filter(WhatsAppCredential.business_id == 2).count() != 0:
        fail("legacy business received credentials")
    db.close()
    ok("legacy business 2 still has 12 orders and no credential row")

    login(client, "new@example.com")
    with patch(
        "services.embedded_signup_service.exchange_embedded_signup_code",
        return_value={"access_token": TENANT_TOKEN, "expires_in": 5184000},
    ), patch(
        "services.embedded_signup_service.fetch_phone_metadata",
        return_value={
            "id": NEW_PHONE,
            "display_phone_number": "92 300 9991111",
            "verified_name": "Fresh Shop",
            "platform_type": "NOT_REGISTERED",
        },
    ), patch(
        "services.embedded_signup_service.list_waba_phone_ids",
        return_value={NEW_PHONE},
    ), patch(
        "services.embedded_signup_service.subscribe_app_to_waba",
    ) as subscribe, patch(
        "services.embedded_signup_service.register_phone_number",
    ) as register, patch(
        "services.embedded_signup_service.generate_two_step_pin",
        return_value="581063",
    ):
        success = client.post(
            "/business/whatsapp/connect/complete",
            json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
        )

    if success.status_code != 200:
        fail(f"complete success expected 200, got {success.status_code} {success.text}")
    biz = success.json()["business"]
    assert_no_secrets(biz, "complete response")
    if biz["whatsapp_connection_status"] != "connected":
        fail(f"status not connected: {biz}")
    if biz["whatsapp_connection_type"] != "embedded_signup":
        fail(f"type not embedded_signup: {biz}")
    if biz["whatsapp_phone_number_id"] != NEW_PHONE:
        fail("phoneNumberId not stored")
    if biz["whatsapp_business_account_id"] != NEW_WABA:
        fail("wabaId not stored")
    if not biz["whatsapp_connected"] or not biz["assistant_active"]:
        fail("connected flags missing")
    if subscribe.call_count != 1 or register.call_count != 1:
        fail("subscribe/register were not called")
    if register.call_args.args[2] != "581063":
        fail("register PIN was not the generated PIN")
    ok("complete connection stores encrypted credentials and safe metadata")

    db = SessionLocal()
    from services.whatsapp_credential_service import (
        load_whatsapp_access_token,
        load_whatsapp_two_step_pin,
    )

    from models.user import User
    from models.business import Business

    user_row = db.query(User).filter(User.email == "new@example.com").one()
    stored_biz = db.query(Business).filter(Business.user_id == user_row.id).one()
    if load_whatsapp_access_token(db, stored_biz.id) != TENANT_TOKEN:
        fail("stored token decrypt mismatch")
    if load_whatsapp_two_step_pin(db, stored_biz.id) != "581063":
        fail("stored PIN decrypt mismatch")
    if db.query(WhatsAppCredential).filter(WhatsAppCredential.business_id == stored_biz.id).count() != 1:
        fail("expected one credential row")
    db.close()
    ok("access token and PIN are encrypted at rest and not serialized")

    login(client, "new@example.com")
    mismatch = None
    with patch(
        "services.embedded_signup_service.exchange_embedded_signup_code",
        return_value={"access_token": TENANT_TOKEN, "expires_in": 100},
    ), patch(
        "services.embedded_signup_service.fetch_phone_metadata",
        return_value={"id": "000111", "display_phone_number": "1", "platform_type": "CLOUD_API"},
    ), patch(
        "services.embedded_signup_service.list_waba_phone_ids",
        return_value={NEW_PHONE},
    ), patch("services.embedded_signup_service.subscribe_app_to_waba") as subscribe:
        mismatch = client.post(
            "/business/whatsapp/connect/complete",
            json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
        )
    if mismatch.status_code != 400:
        fail(f"mismatched IDs expected 400, got {mismatch.status_code} {mismatch.text}")
    if subscribe.called:
        fail("subscribe ran after ID mismatch")
    still_connected = client.get("/business").json()["business"]
    if still_connected["whatsapp_connection_status"] != "connected":
        fail("reconnect ID mismatch wiped an existing Embedded Signup connection")
    db = original_session_local()
    user_row = db.query(User).filter(User.email == "new@example.com").one()
    stored_biz = db.query(Business).filter(Business.user_id == user_row.id).one()
    if load_whatsapp_access_token(db, stored_biz.id) != TENANT_TOKEN:
        fail("reconnect ID mismatch deleted stored credentials")
    db.close()
    ok("mismatched WABA/phone IDs are rejected")

    login(client, "new@example.com")
    with patch(
        "services.embedded_signup_service.exchange_embedded_signup_code",
        return_value={"access_token": TENANT_TOKEN, "expires_in": 100},
    ), patch(
        "services.embedded_signup_service.fetch_phone_metadata",
        return_value={"id": "999111222", "display_phone_number": "1", "platform_type": "CLOUD_API"},
    ), patch(
        "services.embedded_signup_service.list_waba_phone_ids",
        return_value={"999111222"},
    ), patch("services.embedded_signup_service.subscribe_app_to_waba") as subscribe:
        duplicate = client.post(
            "/business/whatsapp/connect/complete",
            json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": "999111222"},
        )
    if duplicate.status_code != 409:
        fail(f"duplicate phone expected 409, got {duplicate.status_code} {duplicate.text}")
    if subscribe.called:
        fail("subscribe ran for a duplicate Phone Number ID")
    ok("duplicate Phone Number ID is rejected")

    login(client, "new@example.com")
    disconnected = client.post("/business/whatsapp/disconnect")
    if disconnected.status_code != 200:
        fail(f"ES disconnect expected 200, got {disconnected.status_code} {disconnected.text}")
    disc_biz = disconnected.json()["business"]
    assert_no_secrets(disc_biz, "disconnect response")
    if (
        disc_biz["whatsapp_connection_status"] != "disconnected"
        or disc_biz["whatsapp_phone_number_id"]
        or disc_biz["whatsapp_connected"]
    ):
        fail(f"ES disconnect did not clear connection: {disc_biz}")
    db = original_session_local()
    user_row = db.query(User).filter(User.email == "new@example.com").one()
    stored_biz = db.query(Business).filter(Business.user_id == user_row.id).one()
    if db.query(WhatsAppCredential).filter(WhatsAppCredential.business_id == stored_biz.id).count() != 0:
        fail("disconnect left encrypted credentials")
    if db.query(Order).filter(Order.business_id == 2).count() != 12:
        fail("disconnect changed legacy orders")
    db.close()
    ok("Embedded Signup disconnect removes credentials and preserves orders")

    fresh_client = bootstrap(embed_enabled=True)
    from database import SessionLocal
    from models.user import User
    from models.business import Business
    from models.whatsapp_credential import WhatsAppCredential
    from services.embedded_signup_service import EmbeddedSignupError

    login(fresh_client, "new@example.com")
    with patch(
        "services.embedded_signup_service.exchange_embedded_signup_code",
        side_effect=EmbeddedSignupError(
            "WhatsApp authorization expired. Please try connecting again.",
            status_code=400,
            code="invalid_code",
        ),
    ):
        invalid = fresh_client.post(
            "/business/whatsapp/connect/complete",
            json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
        )
    if invalid.status_code != 400:
        fail(f"invalid code expected 400, got {invalid.status_code} {invalid.text}")
    if CODE in str(invalid.json()) or TENANT_TOKEN in str(invalid.json()):
        fail("invalid-code payload leaked secrets")
    invalid_biz = fresh_client.get("/business").json()["business"]
    if invalid_biz["whatsapp_connection_status"] != "error" or invalid_biz["whatsapp_connected"]:
        fail(f"invalid code should not connect: {invalid_biz}")
    ok("invalid authorization code is rejected without a stored token")

    with patch(
        "services.embedded_signup_service.exchange_embedded_signup_code",
        side_effect=Exception("code boom"),
    ):
        failed = fresh_client.post(
            "/business/whatsapp/connect/complete",
            json={"code": CODE, "wabaId": NEW_WABA, "phoneNumberId": NEW_PHONE},
        )
    if failed.status_code != 502:
        fail(f"graph failure expected 502, got {failed.status_code} {failed.text}")
    failed_biz = fresh_client.get("/business").json()["business"]
    if failed_biz["whatsapp_connection_status"] != "error":
        fail(f"failed complete should be error, got {failed_biz}")
    if failed_biz["whatsapp_connected"] or failed_biz["whatsapp_phone_number_id"]:
        fail("partial connected state was stored after Graph failure")
    if "EAA_" in str(failed_biz) or CODE in str(failed.json()):
        fail("error payload leaked secrets")
    db = SessionLocal()
    user_row = db.query(User).filter(User.email == "new@example.com").one()
    stored_biz = db.query(Business).filter(Business.user_id == user_row.id).one()
    if db.query(WhatsAppCredential).filter(WhatsAppCredential.business_id == stored_biz.id).count() != 0:
        fail("failed complete stored credentials")
    db.close()
    ok("Graph failure leaves error status without a connected token")

    login(client, "other@example.com")
    isolated = client.post(
        "/business/whatsapp/disconnect",
    )
    # other user is disconnected, disconnect should succeed as local disconnect
    if isolated.status_code not in {200, 409}:
        fail(f"unexpected disconnect status: {isolated.status_code} {isolated.text}")

    login(client, "legacy@example.com")
    legacy_disconnect = client.post("/business/whatsapp/disconnect")
    if legacy_disconnect.status_code != 409:
        fail(f"legacy disconnect expected 409, got {legacy_disconnect.status_code}")
    still = client.get("/business").json()["business"]
    if still["whatsapp_connection_type"] != "legacy" or still["id"] != 2:
        fail("legacy disconnect mutated business 2")
    ok("legacy business 2 cannot be disconnected")

    print("\nAll Embedded Signup connection checks passed.")


if __name__ == "__main__":
    main()
