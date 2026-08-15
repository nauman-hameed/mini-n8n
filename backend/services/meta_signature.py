"""HMAC SHA-256 verification for Meta X-Hub-Signature-256."""

from __future__ import annotations

import hmac
from hashlib import sha256


def verify_meta_signature(
    *,
    raw_body: bytes,
    signature_header: str | None,
    app_secret: str,
) -> bool:
    if not app_secret:
        return False

    if not signature_header or not isinstance(signature_header, str):
        return False

    header = signature_header.strip()
    if not header.lower().startswith("sha256="):
        return False

    received = header.split("=", 1)[1].strip()
    if not received:
        return False

    expected = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, received)
