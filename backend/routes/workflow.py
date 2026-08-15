from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import BACKEND_URL
from services.workflow_store import load_workflow, save_workflow


router = APIRouter()


@router.get("/workflow")
def get_workflow():
    try:
        workflow = load_workflow()

        return {
            "success": True,
            "workflow": workflow,
            "webhook_url": get_webhook_url(),
        }

    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )


@router.post("/workflow")
def save_workflow_route(workflow: dict):
    try:
        save_workflow(workflow)

        return {
            "success": True,
            "message": "Workflow saved for WhatsApp triggers.",
            "webhook_url": get_webhook_url(),
        }

    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )


def get_webhook_url() -> str:
    base_url = (BACKEND_URL or "http://localhost:8000").rstrip(
        "/"
    )
    return f"{base_url}/webhook/whatsapp/editor"
