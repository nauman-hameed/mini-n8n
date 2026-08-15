"""Idempotent schema migrations for n8n orders and WhatsApp connection vault."""

from __future__ import annotations

from sqlalchemy import inspect, text

from models.business import (
    LEGACY_CONNECTED_BUSINESS_ID,
    LEGACY_CONNECTED_PHONE_NUMBER_ID,
    WHATSAPP_CONNECTION_CONNECTED,
    WHATSAPP_CONNECTION_DISCONNECTED,
    WHATSAPP_CONNECTION_TYPE_LEGACY,
)


WHATSAPP_CONNECTION_COLUMNS = (
    "whatsapp_business_account_id",
    "whatsapp_display_phone_number",
    "whatsapp_connection_status",
    "whatsapp_connection_type",
    "whatsapp_connected_at",
    "whatsapp_disconnected_at",
    "whatsapp_connection_error",
)


def migrate_schema(engine) -> None:
    migrate_orders_schema(engine)
    migrate_whatsapp_connection_schema(engine)


def migrate_orders_schema(engine) -> None:
    from database import Base
    from models import business, order, user, whatsapp_credential  # noqa: F401

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


def migrate_whatsapp_connection_schema(engine) -> None:
    from database import Base
    from models import business, order, user, whatsapp_credential  # noqa: F401

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "businesses" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("businesses")
    }
    dialect = engine.dialect.name

    with engine.begin() as connection:
        _add_whatsapp_connection_columns(
            connection,
            dialect=dialect,
            existing_columns=existing_columns,
        )
        _ensure_waba_index(connection, dialect=dialect)

    _backfill_legacy_connected_business(engine)


def rollback_whatsapp_connection_schema(engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "businesses" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("businesses")
    }
    dialect = engine.dialect.name

    with engine.begin() as connection:
        if "whatsapp_credentials" in table_names:
            connection.execute(text("DROP TABLE IF EXISTS whatsapp_credentials"))

        connection.execute(
            text("DROP INDEX IF EXISTS ix_businesses_whatsapp_business_account_id")
        )

        for column_name in WHATSAPP_CONNECTION_COLUMNS:
            if column_name not in existing_columns:
                continue

            if dialect == "postgresql":
                connection.execute(
                    text(
                        f"ALTER TABLE businesses DROP COLUMN IF EXISTS {column_name}"
                    )
                )
            else:
                connection.execute(
                    text(f"ALTER TABLE businesses DROP COLUMN {column_name}")
                )


def _add_whatsapp_connection_columns(
    connection,
    *,
    dialect: str,
    existing_columns: set[str],
) -> None:
    column_sql = {
        "whatsapp_business_account_id": "VARCHAR(64)",
        "whatsapp_display_phone_number": "VARCHAR(32)",
        "whatsapp_connection_status": (
            f"VARCHAR(32) NOT NULL DEFAULT '{WHATSAPP_CONNECTION_DISCONNECTED}'"
        ),
        "whatsapp_connection_type": "VARCHAR(32)",
        "whatsapp_connected_at": "TIMESTAMP",
        "whatsapp_disconnected_at": "TIMESTAMP",
        "whatsapp_connection_error": "VARCHAR(500)",
    }

    for column_name in WHATSAPP_CONNECTION_COLUMNS:
        if column_name in existing_columns:
            continue

        definition = column_sql[column_name]

        if dialect == "postgresql":
            connection.execute(
                text(
                    "ALTER TABLE businesses "
                    f"ADD COLUMN IF NOT EXISTS {column_name} {definition}"
                )
            )
        else:
            connection.execute(
                text(
                    "ALTER TABLE businesses "
                    f"ADD COLUMN {column_name} {definition}"
                )
            )


def _ensure_waba_index(connection, *, dialect: str) -> None:
    if dialect == "postgresql":
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_businesses_whatsapp_business_account_id "
                "ON businesses (whatsapp_business_account_id)"
            )
        )
        return

    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS "
            "ix_businesses_whatsapp_business_account_id "
            "ON businesses (whatsapp_business_account_id)"
        )
    )


def _backfill_legacy_connected_business(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE businesses
                SET
                    whatsapp_connection_status = :status,
                    whatsapp_connection_type = :connection_type,
                    whatsapp_connected_at = COALESCE(
                        whatsapp_connected_at,
                        updated_at,
                        created_at
                    ),
                    whatsapp_display_phone_number = COALESCE(
                        whatsapp_display_phone_number,
                        whatsapp_number
                    ),
                    whatsapp_connection_error = NULL
                WHERE id = :business_id
                  AND whatsapp_phone_number_id = :phone_number_id
                """
            ),
            {
                "status": WHATSAPP_CONNECTION_CONNECTED,
                "connection_type": WHATSAPP_CONNECTION_TYPE_LEGACY,
                "business_id": LEGACY_CONNECTED_BUSINESS_ID,
                "phone_number_id": LEGACY_CONNECTED_PHONE_NUMBER_ID,
            },
        )
