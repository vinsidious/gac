"""AI provider integration for gac.

This module provides core functionality for AI provider interaction.
It consolidates all AI-related functionality including token counting and commit message generation.
"""

import logging
import os
from functools import lru_cache
from typing import Any

import httpx
import tiktoken

from gac.ai_providers import (
    anthropic_generate,
    cerebras_generate,
    groq_generate,
    ollama_generate,
    openai_generate,
)
from gac.constants import EnvDefaults, Utility
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


def generate_commit_message(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate a commit message using direct API calls to AI providers.

    Args:
        model: The model to use in provider:model_name format (e.g., 'anthropic:claude-3-5-haiku-latest')
        prompt: Either a string prompt (for backward compatibility) or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0), lower values are more deterministic
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts

    Example:
        >>> model = "anthropic:claude-3-5-haiku-latest"
        >>> system_prompt, user_prompt = build_prompt("On branch main", "diff --git a/README.md b/README.md")
        >>> generate_commit_message(model, (system_prompt, user_prompt))
        'docs: Update README with installation instructions'
    """
    try:
        _, _ = model.split(":", 1)
    except ValueError as err:
        raise AIError.model_error(
            f"Invalid model format: {model}. Please use the format 'provider:model_name'."
        ) from err

    # Parse the model string to extract provider and model name
    try:
        provider, model_name = model.split(":", 1)
    except ValueError as err:
        raise AIError.model_error(
            f"Invalid model format: {model}. Please use the format 'provider:model_name'."
        ) from err

    # Route to the appropriate provider function
    if provider == "openai":
        return openai_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "anthropic":
        return anthropic_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "groq":
        return groq_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "cerebras":
        return cerebras_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "ollama":
        return ollama_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    else:
        raise AIError.model_error(f"Unsupported provider: {provider}")
