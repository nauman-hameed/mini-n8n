from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY
from models.business import Business
from models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: int) -> str:
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY is missing in backend environment.")

    expires_at = datetime.utcnow() + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    if not JWT_SECRET_KEY:
        return None

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)
    except (JWTError, ValueError):
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email.strip().lower())
        .first()
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
) -> User:
    user = User(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def user_has_completed_onboarding(db: Session, user_id: int) -> bool:
    business = (
        db.query(Business)
        .filter(Business.user_id == user_id)
        .first()
    )

    return bool(business and business.onboarding_completed)


def serialize_user(db: Session, user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "onboarding_completed": user_has_completed_onboarding(
            db,
            user.id,
        ),
    }
