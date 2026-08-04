import json

import requests

from config import OLLAMA_MODEL, OLLAMA_URL


def execute_ai_extractor(message: str) -> dict:
    if not message or not message.strip():
        raise ValueError("WhatsApp message is missing.")

    if not OLLAMA_URL:
        raise ValueError("OLLAMA_URL is missing in .env.")

    if not OLLAMA_MODEL:
        raise ValueError("OLLAMA_MODEL is missing in .env.")

    schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "phone": {
                "type": "string",
            },
            "address": {
                "type": "string",
            },
            "items": {
                "type": "string",
            },
        },
        "required": [
            "name",
            "phone",
            "address",
            "items",
        ],
        "additionalProperties": False,
    }

    system_prompt = """
You extract customer order information from WhatsApp messages.

Extract exactly these fields:
- name
- phone
- address
- items

Rules:
- Return every field as a string.
- Keep the phone number exactly as written.
- Combine multiple ordered products into one readable string.
- Do not invent missing information.
- If a value is missing, return an empty string.
- Do not add explanations.
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": schema,
        "options": {
            "temperature": 0,
        },
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise ValueError(
            f"Could not connect to Ollama: {error}"
        ) from error

    response_data = response.json()

    content = (
        response_data
        .get("message", {})
        .get("content", "")
        .strip()
    )

    if not content:
        raise ValueError(
            "Ollama returned an empty response."
        )

    try:
        extracted_data = json.loads(content)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Ollama returned invalid JSON: {content}"
        ) from error

    return {
        "name": str(
            extracted_data.get("name", "")
        ).strip(),
        "phone": str(
            extracted_data.get("phone", "")
        ).strip(),
        "address": str(
            extracted_data.get("address", "")
        ).strip(),
        "items": str(
            extracted_data.get("items", "")
        ).strip(),
    }