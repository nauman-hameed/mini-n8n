from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.business import (
    WHATSAPP_CONNECTION_CONNECTED,
    WHATSAPP_CONNECTION_DISCONNECTED,
    Business,
)


def get_business_for_user(db: Session, user_id: int) -> Business | None:
    return (
        db.query(Business)
        .filter(Business.user_id == user_id)
        .first()
    )


def save_onboarding(
    db: Session,
    *,
    user_id: int,
    business_name: str,
    whatsapp_number: str,
) -> Business:
    business = get_business_for_user(db, user_id)

    if business:
        business.business_name = business_name
        business.whatsapp_number = whatsapp_number
        business.onboarding_completed = True
    else:
        business = Business(
            user_id=user_id,
            business_name=business_name,
            whatsapp_number=whatsapp_number,
            onboarding_completed=True,
        )
        db.add(business)

    db.commit()
    db.refresh(business)

    return business


def update_business_settings(
    db: Session,
    *,
    user_id: int,
    business_name: str | None = None,
    whatsapp_number: str | None = None,
    whatsapp_phone_number_id: str | None = None,
    clear_phone_number_id: bool = False,
) -> Business | None:
    business = get_business_for_user(db, user_id)

    if not business:
        return None

    if business_name is not None:
        business.business_name = business_name

    if whatsapp_number is not None:
        business.whatsapp_number = whatsapp_number

    if clear_phone_number_id:
        business.whatsapp_phone_number_id = None
    elif whatsapp_phone_number_id is not None:
        duplicate = (
            db.query(Business)
            .filter(
                Business.whatsapp_phone_number_id == whatsapp_phone_number_id,
                Business.id != business.id,
            )
            .first()
        )
        if duplicate:
            raise ValueError(
                "This Meta Phone Number ID is already linked to another business."
            )
        business.whatsapp_phone_number_id = whatsapp_phone_number_id

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(
            "This Meta Phone Number ID is already linked to another business."
        ) from exc

    db.refresh(business)
    return business


def serialize_business(business: Business) -> dict:
    status = (
        business.whatsapp_connection_status
        or WHATSAPP_CONNECTION_DISCONNECTED
    )
    connected = status == WHATSAPP_CONNECTION_CONNECTED

    return {
        "id": business.id,
        "business_name": business.business_name,
        "whatsapp_number": business.whatsapp_number,
        "onboarding_completed": business.onboarding_completed,
        "whatsapp_phone_number_id": business.whatsapp_phone_number_id,
        "whatsapp_business_account_id": business.whatsapp_business_account_id,
        "whatsapp_display_phone_number": business.whatsapp_display_phone_number,
        "whatsapp_connection_status": status,
        "whatsapp_connection_type": business.whatsapp_connection_type,
        "whatsapp_connected_at": _isoformat(business.whatsapp_connected_at),
        "whatsapp_disconnected_at": _isoformat(business.whatsapp_disconnected_at),
        "whatsapp_connection_error": business.whatsapp_connection_error,
        "whatsapp_connected": connected,
        "assistant_active": connected,
    }


def _isoformat(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()
