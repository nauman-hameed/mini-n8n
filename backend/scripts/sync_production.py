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

    credentials_file = STORAGE_DIR / "credentials.json"

    if credentials_file.exists():
        print("Note: encrypted credentials must be saved via the live Credentials UI.")
        print(f"Open {os.getenv('FRONTEND_URL', 'https://mini-n8n-gilt.vercel.app')}")
        print("→ Credentials → paste Meta + Google + set AI Provider to Gemini for Railway.")

    print("\nMeta webhook setup:")
    print(f"  Callback URL: {production_url}/webhook/whatsapp")
    print("  Verify Token: same as in Credentials")
    print("  Subscribe to: messages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
