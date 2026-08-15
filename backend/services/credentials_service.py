import json
from pathlib import Path

from cryptography.fernet import Fernet

from config import CREDENTIAL_ENCRYPTION_KEY


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_FILE = BASE_DIR / "storage" / "credentials.json"


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a short secret for database storage using CREDENTIAL_ENCRYPTION_KEY."""
    if not isinstance(plaintext, str) or not plaintext:
        raise ValueError("Secret plaintext is required.")

    encrypted = _get_cipher().encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a Fernet secret stored by encrypt_secret()."""
    if not isinstance(ciphertext, str) or not ciphertext.strip():
        raise ValueError("Secret ciphertext is required.")

    try:
        decrypted = _get_cipher().decrypt(ciphertext.encode("utf-8"))
    except Exception as error:
        raise ValueError("Stored secret could not be decrypted.") from error

    return decrypted.decode("utf-8")


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