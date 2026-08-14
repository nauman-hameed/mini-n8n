from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


ORDER_STATUS_PENDING = "PENDING"
ORDER_STATUS_CONFIRMED = "CONFIRMED"
ORDER_STATUS_CANCELLED = "CANCELLED"
ORDER_STATUS_SHIPPED = "SHIPPED"

ORDER_STATUSES = {
    ORDER_STATUS_PENDING,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_SHIPPED,
}

ALLOWED_TRANSITIONS = {
    ORDER_STATUS_PENDING: {
        ORDER_STATUS_CONFIRMED,
        ORDER_STATUS_CANCELLED,
    },
    ORDER_STATUS_CONFIRMED: {
        ORDER_STATUS_SHIPPED,
    },
}


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "wa_message_id",
            name="uq_orders_business_wa_message",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    wa_message_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=ORDER_STATUS_PENDING,
        nullable=False,
        index=True,
    )
    courier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    shipment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    business = relationship("Business", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    order = relationship("Order", back_populates="items")
