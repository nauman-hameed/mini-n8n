#!/usr/bin/env python3
"""
Push local env vars to Railway and trigger redeploy.

Requires one of:
  - RAILWAY_TOKEN env var (from railway.app/account/tokens)
  - Railway CLI logged in (`railway login`)

Usage:
  RAILWAY_TOKEN=xxx python scripts/push_railway_env.py
  # or after `railway login`:
  python scripts/push_railway_env.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"
PROJECT_NAME = os.getenv("RAILWAY_PROJECT_NAME", "brave-spirit")
SERVICE_NAME = os.getenv("RAILWAY_SERVICE_NAME", "mini-n8n")


def load_variables() -> dict[str, str]:
    sys.path.insert(0, str(BASE_DIR))

    from scripts.export_railway_env import main as export_main  # noqa: WPS433

    # Reuse export logic inline
    from services.credentials_service import load_credentials

    credentials = load_credentials()
    token_file = BASE_DIR / "tokens" / "google_token.json"

    variables = {
        "META_VERIFY_TOKEN": credentials.get("metaVerifyToken")
        or "mini_n8n_verify_token",
        "META_ACCESS_TOKEN": credentials.get("metaAccessToken", ""),
        "META_PHONE_NUMBER_ID": credentials.get("metaPhoneNumberId", ""),
        "GEMINI_API_KEY": credentials.get("geminiApiKey", ""),
        "AI_PROVIDER": "gemini",
        "CREDENTIAL_ENCRYPTION_KEY": "Ezv8xSACZVdpW3yCnhW9A4YO7rxH2a6h2Js3Aro7bFw=",
        "FRONTEND_URL": "https://mini-n8n-gilt.vercel.app",
        "GOOGLE_SPREADSHEET_ID": credentials.get(
            "googleSpreadsheetId",
            "",
        ),
        "META_API_VERSION": "v23.0",
        "APP_ENV": "production",
    }

    if token_file.exists():
        variables["GOOGLE_TOKEN_JSON"] = token_file.read_text(
            encoding="utf-8"
        ).strip()

    missing = [key for key, value in variables.items() if not str(value).strip()]

    if missing:
        print("ERROR: Missing local values for:", ", ".join(missing))
        sys.exit(1)

    return variables


def graphql(token: str, query: str, variables: dict | None = None) -> dict:
    response = requests.post(
        GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))

    return payload["data"]


def push_with_api(token: str, variables: dict[str, str]) -> None:
    projects = graphql(
        token,
        """
        query {
          projects {
            edges {
              node {
                id
                name
                services {
                  edges {
                    node {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """,
    )

    project_id = None
    service_id = None

    for edge in projects["projects"]["edges"]:
        node = edge["node"]
        if node["name"] != PROJECT_NAME:
            continue

        project_id = node["id"]

        for service_edge in node["services"]["edges"]:
            service_node = service_edge["node"]
            if service_node["name"] == SERVICE_NAME:
                service_id = service_node["id"]
                break

    if not project_id or not service_id:
        raise RuntimeError(
            f"Could not find project '{PROJECT_NAME}' "
            f"or service '{SERVICE_NAME}'."
        )

    print(f"Project: {PROJECT_NAME} ({project_id})")
    print(f"Service: {SERVICE_NAME} ({service_id})")

    for key, value in variables.items():
        graphql(
            token,
            """
            mutation variableUpsert($input: VariableUpsertInput!) {
              variableUpsert(input: $input)
            }
            """,
            {
                "input": {
                    "projectId": project_id,
                    "serviceId": service_id,
                    "name": key,
                    "value": value,
                }
            },
        )
        print(f"  set {key}")

    graphql(
        token,
        """
        mutation serviceInstanceDeploy($serviceId: String!) {
          serviceInstanceDeploy(serviceId: $serviceId)
        }
        """,
        {"serviceId": service_id},
    )
    print("Deploy triggered.")


def cli_command() -> list[str]:
    return ["npx", "@railway/cli"]


def push_with_cli(variables: dict[str, str]) -> None:
    cli = cli_command()

    for key, value in variables.items():
        subprocess.run(
            [*cli, "variables", "set", f"{key}={value}"],
            check=True,
            cwd=BASE_DIR,
        )
        print(f"  set {key}")

    subprocess.run(
        [*cli, "up", "--detach"],
        check=True,
        cwd=BASE_DIR,
    )
    print("Deploy triggered.")


def main() -> int:
    variables = load_variables()
    token = os.getenv("RAILWAY_TOKEN", "").strip()

    print(f"Pushing {len(variables)} variables to Railway...")

    if token:
        push_with_api(token, variables)
        return 0

    if subprocess.run(
        [*cli_command(), "whoami"],
        capture_output=True,
        text=True,
    ).returncode == 0:
        push_with_cli(variables)
        return 0

    print("ERROR: Not authenticated with Railway.")
    print("Option 1: Create a token at https://railway.com/account/tokens")
    print("  RAILWAY_TOKEN=your-token python scripts/push_railway_env.py")
    print("Option 2: Run `railway login` then rerun this script.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
