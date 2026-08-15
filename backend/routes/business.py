from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from schemas.business import BusinessSettingsRequest, OnboardingRequest
from services.business_service import (
    get_business_for_user,
    save_onboarding,
    serialize_business,
    update_business_settings,
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


@router.patch("", response_model=dict)
def patch_business(
    payload: BusinessSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No business fields to update.",
        )

    clear_phone_number_id = (
        "whatsapp_phone_number_id" in update_data
        and update_data.get("whatsapp_phone_number_id") is None
    )

    try:
        business = update_business_settings(
            db,
            user_id=current_user.id,
            business_name=update_data.get("business_name"),
            whatsapp_number=update_data.get("whatsapp_number"),
            whatsapp_phone_number_id=update_data.get("whatsapp_phone_number_id"),
            clear_phone_number_id=clear_phone_number_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    return {
        "success": True,
        "message": "Business settings saved.",
        "business": serialize_business(business),
    }
