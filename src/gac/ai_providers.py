"""Direct HTTP API calls to AI providers using httpx.

This module provides functions for making direct HTTP API calls to various AI providers.
Each provider has its own function to generate commit messages using only httpx.
"""

import logging
import os
import time

import httpx
from halo import Halo

from gac.constants import EnvDefaults
from gac.errors import AIError

logger = logging.getLogger(__name__)


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


def anthropic_generate(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate commit message using Anthropic API with retry logic.

    Args:
        model: The model name (e.g., 'claude-3-5-haiku-latest', 'claude-3-opus-latest')
        prompt: Either a string prompt or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIError.model_error("ANTHROPIC_API_KEY environment variable not set")

    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "user", "content": user_prompt}]
        payload = {
            "model": model,
            "messages": messages,
            "system": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    else:
        # Backward compatibility: treat string as user prompt
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    return _make_request_with_retry(
        url="https://api.anthropic.com/v1/messages",
        headers=headers,
        payload=payload,
        provider_name=f"Anthropic {model}",
        max_retries=max_retries,
        quiet=quiet,
        response_parser=lambda r: r["content"][0]["text"],
    )


def cerebras_generate(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate commit message using Cerebras API with retry logic.

    Args:
        model: The model name (e.g., 'llama3.1-8b', 'llama3.1-70b')
        prompt: Either a string prompt or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts
    """
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise AIError.model_error("CEREBRAS_API_KEY environment variable not set")

    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    else:
        # Backward compatibility: treat string as user prompt
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    return _make_request_with_retry(
        url="https://api.cerebras.ai/v1/chat/completions",
        headers=headers,
        payload=payload,
        provider_name=f"Cerebras {model}",
        max_retries=max_retries,
        quiet=quiet,
        response_parser=lambda r: r["choices"][0]["message"]["content"],
    )


def groq_generate(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate commit message using Groq API with retry logic.

    Args:
        model: The model name (e.g., 'llama3-8b-8192', 'llama3-70b-8192')
        prompt: Either a string prompt or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AIError.model_error("GROQ_API_KEY environment variable not set")

    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    else:
        # Backward compatibility: treat string as user prompt
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    return _make_request_with_retry(
        url="https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        payload=payload,
        provider_name=f"Groq {model}",
        max_retries=max_retries,
        quiet=quiet,
        response_parser=lambda r: r["choices"][0]["message"]["content"],
    )


def ollama_generate(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate commit message using Ollama API with retry logic.

    Args:
        model: The model name (e.g., 'llama3', 'mistral')
        prompt: Either a string prompt or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response (note: Ollama uses 'num_predict')
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts
    """
    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    else:
        # Backward compatibility: treat string as user prompt
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    headers = {
        "Content-Type": "application/json",
    }

    # Ollama typically runs locally on port 11434
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    return _make_request_with_retry(
        url=f"{ollama_url}/api/chat",
        headers=headers,
        payload=payload,
        provider_name=f"Ollama {model}",
        max_retries=max_retries,
        quiet=quiet,
        response_parser=lambda r: r["message"]["content"],
    )


def openai_generate(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate commit message using OpenAI API with retry logic.

    Args:
        model: The model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        prompt: Either a string prompt or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIError.model_error("OPENAI_API_KEY environment variable not set")

    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    else:
        # Backward compatibility: treat string as user prompt
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    return _make_request_with_retry(
        url="https://api.openai.com/v1/chat/completions",
        headers=headers,
        payload=payload,
        provider_name=f"OpenAI {model}",
        max_retries=max_retries,
        quiet=quiet,
        response_parser=lambda r: r["choices"][0]["message"]["content"],
    )


def _make_request_with_retry(
    url: str,
    headers: dict,
    payload: dict,
    provider_name: str,
    max_retries: int,
    quiet: bool,
    response_parser: callable,
) -> str:
    """Make HTTP request with retry logic and common error handling."""
    if quiet:
        spinner = None
    else:
        spinner = Halo(text=f"Generating commit message with {provider_name}...", spinner="dots")
        spinner.start()

    last_error = None
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.debug(f"Trying with {provider_name} (attempt {retry_count + 1}/{max_retries})")

            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                response_data = response.json()
                message = response_parser(response_data)

                if spinner:
                    spinner.succeed(f"Generated commit message with {provider_name}")

                return message

        except Exception as e:
            last_error = e
            retry_count += 1

            if retry_count == max_retries:
                logger.warning(f"Error generating commit message: {e}. Giving up.")
                break

            wait_time = 2**retry_count
            logger.warning(f"Error generating commit message: {e}. Retrying in {wait_time}s...")
            if spinner:
                for i in range(wait_time, 0, -1):
                    spinner.text = f"Retry {retry_count}/{max_retries} in {i}s..."
                    time.sleep(1)
            else:
                time.sleep(wait_time)

    if spinner:
        spinner.fail(f"Failed to generate commit message with {provider_name}")

    error_type = _classify_error(str(last_error))
    raise AIError(
        f"Failed to generate commit message after {max_retries} attempts: {last_error}", error_type=error_type
    )
