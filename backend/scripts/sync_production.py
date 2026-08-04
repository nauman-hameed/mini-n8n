#!/usr/bin/env python3
"""
Sync local workflow + credentials to production backend.
Usage:
  PRODUCTION_URL=https://your-app.up.railway.app python scripts/sync_production.py
"""

import json
import os
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
TOKEN_FILE = BASE_DIR / "tokens" / "google_token.json"


def load_local_credentials() -> dict:
    sys.path.insert(0, str(BASE_DIR))
    from services.credentials_service import load_credentials

    credentials = load_credentials()
    credentials["aiProvider"] = "gemini"

    if TOKEN_FILE.exists():
        credentials["googleTokenJson"] = TOKEN_FILE.read_text(
            encoding="utf-8"
        )

    return credentials


def main() -> int:
    production_url = os.getenv("PRODUCTION_URL", "").strip().rstrip("/")

    if not production_url:
        print("ERROR: Set PRODUCTION_URL to your Railway backend URL.")
        print("Example:")
        print(
            "  PRODUCTION_URL=https://mini-n8n.up.railway.app "
            "python scripts/sync_production.py"
        )
        return 1

    workflow_file = STORAGE_DIR / "workflow.json"

    if not workflow_file.exists():
        print("ERROR: No local workflow found at backend/storage/workflow.json")
        print("Open the editor and save your workflow first.")
        return 1

    workflow = json.loads(
        workflow_file.read_text(encoding="utf-8")
    )

    print(f"Syncing workflow to {production_url}...")
    workflow_response = requests.post(
        f"{production_url}/workflow",
        json=workflow,
        timeout=30,
    )
    workflow_data = workflow_response.json()

    if not workflow_response.ok:
        print("Workflow sync failed:", workflow_data.get("message"))
        return 1

    print("Workflow synced.")
    print("Webhook URL:", workflow_data.get("webhook_url"))

    try:
        credentials = load_local_credentials()
        print("Syncing credentials...")
        credentials_response = requests.post(
            f"{production_url}/credentials",
            json=credentials,
            timeout=30,
        )
        credentials_data = credentials_response.json()

        if not credentials_response.ok:
            print(
                "Credentials sync failed:",
                credentials_data.get("message"),
            )
            print(
                "Ensure Railway has CREDENTIAL_ENCRYPTION_KEY="
                "Ezv8xSACZVdpW3yCnhW9A4YO7rxH2a6h2Js3Aro7bFw="
            )
            return 1

        print("Credentials synced.")
    except Exception as error:
        print("Credentials sync error:", error)
        return 1

    print("\nMeta webhook setup:")
    print(f"  Callback URL: {production_url}/webhook/whatsapp")
    print("  Verify Token: mini_n8n_verify_token")
    print("  Subscribe to: messages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
