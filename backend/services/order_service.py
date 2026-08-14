from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from models.business import Business
from models.order import (
    ALLOWED_TRANSITIONS,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
    Order,
    OrderItem,
)
from schemas.n8n_orders import (
    N8nCreateOrderRequest,
    N8nShipOrderRequest,
    N8nUpdateOrderRequest,
)


class OrderError(Exception):
    def __init__(self, message: str, *, code: str = "order_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class OrderNotFoundError(OrderError):
    def __init__(self, message: str = "Order not found.") -> None:
        super().__init__(message, code="not_found")


class OrderConflictError(OrderError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict")


class OrderValidationError(OrderError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation")


_BUTTON_ID_RE = re.compile(
    r"^(?:confirm_|cancel_)?(\d+)$",
    re.IGNORECASE,
)


def parse_button_order_id(raw_order_id: str) -> int:
    cleaned = (raw_order_id or "").strip()

    if not cleaned:
        raise OrderValidationError("orderId is required.")

    match = _BUTTON_ID_RE.fullmatch(cleaned)

    if not match:
        raise OrderValidationError(
            "Invalid orderId. Expected confirm_<id>, cancel_<id>, or numeric id."
        )

    return int(match.group(1))


def get_business_by_phone_number_id(
    db: Session,
    phone_number_id: str,
) -> Business | None:
    cleaned = phone_number_id.strip()

    if not cleaned:
        return None

    return (
        db.query(Business)
        .filter(Business.whatsapp_phone_number_id == cleaned)
        .first()
    )


def get_order_by_id(db: Session, order_id: int) -> Order | None:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.business))
        .filter(Order.id == order_id)
        .first()
    )


def get_order_by_number(db: Session, order_number: str) -> Order | None:
    cleaned = order_number.strip()

    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.business))
        .filter(Order.order_number == cleaned)
        .first()
    )


def get_order_by_ref(db: Session, order_ref: str) -> Order | None:
    cleaned = order_ref.strip()
    order = get_order_by_number(db, cleaned)

    if order:
        return order

    if cleaned.isdigit():
        return get_order_by_id(db, int(cleaned))

    return None


def list_orders_for_business(db: Session, business_id: int) -> list[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.business_id == business_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_business_owned_order(
    db: Session,
    *,
    business_id: int,
    order_id: int,
) -> Order | None:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.business))
        .filter(Order.id == order_id, Order.business_id == business_id)
        .first()
    )


def _assign_order_number(order: Order) -> None:
    order.order_number = f"ORD-{order.id}"


def _ensure_transition(order: Order, new_status: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())

    if new_status not in allowed:
        raise OrderConflictError(
            f"Cannot transition order from {order.status} to {new_status}."
        )


def create_order_from_n8n(
    db: Session,
    payload: N8nCreateOrderRequest,
) -> Order:
    try:
        business_id = int(str(payload.business_id).strip())
    except ValueError as exc:
        raise OrderValidationError("businessId must be a numeric business id.") from exc

    business = db.query(Business).filter(Business.id == business_id).first()

    if not business:
        raise OrderNotFoundError("Business not found.")

    if payload.wa_message_id:
        existing = (
            db.query(Order)
            .options(joinedload(Order.items), joinedload(Order.business))
            .filter(
                Order.business_id == business_id,
                Order.wa_message_id == payload.wa_message_id,
            )
            .first()
        )
        if existing:
            return existing

    order = Order(
        order_number="PENDING",
        business_id=business.id,
        customer_phone=payload.customer_phone,
        customer_name=payload.customer_name,
        notes=payload.notes or "",
        wa_message_id=payload.wa_message_id,
        status=ORDER_STATUS_PENDING,
    )
    db.add(order)
    db.flush()

    _assign_order_number(order)

    for item in payload.items:
        db.add(
            OrderItem(
                order_id=order.id,
                name=item.name.strip(),
                quantity=item.quantity,
                unit_price=Decimal(item.unit_price),
            )
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if payload.wa_message_id:
            existing = (
                db.query(Order)
                .options(joinedload(Order.items), joinedload(Order.business))
                .filter(
                    Order.business_id == business_id,
                    Order.wa_message_id == payload.wa_message_id,
                )
                .first()
            )
            if existing:
                return existing
        raise OrderConflictError("Could not create order.") from exc

    return get_order_by_id(db, order.id)


def update_order_status_from_n8n(
    db: Session,
    payload: N8nUpdateOrderRequest,
) -> Order:
    order_id = parse_button_order_id(payload.order_id)
    order = get_order_by_id(db, order_id)

    if not order:
        raise OrderNotFoundError()

    if order.status == payload.status:
        return order

    _ensure_transition(order, payload.status)
    order.status = payload.status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    return get_order_by_id(db, order.id)


def mark_order_shipped(
    db: Session,
    *,
    order_number: str,
    payload: N8nShipOrderRequest,
) -> Order:
    order = get_order_by_number(db, order_number)

    if not order:
        raise OrderNotFoundError()

    if order.status != ORDER_STATUS_CONFIRMED:
        raise OrderConflictError(
            f"Order must be CONFIRMED before shipping (current: {order.status})."
        )

    _ensure_transition(order, ORDER_STATUS_SHIPPED)
    order.status = ORDER_STATUS_SHIPPED
    order.courier = payload.courier or None
    order.tracking_number = payload.tracking_number or None
    order.shipment_date = payload.shipment_date
    order.updated_at = datetime.utcnow()
    db.commit()

    return get_order_by_id(db, order.id)


def serialize_order_for_n8n_create(order: Order) -> dict:
    business = order.business

    return {
        "success": True,
        "data": {
            "id": str(order.id),
        },
        "customerPhone": order.customer_phone,
        "order": {
            "id": order.id,
            "orderNumber": order.order_number,
            "status": order.status,
            "business": {
                "id": business.id if business else order.business_id,
                "whatsappNumber": business.whatsapp_number if business else "",
            },
        },
    }


def serialize_order_for_n8n_update(order: Order) -> dict:
    return {
        "success": True,
        "data": {
            "id": str(order.id),
        },
    }


def serialize_order_internal(order: Order) -> dict:
    return {
        "id": order.id,
        "orderNumber": order.order_number,
        "customerPhone": order.customer_phone,
        "customerName": order.customer_name,
        "status": order.status,
        "courier": order.courier,
        "trackingNumber": order.tracking_number,
        "shipmentDate": order.shipment_date.isoformat() if order.shipment_date else None,
        "notes": order.notes,
        "businessId": order.business_id,
    }


# Re-export status constants for tests/routes if needed
__all__ = [
    "OrderConflictError",
    "OrderError",
    "OrderNotFoundError",
    "OrderValidationError",
    "create_order_from_n8n",
    "get_business_by_phone_number_id",
    "get_business_owned_order",
    "get_order_by_id",
    "get_order_by_number",
    "get_order_by_ref",
    "list_orders_for_business",
    "mark_order_shipped",
    "parse_button_order_id",
    "serialize_order_for_n8n_create",
    "serialize_order_for_n8n_update",
    "serialize_order_internal",
    "update_order_status_from_n8n",
    "ORDER_STATUS_CANCELLED",
    "ORDER_STATUS_CONFIRMED",
    "ORDER_STATUS_PENDING",
    "ORDER_STATUS_SHIPPED",
]
