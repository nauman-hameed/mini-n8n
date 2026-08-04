#!/usr/bin/env python3
"""Print Railway env vars from local config for manual paste."""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.credentials_service import load_credentials  # noqa: E402

TOKEN_FILE = BASE_DIR / "tokens" / "google_token.json"


def main() -> int:
    credentials = load_credentials()

    variables = {
        "META_VERIFY_TOKEN": credentials.get("metaVerifyToken")
        or "mini_n8n_verify_token",
        "META_ACCESS_TOKEN": credentials.get("metaAccessToken", ""),
        "META_PHONE_NUMBER_ID": credentials.get("metaPhoneNumberId", ""),
        "GEMINI_API_KEY": credentials.get("geminiApiKey", ""),
        "AI_PROVIDER": "gemini",
        "CREDENTIAL_ENCRYPTION_KEY": "Ezv8xSACZVdpW3yCnhW9A4YO7rxH2a6h2Js3Aro7bFw=",
        "FRONTEND_URL": "https://mini-n8n-gilt.vercel.app",
        "GOOGLE_SPREADSHEET_ID": credentials.get(
            "googleSpreadsheetId",
            "",
        ),
    }

    if TOKEN_FILE.exists():
        variables["GOOGLE_TOKEN_JSON"] = TOKEN_FILE.read_text(
            encoding="utf-8"
        ).strip()

    print("Paste these in Railway -> Variables (then Redeploy):\n")
    for key, value in variables.items():
        if not str(value).strip():
            print(f"# MISSING LOCALLY: {key}")
            continue
        print(f"{key}={value}")

    print(
        "\nAfter redeploy, run:\n"
        "  PRODUCTION_URL=https://mini-n8n-production.up.railway.app "
        "python scripts/sync_production.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
