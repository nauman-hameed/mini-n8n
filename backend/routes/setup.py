from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_TOKEN_JSON,
)
from services.ai_extractor import get_ai_provider
from services.credentials_service import load_credentials
from services.execution_log import LAST_WEBHOOK_RUN
from services.workflow_store import load_workflow
from services.whatsapp_service import get_meta_credentials


router = APIRouter()


@router.post("/setup/import-encrypted-credentials")
def import_encrypted_credentials(payload: dict):
    encrypted = str(payload.get("data", "")).strip()

    if not encrypted:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Encrypted credentials data is missing.",
            },
        )

    from pathlib import Path

    storage_file = (
        Path(__file__).resolve().parent.parent
        / "storage"
        / "credentials.json"
    )
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_text(encrypted, encoding="utf-8")

    try:
        load_credentials()
    except Exception as error:
        storage_file.unlink(missing_ok=True)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": (
                    "Imported credentials could not be decrypted. "
                    f"Check CREDENTIAL_ENCRYPTION_KEY on Railway. ({error})"
                ),
            },
        )

    return {
        "success": True,
        "message": "Encrypted credentials imported.",
    }


@router.get("/setup/status")
def setup_status():
    workflow = load_workflow()
    meta = get_meta_credentials()

    return {
        "success": True,
        "ai_provider": get_ai_provider(),
        "ai_provider_env": AI_PROVIDER,
        "has_gemini_key": bool(str(GEMINI_API_KEY or "").strip()),
        "has_meta_access_token": bool(meta["access_token"]),
        "has_meta_phone_number_id": bool(meta["phone_number_id"]),
        "has_meta_verify_token": bool(meta["verify_token"]),
        "has_google_spreadsheet_id": bool(
            str(GOOGLE_SPREADSHEET_ID or "").strip()
        ),
        "has_google_token": bool(
            str(GOOGLE_TOKEN_JSON or "").strip()
        ),
        "workflow_nodes": len(
            (workflow or {}).get("nodes", [])
        ),
        "ready_for_whatsapp": bool(
            meta["access_token"]
            and meta["phone_number_id"]
            and get_ai_provider() == "gemini"
            and bool(str(GEMINI_API_KEY or "").strip())
        ),
        "last_webhook_run": LAST_WEBHOOK_RUN,
    }
