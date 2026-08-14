import secrets

from fastapi import Header, HTTPException, status

from config import N8N_CALLBACK_SECRET, N8N_INTERNAL_TOKEN


def require_n8n_secret(
    x_n8n_secret: str | None = Header(default=None, alias="x-n8n-secret"),
) -> None:
    if not N8N_CALLBACK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="n8n callback authentication is not configured.",
        )

    if not x_n8n_secret or not secrets.compare_digest(
        x_n8n_secret,
        N8N_CALLBACK_SECRET,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing n8n credentials.",
        )


def require_n8n_bearer(
    authorization: str | None = Header(default=None),
) -> None:
    if not N8N_INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="n8n internal authentication is not configured.",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing n8n credentials.",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token or not secrets.compare_digest(token, N8N_INTERNAL_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing n8n credentials.",
        )
