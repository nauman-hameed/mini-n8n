#!/usr/bin/env python3
"""Run auth/onboarding API checks against a local backend."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

BASE = "http://127.0.0.1:8010"
DB_PATH = BASE_DIR / "storage" / "test_auth_flow.db"
EMAIL = "verify-user@example.com"
PASSWORD = "password123"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def start_server() -> subprocess.Popen:
    env = os.environ.copy()
    env["JWT_SECRET_KEY"] = "local-test-secret"
    env["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"

    if DB_PATH.exists():
        DB_PATH.unlink()

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
        ],
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for _ in range(40):
        try:
            response = httpx.get(f"{BASE}/", timeout=1)
            if response.status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        time.sleep(0.25)

    output = process.stdout.read() if process.stdout else ""
    fail(f"Server did not start.\n{output}")


def main() -> None:
    process = start_server()
    client = httpx.Client(base_url=BASE, timeout=10)

    try:
        # Validation errors
        response = client.post(
            "/auth/signup",
            json={
                "full_name": "",
                "email": "bad-email",
                "password": "short",
                "confirm_password": "other",
            },
        )
        if response.status_code != 422:
            fail(f"Expected 422 for invalid signup, got {response.status_code}")
        ok("Signup validation rejects invalid payload")

        # Successful signup
        response = client.post(
            "/auth/signup",
            json={
                "full_name": "Verify User",
                "email": EMAIL,
                "password": PASSWORD,
                "confirm_password": PASSWORD,
            },
        )
        if response.status_code != 200:
            fail(f"Signup failed: {response.text}")
        user = response.json()["user"]
        if user["onboarding_completed"]:
            fail("New user should not have completed onboarding")
        ok("Signup creates authenticated user")

        # Duplicate email
        response = client.post(
            "/auth/signup",
            json={
                "full_name": "Another User",
                "email": EMAIL,
                "password": PASSWORD,
                "confirm_password": PASSWORD,
            },
        )
        if response.status_code != 409:
            fail(f"Expected 409 for duplicate email, got {response.status_code}")
        ok("Duplicate email rejected")

        # Session restore
        response = client.get("/auth/me")
        if response.status_code != 200:
            fail(f"/auth/me failed: {response.text}")
        ok("/auth/me restores session")

        # Protected business before onboarding
        response = client.get("/business")
        if response.status_code != 200 or response.json()["business"] is not None:
            fail("Business should be empty before onboarding")
        ok("Business empty before onboarding")

        # Invalid WhatsApp
        response = client.post(
            "/business/onboarding",
            json={
                "business_name": "Verify Shop",
                "whatsapp_number": "03001234567",
            },
        )
        if response.status_code != 422:
            fail(f"Expected invalid WhatsApp to fail, got {response.status_code}")
        ok("Invalid WhatsApp number rejected")

        # Onboarding
        response = client.post(
            "/business/onboarding",
            json={
                "business_name": "Verify Shop",
                "whatsapp_number": "+923001234567",
            },
        )
        if response.status_code != 200:
            fail(f"Onboarding failed: {response.text}")
        business = response.json()["business"]
        if not business["onboarding_completed"]:
            fail("Onboarding should mark business complete")
        ok("Onboarding saved business details")

        response = client.get("/auth/me")
        if not response.json()["user"]["onboarding_completed"]:
            fail("User onboarding flag not updated")
        ok("User onboarding flag updated")

        # Logout
        response = client.post("/auth/logout")
        if response.status_code != 200:
            fail(f"Logout failed: {response.text}")

        response = client.get("/auth/me")
        if response.status_code != 401:
            fail("Session should be cleared after logout")
        ok("Logout clears session")

        # Login wrong password
        response = client.post(
            "/auth/login",
            json={"email": EMAIL, "password": "wrong-password"},
        )
        if response.status_code != 401:
            fail(f"Expected 401 for bad password, got {response.status_code}")
        ok("Incorrect password rejected")

        # Login success
        response = client.post(
            "/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        if response.status_code != 200:
            fail(f"Login failed: {response.text}")
        if not response.json()["user"]["onboarding_completed"]:
            fail("Returning user should stay onboarded")
        ok("Returning user login succeeds")

        response = client.get("/business")
        saved = response.json()["business"]
        if saved["whatsapp_number"] != "+923001234567":
            fail("Business data not persisted correctly")
        ok("Business data persisted after re-login")

        # Existing routes still work
        response = client.get("/setup/status")
        if response.status_code != 200:
            fail(f"/setup/status failed: {response.text}")
        ok("Existing /setup/status route still works")

        response = client.get("/workflow")
        if response.status_code != 200:
            fail(f"/workflow failed: {response.text}")
        ok("Existing /workflow route still works")

        # SQLite inspection
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user_row = conn.execute(
            "SELECT email, password_hash FROM users WHERE email = ?",
            (EMAIL,),
        ).fetchone()
        business_row = conn.execute(
            "SELECT business_name, whatsapp_number, onboarding_completed FROM businesses"
        ).fetchone()

        if not user_row:
            fail("User row missing in SQLite")
        if user_row["email"] != EMAIL:
            fail("Email not normalized/stored correctly")
        if user_row["password_hash"] == PASSWORD:
            fail("Password stored as plain text")
        if not user_row["password_hash"].startswith("$2"):
            fail("Password hash is not bcrypt")
        if business_row["business_name"] != "Verify Shop":
            fail("Business row incorrect")
        conn.close()
        ok("SQLite stores hashed passwords and business relationship")

        # PostgreSQL URL normalization
        from database import normalize_database_url

        pg_url = normalize_database_url("postgres://user:pass@host:5432/db")
        if pg_url != "postgresql+psycopg2://user:pass@host:5432/db":
            fail(f"Unexpected postgres URL normalization: {pg_url}")
        ok("PostgreSQL DATABASE_URL normalization works")

        print("\nAll auth/onboarding checks passed.")
    finally:
        client.close()
        process.terminate()
        process.wait(timeout=5)
        if DB_PATH.exists():
            DB_PATH.unlink()


if __name__ == "__main__":
    main()
