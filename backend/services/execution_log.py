from datetime import datetime, timezone
import json
from pathlib import Path

LOG_FILE = (
    Path(__file__).resolve().parent.parent
    / "storage"
    / "last_webhook_run.json"
)

LAST_WEBHOOK_RUN: dict = {
    "status": "idle",
    "from_phone": "",
    "message_preview": "",
    "error": "",
    "finished_at": "",
}


def _persist_log() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(
        json.dumps(LAST_WEBHOOK_RUN, indent=2),
        encoding="utf-8",
    )


def load_last_webhook_run() -> dict:
    if LOG_FILE.exists():
        try:
            return json.loads(
                LOG_FILE.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError:
            pass

    return LAST_WEBHOOK_RUN.copy()


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
    _persist_log(    )
    _persist_log()


def record_webhook_success() -> None:
    LAST_WEBHOOK_RUN.update(
        {
            "status": "success",
            "error": "",
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _persist_log()


def record_webhook_error(error: str) -> None:
    LAST_WEBHOOK_RUN.update(
        {
            "status": "error",
            "error": error,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _persist_log()
