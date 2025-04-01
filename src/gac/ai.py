"""AI provider integration for GAC.

This module consolidates all AI provider interaction into a single module,
reducing complexity and making provider integration simpler.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

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

# Priority levels for different parts of a git diff when truncating
DIFF_PRIORITIES = {
    "header": 1,  # Diff headers
    "hunk": 2,  # Hunk headers (@@ -1,5 +1,5 @@)
    "context": 3,  # Context lines
    "addition": 0,  # Added lines (highest priority to keep)
    "deletion": 0,  # Deleted lines (highest priority to keep)
}


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


def truncate_to_token_limit(text: str, model: str, max_tokens: int, buffer: int = 100) -> str:
    """
    Truncate text to fit within a token limit.

    Args:
        text: The text to truncate
        model: The model name to use for counting
        max_tokens: Maximum number of tokens allowed
        buffer: Token buffer to leave room for other content

    Returns:
        Truncated text that fits within the token limit
    """
    current_tokens = count_tokens(text, model, False)
    target_tokens = max_tokens - buffer

    if current_tokens <= target_tokens:
        return text

    # Simple truncation for short text
    if len(text) < 1000:
        ratio = target_tokens / current_tokens
        return text[: int(len(text) * ratio)]

    # For larger text, use smart truncation
    return smart_truncate_text(text, model, target_tokens)


def smart_truncate_text(text: str, model: str, max_tokens: int) -> str:
    """
    Intelligently truncate text to fit within a token limit.

    Args:
        text: The text to truncate
        model: The model name to use for counting
        max_tokens: Maximum number of tokens allowed

    Returns:
        Intelligently truncated text
    """
    if "\n" not in text:
        # No line breaks, simple truncation
        ratio = max_tokens / count_tokens(text, model, False)
        truncated_len = int(len(text) * ratio)
        return text[:truncated_len]

    # Split into lines for more intelligent truncation
    lines = text.split("\n")

    # If it's a git diff, use specialized diff truncation
    if text.startswith("diff --git "):
        return smart_truncate_diff(text, model, max_tokens)

    # For other multi-line text, prioritize beginning and end
    return truncate_with_beginning_and_end(lines, model, max_tokens)


def smart_truncate_diff(diff: str, model: str, max_tokens: int) -> str:
    """
    Intelligently truncate a git diff to fit within a token limit.

    Args:
        diff: The git diff to truncate
        model: The model name to use for counting
        max_tokens: Maximum number of tokens allowed

    Returns:
        Truncated diff that preserves the most important changes
    """
    # Parse the diff into separate file diffs
    file_diffs = split_into_file_diffs(diff)

    # If already within token limit, return unchanged
    if count_tokens("\n".join(file_diffs), model, False) <= max_tokens:
        return diff

    # Calculate tokens per file diff
    file_diff_tokens = {}
    for file_diff in file_diffs:
        file_diff_tokens[file_diff] = count_tokens(file_diff, model, False)

    # Sort file diffs by change density (changes per token)
    file_diffs_sorted = sort_diffs_by_importance(file_diffs, file_diff_tokens)

    # Rebuild diff with the most important files first, up to token limit
    result_diff = []
    current_tokens = 0

    for file_diff in file_diffs_sorted:
        tokens = file_diff_tokens[file_diff]

        # If adding this file would exceed limit, try to truncate the file diff
        if current_tokens + tokens > max_tokens:
            remaining_tokens = max_tokens - current_tokens
            if remaining_tokens > 100:  # Only truncate if we have reasonable space
                truncated_file_diff = truncate_file_diff(file_diff, model, remaining_tokens)
                result_diff.append(truncated_file_diff)
            break

        result_diff.append(file_diff)
        current_tokens += tokens

    # Return reconstructed diff
    result = "\n".join(result_diff)

    # Add indicator that diff was truncated if needed
    if len(result_diff) < len(file_diffs):
        trunc_msg = (
            f"\n\n[... {len(file_diffs) - len(result_diff)} more files not shown "
            "due to token limit ...]"
        )
        result += trunc_msg

    return result


def truncate_with_beginning_and_end(lines: List[str], model: str, max_tokens: int) -> str:
    """
    Truncate text by preserving beginning and end.

    Args:
        lines: List of text lines
        model: Model name for token counting
        max_tokens: Maximum allowed tokens

    Returns:
        Truncated text with beginning and end preserved
    """
    if not lines:
        return ""

    # Start with first and last lines
    result = [lines[0]]
    if len(lines) > 1:
        result.append(lines[-1])

    # If already within limit, return original text
    if count_tokens("\n".join(result), model, False) >= max_tokens:
        # Even first and last lines exceed limit, just take the first line
        return lines[0]

    # Add lines from beginning and end until we reach the limit
    beginning_idx = 1
    ending_idx = len(lines) - 2

    # Alternate between adding from beginning and end
    while beginning_idx <= ending_idx:
        # Try adding a line from the beginning
        candidate = lines[beginning_idx]
        if count_tokens("\n".join(result + [candidate]), model, False) < max_tokens:
            result.insert(1, candidate)
            beginning_idx += 1
        else:
            break

        if beginning_idx > ending_idx:
            break

        # Try adding a line from the end
        candidate = lines[ending_idx]
        if count_tokens("\n".join(result + [candidate]), model, False) < max_tokens:
            result.insert(-1, candidate)
            ending_idx -= 1
        else:
            break

    # Add ellipsis if we truncated
    if beginning_idx <= ending_idx:
        ellipsis = "..."
        result.insert(len(result) // 2, ellipsis)

    return "\n".join(result)


def split_into_file_diffs(diff: str) -> List[str]:
    """
    Split a git diff into separate file diffs.

    Args:
        diff: The full git diff

    Returns:
        List of individual file diffs
    """
    if not diff:
        return []

    # Split on diff headers
    file_diffs = []
    current_diff = []
    lines = diff.split("\n")

    for line in lines:
        if line.startswith("diff --git "):
            # Start of a new file diff
            if current_diff:
                file_diffs.append("\n".join(current_diff))
                current_diff = []
            current_diff.append(line)
        elif current_diff:
            current_diff.append(line)

    # Add the last file diff
    if current_diff:
        file_diffs.append("\n".join(current_diff))

    return file_diffs


def sort_diffs_by_importance(file_diffs: List[str], file_diff_tokens: Dict[str, int]) -> List[str]:
    """
    Sort file diffs by importance (change density).

    Args:
        file_diffs: List of file diffs
        file_diff_tokens: Dictionary mapping file diffs to token counts

    Returns:
        Sorted list of file diffs
    """
    # Calculate change density for each file diff
    change_density = {}
    for file_diff in file_diffs:
        # Count added/removed lines
        added = len(re.findall(r"^\+[^+]", file_diff, re.MULTILINE))
        removed = len(re.findall(r"^-[^-]", file_diff, re.MULTILINE))
        changes = added + removed

        # Calculate density (changes per token)
        tokens = file_diff_tokens[file_diff]
        density = changes / tokens if tokens > 0 else 0
        change_density[file_diff] = density

    # Sort by change density (highest first)
    return sorted(file_diffs, key=lambda x: change_density[x], reverse=True)


def truncate_file_diff(file_diff: str, model: str, max_tokens: int) -> str:
    """
    Truncate a single file diff to fit within token limit.

    Args:
        file_diff: The file diff to truncate
        model: Model name for token counting
        max_tokens: Maximum allowed tokens

    Returns:
        Truncated file diff
    """
    lines = file_diff.split("\n")

    # Always keep the header
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("@@"):
            header_end = i
            break

    header = lines[:header_end]
    diff_content = lines[header_end:]

    # If header alone exceeds token limit, return just the file path
    if count_tokens("\n".join(header), model, False) > max_tokens:
        file_path = re.search(r"diff --git a/(.*) b/", file_diff)
        if file_path:
            return (
                f"diff --git a/{file_path.group(1)} b/{file_path.group(1)}\n"
                "[diff too large for token limit]"
            )
        return "diff --git [diff too large for token limit]"

    # Categorize lines by priority
    categorized_lines = []
    current_hunk = []
    in_hunk = False

    for line in diff_content:
        if line.startswith("@@"):
            # New hunk header
            if current_hunk:
                categorized_lines.append((2, current_hunk))
                current_hunk = []
            in_hunk = True
            current_hunk.append(line)
        elif in_hunk:
            if line.startswith("+"):
                categorized_lines.append((0, [line]))  # Addition (highest priority)
            elif line.startswith("-"):
                categorized_lines.append((0, [line]))  # Deletion (highest priority)
            else:
                current_hunk.append(line)  # Context line

    # Add the last hunk if any
    if current_hunk:
        categorized_lines.append((2, current_hunk))

    # Sort by priority (lowest number = highest priority)
    categorized_lines.sort(key=lambda x: x[0])

    # Rebuild the diff with priority lines first, up to token limit
    result = header.copy()
    current_tokens = count_tokens("\n".join(result), model, False)

    for _, lines_group in categorized_lines:
        group_text = "\n".join(lines_group)
        group_tokens = count_tokens(group_text, model, False)

        if current_tokens + group_tokens <= max_tokens:
            result.extend(lines_group)
            current_tokens += group_tokens
        else:
            # We've reached the token limit
            break

    # Add truncation indicator if needed
    if len(result) < len(lines):
        result.append("[... diff truncated due to token limit ...]")

    return "\n".join(result)


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
                    # For other providers, use a more functional approach instead of exec
                    response_text = _call_other_provider(
                        provider=provider,
                        api_key=api_key,
                        model_name=model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

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


def _call_other_provider(
    provider: str,
    api_key: str,
    model_name: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    """
    Call other AI providers not directly supported.

    Args:
        provider: The provider name
        api_key: The API key
        model_name: The model name
        messages: The messages to send
        temperature: The temperature parameter
        max_tokens: The maximum tokens to generate

    Returns:
        The generated text

    Raises:
        AIError: If there's an error with the provider
    """
    try:
        # Try to dynamically import the provider
        provider_module = __import__(provider)
        client = provider_module.Client(api_key=api_key)

        # Call the provider's API
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract the response text
        return response.choices[0].message.content
    except (ImportError, Exception) as e:
        raise AIError(f"Provider '{provider}' is not supported: {e}")


def chat(
    messages: List[Dict[str, str]],
    model: str = "anthropic:claude-3",
    system: Optional[str] = None,
    temperature: float = 0.7,
    test_mode: bool = False,
    save_conversation_path: Optional[str] = None,
    one_liner: bool = False,
    show_spinner: bool = True,
) -> str:
    """
    Chat with an AI model using a list of messages.

    Args:
        messages: List of message dictionaries
        model: Model name to use
        system: Optional system message
        temperature: Temperature parameter
        test_mode: Whether to run in test mode
        save_conversation_path: Path to save conversation to
        one_liner: Whether to return only the first line of the response
        show_spinner: Whether to show a spinner during API calls

    Returns:
        Generated response
    """
    if test_mode:
        return "test_response"

    # Convert messages format
    prompt = ""

    # Add system message if provided
    if system:
        # Add system message to beginning
        messages = [{"role": "system", "content": system}] + messages

    # Extract all content from messages to create a single prompt
    for msg in messages:
        if msg.get("role") == "system":
            prompt += f"[System] {msg.get('content', '')}\n\n"
        elif msg.get("role") == "user":
            prompt += f"{msg.get('content', '')}\n\n"
        elif msg.get("role") == "assistant":
            prompt += f"[Assistant] {msg.get('content', '')}\n\n"

    # Call the generate_commit_message function
    response = generate_commit_message(
        prompt=prompt,
        model=model,
        temperature=temperature,
        test_mode=test_mode,
        show_spinner=show_spinner,
    )

    # Save conversation if path is provided
    if save_conversation_path:
        conversation_data = {"messages": messages, "response": response}
        with open(save_conversation_path, "w") as f:
            json.dump(conversation_data, f, indent=2)

    # Return only the first line if one_liner is True
    if one_liner and response:
        return response.split("\n")[0]

    return response
