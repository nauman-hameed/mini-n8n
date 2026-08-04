from fastapi import APIRouter

from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_TOKEN_JSON,
    META_ACCESS_TOKEN,
    META_PHONE_NUMBER_ID,
    META_VERIFY_TOKEN,
)
from services.ai_extractor import get_ai_provider
from services.workflow_store import load_workflow
from services.whatsapp_service import get_meta_credentials


router = APIRouter()


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
    }
