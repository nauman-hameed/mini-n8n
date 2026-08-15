from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


WHATSAPP_CONNECTION_DISCONNECTED = "disconnected"
WHATSAPP_CONNECTION_CONNECTING = "connecting"
WHATSAPP_CONNECTION_CONNECTED = "connected"
WHATSAPP_CONNECTION_EXPIRED = "expired"
WHATSAPP_CONNECTION_ERROR = "error"

WHATSAPP_CONNECTION_TYPE_LEGACY = "legacy"
WHATSAPP_CONNECTION_TYPE_EMBEDDED_SIGNUP = "embedded_signup"

LEGACY_CONNECTED_BUSINESS_ID = 2
LEGACY_CONNECTED_PHONE_NUMBER_ID = "1160990267106849"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    business_name: Mapped[str] = mapped_column(String(160), nullable=False)
    whatsapp_number: Mapped[str] = mapped_column(String(32), nullable=False)
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
    )
    whatsapp_business_account_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    whatsapp_display_phone_number: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    whatsapp_connection_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=WHATSAPP_CONNECTION_DISCONNECTED,
        server_default=WHATSAPP_CONNECTION_DISCONNECTED,
    )
    whatsapp_connection_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    whatsapp_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    whatsapp_disconnected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    whatsapp_connection_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
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

    user = relationship("User", back_populates="business")
    orders = relationship(
        "Order",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    whatsapp_credential = relationship(
        "WhatsAppCredential",
        back_populates="business",
        uselist=False,
        cascade="all, delete-orphan",
    )
