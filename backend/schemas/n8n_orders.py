from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class N8nOrderItemIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=255)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(default=Decimal("0"), alias="unitPrice", ge=0)


class N8nCreateOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    business_id: str = Field(alias="businessId", min_length=1)
    customer_phone: str = Field(alias="customerPhone", min_length=1, max_length=32)
    customer_name: str = Field(alias="customerName", min_length=1, max_length=160)
    notes: str = Field(default="", max_length=4000)
    wa_message_id: str | None = Field(default=None, alias="waMessageId", max_length=128)
    items: list[N8nOrderItemIn] = Field(min_length=1)

    @field_validator("customer_phone", "customer_name", "notes", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("wa_message_id", mode="before")
    @classmethod
    def empty_wa_to_none(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class N8nUpdateOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_id: str = Field(alias="orderId", min_length=1)
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip().upper()

        if cleaned not in {"CONFIRMED", "CANCELLED"}:
            raise ValueError("status must be CONFIRMED or CANCELLED.")

        return cleaned


class N8nShipOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    courier: str = Field(default="", max_length=120)
    tracking_number: str = Field(default="", alias="trackingNumber", max_length=120)
    shipment_date: datetime = Field(alias="shipmentDate")

    @field_validator("status")
    @classmethod
    def validate_ship_status(cls, value: str) -> str:
        cleaned = value.strip().upper()

        if cleaned != "SHIPPED":
            raise ValueError("status must be SHIPPED.")

        return cleaned

    @field_validator("courier", "tracking_number", mode="before")
    @classmethod
    def strip_optional(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value
