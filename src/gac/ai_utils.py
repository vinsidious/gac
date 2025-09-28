"""Utilities for AI provider integration for gac.

This module provides utility functions that support the AI provider implementations.
"""

import logging
import os
import time
from functools import lru_cache
from typing import Any

import httpx
import tiktoken
from halo import Halo

from gac.constants import Utility
from gac.errors import AIError

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


def generate_with_retries(
    provider_funcs: dict,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
    quiet: bool = False,
) -> str:
    """Generate content with retry logic using direct API calls."""
    # Parse model string to determine provider and actual model
    if ":" not in model:
        raise AIError.model_error(f"Invalid model format. Expected 'provider:model', got '{model}'")

    provider, model_name = model.split(":", 1)

    # Validate provider
    supported_providers = ["anthropic", "openai", "groq", "cerebras", "ollama", "openrouter"]
    if provider not in supported_providers:
        raise AIError.model_error(f"Unsupported provider: {provider}. Supported providers: {supported_providers}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Set up spinner
    if quiet:
        spinner = None
    else:
        spinner = Halo(text=f"Generating commit message with {provider} {model_name}...", spinner="dots")
        spinner.start()

    last_exception = None

    for attempt in range(max_retries):
        try:
            if not quiet and attempt > 0:
                if spinner:
                    spinner.text = f"Retry {attempt + 1}/{max_retries} with {provider} {model_name}..."
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Call the appropriate provider function
            provider_func = provider_funcs.get(provider)
            if not provider_func:
                raise AIError.model_error(f"Provider function not found for: {provider}")

            content = provider_func(model=model_name, messages=messages, temperature=temperature, max_tokens=max_tokens)

            if spinner:
                spinner.succeed(f"Generated commit message with {provider} {model_name}")

            if content:
                return content.strip()
            else:
                raise AIError.model_error("Empty response from AI model")

        except Exception as e:
            last_exception = e
            error_type = _classify_error(str(e))

            if error_type in ["authentication", "model"]:
                # Don't retry these errors
                if spinner:
                    spinner.fail(f"Failed to generate commit message with {provider} {model_name}")
                raise AIError.authentication_error(f"AI generation failed: {str(e)}") from e

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet:
                    logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")

                if spinner:
                    for i in range(wait_time, 0, -1):
                        spinner.text = f"Retry {attempt + 1}/{max_retries} in {i}s..."
                        time.sleep(1)
                else:
                    time.sleep(wait_time)
            else:
                logger.error(f"AI generation failed after {max_retries} attempts: {str(e)}")

    if spinner:
        spinner.fail(f"Failed to generate commit message with {provider} {model_name}")

    # If we get here, all retries failed
    raise AIError.model_error(
        f"AI generation failed after {max_retries} attempts: {str(last_exception)}"
    ) from last_exception
