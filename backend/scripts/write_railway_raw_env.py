#!/usr/bin/env python3
"""Write Railway Raw Editor content to railway-vars.raw.env"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.credentials_service import load_credentials

TOKEN_FILE = BASE_DIR / "tokens" / "google_token.json"
OUTPUT = BASE_DIR / "railway-vars.raw.env"


def main() -> int:
    credentials = load_credentials()

    variables = {
        "META_VERIFY_TOKEN": credentials.get("metaVerifyToken")
        or "mini_n8n_verify_token",
        "META_ACCESS_TOKEN": credentials.get("metaAccessToken", ""),
        "META_PHONE_NUMBER_ID": credentials.get("metaPhoneNumberId", ""),
        "META_API_VERSION": "v23.0",
        "GEMINI_API_KEY": credentials.get("geminiApiKey", ""),
        "AI_PROVIDER": "gemini",
        "CREDENTIAL_ENCRYPTION_KEY": "Ezv8xSACZVdpW3yCnhW9A4YO7rxH2a6h2Js3Aro7bFw=",
        "FRONTEND_URL": "https://mini-n8n-gilt.vercel.app",
        "APP_ENV": "production",
        "GOOGLE_SPREADSHEET_ID": credentials.get(
            "googleSpreadsheetId",
            "",
        ),
    }

    if TOKEN_FILE.exists():
        variables["GOOGLE_TOKEN_JSON"] = TOKEN_FILE.read_text(
            encoding="utf-8"
        ).strip()

    lines = [
        f"{key}={value}"
        for key, value in variables.items()
        if str(value).strip()
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} variables to {OUTPUT}")
    print("Railway: Variables tab → Raw Editor → paste file contents → Deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
