import re

import requests

from config import (
    META_ACCESS_TOKEN,
    META_API_VERSION,
    META_PHONE_NUMBER_ID,
)
from services.credentials_service import load_credentials


def get_meta_credentials() -> dict:
    stored = load_credentials()

    access_token = str(
        stored.get("metaAccessToken", "")
    ).strip() or str(META_ACCESS_TOKEN or "").strip()

    phone_number_id = str(
        stored.get("metaPhoneNumberId", "")
    ).strip() or str(META_PHONE_NUMBER_ID or "").strip()

    verify_token = str(
        stored.get("metaVerifyToken", "")
    ).strip()

    return {
        "access_token": access_token,
        "phone_number_id": phone_number_id,
        "verify_token": verify_token,
        "api_version": META_API_VERSION or "v23.0",
    }


def parse_incoming_messages(body: dict) -> list[dict]:
    if body.get("object") != "whatsapp_business_account":
        return []

    messages = []

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            if change.get("field") != "messages":
                continue

            metadata = value.get("metadata", {})
            phone_number_id = str(
                metadata.get("phone_number_id", "")
            ).strip()

            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue

                text_body = (
                    message.get("text", {}).get("body", "")
                ).strip()

                from_phone = str(
                    message.get("from", "")
                ).strip()

                if not text_body or not from_phone:
                    continue

                messages.append(
                    {
                        "from_phone": from_phone,
                        "message": text_body,
                        "message_id": str(
                            message.get("id", "")
                        ).strip(),
                        "phone_number_id": phone_number_id,
                    }
                )

    return messages


def render_reply_template(
    template: str,
    data: dict,
) -> str:
    placeholders = {
        "{{name}}": str(data.get("name", "")),
        "{{phone}}": str(
            data.get("phone", "")
            or data.get("from_phone", "")
        ),
        "{{address}}": str(data.get("address", "")),
        "{{items}}": str(data.get("items", "")),
    }

    rendered = template

    for key, value in placeholders.items():
        rendered = rendered.replace(key, value)

    return rendered.strip()


def send_whatsapp_text(
    to_phone: str,
    message: str,
    *,
    phone_number_id: str | None = None,
) -> dict:
    credentials = get_meta_credentials()

    access_token = credentials["access_token"]
    resolved_phone_number_id = (
        phone_number_id
        or credentials["phone_number_id"]
    )

    if not access_token:
        raise ValueError(
            "Meta Access Token is missing. "
            "Add it in Credentials."
        )

    if not resolved_phone_number_id:
        raise ValueError(
            "Meta Phone Number ID is missing. "
            "Add it in Credentials."
        )

    if not to_phone:
        raise ValueError(
            "Recipient phone number is missing."
        )

    if not message.strip():
        raise ValueError(
            "WhatsApp reply message is empty."
        )

    api_version = credentials["api_version"]
    url = (
        f"https://graph.facebook.com/{api_version}/"
        f"{resolved_phone_number_id}/messages"
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalize_phone_number(to_phone),
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message.strip(),
        },
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        response_data = response.json()

        if not response.ok:
            error_message = extract_meta_error(
                response_data
            )
            raise ValueError(error_message)

    except requests.RequestException as error:
        raise ValueError(
            f"Could not send WhatsApp message: {error}"
        ) from error

    message_id = (
        response_data.get("messages", [{}])[0].get("id", "")
    )

    return {
        "success": True,
        "message_id": message_id,
        "to": normalize_phone_number(to_phone),
    }


def extract_meta_error(response_data: dict) -> str:
    error = response_data.get("error", {})
    message = error.get("message", "Meta API request failed.")
    details = error.get("error_data", {}).get(
        "details",
        "",
    )

    if details:
        return f"{message} ({details})"

    return message


def normalize_phone_number(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)

    # Pakistan local format: 03XXXXXXXXX → 923XXXXXXXXX
    if digits.startswith("0") and len(digits) == 11:
        digits = "92" + digits[1:]

    return digits
