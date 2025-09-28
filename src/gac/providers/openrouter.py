"""OpenRouter API provider for gac."""

import os

import httpx

from gac.errors import AIError


def call_openrouter_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call OpenRouter API directly."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise AIError.model_error("OPENROUTER_API_KEY environment variable not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Add optional headers if environment variables are set
    site_url = os.getenv("OPENROUTER_SITE_URL")
    if site_url:
        headers["HTTP-Referer"] = site_url

    site_name = os.getenv("OPENROUTER_SITE_NAME")
    if site_name:
        headers["X-Title"] = site_name

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise AIError.model_error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling OpenRouter API: {str(e)}") from e
