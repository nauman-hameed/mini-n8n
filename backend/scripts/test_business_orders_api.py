#!/usr/bin/env python3
"""Auth and isolation tests for dashboard business orders."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


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
    os.environ["N8N_CALLBACK_SECRET"] = "test-n8n-callback-secret"
    os.environ["N8N_INTERNAL_TOKEN"] = "test-n8n-internal-token"

    for module_name in list(sys.modules):
        if (
            module_name in {
                "config",
                "database",
                "main",
            }
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
    from models.business import Business
    from models.order import ORDER_STATUS_PENDING, Order, OrderItem
    from models.user import User
    from services.auth_service import hash_password

    init_db()
    db = SessionLocal()

    owner = User(
        full_name="Owner One",
        email="owner1@example.com",
        password_hash=hash_password("password12345"),
    )
    other = User(
        full_name="Owner Two",
        email="owner2@example.com",
        password_hash=hash_password("password12345"),
    )
    db.add_all([owner, other])
    db.flush()

    business = Business(
        user_id=owner.id,
        business_name="NH",
        whatsapp_number="+923071055454",
        whatsapp_phone_number_id="1160990267106849",
        onboarding_completed=True,
    )
    other_business = Business(
        user_id=other.id,
        business_name="Other Shop",
        whatsapp_number="+923001111111",
        onboarding_completed=True,
    )
    db.add_all([business, other_business])
    db.flush()

    order = Order(
        order_number="ORD-PENDING",
        business_id=business.id,
        customer_phone="923009998887",
        customer_name="Ali",
        notes="House 4B",
        status=ORDER_STATUS_PENDING,
    )
    db.add(order)
    db.flush()
    order.order_number = f"ORD-{order.id}"
    db.add(
        OrderItem(
            order_id=order.id,
            name="Blue Kurta",
            quantity=2,
            unit_price=0,
        )
    )
    db.commit()
    order_id = order.id
    db.close()

    client = TestClient(app)

    response = client.get("/business/orders")
    if response.status_code != 401:
        fail(f"unauthenticated list expected 401, got {response.status_code}")
    ok("unauthenticated GET /business/orders → 401")

    login = client.post(
        "/auth/login",
        json={"email": "owner1@example.com", "password": "password12345"},
    )
    if login.status_code != 200:
        fail(f"owner login failed: {login.status_code} {login.text}")

    listed = client.get("/business/orders")
    if listed.status_code != 200:
        fail(f"list orders failed: {listed.status_code} {listed.text}")
    payload = listed.json()
    if not payload.get("success") or len(payload.get("orders", [])) != 1:
        fail(f"unexpected list payload: {payload}")
    first = payload["orders"][0]
    if first["customerName"] != "Ali" or first["status"] != "PENDING":
        fail(f"unexpected order row: {first}")
    if "unitPrice" not in first["items"][0]:
        fail("order items missing unitPrice")
    ok("authenticated owner lists own orders")

    detail = client.get(f"/business/orders/{order_id}")
    if detail.status_code != 200:
        fail(f"order detail failed: {detail.status_code} {detail.text}")
    if detail.json()["order"]["id"] != order_id:
        fail("order detail id mismatch")
    ok("owner can load order detail")

    other_login = client.post(
        "/auth/login",
        json={"email": "owner2@example.com", "password": "password12345"},
    )
    if other_login.status_code != 200:
        fail(f"other login failed: {other_login.status_code}")

    isolated_list = client.get("/business/orders")
    if isolated_list.status_code != 200:
        fail(f"other list failed: {isolated_list.status_code}")
    if isolated_list.json().get("orders"):
        fail("other user must not see owner orders")
    ok("other user list is empty (isolation)")

    isolated_detail = client.get(f"/business/orders/{order_id}")
    if isolated_detail.status_code != 404:
        fail(f"cross-business detail expected 404, got {isolated_detail.status_code}")
    ok("other user cannot fetch owner order detail")

    settings = client.patch(
        "/business",
        json={
            "business_name": "Other Shop",
            "whatsapp_number": "+923001111111",
            "whatsapp_phone_number_id": "1160990267106849",
        },
    )
    if settings.status_code != 409:
        fail(f"duplicate Meta ID expected 409, got {settings.status_code} {settings.text}")
    ok("duplicate Meta Phone Number ID → 409")

    owner_login = client.post(
        "/auth/login",
        json={"email": "owner1@example.com", "password": "password12345"},
    )
    if owner_login.status_code != 200:
        fail("owner re-login failed")

    me_business = client.get("/business")
    body = me_business.json().get("business") or {}
    if body.get("whatsapp_phone_number_id") != "1160990267106849":
        fail(f"GET /business missing phone id: {body}")
    if "N8N_" in str(body) or "token" in "".join(str(body).lower().split()):
        fail("business payload looks like it leaked a secret")
    ok("GET /business includes Meta Phone Number ID, no secrets")

    print("\nAll dashboard order/settings API checks passed.")


if __name__ == "__main__":
    main()
