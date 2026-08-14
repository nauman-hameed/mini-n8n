#!/usr/bin/env python3
"""API tests for n8n order integration contracts."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

SECRET = "test-n8n-callback-secret"
TOKEN = "test-n8n-internal-token"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def main() -> None:
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    os.environ["JWT_SECRET_KEY"] = "local-test-secret"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["N8N_CALLBACK_SECRET"] = SECRET
    os.environ["N8N_INTERNAL_TOKEN"] = TOKEN

    # Reload config-dependent modules against the temp DB.
    for module_name in list(sys.modules):
        if module_name in {
            "config",
            "database",
            "main",
            "models",
            "models.business",
            "models.order",
            "models.user",
            "services.order_service",
            "services.schema_migration",
            "routes.n8n_api",
            "routes.internal_orders",
            "dependencies.n8n_auth",
        } or module_name.startswith("routes.") or module_name.startswith("services."):
            del sys.modules[module_name]

    from fastapi.testclient import TestClient
    from main import app
    from database import SessionLocal, init_db
    from models.business import Business
    from models.user import User
    from services.auth_service import hash_password

    init_db()

    db = SessionLocal()
    user = User(
        full_name="Test Owner",
        email="owner@example.com",
        password_hash=hash_password("password12345"),
    )
    db.add(user)
    db.flush()
    business = Business(
        user_id=user.id,
        business_name="Test Store",
        whatsapp_number="+923001234567",
        whatsapp_phone_number_id="1192018783994580",
        onboarding_completed=True,
    )
    db.add(business)
    db.commit()
    business_id = business.id
    db.close()

    client = TestClient(app)
    n8n_headers = {"x-n8n-secret": SECRET}
    bearer_headers = {"Authorization": f"Bearer {TOKEN}"}

    # Auth: missing / wrong secret
    response = client.get(
        "/api/n8n/businesses/by-whatsapp-phone-id/1192018783994580"
    )
    if response.status_code != 401:
        fail(f"missing secret expected 401, got {response.status_code}")
    ok("missing x-n8n-secret → 401")

    response = client.get(
        "/api/n8n/businesses/by-whatsapp-phone-id/1192018783994580",
        headers={"x-n8n-secret": "wrong"},
    )
    if response.status_code != 401:
        fail(f"wrong secret expected 401, got {response.status_code}")
    ok("wrong x-n8n-secret → 401")

    response = client.get(
        "/api/internal/orders/ORD-1",
        headers={"Authorization": "Bearer wrong"},
    )
    if response.status_code != 401:
        fail(f"wrong bearer expected 401, got {response.status_code}")
    ok("wrong Bearer → 401")

    # Find business
    response = client.get(
        "/api/n8n/businesses/by-whatsapp-phone-id/1192018783994580",
        headers=n8n_headers,
    )
    if response.status_code != 200:
        fail(f"find business failed: {response.status_code} {response.text}")
    if response.json()["data"]["businessId"] != str(business_id):
        fail(f"unexpected businessId: {response.json()}")
    ok("Find Business returns businessId")

    response = client.get(
        "/api/n8n/businesses/by-whatsapp-phone-id/does-not-exist",
        headers=n8n_headers,
    )
    if response.status_code != 404:
        fail(f"unknown phone id expected 404, got {response.status_code}")
    ok("unknown phone_number_id → 404")

    create_body = {
        "businessId": str(business_id),
        "customerPhone": "923001112233",
        "customerName": "Ali",
        "notes": "House 4B",
        "waMessageId": "wamid.TEST123",
        "items": [
            {"name": "Blue Kurta", "quantity": 2, "unitPrice": 0},
        ],
    }

    response = client.post(
        "/api/n8n/callback",
        headers=n8n_headers,
        json=create_body,
    )
    if response.status_code != 201:
        fail(f"create order failed: {response.status_code} {response.text}")

    payload = response.json()
    order_id = payload["data"]["id"]
    order_number = payload["order"]["orderNumber"]

    if payload["order"]["status"] != "PENDING":
        fail(f"expected PENDING, got {payload['order']['status']}")
    if not order_number.startswith("ORD-"):
        fail(f"unexpected orderNumber: {order_number}")
    if payload["customerPhone"] != "923001112233":
        fail("customerPhone missing in create response")
    if payload["order"]["business"]["whatsappNumber"] != "+923001234567":
        fail("business whatsappNumber missing")
    ok("Create Order → PENDING + data.id + orderNumber")

    # Idempotent create
    response = client.post(
        "/api/n8n/callback",
        headers=n8n_headers,
        json=create_body,
    )
    if response.status_code != 201:
        fail(f"idempotent create failed: {response.status_code} {response.text}")
    if response.json()["data"]["id"] != order_id:
        fail("idempotent create returned different order id")
    ok("repeated waMessageId does not duplicate order")

    # Confirm
    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": f"confirm_{order_id}", "status": "CONFIRMED"},
    )
    if response.status_code != 200:
        fail(f"confirm failed: {response.status_code} {response.text}")
    if response.json()["data"]["id"] != str(order_id):
        fail("confirm response id mismatch")
    ok("PENDING → CONFIRMED via confirm_<id>")

    # Invalid: confirm again to CANCELLED from CONFIRMED via cancel should fail
    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": f"cancel_{order_id}", "status": "CANCELLED"},
    )
    if response.status_code != 409:
        fail(f"CONFIRMED → CANCELLED expected 409, got {response.status_code}")
    ok("CONFIRMED → CANCELLED rejected")

    # Create second order for cancel path
    create_body_2 = {
        **create_body,
        "waMessageId": "wamid.TEST456",
        "customerName": "Sara",
    }
    response = client.post(
        "/api/n8n/callback",
        headers=n8n_headers,
        json=create_body_2,
    )
    order_id_2 = response.json()["data"]["id"]

    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": f"cancel_{order_id_2}", "status": "CANCELLED"},
    )
    if response.status_code != 200:
        fail(f"cancel failed: {response.status_code} {response.text}")
    ok("PENDING → CANCELLED via cancel_<id>")

    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": f"confirm_{order_id_2}", "status": "CONFIRMED"},
    )
    if response.status_code != 409:
        fail(f"CANCELLED → CONFIRMED expected 409, got {response.status_code}")
    ok("CANCELLED → CONFIRMED rejected")

    # PENDING → SHIPPED via callback not allowed (only CONFIRMED/CANCELLED on PATCH)
    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": order_id, "status": "SHIPPED"},
    )
    if response.status_code != 422:
        fail(f"SHIPPED via n8n callback expected 422, got {response.status_code}")
    ok("SHIPPED via /api/n8n/callback rejected by schema")

    # Invalid button id
    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": "confirm_abc", "status": "CONFIRMED"},
    )
    if response.status_code != 400:
        fail(f"invalid button id expected 400, got {response.status_code}")
    ok("invalid orderId rejected")

    # Shipping
    response = client.get(
        f"/api/internal/orders/{order_number}",
        headers=bearer_headers,
    )
    if response.status_code != 200:
        fail(f"get internal order failed: {response.status_code} {response.text}")
    body = response.json()
    if body["orderNumber"] != order_number or body["status"] != "CONFIRMED":
        fail(f"unexpected get body: {body}")
    ok("GET internal order by order_number")

    response = client.patch(
        f"/api/internal/orders/{order_number}/status",
        headers=bearer_headers,
        json={
            "status": "SHIPPED",
            "courier": "TCS",
            "trackingNumber": "TCS123",
            "shipmentDate": datetime.now(timezone.utc).isoformat(),
        },
    )
    if response.status_code != 200:
        fail(f"ship failed: {response.status_code} {response.text}")
    if response.json()["status"] != "SHIPPED":
        fail(f"expected SHIPPED, got {response.json()}")
    ok("CONFIRMED → SHIPPED")

    response = client.patch(
        f"/api/internal/orders/{order_number}/status",
        headers=bearer_headers,
        json={
            "status": "SHIPPED",
            "courier": "TCS",
            "trackingNumber": "TCS999",
            "shipmentDate": datetime.now(timezone.utc).isoformat(),
        },
    )
    if response.status_code != 409:
        fail(f"SHIPPED → SHIPPED expected 409, got {response.status_code}")
    ok("SHIPPED → other status rejected")

    # Bare numeric id confirm on a fresh pending order
    create_body_3 = {
        **create_body,
        "waMessageId": "wamid.TEST789",
    }
    response = client.post(
        "/api/n8n/callback",
        headers=n8n_headers,
        json=create_body_3,
    )
    order_id_3 = response.json()["data"]["id"]
    response = client.patch(
        "/api/n8n/callback",
        headers=n8n_headers,
        json={"orderId": str(order_id_3), "status": "CONFIRMED"},
    )
    if response.status_code != 200:
        fail(f"bare id confirm failed: {response.status_code} {response.text}")
    ok("bare numeric orderId confirm works")

    print("\nAll n8n order API checks passed.")


if __name__ == "__main__":
    main()
