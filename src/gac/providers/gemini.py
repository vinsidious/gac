"""Gemini AI provider implementation."""

import os
from typing import Any

import httpx

from gac.errors import AIError


def call_gemini_api(model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int) -> str:
    """Call Gemini API directly."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIError.authentication_error("GEMINI_API_KEY not found in environment variables")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # Build contents array following 2025 Gemini API format
    contents = []

    # Add system instruction as first content with role "system" (2025 format)
    for msg in messages:
        if msg["role"] == "system":
            contents.append({"role": "system", "parts": [{"text": msg["content"]}]})
            break

    # Add user and assistant messages
    for msg in messages:
        if msg["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            contents.append(
                {
                    "role": "model",  # Gemini uses "model" instead of "assistant"
                    "parts": [{"text": msg["content"]}],
                }
            )

    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }

    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        # Check for candidates and proper response structure
        if not response_data.get("candidates"):
            raise AIError.model_error("Gemini API response missing candidates")

        candidate = response_data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"] or not candidate["content"]["parts"]:
            raise AIError.model_error("Gemini API response has invalid content structure")

        content = candidate["content"]["parts"][0].get("text")
        if content is None or content == "":
            raise AIError.model_error("Gemini API response missing text content")

        return content
    except AIError:
        raise
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AIError.rate_limit_error(f"Gemini API rate limit exceeded: {e.response.text}") from e
        raise AIError.model_error(f"Gemini API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Gemini API request timed out: {str(e)}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Gemini API: {str(e)}") from e
