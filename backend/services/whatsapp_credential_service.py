"""Store and retrieve per-business WhatsApp Cloud API secrets.

Reuses CREDENTIAL_ENCRYPTION_KEY (Fernet) already used for editor
credentials.json. No new encryption key: tokens and PINs are encrypted
field-by-field for the whatsapp_credentials table.

Never include ciphertext or plaintext secrets in API payloads.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models.whatsapp_credential import WhatsAppCredential
from services.credentials_service import decrypt_secret, encrypt_secret


def get_whatsapp_credential(
    db: Session,
    business_id: int,
) -> WhatsAppCredential | None:
    return (
        db.query(WhatsAppCredential)
        .filter(WhatsAppCredential.business_id == business_id)
        .first()
    )


def store_whatsapp_secrets(
    db: Session,
    *,
    business_id: int,
    access_token: str,
    two_step_pin: str | None = None,
    token_expires_at: datetime | None = None,
    commit: bool = True,
) -> WhatsAppCredential:
    token = (access_token or "").strip()
    if not token:
        raise ValueError("WhatsApp access token is required.")

    pin = (two_step_pin or "").strip() or None
    encrypted_token = encrypt_secret(token)
    encrypted_pin = encrypt_secret(pin) if pin else None

    row = get_whatsapp_credential(db, business_id)

    if row:
        row.encrypted_access_token = encrypted_token
        row.encrypted_two_step_pin = encrypted_pin
        row.token_expires_at = token_expires_at
        row.last_refreshed_at = datetime.utcnow()
        row.updated_at = datetime.utcnow()
    else:
        row = WhatsAppCredential(
            business_id=business_id,
            encrypted_access_token=encrypted_token,
            encrypted_two_step_pin=encrypted_pin,
            token_expires_at=token_expires_at,
            last_refreshed_at=datetime.utcnow(),
        )
        db.add(row)

    if commit:
        db.commit()
        db.refresh(row)

    return row


def load_whatsapp_access_token(db: Session, business_id: int) -> str | None:
    row = get_whatsapp_credential(db, business_id)
    if not row:
        return None
    return decrypt_secret(row.encrypted_access_token)


def load_whatsapp_two_step_pin(db: Session, business_id: int) -> str | None:
    row = get_whatsapp_credential(db, business_id)
    if not row or not row.encrypted_two_step_pin:
        return None
    return decrypt_secret(row.encrypted_two_step_pin)


def delete_whatsapp_secrets(
    db: Session,
    business_id: int,
    *,
    commit: bool = True,
) -> None:
    row = get_whatsapp_credential(db, business_id)
    if not row:
        return
    db.delete(row)
    if commit:
        db.commit()
