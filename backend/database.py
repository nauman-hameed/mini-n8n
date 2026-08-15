from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "storage" / "app.db"


def normalize_database_url(url: str | None) -> str:
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    cleaned = url.strip()

    if cleaned.startswith("postgres://"):
        cleaned = cleaned.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1,
        )
    elif cleaned.startswith("postgresql://") and "+psycopg2" not in cleaned:
        cleaned = cleaned.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1,
        )

    return cleaned


database_url = normalize_database_url(DATABASE_URL)
is_sqlite = database_url.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine_kwargs = {
    "connect_args": connect_args,
}

if not is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    from models import business, order, user, whatsapp_credential  # noqa: F401
    from services.schema_migration import migrate_schema

    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
