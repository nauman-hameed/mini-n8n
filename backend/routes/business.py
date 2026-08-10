from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from schemas.business import OnboardingRequest
from services.business_service import (
    get_business_for_user,
    save_onboarding,
    serialize_business,
)


router = APIRouter(prefix="/business", tags=["business"])


@router.get("", response_model=dict)
def get_business(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = get_business_for_user(db, current_user.id)

    if not business:
        return {
            "success": True,
            "business": None,
        }

    return {
        "success": True,
        "business": serialize_business(business),
    }


@router.post("/onboarding", response_model=dict)
def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    business = save_onboarding(
        db,
        user_id=current_user.id,
        business_name=payload.business_name,
        whatsapp_number=payload.whatsapp_number,
    )

    return {
        "success": True,
        "message": "Business onboarding saved.",
        "business": serialize_business(business),
    }
