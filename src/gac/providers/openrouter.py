"""OpenRouter API provider for gac."""

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
    """Generate commit message using OpenRouter API with retry logic."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise AIError.model_error("OPENROUTER_API_KEY environment variable not set")

    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    else:
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

    site_url = os.getenv("OPENROUTER_SITE_URL")
    if site_url:
        headers["HTTP-Referer"] = site_url

    site_name = os.getenv("OPENROUTER_SITE_NAME")
    if site_name:
        headers["X-Title"] = site_name

    return _make_request_with_retry(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        payload=payload,
        provider_name=f"OpenRouter {model}",
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
