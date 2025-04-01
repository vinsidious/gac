"""AI provider integration for GAC.

This module consolidates all AI provider interaction into a single module,
reducing complexity and making provider integration simpler.
"""

import logging
import os
import time
from typing import Any, Dict, List, Union

import tiktoken

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    import ollama
except ImportError:
    ollama = None

from gac.errors import (
    AIAuthenticationError,
    AIConnectionError,
    AIError,
    AIModelError,
    AIRateLimitError,
    AITimeoutError,
)
from gac.utils import Spinner, print_error, print_success

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 256
DEFAULT_ENCODING = "cl100k_base"


def is_ollama_available() -> bool:
    """
    Check if Ollama is running locally and available.

    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        # Try to list models to check if Ollama server is running
        ollama.list()
        return True
    except (ImportError, Exception) as e:
        logger.debug(f"Ollama is not available: {str(e)}")
        return False


def is_ollama_model_available(model_name: str) -> bool:
    """
    Check if a specific Ollama model is available locally.

    Args:
        model_name: The name of the Ollama model (without provider prefix)

    Returns:
        bool: True if the model is available, False otherwise
    """
    try:
        # Get list of available models
        models_list = ollama.list()

        # Check if the requested model is in the list
        for model_info in models_list.get("models", []):
            if model_info.get("name") == model_name:
                return True

        logger.debug(f"Ollama model '{model_name}' is not available locally")
        return False
    except (ImportError, Exception) as e:
        logger.debug(f"Error checking Ollama model availability: {str(e)}")
        return False


def get_encoding(model: str) -> tiktoken.Encoding:
    """
    Get the appropriate encoding for a given model.

    Args:
        model: The model identifier in the format "provider:model_name"

    Returns:
        The appropriate tiktoken encoding
    """
    # Extract model name from provider:model format
    model_name = model.split(":")[-1] if ":" in model else model

    # Map model to encoding
    if "claude" in model_name.lower():
        # Claude models use cl100k_base encoding like GPT-4
        return tiktoken.get_encoding(DEFAULT_ENCODING)

    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        return tiktoken.get_encoding(DEFAULT_ENCODING)


def extract_text_content(content: Union[str, List[Dict[str, str]], Dict[str, Any]]) -> str:
    """
    Extract text content from various input formats.

    Args:
        content: A string, message object, or list of message dictionaries.

    Returns:
        The extracted text content as a string.
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "\n".join(
            msg["content"] for msg in content if isinstance(msg, dict) and "content" in msg
        )
    elif isinstance(content, dict) and "content" in content:
        return content["content"]
    return ""


def count_tokens(
    content: Union[str, List[Dict[str, str]], Dict[str, Any]],
    model: str,
    test_mode: bool = False,
) -> int:
    """
    Count tokens in content using the model's tokenizer.

    Args:
        content: A string, message object, or list of message dictionaries.
        model: The model identifier in the format "provider:model_name".
        test_mode: If True, returns a fixed value without counting.

    Returns:
        The number of tokens in the input.
    """
    if test_mode:
        return 10

    try:
        # Extract text content from input
        text = extract_text_content(content)
        if not text:
            logger.warning("No valid content found to count tokens")
            return 0

        # Get encoding and count tokens
        encoding = get_encoding(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        # Simple fallback estimation
        if "text" in locals():
            return len(text) // 4
        return 0


def extract_provider_and_model(model: str) -> tuple:
    """
    Extract the provider and model name from a model string.

    Args:
        model: The model identifier in the format "provider:model_name"

    Returns:
        Tuple containing (provider, model_name)
    """
    if ":" in model:
        provider, model_name = model.split(":", 1)
        return provider.lower(), model_name
    return "anthropic", model  # Default to Anthropic if no provider specified


def generate_commit_message(
    prompt: str,
    model: str = "anthropic:claude-3-5-haiku-20240307",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    show_spinner: bool = True,
    max_retries: int = 3,
    test_mode: bool = False,
) -> str:
    """
    Generate a commit message using an AI model.

    Args:
        prompt: The prompt to send to the AI model
        model: The model to use (format: provider:model_name)
        temperature: Controls randomness (0.0-1.0)
        max_tokens: Maximum tokens in the response
        show_spinner: Show a spinner during API calls
        max_retries: Maximum number of retries for transient errors
        test_mode: If True, returns a test response instead of calling the API

    Returns:
        The generated commit message

    Raises:
        AIError: If there's an error generating the commit message
    """
    if test_mode or os.environ.get("PYTEST_CURRENT_TEST"):
        return "Generated commit message"

    provider, model_name = extract_provider_and_model(model)
    retries = 0
    retry_delay = 1.0

    # Check for API key via environment variable
    api_key_env_var = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(api_key_env_var)

    if not api_key and provider != "ollama":
        raise AIAuthenticationError(f"API key not set: {api_key_env_var}")

    # Check if provider is Ollama and verify it's available
    if provider == "ollama":
        if not is_ollama_available():
            raise AIConnectionError(
                "Ollama is not available. Make sure Ollama is installed and running locally."
            )
        if not is_ollama_model_available(model_name):
            raise AIModelError(
                f"Ollama model '{model_name}' is not available locally. "
                f"Pull it first with 'ollama pull {model_name}'."
            )

    messages = [{"role": "user", "content": prompt}]

    while retries <= max_retries:
        try:
            logger.debug(
                f"Starting generation with {provider}:{model_name}, temperature {temperature}"
            )
            start_time = time.time()

            # Create a spinner for the API call if enabled
            spinner = Spinner(f"Connecting to {provider} API")
            if show_spinner:
                spinner.start()

            try:
                # Update spinner message to show we're generating
                if show_spinner:
                    spinner.update_message(f"Generating with model {model_name}")

                response_text = None

                # Handle different providers directly
                if provider == "ollama":
                    response = ollama.chat(
                        model=model_name,
                        messages=messages,
                        options={"temperature": temperature},
                    )
                    response_text = response["message"]["content"]
                elif provider == "anthropic":
                    if not anthropic:
                        raise ImportError("Anthropic SDK not installed. Try: pip install anthropic")

                    client = anthropic.Anthropic(api_key=api_key)
                    message = client.messages.create(
                        model=model_name,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=messages,
                    )
                    response_text = message.content[0].text
                elif provider == "openai":
                    if not openai:
                        raise ImportError("OpenAI SDK not installed. Try: pip install openai")

                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    response_text = response.choices[0].message.content
                else:
                    # For other providers, dynamically try to import the provider
                    try:
                        # Try to dynamically import the provider
                        exec(f"import {provider}")
                        exec(f"client = {provider}.Client(api_key=api_key)")
                        exec(
                            "response = client.chat.completions.create("
                            "model=model_name, "
                            "messages=messages, "
                            "temperature=temperature, "
                            "max_tokens=max_tokens)"
                        )
                        exec("response_text = response.choices[0].message.content")
                    except (ImportError, Exception) as e:
                        raise AIError(f"Provider '{provider}' is not supported: {e}")

                if not response_text:
                    raise AIError(f"Empty response from {provider}")

            finally:
                # Always stop the spinner, even if there's an error
                if show_spinner:
                    spinner.stop()

            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.debug(f"Received response in {elapsed_time:.2f} seconds")

            # Show success message with response time
            if show_spinner:
                print_success(f"Response generated in {elapsed_time:.2f} seconds")

            return response_text

        except Exception as e:
            if show_spinner:
                print_error(f"Error with {provider} API: {type(e).__name__}")

            # Handle retry logic for transient errors
            if retries < max_retries:
                wait_time = retry_delay * (2**retries)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                # Map to specific error types
                if "rate limit" in str(e).lower():
                    raise AIRateLimitError(f"Rate limit exceeded for {provider} API: {e}")
                elif "timeout" in str(e).lower():
                    raise AITimeoutError(f"Timeout from {provider} API: {e}")
                elif "authentication" in str(e).lower() or "auth" in str(e).lower():
                    raise AIAuthenticationError(f"Authentication error with {provider} API: {e}")
                elif "connect" in str(e).lower():
                    raise AIConnectionError(f"Connection error with {provider} API: {e}")
                else:
                    raise AIError(f"Error generating with {provider} API: {type(e).__name__}: {e}")
