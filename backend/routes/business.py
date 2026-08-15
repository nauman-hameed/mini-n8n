from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_user
from models.user import User
from schemas.business import (
    BusinessSettingsRequest,
    OnboardingRequest,
    WhatsAppConnectCompleteRequest,
)
from services.business_service import (
    get_business_for_user,
    save_onboarding,
    serialize_business,
    update_business_settings,
)
from services.embedded_signup_service import (
    EmbeddedSignupError,
    complete_embedded_signup,
    disconnect_whatsapp,
    get_connect_config,
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


def _raise_embedded_http(error: EmbeddedSignupError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error.message,
    ) from error


@router.get("/whatsapp/connect-config")
def get_whatsapp_connect_config(
    current_user: User = Depends(get_current_user),
):
    return {
        "success": True,
        **get_connect_config(),
    }


@router.post("/whatsapp/connect/complete")
def complete_whatsapp_connection(
    payload: WhatsAppConnectCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        business = complete_embedded_signup(
            db,
            user_id=current_user.id,
            code=payload.code,
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
        )
    except EmbeddedSignupError as error:
        _raise_embedded_http(error)

    return {
        "success": True,
        "message": "WhatsApp connected.",
        "business": serialize_business(business),
    }


@router.post("/whatsapp/disconnect")
def disconnect_whatsapp_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        business = disconnect_whatsapp(db, user_id=current_user.id)
    except EmbeddedSignupError as error:
        _raise_embedded_http(error)

    return {
        "success": True,
        "message": "WhatsApp disconnected.",
        "business": serialize_business(business),
    }
