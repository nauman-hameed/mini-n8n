from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from dependencies.n8n_auth import require_n8n_bearer
from schemas.whatsapp_internal import WhatsAppSendRequest
from services.whatsapp_graph import (
    WhatsAppGraphError,
    download_whatsapp_media,
    parse_business_id,
    send_whatsapp_message,
)


router = APIRouter(
    prefix="/api/internal/whatsapp",
    tags=["internal-whatsapp"],
)


def _raise_graph_http(error: WhatsAppGraphError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error.message,
    ) from error


@router.post("/send", dependencies=[Depends(require_n8n_bearer)])
def send_internal_whatsapp_message(
    payload: WhatsAppSendRequest,
    db: Session = Depends(get_db),
):
    try:
        return send_whatsapp_message(
            db,
            business_id=payload.business_id,
            to=payload.to,
            message=payload.message,
        )
    except WhatsAppGraphError as error:
        _raise_graph_http(error)


@router.get("/media/{media_id}", dependencies=[Depends(require_n8n_bearer)])
def get_internal_whatsapp_media(
    media_id: str,
    business_id: str = Query(..., alias="businessId"),
    db: Session = Depends(get_db),
):
    try:
        parsed_business_id = parse_business_id(business_id)
        content, mime_type = download_whatsapp_media(
            db,
            business_id=parsed_business_id,
            media_id=media_id,
        )
    except WhatsAppGraphError as error:
        _raise_graph_http(error)

    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )
