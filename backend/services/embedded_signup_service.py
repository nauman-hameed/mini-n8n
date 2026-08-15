"""Official Meta Embedded Signup completion for Tech Provider tenants.

Authorization codes and access tokens are never logged or returned to React.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import (
    CREDENTIAL_ENCRYPTION_KEY,
    META_API_VERSION,
    META_APP_ID,
    META_APP_SECRET,
    META_EMBEDDED_SIGNUP_CONFIG_ID,
)
from models.business import (
    WHATSAPP_CONNECTION_CONNECTED,
    WHATSAPP_CONNECTION_CONNECTING,
    WHATSAPP_CONNECTION_DISCONNECTED,
    WHATSAPP_CONNECTION_ERROR,
    WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP,
    WHATSAPP_CONNECTION_TYPE_LEGACY,
    Business,
)
from services.business_service import get_business_for_user
from services.whatsapp_credential_service import (
    delete_whatsapp_secrets,
    load_whatsapp_access_token,
    store_whatsapp_secrets,
)
from services.whatsapp_graph import (
    GRAPH_TIMEOUT_SECONDS,
    _get_graph_json,
    _graph_url,
    _post_graph_json,
    sanitize_meta_error_message,
)


class EmbeddedSignupError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "embedded_signup_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


ALREADY_REGISTERED_MARKERS = (
    "already registered",
    "already been registered",
    "#133016",
    "(#133016)",
)


def embedded_signup_enabled() -> bool:
    return bool(
        META_APP_ID
        and META_EMBEDDED_SIGNUP_CONFIG_ID
        and META_APP_SECRET
        and CREDENTIAL_ENCRYPTION_KEY
    )


def get_connect_config() -> dict:
    if not embedded_signup_enabled():
        return {"enabled": False}

    return {
        "enabled": True,
        "appId": META_APP_ID,
        "configId": META_EMBEDDED_SIGNUP_CONFIG_ID,
        "graphVersion": (META_API_VERSION or "v23.0").strip(),
    }


def complete_embedded_signup(
    db: Session,
    *,
    user_id: int,
    code: str,
    waba_id: str,
    phone_number_id: str,
) -> Business:
    business = get_business_for_user(db, user_id)
    if not business:
        raise EmbeddedSignupError("Business not found.", status_code=404)

    if business.whatsapp_connection_type == WHATSAPP_CONNECTION_TYPE_LEGACY:
        raise EmbeddedSignupError(
            "This WhatsApp number is already connected. Embedded Signup "
            "migration is not available yet.",
            status_code=409,
            code="legacy_locked",
        )

    if not embedded_signup_enabled():
        raise EmbeddedSignupError(
            "WhatsApp connection is not available yet.",
            status_code=503,
            code="not_configured",
        )

    cleaned_code = (code or "").strip()
    cleaned_waba = (waba_id or "").strip()
    cleaned_phone = (phone_number_id or "").strip()

    if not cleaned_code or not cleaned_waba or not cleaned_phone:
        raise EmbeddedSignupError(
            "WhatsApp authorization details are incomplete. Please try again."
        )

    if not cleaned_waba.isdigit() or not cleaned_phone.isdigit():
        raise EmbeddedSignupError(
            "WhatsApp could not verify this business number."
        )

    previous = {
        "status": business.whatsapp_connection_status,
        "error": business.whatsapp_connection_error,
        "type": business.whatsapp_connection_type,
        "waba": business.whatsapp_business_account_id,
        "phone": business.whatsapp_phone_number_id,
        "display": business.whatsapp_display_phone_number,
        "connected_at": business.whatsapp_connected_at,
    }

    _set_connecting(db, business)

    subscribed = False
    access_token = None

    try:
        token_payload = exchange_embedded_signup_code(cleaned_code)
        access_token = token_payload["access_token"]
        expires_in = token_payload.get("expires_in")

        phone_meta = fetch_phone_metadata(access_token, cleaned_phone)
        waba_phone_ids = list_waba_phone_ids(access_token, cleaned_waba)

        if str(phone_meta.get("id") or "").strip() != cleaned_phone:
            raise EmbeddedSignupError(
                "WhatsApp could not verify this business number.",
                code="id_mismatch",
            )

        if cleaned_phone not in waba_phone_ids:
            raise EmbeddedSignupError(
                "WhatsApp could not verify this business number.",
                code="id_mismatch",
            )

        _reject_duplicate_phone(db, business.id, cleaned_phone)

        subscribe_app_to_waba(access_token, cleaned_waba)
        subscribed = True

        two_step_pin = None
        if not _phone_already_registered(phone_meta):
            two_step_pin = generate_two_step_pin()
            register_phone_number(access_token, cleaned_phone, two_step_pin)

        expires_at = None
        if isinstance(expires_in, int) and expires_in > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        display = str(phone_meta.get("display_phone_number") or "").strip() or None
        if display and not display.startswith("+"):
            digits = "".join(ch for ch in display if ch.isdigit())
            display = f"+{digits}" if digits else display

        store_whatsapp_secrets(
            db,
            business_id=business.id,
            access_token=access_token,
            two_step_pin=two_step_pin,
            token_expires_at=expires_at,
            commit=False,
        )

        business.whatsapp_business_account_id = cleaned_waba
        business.whatsapp_phone_number_id = cleaned_phone
        business.whatsapp_display_phone_number = display or business.whatsapp_number
        business.whatsapp_connection_status = WHATSAPP_CONNECTION_CONNECTED
        business.whatsapp_connection_type = WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP
        business.whatsapp_connected_at = datetime.utcnow()
        business.whatsapp_disconnected_at = None
        business.whatsapp_connection_error = None
        db.commit()
        db.refresh(business)
        return business

    except EmbeddedSignupError as error:
        _rollback_incomplete_connection(
            db,
            business,
            access_token=access_token,
            waba_id=cleaned_waba,
            subscribed=subscribed,
            previous=previous,
            message=error.message,
        )
        raise
    except IntegrityError:
        _rollback_incomplete_connection(
            db,
            business,
            access_token=access_token,
            waba_id=cleaned_waba,
            subscribed=subscribed,
            previous=previous,
            message="This WhatsApp number is already connected to another account.",
        )
        raise EmbeddedSignupError(
            "This WhatsApp number is already connected to another account.",
            status_code=409,
            code="duplicate_phone",
        )
    except Exception:
        _rollback_incomplete_connection(
            db,
            business,
            access_token=access_token,
            waba_id=cleaned_waba,
            subscribed=subscribed,
            previous=previous,
            message="Could not complete WhatsApp connection. Please try again.",
        )
        raise EmbeddedSignupError(
            "Could not complete WhatsApp connection. Please try again.",
            status_code=502,
        )


def disconnect_whatsapp(db: Session, *, user_id: int) -> Business:
    business = get_business_for_user(db, user_id)
    if not business:
        raise EmbeddedSignupError("Business not found.", status_code=404)

    if business.whatsapp_connection_type == WHATSAPP_CONNECTION_TYPE_LEGACY:
        raise EmbeddedSignupError(
            "This WhatsApp number is managed as a legacy connection and cannot "
            "be disconnected here.",
            status_code=409,
            code="legacy_locked",
        )

    token = None
    waba_id = (business.whatsapp_business_account_id or "").strip()
    try:
        token = load_whatsapp_access_token(db, business.id)
    except Exception:
        token = None

    if token and waba_id:
        unsubscribe_app_from_waba(token, waba_id)

    delete_whatsapp_secrets(db, business.id, commit=False)
    business.whatsapp_phone_number_id = None
    business.whatsapp_business_account_id = None
    business.whatsapp_display_phone_number = None
    business.whatsapp_connection_status = WHATSAPP_CONNECTION_DISCONNECTED
    business.whatsapp_connection_type = None
    business.whatsapp_connection_error = None
    business.whatsapp_disconnected_at = datetime.utcnow()
    db.commit()
    db.refresh(business)
    return business


def exchange_embedded_signup_code(code: str) -> dict:
    url = _graph_url("oauth", "access_token")

    try:
        # POST form body so the short-lived code is not placed in the URL.
        # Never log this request body, the code, or the returned token.
        response = requests.post(
            url,
            data={
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "code": code,
            },
            timeout=GRAPH_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise EmbeddedSignupError(
            "WhatsApp authorization expired. Please try connecting again.",
            status_code=502,
            code="code_exchange_failed",
        ) from error

    payload = {}
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if not response.ok or not isinstance(payload, dict):
        raise EmbeddedSignupError(
            "WhatsApp authorization expired. Please try connecting again.",
            status_code=400,
            code="invalid_code",
        )

    access_token = str(payload.get("access_token") or "").strip()
    if not access_token:
        raise EmbeddedSignupError(
            "WhatsApp authorization expired. Please try connecting again.",
            status_code=400,
            code="invalid_code",
        )

    expires_in = payload.get("expires_in")
    if expires_in is not None:
        try:
            expires_in = int(expires_in)
        except (TypeError, ValueError):
            expires_in = None

    return {
        "access_token": access_token,
        "expires_in": expires_in,
    }


def fetch_phone_metadata(access_token: str, phone_number_id: str) -> dict:
    url = _graph_url(phone_number_id)
    url = (
        f"{url}?fields=id,display_phone_number,verified_name,"
        "code_verification_status,platform_type"
    )
    data, status_code = _get_graph_json(url, access_token)
    if status_code >= 400:
        raise EmbeddedSignupError(
            "WhatsApp could not verify this business number.",
            status_code=502,
            code="phone_lookup_failed",
        )
    return data


def list_waba_phone_ids(access_token: str, waba_id: str) -> set[str]:
    url = _graph_url(waba_id, "phone_numbers")
    data, status_code = _get_graph_json(url, access_token)
    if status_code >= 400:
        raise EmbeddedSignupError(
            "WhatsApp could not verify this business number.",
            status_code=502,
            code="waba_lookup_failed",
        )

    ids: set[str] = set()
    for item in data.get("data") or []:
        if isinstance(item, dict) and item.get("id"):
            ids.add(str(item["id"]).strip())
    return ids


def subscribe_app_to_waba(access_token: str, waba_id: str) -> None:
    url = _graph_url(waba_id, "subscribed_apps")
    data, status_code = _post_graph_json(url, access_token, {})
    if status_code >= 400:
        raise EmbeddedSignupError(
            "Could not finish WhatsApp setup. Please try again.",
            status_code=502,
            code="subscribe_failed",
        )
    if isinstance(data, dict) and data.get("error"):
        raise EmbeddedSignupError(
            "Could not finish WhatsApp setup. Please try again.",
            status_code=502,
            code="subscribe_failed",
        )


def register_phone_number(access_token: str, phone_number_id: str, pin: str) -> None:
    url = _graph_url(phone_number_id, "register")
    data, status_code = _post_graph_json(
        url,
        access_token,
        {
            "messaging_product": "whatsapp",
            "pin": pin,
        },
    )
    if status_code < 400:
        return

    message = sanitize_meta_error_message(data).lower()
    if any(marker in message for marker in ALREADY_REGISTERED_MARKERS):
        return

    raise EmbeddedSignupError(
        "Could not finish WhatsApp setup. Please try again.",
        status_code=502,
        code="register_failed",
    )


def unsubscribe_app_from_waba(access_token: str, waba_id: str) -> None:
    url = _graph_url(waba_id, "subscribed_apps")
    try:
        requests.delete(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=GRAPH_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        return


def generate_two_step_pin() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _phone_already_registered(phone_meta: dict) -> bool:
    platform = str(phone_meta.get("platform_type") or "").strip().upper()
    return platform == "CLOUD_API"


def _reject_duplicate_phone(db: Session, business_id: int, phone_number_id: str) -> None:
    duplicate = (
        db.query(Business)
        .filter(
            Business.whatsapp_phone_number_id == phone_number_id,
            Business.id != business_id,
        )
        .first()
    )
    if duplicate:
        raise EmbeddedSignupError(
            "This WhatsApp number is already connected to another account.",
            status_code=409,
            code="duplicate_phone",
        )


def _set_connecting(db: Session, business: Business) -> None:
    business.whatsapp_connection_status = WHATSAPP_CONNECTION_CONNECTING
    business.whatsapp_connection_error = None
    db.commit()
    db.refresh(business)


def _rollback_incomplete_connection(
    db: Session,
    business: Business,
    *,
    access_token: str | None,
    waba_id: str,
    subscribed: bool,
    previous: dict,
    message: str,
) -> None:
    """Do not persist a half-valid token as connected.

    If POST /{wabaId}/subscribed_apps succeeded and a later step failed
    (register or storage), best-effort DELETE /{wabaId}/subscribed_apps.
    Retry Connect to subscribe again. Phone registration is skipped when
    Meta reports platform_type=CLOUD_API, so a prior Cloud API
    registration is left intact.
    """
    try:
        db.rollback()
    except Exception:
        pass

    if subscribed and access_token and waba_id:
        unsubscribe_app_from_waba(access_token, waba_id)

    fresh = (
        db.query(Business)
        .filter(Business.id == business.id)
        .first()
    )
    if not fresh:
        return

    if fresh.whatsapp_connection_type == WHATSAPP_CONNECTION_TYPE_LEGACY:
        return

    if previous.get("status") == WHATSAPP_CONNECTION_CONNECTED:
        fresh.whatsapp_connection_status = WHATSAPP_CONNECTION_CONNECTED
        fresh.whatsapp_connection_error = None
        fresh.whatsapp_connection_type = previous.get("type")
        fresh.whatsapp_business_account_id = previous.get("waba")
        fresh.whatsapp_phone_number_id = previous.get("phone")
        fresh.whatsapp_display_phone_number = previous.get("display")
        fresh.whatsapp_connected_at = previous.get("connected_at")
        try:
            db.commit()
        except Exception:
            db.rollback()
        return

    delete_whatsapp_secrets(db, fresh.id, commit=False)
    fresh.whatsapp_connection_status = WHATSAPP_CONNECTION_ERROR
    fresh.whatsapp_connection_error = message[:500]
    try:
        db.commit()
    except Exception:
        db.rollback()
