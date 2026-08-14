from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.n8n_auth import require_n8n_secret
from schemas.n8n_orders import N8nCreateOrderRequest, N8nUpdateOrderRequest
from services.order_service import (
    OrderConflictError,
    OrderNotFoundError,
    OrderValidationError,
    create_order_from_n8n,
    get_business_by_phone_number_id,
    serialize_order_for_n8n_create,
    serialize_order_for_n8n_update,
    update_order_status_from_n8n,
)


router = APIRouter(prefix="/api/n8n", tags=["n8n"])


def _raise_order_http(error: Exception) -> None:
    if isinstance(error, OrderValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.message,
        ) from error

    if isinstance(error, OrderNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error.message,
        ) from error

    if isinstance(error, OrderConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.message,
        ) from error

    raise error


@router.get(
    "/businesses/by-whatsapp-phone-id/{phone_number_id}",
    dependencies=[Depends(require_n8n_secret)],
)
def find_business_by_whatsapp_phone_id(
    phone_number_id: str,
    db: Session = Depends(get_db),
):
    business = get_business_by_phone_number_id(db, phone_number_id)

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    return {
        "data": {
            "businessId": str(business.id),
        }
    }


@router.post(
    "/callback",
    dependencies=[Depends(require_n8n_secret)],
    status_code=status.HTTP_201_CREATED,
)
def create_order_callback(
    payload: N8nCreateOrderRequest,
    db: Session = Depends(get_db),
):
    try:
        order = create_order_from_n8n(db, payload)
    except (OrderValidationError, OrderNotFoundError, OrderConflictError) as error:
        _raise_order_http(error)

    return serialize_order_for_n8n_create(order)


@router.patch(
    "/callback",
    dependencies=[Depends(require_n8n_secret)],
)
def update_order_callback(
    payload: N8nUpdateOrderRequest,
    db: Session = Depends(get_db),
):
    try:
        order = update_order_status_from_n8n(db, payload)
    except (OrderValidationError, OrderNotFoundError, OrderConflictError) as error:
        _raise_order_http(error)

    return serialize_order_for_n8n_update(order)
