from datetime import datetime, timezone

LAST_WEBHOOK_RUN: dict = {
    "status": "idle",
    "from_phone": "",
    "message_preview": "",
    "error": "",
    "finished_at": "",
}


def record_webhook_start(from_phone: str, message: str) -> None:
    LAST_WEBHOOK_RUN.update(
        {
            "status": "running",
            "from_phone": from_phone,
            "message_preview": message[:120],
            "error": "",
            "finished_at": "",
        }
    )


def record_webhook_success() -> None:
    LAST_WEBHOOK_RUN.update(
        {
            "status": "success",
            "error": "",
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def record_webhook_error(error: str) -> None:
    LAST_WEBHOOK_RUN.update(
        {
            "status": "error",
            "error": error,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )
