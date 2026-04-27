import json

import httpx

from .config import settings


class DeepSeekError(RuntimeError):
    """Raised for DeepSeek API failures."""


def chat_completion(messages: list[dict]) -> str:
    if not settings.deepseek_api_key:
        raise DeepSeekError("Missing DEEPSEEK_API_KEY. Set it in your environment or .env file.")

    endpoint = f"{settings.deepseek_base_url.rstrip('/')}" + "/chat/completions"

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.2,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=90.0)
    except httpx.HTTPError as exc:
        raise DeepSeekError(f"DeepSeek request failed: {exc}") from exc

    if response.status_code >= 400:
        details = response.text
        try:
            details = json.dumps(response.json())
        except ValueError:
            pass
        raise DeepSeekError(f"DeepSeek error {response.status_code}: {details}")

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise DeepSeekError("Unexpected DeepSeek response format.") from exc

    return (content or "").strip()
