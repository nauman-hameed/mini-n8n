from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import ADMIN_PIN


router = APIRouter()


@router.post("/auth/verify-pin")
def verify_pin(payload: dict):
    pin = str(payload.get("pin", "")).strip()
    expected_pin = str(ADMIN_PIN or "").strip()

    if not expected_pin:
        return {
            "success": True,
            "message": "Editor access is open (no PIN configured).",
        }

    if pin == expected_pin:
        return {
            "success": True,
            "message": "PIN verified.",
        }

    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "message": "Incorrect PIN.",
        },
    )


@router.get("/auth/pin-required")
def pin_required():
    return {
        "success": True,
        "pin_required": bool(str(ADMIN_PIN or "").strip()),
    }
