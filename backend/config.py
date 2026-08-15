from dotenv import load_dotenv
import os

load_dotenv()

APP_ENV = os.getenv("APP_ENV")

def _clean_env(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip().strip('"').strip("'")
    return cleaned or None


CREDENTIAL_ENCRYPTION_KEY = _clean_env(
    os.getenv("CREDENTIAL_ENCRYPTION_KEY")
)

FRONTEND_URL = _clean_env(os.getenv("FRONTEND_URL"))
if FRONTEND_URL:
    FRONTEND_URL = FRONTEND_URL.rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL")

_railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if not BACKEND_URL and _railway_domain:
    BACKEND_URL = f"https://{_railway_domain}"

ADMIN_PIN = os.getenv("ADMIN_PIN")

AI_PROVIDER = _clean_env(os.getenv("AI_PROVIDER")) or (
    "gemini"
    if os.getenv("RAILWAY_PUBLIC_DOMAIN")
    else None
)

if (
    os.getenv("RAILWAY_PUBLIC_DOMAIN")
    and AI_PROVIDER == "ollama"
):
    AI_PROVIDER = "gemini"
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = _clean_env(os.getenv("GEMINI_MODEL")) or "gemini-2.0-flash"

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN") or (
    "mini_n8n_verify_token"
    if os.getenv("RAILWAY_PUBLIC_DOMAIN")
    else ""
)
META_APP_SECRET = _clean_env(os.getenv("META_APP_SECRET"))
META_API_VERSION = os.getenv("META_API_VERSION", "v23.0")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_SPREADSHEET_ID = _clean_env(
    os.getenv("GOOGLE_SPREADSHEET_ID")
)
GOOGLE_TOKEN_JSON = os.getenv("GOOGLE_TOKEN_JSON")

JWT_SECRET_KEY = _clean_env(os.getenv("JWT_SECRET_KEY"))
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
)

DATABASE_URL = _clean_env(os.getenv("DATABASE_URL"))

# n8n → FastAPI integration (never expose these to the frontend)
N8N_CALLBACK_SECRET = _clean_env(os.getenv("N8N_CALLBACK_SECRET"))
N8N_INTERNAL_TOKEN = _clean_env(os.getenv("N8N_INTERNAL_TOKEN"))
N8N_WHATSAPP_WEBHOOK_URL = _clean_env(os.getenv("N8N_WHATSAPP_WEBHOOK_URL"))
N8N_WHATSAPP_WEBHOOK_SECRET = _clean_env(
    os.getenv("N8N_WHATSAPP_WEBHOOK_SECRET")
) or N8N_CALLBACK_SECRET
N8N_WHATSAPP_FORWARD_TIMEOUT_SECONDS = int(
    os.getenv("N8N_WHATSAPP_FORWARD_TIMEOUT_SECONDS", "8")
)

AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "").lower() in {
    "1",
    "true",
    "yes",
} or bool(os.getenv("RAILWAY_PUBLIC_DOMAIN"))

AUTH_COOKIE_SAMESITE = _clean_env(
    os.getenv("AUTH_COOKIE_SAMESITE")
) or "none" if AUTH_COOKIE_SECURE else "lax"