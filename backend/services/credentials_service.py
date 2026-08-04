import json
from pathlib import Path

from cryptography.fernet import Fernet

from config import CREDENTIAL_ENCRYPTION_KEY


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_FILE = BASE_DIR / "storage" / "credentials.json"


def _get_cipher() -> Fernet:
    if not CREDENTIAL_ENCRYPTION_KEY:
        raise ValueError(
            "CREDENTIAL_ENCRYPTION_KEY is missing in backend/.env."
        )

    try:
        return Fernet(
            CREDENTIAL_ENCRYPTION_KEY.encode("utf-8")
        )
    except Exception as error:
        raise ValueError(
            "CREDENTIAL_ENCRYPTION_KEY is invalid."
        ) from error


def save_credentials(credentials: dict) -> None:
    cipher = _get_cipher()

    raw_data = json.dumps(
        credentials
    ).encode("utf-8")

    encrypted_data = cipher.encrypt(raw_data)

    STORAGE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    STORAGE_FILE.write_text(
        encrypted_data.decode("utf-8"),
        encoding="utf-8",
    )


def load_credentials() -> dict:
    if not STORAGE_FILE.exists():
        return {}

    encrypted_text = STORAGE_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not encrypted_text:
        return {}

    cipher = _get_cipher()

    try:
        decrypted_data = cipher.decrypt(
            encrypted_text.encode("utf-8")
        )

    except Exception as error:
        raise ValueError(
            "Stored credentials could not be decrypted."
        ) from error

    try:
        return json.loads(
            decrypted_data.decode("utf-8")
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            "Stored credentials contain invalid JSON."
        ) from error