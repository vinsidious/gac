"""Groq API provider for gac."""

import logging
import os
import time

import httpx
from halo import Halo

from gac.ai_utils import _classify_error
from gac.constants import EnvDefaults
from gac.errors import AIError

logger = logging.getLogger(__name__)


def generate(
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
