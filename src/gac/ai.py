"""AI provider integration for GAC.

This module consolidates all AI provider interaction into a single module,
reducing complexity and making provider integration simpler.
"""

import functools
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Union

import aisuite
import tiktoken
import unidiff
from halo import Halo

from gac.config import API_KEY_ENV_VARS
from gac.errors import AIError
from gac.utils import print_message

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 256
DEFAULT_ENCODING = "cl100k_base"

EXAMPLES = [
    "Generated commit message",
    "This is a generated commit message",
    "Another example of a generated commit message",
    "Yet another example of a generated commit message",
    "One more example of a generated commit message",
]


def is_ollama_available() -> bool:
    """Check if Ollama is available."""
    try:
        import ollama

        _ = ollama.list()
        return True
    except (ImportError, Exception) as e:
        logger.debug(f"Ollama is not available: {str(e)}")
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
) -> int:
    """
    Count tokens in content using the model's tokenizer.

    Args:
        content: A string, message object, or list of message dictionaries.
        model: The model identifier in the format "provider:model_name".

    Returns:
        The number of tokens in the input.
    """
    # Extract text content from input
    text = extract_text_content(content)
    if not text:
        logger.warning("No valid content found to count tokens")
        return 0

    try:
        encoding = get_encoding(model)
        token_count = len(encoding.encode(text))
        return token_count
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        # Simple fallback estimation
        token_count = len(text) // 4
        return token_count


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
    # If already under the token limit, return as is
    if count_tokens(text, model) <= max_tokens:
        return text

    # Simple case - no line breaks
    if "\n" not in text:
        ratio = max_tokens / count_tokens(text, model)
        truncated_len = int(len(text) * ratio)
        return text[:truncated_len]

    # If it's a git diff, use specialized treatment
    if text.startswith("diff --git "):
        return truncate_git_diff(text, model, max_tokens)

    # For other multi-line text, preserve beginning and end
    lines = text.split("\n")
    return truncate_with_beginning_and_end(lines, model, max_tokens)


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
    if count_tokens("\n".join(result), model) >= max_tokens:
        # Even first and last lines exceed limit, just take the first line
        return lines[0]

    # Add lines from beginning and end until we reach the limit
    beginning_idx = 1
    ending_idx = len(lines) - 2

    # Alternate between adding from beginning and end
    while beginning_idx <= ending_idx:
        # Try adding a line from the beginning
        candidate = lines[beginning_idx]
        if count_tokens("\n".join(result + [candidate]), model) < max_tokens:
            result.insert(1, candidate)
            beginning_idx += 1
        else:
            break

        if beginning_idx > ending_idx:
            break

        # Try adding a line from the end
        candidate = lines[ending_idx]
        if count_tokens("\n".join(result + [candidate]), model) < max_tokens:
            result.insert(-1, candidate)
            ending_idx -= 1
        else:
            break

    # Add ellipsis if we truncated
    if beginning_idx <= ending_idx:
        ellipsis = "..."
        result.insert(len(result) // 2, ellipsis)

    return "\n".join(result)


def truncate_git_diff(diff: str, model: str, max_tokens: int) -> str:
    """
    Truncate a git diff to fit within token limit using unidiff library.

    Args:
        diff: The git diff to truncate
        model: Model name for token counting
        max_tokens: Maximum allowed tokens

    Returns:
        Truncated git diff preserving the most important parts
    """
    # If already under token limit, return unchanged
    if count_tokens(diff, model) <= max_tokens:
        return diff

    try:
        # Parse the diff with unidiff
        patch_set = unidiff.PatchSet.from_string(diff)

        # If we have no files, return as is (unlikely)
        if not patch_set:
            return diff

        # Calculate importance for each file (changes per token ratio)
        file_importances = []
        for patched_file in patch_set:
            # Get statistics
            added = patched_file.added
            removed = patched_file.removed
            file_diff = str(patched_file)
            tokens = count_tokens(file_diff, model)

            # Calculate importance score - prioritize files with more changes relative to size
            importance = (added + removed) / tokens if tokens > 0 else 0
            file_importances.append((patched_file, importance, tokens, file_diff))

        # Sort by importance (most important first)
        file_importances.sort(key=lambda x: x[1], reverse=True)

        # Build result with most important files first, up to token limit
        result_diffs = []
        current_tokens = 0

        for patched_file, _, tokens, file_diff in file_importances:
            if current_tokens + tokens <= max_tokens:
                result_diffs.append(file_diff)
                current_tokens += tokens
            else:
                # Try to include a truncated version of this file if there's room
                remaining_tokens = max_tokens - current_tokens
                if remaining_tokens > 100:  # Only if we have meaningful space left
                    truncated_file = truncate_single_file_diff(file_diff, model, remaining_tokens)
                    result_diffs.append(truncated_file)
                break

        result = "".join(result_diffs).rstrip()

        # Add truncation indicator if needed
        if len(result_diffs) < len(patch_set):
            trunc_msg = f"\n\n[... {len(patch_set) - len(result_diffs)} more files not shown due to token limit ...]"
            result += trunc_msg

        return result

    except Exception as e:
        # Fallback to the file if unidiff parsing fails
        logger.debug(f"Error parsing diff with unidiff: {e}")
        # Use simple truncation as fallback
        ratio = max_tokens / count_tokens(diff, model)
        return diff[: int(len(diff) * ratio)]


def truncate_single_file_diff(file_diff: str, model: str, max_tokens: int) -> str:
    """
    Truncate a single file diff to fit within token limit.

    Args:
        file_diff: The file diff to truncate
        model: Model name for token counting
        max_tokens: Maximum allowed tokens

    Returns:
        Truncated file diff
    """
    # If already under token limit, return unchanged
    if count_tokens(file_diff, model) <= max_tokens:
        return file_diff

    try:
        # Parse with unidiff
        patched_file = unidiff.PatchSet.from_string(file_diff)[0]

        # Extract header (everything up to the first hunk)
        header_lines = []
        for line in file_diff.splitlines():
            header_lines.append(line)
            if line.startswith("@@"):
                break

        header = "\n".join(header_lines)

        # If header alone exceeds token limit, return just the file path
        if count_tokens(header, model) > max_tokens:
            file_path = f"{patched_file.source_file} → {patched_file.target_file}"
            return f"diff --git {file_path}\n[diff too large for token limit]"

        # Collect and prioritize hunks
        prioritized_hunks = []
        for hunk in patched_file:
            # Count significant changes in this hunk
            changes = sum(1 for line in hunk if line.is_added or line.is_removed)
            hunk_str = str(hunk)
            tokens = count_tokens(hunk_str, model)
            importance = changes / tokens if tokens > 0 else 0
            prioritized_hunks.append((hunk, importance, hunk_str, tokens))

        # Sort hunks by importance
        prioritized_hunks.sort(key=lambda x: x[1], reverse=True)

        # Start with the header
        result = [header]
        current_tokens = count_tokens(header, model)

        # Add hunks until we reach the token limit
        included_hunks = 0
        for _, _, hunk_str, tokens in prioritized_hunks:
            if current_tokens + tokens <= max_tokens:
                result.append(hunk_str)
                current_tokens += tokens
                included_hunks += 1
            else:
                break

        # Always add truncation indicator if we didn't include all hunks or if the output is shorter
        if len(result) < len(prioritized_hunks) + 1 or included_hunks < len(prioritized_hunks):
            result.append("[... diff truncated due to token limit ...]")

        return "\n".join(result)

    except Exception as e:
        # Fallback if unidiff parsing fails
        logger.debug(f"Error parsing single file diff with unidiff: {e}")

        # Simple fallback using regex to find and prioritize changed lines
        lines = file_diff.splitlines()

        # Find header end (first @@ line)
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("@@"):
                header_end = i
                break

        header = lines[: header_end + 1]
        content = lines[header_end + 1 :]

        # If header alone exceeds token limit, return just the file path
        if count_tokens("\n".join(header), model) > max_tokens:
            file_path = re.search(r"diff --git a/(.*) b/", file_diff)
            if file_path:
                return f"diff --git a/{file_path.group(1)} b/{file_path.group(1)}\n[diff too large for token limit]"
            return "diff --git [diff too large for token limit]"

        # Prioritize lines with changes
        prioritized_lines = []
        context_lines = []

        for line in content:
            if line.startswith("+") or line.startswith("-"):
                prioritized_lines.append((0, line))  # Changed lines - highest priority
            elif line.startswith("@@"):
                prioritized_lines.append((1, line))  # Hunk headers - medium priority
            else:
                context_lines.append((2, line))  # Context lines - lowest priority

        # Sort by priority and add context lines at the end
        prioritized_lines.sort(key=lambda x: x[0])
        prioritized_lines.extend(context_lines)

        # Build result with header and as many prioritized lines as fit
        result = header.copy()
        current_tokens = count_tokens("\n".join(result), model)
        included_lines = 0

        for _, line in prioritized_lines:
            line_tokens = count_tokens(line, model)
            if current_tokens + line_tokens <= max_tokens:
                result.append(line)
                current_tokens += line_tokens
                included_lines += 1
            else:
                break

        # Always add truncation indicator if we didn't include all content
        if included_lines < len(prioritized_lines):
            result.append("[... diff truncated due to token limit ...]")

        return "\n".join(result)


def _process_ai_response(response) -> str:
    """
    Extract and validate text content from AI response

    Args:
        response: The response object from the AI provider

    Returns:
        The extracted text content

    Raises:
        AIError: If the response is empty
    """
    response_text = response.choices[0].message.content
    if not response_text:
        raise AIError("Empty response from AI provider")
    return response_text


def handle_ai_errors(func):
    """
    Decorator for handling AI API errors with consistent retry logic

    Args:
        func: The function to wrap

    Returns:
        The wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = kwargs.get("max_retries", 3)
        retry_delay = 1.0
        provider_name = kwargs.get("provider_name", "AI provider")

        retries = 0
        while retries <= max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if kwargs.get("show_spinner", True):
                    print_message(
                        f"Error with {provider_name} API: {type(e).__name__}", level="error"
                    )

                # Handle retry logic for transient errors
                if retries < max_retries:
                    wait_time = retry_delay * (2**retries)
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    # Map common errors to AIError with descriptive message
                    err_str = str(e).lower()
                    if "rate limit" in err_str or "too many requests" in err_str:
                        raise AIError(f"Rate limit exceeded for {provider_name} API: {e}")
                    elif "timeout" in err_str:
                        raise AIError(f"Timeout from {provider_name} API: {e}")
                    elif "auth" in err_str or "key" in err_str or "credentials" in err_str:
                        raise AIError(f"Authentication error with {provider_name} API: {e}")
                    else:
                        raise AIError(f"Error with {provider_name} API: {e}")

    return wrapper


def generate_commit_message(
    prompt: str,
    model: str = "anthropic:claude-3-5-haiku-20240307",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    show_spinner: bool = True,
    max_retries: int = 3,
) -> str:
    """
    Generate a commit message using aisuite.

    Args:
        prompt: The prompt to send to the AI
        model: The model to use (format: provider:model_name)
        temperature: Temperature parameter (0.0 to 1.0) for randomness
        max_tokens: Maximum tokens in the generated response
        show_spinner: Whether to show a spinner during API calls
        max_retries: Maximum number of retries for failed API calls

    Returns:
        Generated commit message

    Raises:
        AIError: If there's an issue with the AI provider
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return random.choice(EXAMPLES)

    if not aisuite:
        raise AIError("aisuite is not installed. Try: pip install aisuite")

    provider_name, model_name = model.split(":", 1)

    api_key = None
    if provider_name.lower() != "ollama":
        api_key_env_var = API_KEY_ENV_VARS.get(provider_name.lower())
        if not api_key_env_var:
            logger.error(f"API key environment variable not defined for provider: {provider_name}")
            raise AIError(f"API key environment variable not defined for provider: {provider_name}")

        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            logger.error(f"API key not set: {api_key_env_var}")
            raise AIError(f"API key not set: {api_key_env_var}")

    if provider_name.lower() == "ollama" and not is_ollama_available():
        raise AIError("Ollama is not available. Make sure it's installed and running.")

    messages = [{"role": "user", "content": prompt}]

    if provider_name.lower() == "ollama":
        client = aisuite.Client(provider_configs={"ollama": {}})
    else:
        client = aisuite.Client(provider_configs={provider_name.lower(): {"api_key": api_key}})

    logger.debug(
        f"Starting generation with {provider_name}:{model_name}, temperature {temperature}"
    )
    start_time = time.time()

    @handle_ai_errors
    def make_api_call(
        client, model, messages, temperature, max_tokens, show_spinner, provider_name, model_name
    ):
        if show_spinner:
            with Halo(
                text=f"Connecting to {provider_name} API", spinner="dots", color="cyan"
            ) as spinner:
                spinner.text = f"Generating with model {model_name}"

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                return _process_ai_response(response)
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return _process_ai_response(response)

    # Make the API call with error handling
    response_text = make_api_call(
        client=client,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        show_spinner=show_spinner,
        provider_name=provider_name,
        model_name=model_name,
    )

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.debug(f"Received response in {elapsed_time:.2f} seconds")

    # Show notification message with response time
    if show_spinner:
        print_message(f"Response generated in {elapsed_time:.2f} seconds", "notification")

    return response_text
