"""Utility functions for AI agents."""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

import aisuite as ai
import tiktoken

from gac.cache import Cache, cached

# Try to import ollama, but don't fail if it's not installed
try:
    import ollama
except ImportError:
    ollama = None

# Set up logging
logger = logging.getLogger(__name__)

# Default maximum output tokens
MAX_OUTPUT_TOKENS = 8192
# Default encoding to use as fallback
DEFAULT_ENCODING = "cl100k_base"
# Default cache expiration time for LLM responses (12 hours)
LLM_CACHE_EXPIRATION = 12 * 60 * 60

# Create a global cache instance for LLM responses
llm_cache = Cache(expiration=LLM_CACHE_EXPIRATION)


class AIError(Exception):
    """Base class for AI-related errors."""

    pass


class APIConnectionError(AIError):
    """Error connecting to the AI provider's API."""

    pass


class APITimeoutError(AIError):
    """Timeout when calling the AI provider's API."""

    pass


class APIRateLimitError(AIError):
    """Rate limit exceeded for the AI provider's API."""

    pass


class APIAuthenticationError(AIError):
    """Authentication error with the AI provider's API."""

    pass


class APIUnsupportedModelError(AIError):
    """Model specified is not supported by the provider."""

    pass


class APIResponseError(AIError):
    """Error with the response from the AI provider's API."""

    pass


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


def extract_model_name(model: str) -> str:
    """
    Extract the model name from provider:model format.

    Args:
        model: The model identifier in the format "provider:model_name"

    Returns:
        The model name without the provider prefix
    """
    if ":" in model:
        # Split on the first colon to handle model names that may contain colons
        parts = model.split(":", 1)
        if len(parts) > 1:
            return parts[1]
    return model


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


@cached(cache_instance=llm_cache)
def chat(
    messages: List[Dict[str, str]],
    model: str = "anthropic:claude-3-5-sonnet-20240620",
    temperature: float = 1.0,
    save_conversation_path: Optional[str] = None,
    test_mode: bool = False,
    system: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    cache_skip: bool = False,
    show_spinner: bool = True,
    one_liner: bool = False,
    **kwargs,
) -> str:
    """
    Chat with an AI model using aisuite as a provider-agnostic interface.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys.
        model: The model identifier in the format "provider:model_name".
        temperature: Controls randomness in the response (0.0 to 1.0).
        save_conversation_path: Optional path to save the conversation history.
        test_mode: If True, returns a test response without making an API call.
        system: Optional system message to set the behavior of the assistant.
        max_retries: Maximum number of retries for transient errors.
        retry_delay: Delay between retries in seconds.
        cache_skip: If True, bypass cache and force a new API call.
        show_spinner: If True, show a spinner during API calls.
        one_liner: If True, ensure response is a single line (no newlines).
        **kwargs: Additional keyword arguments to pass to the AI provider.

    Returns:
        The model's response as a string.

    Raises:
        APIConnectionError: Error connecting to the API.
        APITimeoutError: Timeout when calling the API.
        APIRateLimitError: Rate limit exceeded.
        APIAuthenticationError: Authentication error.
        APIUnsupportedModelError: Model not supported.
        APIResponseError: Error with the API response.
        AIError: Other AI-related errors.
    """
    if test_mode:
        return "test_response"

    provider = model.split(":")[0] if ":" in model else "unknown"
    model_name = extract_model_name(model)
    retries = 0

    logger.debug(f"Chat function called with model: {model}")

    # Check for API key via environment variable
    api_key_env_var = f"{provider.upper()}_API_KEY"
    if os.environ.get(api_key_env_var):
        logger.debug(f"Found API key for {provider} from environment variable")
    else:
        logger.debug(f"No API key found in {api_key_env_var}, will need to be provided by client")

    # Check if provider is Ollama and verify it's available
    if provider.lower() == "ollama":
        if not is_ollama_available():
            raise APIConnectionError(
                "Ollama is not available. Make sure Ollama is installed and running locally."
            )
        if not is_ollama_model_available(model_name):
            raise APIUnsupportedModelError(
                f"Ollama model '{model_name}' is not available locally. "
                f"Pull it first with 'ollama pull {model_name}'."
            )

    # Import here to avoid circular imports
    from gac.utils import Spinner, print_error, print_success

    while retries <= max_retries:
        try:
            logger.debug(f"Starting chat with model {model}, temperature {temperature}")
            start_time = time.time()

            # Check for existing system message in the messages list
            has_system_message = messages and messages[0].get("role") == "system"

            # If system parameter is provided and there's no system message, add it
            if system and not has_system_message:
                system_message = {"role": "system", "content": system}
                messages = [system_message] + messages
                logger.debug(f"Added system message: {system}")

            # Create a spinner for the API call if enabled
            spinner = Spinner(f"Connecting to {provider} API")
            if show_spinner:
                spinner.start()

            try:
                # Update spinner message to show we're generating
                if show_spinner:
                    spinner.update_message(f"Generating with {model_name}")

                # Handle Ollama provider directly
                if provider.lower() == "ollama":
                    try:
                        formatted_messages = []
                        system_content = None
                        # Format messages for Ollama
                        for msg in messages:
                            if msg["role"] == "system":
                                # Ollama uses system as a parameter, not a message
                                system_content = msg["content"]
                            else:
                                formatted_messages.append(msg)

                        # Generate with Ollama
                        logger.debug(f"Generating with Ollama model {model_name}")
                        response = ollama.chat(
                            model=model_name,
                            messages=formatted_messages,
                            options={
                                "temperature": temperature,
                                **({"system": system_content} if system_content else {}),
                            },
                        )
                        reply = response["message"]["content"]
                    except Exception as e:
                        logger.error(f"Error generating with Ollama: {e}")
                        raise APIResponseError(f"Error with Ollama: {e}")
                else:
                    # Initialize the aisuite client for other providers
                    client = ai.Client()
                    # Make the request through aisuite's unified interface
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=kwargs.pop("max_tokens", MAX_OUTPUT_TOKENS),
                        **kwargs,
                    )
                    # Extract the response content
                    reply = response.choices[0].message.content

                # Update spinner to show we're processing the response
                if show_spinner:
                    spinner.update_message("Processing response")
            finally:
                # Always stop the spinner, even if there's an error
                if show_spinner:
                    spinner.stop()

            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.debug(f"Received response in {elapsed_time:.2f} seconds")

            # Show success message with response time
            if show_spinner:
                print_success(f"Response generated in {elapsed_time:.2f} seconds\n")

            # Save conversation history if requested
            if save_conversation_path:
                save_data = {
                    "messages": messages,
                    "response": reply,
                    "model": model,
                    "temperature": temperature,
                    "time": elapsed_time,
                }
                try:
                    with open(save_conversation_path, "w") as f:
                        json.dump(save_data, f, indent=2)
                    logger.debug(f"Saved conversation to {save_conversation_path}")
                except Exception as e:
                    logger.warning(f"Failed to save conversation: {e}")

            # If one_liner is True, ensure the response is a single line
            if one_liner:
                # Replace all newlines with spaces and remove excess spaces
                reply = " ".join(reply.replace("\n", " ").split())
                logger.debug("Converted response to a single line as requested")

            return reply

        # Handle different types of errors with specific responses
        except ai.APIConnectionError as e:
            err_msg = f"Connection error with {provider} API: {str(e)}"
            logger.error(err_msg)

            if show_spinner:
                print_error(f"Connection error with {provider} API")

            if retries < max_retries:
                wait_time = retry_delay * (2**retries)  # Exponential backoff
                logger.info(f"Retrying in {wait_time:.1f} seconds...")

                if show_spinner:
                    retry_spinner = Spinner(f"Retrying in {wait_time:.1f} seconds...")
                    retry_spinner.start()
                    time.sleep(wait_time)
                    retry_spinner.stop()
                else:
                    time.sleep(wait_time)

                retries += 1
            else:
                raise APIConnectionError(err_msg)

        except ai.APITimeoutError as e:
            err_msg = f"Timeout while waiting for {provider} API response: {str(e)}"
            logger.error(err_msg)

            if show_spinner:
                print_error(f"Timeout while waiting for {provider} API response")

            if retries < max_retries:
                wait_time = retry_delay * (2**retries)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")

                if show_spinner:
                    retry_spinner = Spinner(f"Retrying in {wait_time:.1f} seconds...")
                    retry_spinner.start()
                    time.sleep(wait_time)
                    retry_spinner.stop()
                else:
                    time.sleep(wait_time)

                retries += 1
            else:
                raise APITimeoutError(err_msg)

        except ai.APIRateLimitError as e:
            err_msg = f"Rate limit exceeded for {provider} API: {str(e)}. Try again later."
            logger.error(err_msg)

            if show_spinner:
                print_error(f"Rate limit exceeded for {provider} API")

            if retries < max_retries:
                wait_time = retry_delay * (2**retries) * 2  # Longer backoff for rate limits
                logger.info(f"Retrying in {wait_time:.1f} seconds...")

                if show_spinner:
                    retry_spinner = Spinner(f"Retrying in {wait_time:.1f} seconds...")
                    retry_spinner.start()
                    time.sleep(wait_time)
                    retry_spinner.stop()
                else:
                    time.sleep(wait_time)

                retries += 1
            else:
                raise APIRateLimitError(err_msg)

        except ai.APIAuthenticationError as e:
            err_msg = (
                f"Authentication error with {provider} API: {str(e)}. "
                f"Check your {provider.upper()}_API_KEY environment variable."
            )
            logger.error(err_msg)

            if show_spinner:
                print_error(f"Authentication error with {provider} API")

            raise APIAuthenticationError(err_msg)

        except ai.APINotFoundError as e:
            if "model" in str(e).lower():
                err_msg = f"Model '{model}' not supported by {provider}: {str(e)}"
                logger.error(err_msg)
                raise APIUnsupportedModelError(err_msg)
            else:
                err_msg = f"Resource not found on {provider} API: {str(e)}"
                logger.error(err_msg)
                raise APIResponseError(err_msg)

        except Exception as e:
            err_msg = f"Error with {provider} API: {str(e)}"
            logger.error(err_msg)

            if retries < max_retries and any(
                keyword in str(e).lower()
                for keyword in ["timeout", "connection", "network", "temporary", "retry"]
            ):
                wait_time = retry_delay * (2**retries)
                logger.info(f"Possible transient error, retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise AIError(err_msg)
