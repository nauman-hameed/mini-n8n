import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import GOOGLE_SPREADSHEET_ID, GOOGLE_TOKEN_JSON
from services.credentials_service import load_credentials


BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_FILE = BASE_DIR / "tokens" / "google_token.json"

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


def _load_google_credentials() -> Credentials:
    if TOKEN_FILE.exists():
        return Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            scopes=GOOGLE_SCOPES,
        )

    saved_credentials = load_credentials()
    token_json = (
        saved_credentials.get("googleTokenJson")
        or GOOGLE_TOKEN_JSON
    )

    if not token_json:
        raise ValueError(
            "Google Sheets is not connected. "
            "Open /auth/google first."
        )

    if isinstance(token_json, str):
        token_data = json.loads(token_json)
    else:
        token_data = token_json

    return Credentials.from_authorized_user_info(
        token_data,
        scopes=GOOGLE_SCOPES,
    )


def append_order_to_sheet(
    order_data: dict,
    sheet_name: str = "Orders",
) -> dict:
    saved_credentials = load_credentials()

    spreadsheet_id = (
        str(
            saved_credentials.get(
                "googleSpreadsheetId",
                "",
            )
        ).strip()
        or str(GOOGLE_SPREADSHEET_ID or "").strip()
    )

    if not spreadsheet_id:
        raise ValueError(
            "Google Spreadsheet ID is missing. "
            "Open Credentials and add it first."
        )

    google_credentials = _load_google_credentials()

    service = build(
        "sheets",
        "v4",
        credentials=google_credentials,
    )

    values = [
        [
            str(order_data.get("name", "")),
            str(order_data.get("phone", "")),
            str(order_data.get("address", "")),
            str(order_data.get("items", "")),
        ]
    ]

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:D",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": values,
            },
        )
        .execute()
    )

    updates = result.get("updates", {})

    return {
        "updated_range": updates.get(
            "updatedRange",
            "",
        ),
        "updated_rows": updates.get(
            "updatedRows",
            0,
        ),
    }