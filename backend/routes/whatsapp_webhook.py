from fastapi import APIRouter, Query, Request
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
)

from config import META_VERIFY_TOKEN
from services.workflow_runner import run_workflow
from services.workflow_store import load_workflow
from services.whatsapp_service import (
    get_meta_credentials,
    parse_incoming_messages,
    send_whatsapp_text,
)
from services.credentials_service import load_credentials
from services.execution_log import (
    record_webhook_error,
    record_webhook_start,
    record_webhook_success,
)


router = APIRouter()


def process_whatsapp_message(message_data: dict) -> None:
    record_webhook_start(
        message_data.get("from_phone", ""),
        message_data.get("message", ""),
    )

    try:
        workflow = load_workflow()

        if not workflow:
            print(
                "WhatsApp webhook: no saved workflow. "
                "Open the editor and run/save the workflow first."
            )
            return

        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        has_trigger = any(
            node.get("data", {}).get("nodeType")
            == "whatsappTrigger"
            for node in nodes
        )

        if not has_trigger:
            print(
                "WhatsApp webhook: saved workflow has no "
                "WhatsApp Trigger node."
            )
            return

        trigger_context = {
            "message": message_data["message"],
            "from_phone": message_data["from_phone"],
            "message_id": message_data.get("message_id", ""),
            "phone_number_id": message_data.get(
                "phone_number_id",
                "",
            ),
        }

        print(
            "\n===================================",
            "Running WhatsApp-triggered workflow",
            f"From: {trigger_context['from_phone']}",
            f"Message: {trigger_context['message']}",
            "===================================\n",
        )

        result = run_workflow(
            nodes=nodes,
            edges=edges,
            trigger_context=trigger_context,
        )

        print("WhatsApp workflow result:", result)
        record_webhook_success()

    except Exception as error:
        error_message = str(error)
        print("WhatsApp workflow error:", error_message)
        record_webhook_error(error_message)

        try:
            send_whatsapp_text(
                to_phone=message_data.get("from_phone", ""),
                message=(
                    "Sorry, we could not process your order "
                    "right now. Please try again shortly."
                ),
                phone_number_id=message_data.get(
                    "phone_number_id"
                ),
            )
        except Exception as send_error:
            print(
                "Could not send WhatsApp error reply:",
                send_error,
            )


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
        meta_credentials = get_meta_credentials()

        verify_token = (
            str(credentials.get("metaVerifyToken", "")).strip()
            or meta_credentials["verify_token"]
            or str(META_VERIFY_TOKEN or "").strip()
        )

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

        incoming_messages = parse_incoming_messages(body)

        for message_data in incoming_messages:
            process_whatsapp_message(message_data)

        return {
            "success": True,
            "message": (
                "Webhook received."
                if incoming_messages
                else "Webhook received (no text messages)."
            ),
            "processed_messages": len(incoming_messages),
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
