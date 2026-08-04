import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = BASE_DIR / "storage" / "workflow.json"
DEFAULT_WORKFLOW_FILE = BASE_DIR / "data" / "default_workflow.json"


def _seed_default_workflow_if_needed() -> None:
    if WORKFLOW_FILE.exists():
        return

    if not DEFAULT_WORKFLOW_FILE.exists():
        return

    WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_FILE.write_text(
        DEFAULT_WORKFLOW_FILE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def save_workflow(workflow: dict) -> None:
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    WORKFLOW_FILE.write_text(
        json.dumps(
            {
                "nodes": nodes,
                "edges": edges,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_workflow() -> dict | None:
    _seed_default_workflow_if_needed()

    if not WORKFLOW_FILE.exists():
        return None

    try:
        data = json.loads(
            WORKFLOW_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "Saved workflow contains invalid JSON."
        ) from error

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not nodes:
        return None

    return {
        "nodes": nodes,
        "edges": edges,
    }
