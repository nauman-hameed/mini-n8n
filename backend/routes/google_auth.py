import json
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from config import (
    APP_ENV,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)


# Sirf localhost development mein HTTP OAuth allow hoga.
if APP_ENV == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

TOKEN_FILE = (
    BASE_DIR / "tokens" / "google_token.json"
)

FLOW_DATA_FILE = (
    BASE_DIR / "tokens" / "google_flow_data.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


def validate_google_settings():
    if not GOOGLE_CLIENT_ID:
        raise ValueError(
            "GOOGLE_CLIENT_ID is missing in backend/.env."
        )

    if not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "GOOGLE_CLIENT_SECRET is missing in backend/.env."
        )

    if not GOOGLE_REDIRECT_URI:
        raise ValueError(
            "GOOGLE_REDIRECT_URI is missing in backend/.env."
        )


def create_google_flow(
    *,
    state=None,
    code_verifier=None,
):
    validate_google_settings()

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),
            "redirect_uris": [
                GOOGLE_REDIRECT_URI
            ],
        }
    }

    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI,
        code_verifier=code_verifier,
        autogenerate_code_verifier=(
            code_verifier is None
        ),
    )


@router.get("/auth/google")
def google_login():
    flow = create_google_flow()

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="false",
        )
    )

    FLOW_DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    FLOW_DATA_FILE.write_text(
        json.dumps(
            {
                "state": state,
                "code_verifier": flow.code_verifier,
            }
        ),
        encoding="utf-8",
    )

    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback")
def google_callback(request: Request):
    if not FLOW_DATA_FILE.exists():
        raise ValueError(
            "OAuth flow data is missing. "
            "Please start again from /auth/google."
        )

    flow_data = json.loads(
        FLOW_DATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    returned_state = request.query_params.get(
        "state"
    )

    if returned_state != flow_data.get("state"):
        raise ValueError(
            "OAuth state verification failed."
        )

    flow = create_google_flow(
        state=flow_data["state"],
        code_verifier=flow_data[
            "code_verifier"
        ],
    )

    flow.fetch_token(
        authorization_response=str(request.url)
    )

    TOKEN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TOKEN_FILE.write_text(
        flow.credentials.to_json(),
        encoding="utf-8",
    )

    FLOW_DATA_FILE.unlink(
        missing_ok=True
    )

    return {
        "success": True,
        "message": (
            "Google Sheets connected successfully."
        ),
    }