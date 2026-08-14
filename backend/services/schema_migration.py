"""Idempotent schema migration for n8n order integration."""

from __future__ import annotations

from sqlalchemy import inspect, text


def migrate_orders_schema(engine) -> None:
    from database import Base
    from models import business, order, user  # noqa: F401

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "businesses" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("businesses")}

    if "whatsapp_phone_number_id" in columns:
        return

    dialect = engine.dialect.name

    with engine.begin() as connection:
        if dialect == "postgresql":
            connection.execute(
                text(
                    "ALTER TABLE businesses "
                    "ADD COLUMN IF NOT EXISTS whatsapp_phone_number_id "
                    "VARCHAR(64)"
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "ix_businesses_whatsapp_phone_number_id "
                    "ON businesses (whatsapp_phone_number_id)"
                )
            )
        else:
            connection.execute(
                text(
                    "ALTER TABLE businesses "
                    "ADD COLUMN whatsapp_phone_number_id VARCHAR(64)"
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    "ix_businesses_whatsapp_phone_number_id "
                    "ON businesses (whatsapp_phone_number_id)"
                )
            )
