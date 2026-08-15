from pydantic import BaseModel, ConfigDict, Field, field_validator


class WhatsAppSendRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    business_id: int = Field(alias="businessId")
    to: str = Field(min_length=6, max_length=32)
    message: dict

    @field_validator("to", mode="before")
    @classmethod
    def strip_to(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("message")
    @classmethod
    def require_message(cls, value):
        if not isinstance(value, dict) or not value:
            raise ValueError("message payload is required.")
        if not str(value.get("type") or "").strip():
            raise ValueError("message.type is required.")
        return value
