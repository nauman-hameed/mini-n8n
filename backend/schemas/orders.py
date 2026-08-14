from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    quantity: int
    unit_price: Decimal = Field(alias="unitPrice")


class OrderBusinessResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    whatsapp_number: str = Field(alias="whatsappNumber")


class OrderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    order_number: str = Field(alias="orderNumber")
    business_id: int = Field(alias="businessId")
    customer_phone: str = Field(alias="customerPhone")
    customer_name: str = Field(alias="customerName")
    notes: str
    wa_message_id: str | None = Field(default=None, alias="waMessageId")
    status: str
    courier: str | None = None
    tracking_number: str | None = Field(default=None, alias="trackingNumber")
    shipment_date: datetime | None = Field(default=None, alias="shipmentDate")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    items: list[OrderItemResponse] = Field(default_factory=list)
    business: OrderBusinessResponse | None = None
