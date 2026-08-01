import time
from typing import Any

import httpx

from config import (
    MODEL_MAX_RETRIES,
    MODEL_MAX_TOKENS,
    MODEL_RETRY_DELAY_SECONDS,
    MODEL_TIMEOUT_SECONDS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)


def chat_completion(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    images: list[dict[str, Any]] | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    base_url = base_url or OPENROUTER_BASE_URL
    api_key = api_key or OPENROUTER_API_KEY

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if "openrouter.ai" in base_url:
        headers["HTTP-Referer"] = "http://localhost:3000"
        headers["X-Title"] = "OncoAssignment Tumor Board"

    user_content: str | list[Any] = user_prompt
    if images:
        user_content = [{"type": "text", "text": user_prompt}] + images

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": MODEL_MAX_TOKENS,
        "temperature": 0.2,
    }

    response: httpx.Response | None = None
    for attempt in range(MODEL_MAX_RETRIES + 1):
        response = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=MODEL_TIMEOUT_SECONDS,
        )
        if response.status_code not in (429, 503) or attempt == MODEL_MAX_RETRIES:
            break
        retry_after_raw = response.headers.get("Retry-After", "")
        delay = (
            float(retry_after_raw)
            if retry_after_raw.isdigit()
            else MODEL_RETRY_DELAY_SECONDS
        )
        time.sleep(delay)

    if response is None:
        raise RuntimeError("Model request was not attempted.")
    if response.status_code >= 400:
        raise RuntimeError(
            f"Model API returned {response.status_code}: {response.text}"
        )

    data = response.json()
    message = data["choices"][0]["message"]
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    reasoning = message.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning
    return str(message)
