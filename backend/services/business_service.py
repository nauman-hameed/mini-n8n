from sqlalchemy.orm import Session

from models.business import Business


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


def serialize_business(business: Business) -> dict:
    return {
        "id": business.id,
        "business_name": business.business_name,
        "whatsapp_number": business.whatsapp_number,
        "onboarding_completed": business.onboarding_completed,
    }
