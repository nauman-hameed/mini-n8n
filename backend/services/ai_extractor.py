import json

import requests

from config import AI_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, OLLAMA_MODEL, OLLAMA_URL
from services.credentials_service import load_credentials

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "address": {"type": "string"},
        "items": {"type": "string"},
    },
    "required": ["name", "phone", "address", "items"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """
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


def get_ai_provider() -> str:
    stored = load_credentials()
    provider = str(
        stored.get("aiProvider", "")
    ).strip().lower()

    if provider in {"ollama", "gemini"}:
        return provider

    env_provider = str(AI_PROVIDER or "").strip().lower()

    if env_provider in {"ollama", "gemini"}:
        return env_provider

    return "ollama"


def execute_ai_extractor(message: str) -> dict:
    if not message or not message.strip():
        raise ValueError("WhatsApp message is missing.")

    provider = get_ai_provider()

    if provider == "gemini":
        extracted_data = extract_with_gemini(message)
    else:
        extracted_data = extract_with_ollama(message)

    return normalize_extracted_data(extracted_data)


def normalize_extracted_data(extracted_data: dict) -> dict:
    return {
        "name": str(extracted_data.get("name", "")).strip(),
        "phone": str(extracted_data.get("phone", "")).strip(),
        "address": str(extracted_data.get("address", "")).strip(),
        "items": str(extracted_data.get("items", "")).strip(),
    }


def extract_with_ollama(message: str) -> dict:
    if not OLLAMA_URL:
        raise ValueError("OLLAMA_URL is missing in .env.")

    if not OLLAMA_MODEL:
        raise ValueError("OLLAMA_MODEL is missing in .env.")

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": EXTRACTION_SCHEMA,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
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

    content = (
        response.json()
        .get("message", {})
        .get("content", "")
        .strip()
    )

    return parse_json_content(content, "Ollama")


def extract_with_gemini(message: str) -> dict:
    stored = load_credentials()
    api_key = str(
        stored.get("geminiApiKey", "")
    ).strip() or str(GEMINI_API_KEY or "").strip()

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. "
            "Add it in Credentials or set GEMINI_API_KEY."
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"{SYSTEM_PROMPT}\n\n"
                            f"WhatsApp message:\n{message}\n\n"
                            "Return only valid JSON."
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise ValueError(
            f"Could not connect to Gemini: {error}"
        ) from error

    response_data = response.json()

    content = (
        response_data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
        .strip()
    )

    return parse_json_content(content, "Gemini")


def parse_json_content(content: str, provider_name: str) -> dict:
    if not content:
        raise ValueError(
            f"{provider_name} returned an empty response."
        )

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{provider_name} returned invalid JSON: {content}"
        ) from error
