from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.n8n_auth import require_n8n_bearer
from schemas.n8n_orders import N8nShipOrderRequest
from services.order_service import (
    OrderConflictError,
    OrderNotFoundError,
    OrderValidationError,
    get_order_by_ref,
    mark_order_shipped,
    serialize_order_internal,
)


router = APIRouter(prefix="/api/internal/orders", tags=["internal-orders"])


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
    "/{order_ref}",
    dependencies=[Depends(require_n8n_bearer)],
)
def get_internal_order(
    order_ref: str,
    db: Session = Depends(get_db),
):
    order = get_order_by_ref(db, order_ref)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return serialize_order_internal(order)


@router.patch(
    "/{order_number}/status",
    dependencies=[Depends(require_n8n_bearer)],
)
def patch_internal_order_status(
    order_number: str,
    payload: N8nShipOrderRequest,
    db: Session = Depends(get_db),
):
    try:
        order = mark_order_shipped(
            db,
            order_number=order_number,
            payload=payload,
        )
    except (OrderValidationError, OrderNotFoundError, OrderConflictError) as error:
        _raise_order_http(error)

    return serialize_order_internal(order)
