from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from services.business_service import get_business_for_user
from services.order_service import (
    get_business_owned_order,
    list_orders_for_business,
    serialize_order_for_dashboard,
)


router = APIRouter(prefix="/business", tags=["business-orders"])


@router.get("/orders")
def list_business_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = get_business_for_user(db, current_user.id)

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    orders = list_orders_for_business(db, business.id)

    return {
        "success": True,
        "orders": [serialize_order_for_dashboard(order) for order in orders],
    }


@router.get("/orders/{order_id}")
def get_business_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = get_business_for_user(db, current_user.id)

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    order = get_business_owned_order(
        db,
        business_id=business.id,
        order_id=order_id,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return {
        "success": True,
        "order": serialize_order_for_dashboard(order),
    }
