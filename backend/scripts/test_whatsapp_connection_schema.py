#!/usr/bin/env python3
"""P1 WhatsApp connection schema, backfill, encryption, and safe GET /business."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, inspect, text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

LEGACY_PHONE_ID = "1160990267106849"
SECRET_KEY_FRAGMENTS = (
    "token",
    "pin",
    "secret",
    "encrypted",
    "credential",
    "hash",
    "cipher",
    "password",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def _engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}")


def _create_pre_p1_schema(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE businesses (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    business_name VARCHAR(160) NOT NULL,
                    whatsapp_number VARCHAR(32) NOT NULL,
                    whatsapp_phone_number_id VARCHAR(64),
                    onboarding_completed BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    order_number VARCHAR(64) NOT NULL UNIQUE,
                    business_id INTEGER NOT NULL,
                    customer_phone VARCHAR(32) NOT NULL,
                    customer_name VARCHAR(160) NOT NULL,
                    notes TEXT NOT NULL,
                    wa_message_id VARCHAR(128),
                    status VARCHAR(32) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        now = datetime.utcnow().isoformat(sep=" ")
        connection.execute(
            text(
                """
                INSERT INTO users (
                    id, full_name, email, password_hash, created_at, updated_at
                ) VALUES (5, 'Khizar', 'nhworldchannel01@example.test', 'x', :now, :now)
                """
            ),
            {"now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO businesses (
                    id, user_id, business_name, whatsapp_number,
                    whatsapp_phone_number_id, onboarding_completed,
                    created_at, updated_at
                ) VALUES (
                    2, 5, 'NH', '+923071055454', :phone_id, 1, :now, :now
                )
                """
            ),
            {"phone_id": LEGACY_PHONE_ID, "now": now},
        )
        for index in range(1, 4):
            connection.execute(
                text(
                    """
                    INSERT INTO orders (
                        id, order_number, business_id, customer_phone,
                        customer_name, notes, status, created_at, updated_at
                    ) VALUES (
                        :id, :order_number, 2, '923001000001', 'Ali',
                        'addr', 'PENDING', :now, :now
                    )
                    """
                ),
                {
                    "id": index,
                    "order_number": f"ORD-{index}",
                    "now": now,
                },
            )


def _assert_no_secret_keys(payload: dict, label: str) -> None:
    serialized = json.dumps(payload)
    lowered = serialized.lower()

    for key in payload:
        key_lower = str(key).lower()
        if any(fragment in key_lower for fragment in SECRET_KEY_FRAGMENTS):
            fail(f"{label} leaked secret-looking key: {key}")

    if "gAAAA" in serialized:
        fail(f"{label} leaked Fernet ciphertext")

    if "n8n_" in lowered or "bearer " in lowered:
        fail(f"{label} leaked integration secret")


def test_forward_backfill_and_rollback() -> None:
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    engine = _engine(db_path)
    _create_pre_p1_schema(engine)

    from services.schema_migration import (
        WHATSAPP_CONNECTION_COLUMNS,
        migrate_whatsapp_connection_schema,
        rollback_whatsapp_connection_schema,
    )

    migrate_whatsapp_connection_schema(engine)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("businesses")}
    tables = set(inspector.get_table_names())

    missing = set(WHATSAPP_CONNECTION_COLUMNS) - columns
    if missing:
        fail(f"forward migration missing columns: {sorted(missing)}")
    if "whatsapp_credentials" not in tables:
        fail("whatsapp_credentials table was not created")
    ok("forward migration added connection columns and credentials table")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, user_id, whatsapp_phone_number_id,
                       whatsapp_connection_status, whatsapp_connection_type,
                       whatsapp_connected_at, whatsapp_display_phone_number
                FROM businesses WHERE id = 2
                """
            )
        ).mappings().one()
        order_count = connection.execute(
            text("SELECT COUNT(*) FROM orders WHERE business_id = 2")
        ).scalar_one()
        credential_count = connection.execute(
            text("SELECT COUNT(*) FROM whatsapp_credentials")
        ).scalar_one()

    if row["user_id"] != 5:
        fail(f"business 2 user_id changed: {row['user_id']}")
    if row["whatsapp_phone_number_id"] != LEGACY_PHONE_ID:
        fail("business 2 Phone Number ID changed")
    if row["whatsapp_connection_status"] != "connected":
        fail(f"expected connected, got {row['whatsapp_connection_status']}")
    if row["whatsapp_connection_type"] != "legacy":
        fail(f"expected legacy, got {row['whatsapp_connection_type']}")
    if not row["whatsapp_connected_at"]:
        fail("legacy connected_at was not backfilled")
    if row["whatsapp_display_phone_number"] != "+923071055454":
        fail("display number was not copied from whatsapp_number")
    if order_count != 3:
        fail(f"orders changed during migration: {order_count}")
    if credential_count != 0:
        fail("legacy business 2 must not get a credentials row")
    ok("business 2 backfilled as legacy connected; orders and Phone Number ID unchanged")

    migrate_whatsapp_connection_schema(engine)
    ok("forward migration is idempotent")

    rollback_whatsapp_connection_schema(engine)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("businesses")}
    tables = set(inspector.get_table_names())

    leftover = set(WHATSAPP_CONNECTION_COLUMNS) & columns
    if leftover:
        fail(f"rollback left columns: {sorted(leftover)}")
    if "whatsapp_credentials" in tables:
        fail("rollback left whatsapp_credentials")
    if "whatsapp_phone_number_id" not in columns:
        fail("rollback dropped whatsapp_phone_number_id")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, user_id, whatsapp_phone_number_id, business_name
                FROM businesses WHERE id = 2
                """
            )
        ).mappings().one()
        order_count = connection.execute(
            text("SELECT COUNT(*) FROM orders WHERE business_id = 2")
        ).scalar_one()

    if row["id"] != 2 or row["user_id"] != 5:
        fail("rollback changed business 2 identity")
    if row["whatsapp_phone_number_id"] != LEGACY_PHONE_ID:
        fail("rollback changed Phone Number ID")
    if order_count != 3:
        fail("rollback changed orders")
    ok("rollback dropped P1 columns/table without touching business 2 or orders")

    migrate_whatsapp_connection_schema(engine)
    with engine.connect() as connection:
        status = connection.execute(
            text(
                "SELECT whatsapp_connection_status, whatsapp_connection_type "
                "FROM businesses WHERE id = 2"
            )
        ).one()
        credential_count = connection.execute(
            text("SELECT COUNT(*) FROM whatsapp_credentials")
        ).scalar_one()

    if status[0] != "connected" or status[1] != "legacy":
        fail("re-apply after rollback did not backfill business 2")
    if credential_count != 0:
        fail("re-apply created a credentials row for business 2")
    ok("migration re-applies after rollback")

    engine.dispose()
    Path(db_path).unlink(missing_ok=True)


def test_safe_serialization_and_encryption() -> None:
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    os.environ["JWT_SECRET_KEY"] = "local-test-secret"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["CREDENTIAL_ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
    os.environ["N8N_CALLBACK_SECRET"] = "test-n8n-callback-secret"
    os.environ["N8N_INTERNAL_TOKEN"] = "test-n8n-internal-token"

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
        WHATSAPP_CONNECTION_TYPE_LEGACY,
        Business,
    )
    from models.user import User
    from models.whatsapp_credential import WhatsAppCredential
    from datetime import datetime as dt

    from services.auth_service import hash_password
    from services.business_service import serialize_business
    from services.whatsapp_credential_service import (
        load_whatsapp_access_token,
        load_whatsapp_two_step_pin,
        store_whatsapp_secrets,
    )

    init_db()
    db = SessionLocal()

    owner = User(
        full_name="Khizar",
        email="owner-safe@example.com",
        password_hash=hash_password("password12345"),
    )
    other = User(
        full_name="Other",
        email="other-safe@example.com",
        password_hash=hash_password("password12345"),
    )
    db.add_all([owner, other])
    db.flush()

    connected = Business(
        user_id=owner.id,
        business_name="NH",
        whatsapp_number="+923071055454",
        whatsapp_phone_number_id=LEGACY_PHONE_ID,
        whatsapp_display_phone_number="+923071055454",
        whatsapp_connection_status=WHATSAPP_CONNECTION_CONNECTED,
        whatsapp_connection_type=WHATSAPP_CONNECTION_TYPE_LEGACY,
        whatsapp_connected_at=dt.utcnow(),
        onboarding_completed=True,
    )
    disconnected = Business(
        user_id=other.id,
        business_name="KHi empty",
        whatsapp_number="+923001111111",
        onboarding_completed=True,
    )
    db.add_all([connected, disconnected])
    db.commit()
    owner_business_id = connected.id
    db.close()

    db = SessionLocal()
    store_whatsapp_secrets(
        db,
        business_id=owner_business_id,
        access_token="EAA_TEST_ACCESS_TOKEN",
        two_step_pin="581063",
        token_expires_at=dt.utcnow(),
    )
    row = (
        db.query(WhatsAppCredential)
        .filter(WhatsAppCredential.business_id == owner_business_id)
        .one()
    )
    if row.encrypted_access_token == "EAA_TEST_ACCESS_TOKEN":
        fail("access token stored in plaintext")
    if row.encrypted_two_step_pin == "581063":
        fail("PIN stored in plaintext")
    if load_whatsapp_access_token(db, owner_business_id) != "EAA_TEST_ACCESS_TOKEN":
        fail("access token decrypt roundtrip failed")
    if load_whatsapp_two_step_pin(db, owner_business_id) != "581063":
        fail("PIN decrypt roundtrip failed")
    ok("tokens and PINs encrypt at rest and round-trip")

    business = db.query(Business).filter(Business.id == owner_business_id).one()
    payload = serialize_business(business)
    _assert_no_secret_keys(payload, "serialize_business")
    if payload["whatsapp_connected"] is not True:
        fail("connected business serialize expected whatsapp_connected true")
    if payload["assistant_active"] is not True:
        fail("connected business serialize expected assistant_active true")
    dumped = json.dumps(payload)
    if "EAA_TEST_ACCESS_TOKEN" in dumped or "581063" in dumped:
        fail("serialize_business leaked plaintext secrets")
    db.close()
    ok("serialize_business returns only safe connection metadata")

    client = TestClient(app)
    login = client.post(
        "/auth/login",
        json={"email": "owner-safe@example.com", "password": "password12345"},
    )
    if login.status_code != 200:
        fail(f"login failed: {login.status_code} {login.text}")

    response = client.get("/business")
    if response.status_code != 200:
        fail(f"GET /business failed: {response.status_code} {response.text}")

    body = response.json().get("business") or {}
    _assert_no_secret_keys(body, "GET /business")
    if body.get("whatsapp_phone_number_id") != LEGACY_PHONE_ID:
        fail(f"GET /business dropped Phone Number ID: {body}")
    if body.get("whatsapp_connection_status") != "connected":
        fail(f"GET /business missing connected status: {body}")
    if body.get("whatsapp_connection_type") != "legacy":
        fail(f"GET /business missing legacy type: {body}")
    if body.get("whatsapp_connected") is not True:
        fail("GET /business whatsapp_connected should be true")
    if body.get("assistant_active") is not True:
        fail("GET /business assistant_active should be true")
    raw = response.text
    if "EAA_TEST_ACCESS_TOKEN" in raw or "581063" in raw or "gAAAA" in raw:
        fail("GET /business leaked credential ciphertext or plaintext")
    ok("GET /business returns safe connection metadata only")

    other_login = client.post(
        "/auth/login",
        json={"email": "other-safe@example.com", "password": "password12345"},
    )
    if other_login.status_code != 200:
        fail("other user login failed")
    other_body = client.get("/business").json().get("business") or {}
    if other_body.get("whatsapp_connection_status") != "disconnected":
        fail("new business should default to disconnected")
    if other_body.get("whatsapp_connected") is not False:
        fail("disconnected business should not appear connected")
    if other_body.get("assistant_active") is not False:
        fail("disconnected business should not be assistant_active")
    ok("disconnected business serializes as Not Connected")


def main() -> None:
    test_forward_backfill_and_rollback()
    test_safe_serialization_and_encryption()
    print("\nAll WhatsApp connection schema checks passed.")


if __name__ == "__main__":
    main()
