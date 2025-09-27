"""Utilities for AI provider integration for gac.

This module provides utility functions that support the AI provider implementations.
"""

import logging
import os
from functools import lru_cache
from typing import Any

import httpx
import tiktoken

from gac.constants import Utility

logger = logging.getLogger(__name__)


def count_tokens(content: str | list[dict[str, str]] | dict[str, Any], model: str) -> int:
    """Count tokens in content using the model's tokenizer."""
    text = extract_text_content(content)
    if not text:
        return 0

    if model.startswith("anthropic"):
        anthropic_tokens = anthropic_count_tokens(text, model)
        if anthropic_tokens is not None:
            return anthropic_tokens
        return len(text) // 4

    try:
        encoding = get_encoding(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return len(text) // 4


def anthropic_count_tokens(text: str, model: str) -> int | None:
    """Call Anthropic's token count endpoint and return the token usage.

    Returns the token count when successful, otherwise ``None`` so callers can
    fall back to a heuristic estimate.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.debug("ANTHROPIC_API_KEY not set; using heuristic token estimation for Anthropic model")
        return None

    model_name = model.split(":", 1)[1] if ":" in model else "claude-3-5-haiku-latest"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                    }
                ],
            }
        ],
    }

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages/count_tokens",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if "input_tokens" in data:
            return data["input_tokens"]
        if "usage" in data and "input_tokens" in data["usage"]:
            return data["usage"]["input_tokens"]

        logger.warning("Unexpected response format from Anthropic token count API: %s", data)
    except Exception as exc:
        logger.warning("Failed to retrieve Anthropic token count via HTTP: %s", exc)

    return None


def extract_text_content(content: str | list[dict[str, str]] | dict[str, Any]) -> str:
    """Extract text content from various input formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "\n".join(msg["content"] for msg in content if isinstance(msg, dict) and "content" in msg)
    elif isinstance(content, dict) and "content" in content:
        return content["content"]
    return ""


@lru_cache(maxsize=1)
def get_encoding(model: str) -> tiktoken.Encoding:
    """Get the appropriate encoding for a given model."""
    model_name = model.split(":")[-1] if ":" in model else model
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding(Utility.DEFAULT_ENCODING)


def _classify_error(error_str: str) -> str:
    """Classify error types based on error message content."""
    error_str = error_str.lower()

    if (
        "api key" in error_str
        or "unauthorized" in error_str
        or "authentication" in error_str
        or "invalid api key" in error_str
    ):
        return "authentication"
    elif "timeout" in error_str or "timed out" in error_str or "request timeout" in error_str:
        return "timeout"
    elif "rate limit" in error_str or "too many requests" in error_str or "rate limit exceeded" in error_str:
        return "rate_limit"
    elif "connect" in error_str or "network" in error_str or "network connection failed" in error_str:
        return "connection"
    elif "model" in error_str or "not found" in error_str or "model not found" in error_str:
        return "model"
    else:
        return "unknown"
