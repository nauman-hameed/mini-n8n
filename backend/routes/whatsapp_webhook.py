import json

from fastapi import APIRouter, BackgroundTasks, Query, Request
from fastapi.responses import (
    JSONResponse,
    PlainTextResponse,
)

from config import META_APP_SECRET, META_VERIFY_TOKEN
from database import SessionLocal
from models.business import WHATSAPP_CONNECTION_CONNECTED
from services.credentials_service import load_credentials
from services.execution_log import (
    record_webhook_error,
    record_webhook_start,
    record_webhook_success,
)
from services.meta_signature import verify_meta_signature
from services.order_service import get_business_by_phone_number_id
from services.whatsapp_events import extract_waba_id, normalize_message
from services.whatsapp_forwarder import forward_whatsapp_event
from services.whatsapp_service import (
    get_meta_credentials,
    parse_incoming_messages,
    send_whatsapp_text,
)
from services.workflow_runner import run_workflow
from services.workflow_store import load_workflow


router = APIRouter()


def process_editor_whatsapp_message(message_data: dict) -> None:
    record_webhook_start(
        message_data.get("from_phone", ""),
        message_data.get("message", ""),
    )

    try:
        workflow = load_workflow()

        if not workflow:
            print(
                "WhatsApp editor webhook: no saved workflow. "
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
                "WhatsApp editor webhook: saved workflow has no "
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
            "WhatsApp editor workflow from=",
            trigger_context["from_phone"],
        )

        result = run_workflow(
            nodes=nodes,
            edges=edges,
            trigger_context=trigger_context,
        )

        print("WhatsApp editor workflow result keys=", sorted(result.keys()) if isinstance(result, dict) else type(result).__name__)
        record_webhook_success()

    except Exception as error:
        print("WhatsApp editor workflow error")
        record_webhook_error(str(error))

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
        except Exception:
            print("Could not send WhatsApp editor error reply")


def _route_saas_events(body: dict, background_tasks: BackgroundTasks) -> dict:
    forwarded = 0
    skipped = 0
    db = SessionLocal()

    try:
        if not isinstance(body, dict) or body.get("object") != "whatsapp_business_account":
            return {"forwarded": 0, "skipped": 0}

        default_waba_id = extract_waba_id(body)

        for entry in body.get("entry") or []:
            if not isinstance(entry, dict):
                continue

            waba_id = str(entry.get("id") or "").strip() or default_waba_id

            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                if change.get("field") != "messages":
                    continue

                value = change.get("value") or {}
                if not isinstance(value, dict):
                    continue

                metadata = value.get("metadata") or {}
                phone_number_id = str(
                    (metadata.get("phone_number_id") if isinstance(metadata, dict) else "")
                    or ""
                ).strip()
                messages = value.get("messages") or []

                if not phone_number_id:
                    skipped += len(messages) if isinstance(messages, list) else 0
                    continue

                business = get_business_by_phone_number_id(db, phone_number_id)
                connected = bool(
                    business
                    and business.whatsapp_connection_status
                    == WHATSAPP_CONNECTION_CONNECTED
                )

                if not connected:
                    print(
                        "WhatsApp saas webhook skipped phone_id="
                        f"{phone_number_id} reason="
                        f"{'unknown' if not business else business.whatsapp_connection_status}"
                    )
                    skipped += len(messages) if isinstance(messages, list) else 0
                    continue

                if not isinstance(messages, list):
                    continue

                for message in messages:
                    event = normalize_message(
                        message,
                        business_id=business.id,
                        phone_number_id=phone_number_id,
                        waba_id=waba_id or business.whatsapp_business_account_id,
                    )
                    if not event:
                        skipped += 1
                        continue

                    background_tasks.add_task(forward_whatsapp_event, event)
                    forwarded += 1
                    print(
                        "WhatsApp saas webhook queued "
                        f"business_id={business.id} type={event.get('messageType')}"
                    )
    finally:
        db.close()

    return {"forwarded": forwarded, "skipped": skipped}


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
        try:
            credentials = load_credentials()
        except Exception:
            credentials = {}

        try:
            meta_credentials = get_meta_credentials()
        except Exception:
            meta_credentials = {
                "verify_token": str(META_VERIFY_TOKEN or "").strip(),
            }

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

    except Exception:
        print("WhatsApp verification error")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Could not verify WhatsApp webhook.",
            },
        )


@router.post("/webhook/whatsapp")
async def receive_saas_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    if not META_APP_SECRET:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "WhatsApp webhook signature verification is not configured.",
            },
        )

    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not verify_meta_signature(
        raw_body=raw_body,
        signature_header=signature_header,
        app_secret=META_APP_SECRET,
    ):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": "Invalid webhook signature.",
            },
        )

    try:
        body = json.loads(raw_body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid webhook payload.",
            },
        )

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid webhook payload.",
            },
        )

    counts = _route_saas_events(body, background_tasks)
    return {
        "success": True,
        "message": "Webhook received.",
        "forwarded": counts["forwarded"],
        "skipped": counts["skipped"],
    }


@router.post("/webhook/whatsapp/editor")
async def receive_editor_whatsapp_message(request: Request):
    try:
        body = await request.json()
        incoming_messages = parse_incoming_messages(body)

        for message_data in incoming_messages:
            process_editor_whatsapp_message(message_data)

        return {
            "success": True,
            "message": (
                "Editor webhook received."
                if incoming_messages
                else "Editor webhook received (no text messages)."
            ),
            "processed_messages": len(incoming_messages),
        }

    except Exception:
        print("WhatsApp editor webhook error")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Editor webhook failed.",
            },
        )
