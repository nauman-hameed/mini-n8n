from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import AUTH_COOKIE_SECURE, AUTH_COOKIE_SAMESITE
from database import get_db
from dependencies.auth import AUTH_COOKIE_NAME, get_current_user
from models.user import User
from schemas.auth import AuthResponse, LoginRequest, SignupRequest
from services.auth_service import (
    create_access_token,
    create_user,
    get_user_by_email,
    serialize_user,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 7,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value="",
        max_age=0,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def _issue_auth_token(response: Response, user_id: int) -> None:
    try:
        token = create_access_token(user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    _set_auth_cookie(response, token)


@router.post("/signup", response_model=AuthResponse)
def signup(
    payload: SignupRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(db, payload.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        user = create_user(
            db,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None

    _issue_auth_token(response, user.id)

    return {
        "success": True,
        "user": serialize_user(db, user),
    }


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, payload.email)

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    _issue_auth_token(response, user.id)

    return {
        "success": True,
        "user": serialize_user(db, user),
    }


@router.post("/logout")
def logout(response: Response):
    _clear_auth_cookie(response)

    return {
        "success": True,
        "message": "Logged out successfully.",
    }


@router.get("/me", response_model=AuthResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "user": serialize_user(db, current_user),
    }
