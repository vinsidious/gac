"""Gemini AI provider implementation."""

import os
from typing import Any

import httpx

from gac.errors import AIError


def call_gemini_api(model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int) -> str:
    """Call Gemini API directly."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIError.model_error("GEMINI_API_KEY not found in environment variables")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    system_content = ""
    user_content = ""

    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        elif msg["role"] == "user":
            user_content = msg["content"]

    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }

    if system_content:
        payload["systemInstruction"] = {"parts": [{"text": system_content}]}

    try:
        response = httpx.post(url, params={"key": api_key}, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        content = response_data["candidates"][0]["content"]["parts"][0]["text"]
        if content is None or content == "":
            raise AIError.model_error("Gemini API response missing text content")
        return content
    except AIError:
        raise
    except httpx.HTTPStatusError as e:
        raise AIError.model_error(f"Gemini API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Gemini API: {str(e)}") from e
