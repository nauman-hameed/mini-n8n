#!/usr/bin/env python3
"""
Generate a private handoff document for your teacher (contains secrets).
Output: backend/teacher-handoff.txt (gitignored — send privately, never commit)

Usage:
  cd backend && source venv/bin/activate && python scripts/export_teacher_package.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.credentials_service import load_credentials

OUTPUT = BASE_DIR / "teacher-handoff.txt"
TOKEN_FILE = BASE_DIR / "tokens" / "google_token.json"


def main() -> int:
    credentials = load_credentials()

    lines = [
        "=" * 60,
        "MINI-N8N — TEACHER TESTING PACKAGE (CONFIDENTIAL)",
        "=" * 60,
        "",
        "Do NOT share publicly or commit to GitHub.",
        "",
        "── LIVE APP ──",
        "Web app:     https://mini-n8n-gilt.vercel.app",
        "Backend:     https://mini-n8n-production.up.railway.app",
        "Status:      https://mini-n8n-production.up.railway.app/setup/status",
        "",
        "── HOW TO TEST ──",
        "1. Open the web app link above",
        "2. Click 'Open Editor' → empty canvas",
        "3. Click 'Credentials' in the navbar",
        "4. Paste each value below into the matching field",
        "5. Click 'Save Credentials'",
        "6. Build workflow: WhatsApp Trigger → AI Extractor → Google Sheets → WhatsApp Reply",
        "7. Connect nodes, configure each node, click 'Execute Workflow'",
        "",
        "WhatsApp live test:",
        "  • Send a message TO: +1 555 185 1299",
        "  • Your number must be added as a Meta test recipient (ask student to add it)",
        "  • Sample message:",
        "    Hi, I want 2 blue shirts. Name: Ahmed, Address: Karachi, Phone: 03001234567",
        "",
        "── CREDENTIALS (paste into app) ──",
        "",
        f"Google Client ID:",
        f"  {credentials.get('googleClientId', '')}",
        "",
        f"Google Client Secret:",
        f"  {credentials.get('googleClientSecret', '')}",
        "",
        f"Google Spreadsheet ID:",
        f"  {credentials.get('googleSpreadsheetId', '')}",
        "",
        f"Meta Access Token:",
        f"  {credentials.get('metaAccessToken', '')}",
        "",
        f"Meta Phone Number ID:",
        f"  {credentials.get('metaPhoneNumberId', '')}",
        "",
        f"Meta Verify Token:",
        f"  {credentials.get('metaVerifyToken', 'mini_n8n_verify_token')}",
        "",
        f"AI Provider: gemini",
        "",
        f"Gemini API Key:",
        f"  {credentials.get('geminiApiKey', '')}",
        "",
        "── META WEBHOOK (already configured on server) ──",
        "Callback URL: https://mini-n8n-production.up.railway.app/webhook/whatsapp",
        "Verify Token: mini_n8n_verify_token",
        "Subscribe to: messages",
        "",
        "── GOOGLE SHEETS NOTE ──",
        "Google Sheets on the live server uses a pre-configured OAuth token.",
        "Saving credentials in the UI updates Meta/Gemini settings.",
        "For Execute Workflow → Sheets to work locally, visit:",
        "  http://localhost:8000/auth/google (local only)",
        "",
    ]

    if TOKEN_FILE.exists():
        lines.extend(
            [
                "── GOOGLE OAUTH (server already has token; for reference) ──",
                "The live backend already has Google Sheets connected.",
                "Execute Workflow on production should write to the sheet.",
                "",
            ]
        )

    lines.extend(
        [
            "── END ──",
            "",
        ]
    )

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Created: {OUTPUT}")
    print("Send this file to your teacher privately (WhatsApp, email, PDF).")
    print("Do NOT upload to GitHub or post online.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
