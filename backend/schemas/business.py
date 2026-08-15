import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


WHATSAPP_NUMBER_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class OnboardingRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=160)
    whatsapp_number: str = Field(min_length=8, max_length=32)

    @field_validator("business_name")
    @classmethod
    def validate_business_name(cls, value: str) -> str:
        cleaned = value.strip()

        if len(cleaned) < 2:
            raise ValueError("Business name must be at least 2 characters.")

        return cleaned

    @field_validator("whatsapp_number")
    @classmethod
    def validate_whatsapp_number(cls, value: str) -> str:
        cleaned = value.strip().replace(" ", "").replace("-", "")

        if not WHATSAPP_NUMBER_PATTERN.match(cleaned):
            raise ValueError(
                "Enter a valid WhatsApp number with country code, e.g. +923001234567."
            )

        return cleaned


class BusinessSettingsRequest(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=160)
    whatsapp_number: str | None = Field(default=None, min_length=8, max_length=32)
    whatsapp_phone_number_id: str | None = Field(default=None, max_length=64)

    @field_validator("business_name")
    @classmethod
    def validate_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if len(cleaned) < 2:
            raise ValueError("Business name must be at least 2 characters.")

        return cleaned

    @field_validator("whatsapp_number")
    @classmethod
    def validate_optional_whatsapp(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().replace(" ", "").replace("-", "")

        if not WHATSAPP_NUMBER_PATTERN.match(cleaned):
            raise ValueError(
                "Enter a valid WhatsApp number with country code, e.g. +923001234567."
            )

        return cleaned

    @field_validator("whatsapp_phone_number_id")
    @classmethod
    def validate_optional_phone_id(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        if not cleaned.isdigit() or len(cleaned) > 64:
            raise ValueError("Meta Phone Number ID must be digits only.")

        return cleaned


class BusinessResponse(BaseModel):
    id: int
    business_name: str
    whatsapp_number: str
    onboarding_completed: bool
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_display_phone_number: str | None = None
    whatsapp_connection_status: str = "disconnected"
    whatsapp_connection_type: str | None = None
    whatsapp_connected_at: str | None = None
    whatsapp_disconnected_at: str | None = None
    whatsapp_connection_error: str | None = None
    whatsapp_connected: bool = False
    assistant_active: bool = False


class WhatsAppConnectCompleteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(min_length=8, max_length=500)
    waba_id: str = Field(alias="wabaId", min_length=5, max_length=64)
    phone_number_id: str = Field(alias="phoneNumberId", min_length=5, max_length=64)

    @field_validator("code", "waba_id", "phone_number_id")
    @classmethod
    def strip_connect_fields(cls, value: str) -> str:
        return value.strip()
