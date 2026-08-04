from fastapi import APIRouter, Query, Request
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
)

from services.credentials_service import load_credentials


router = APIRouter()


@router.get("/webhook/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(
        default=None,
        alias="hub.mode",
    ),
    hub_verify_token: str | None = Query(
        default=None,
        alias="hub.verify_token",
    ),
    hub_challenge: str | None = Query(
        default=None,
        alias="hub.challenge",
    ),
):
    try:
        credentials = load_credentials()

        verify_token = str(
            credentials.get(
                "metaVerifyToken",
                "",
            )
        ).strip()

        if not verify_token:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": (
                        "Meta Verify Token is missing "
                        "in Credentials."
                    ),
                },
            )

        if (
            hub_mode == "subscribe"
            and hub_verify_token == verify_token
        ):
            return PlainTextResponse(
                content=hub_challenge or "",
                status_code=200,
            )

        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Invalid verify token.",
            },
        )

    except Exception as error:
        print(
            "WhatsApp verification error:",
            error,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(error),
            },
        )


@router.post("/webhook/whatsapp")
async def receive_whatsapp_message(
    request: Request,
):
    try:
        body = await request.json()

        print("\n===================================")
        print("Incoming WhatsApp Webhook")
        print("===================================")
        print(body)
        print("===================================\n")

        return {
            "success": True,
            "message": "Webhook received.",
        }

    except Exception as error:
        print(
            "WhatsApp webhook error:",
            error,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(error),
            },
        )