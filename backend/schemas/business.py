import re

from pydantic import BaseModel, Field, field_validator


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


class BusinessResponse(BaseModel):
    id: int
    business_name: str
    whatsapp_number: str
    onboarding_completed: bool
