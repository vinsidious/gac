"""
Compatibility module for AI utilities.

This module is maintained for backward compatibility with tests.
New code should use the ai.py module directly.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

# We need ollama for the patch imports to work in tests
try:
    import ollama  # noqa
except ImportError:
    ollama = None

# We need anthropic for the patch imports to work in tests
try:
    import anthropic  # noqa
except ImportError:
    # Create a dummy module for tests to patch
    class DummyModule:
        class Client:
            pass

    anthropic = DummyModule()

# Import error types directly from errors.py to avoid circular imports
from gac.errors import AIAuthenticationError as APIAuthenticationError  # noqa
from gac.errors import AIConnectionError as APIConnectionError  # noqa
from gac.errors import AIError  # noqa
from gac.errors import AIModelError as APIUnsupportedModelError  # noqa
from gac.errors import AIRateLimitError as APIRateLimitError  # noqa
from gac.errors import AITimeoutError as APITimeoutError  # noqa

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 256


# For backwards compatibility
ai = None  # This is needed for the test patches to work


# Forward declarations for functions imported from ai.py
# These are defined here to avoid circular imports
def count_tokens(
    content: Union[str, List[Dict[str, str]], Dict[str, Any]], model: str, test_mode: bool = False
) -> int:
    """Forward to gac.ai.count_tokens - import at runtime to avoid circular imports."""
    from gac.ai import count_tokens as ai_count_tokens

    return ai_count_tokens(content, model, test_mode)


def generate_commit_message(
    prompt: str,
    model: str = "anthropic:claude-3-5-haiku-20240307",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    show_spinner: bool = True,
    max_retries: int = 3,
    test_mode: bool = False,
) -> str:
    """Forward to gac.ai.generate_commit_message - import at runtime to avoid circular imports."""
    from gac.ai import generate_commit_message as ai_generate_commit_message

    return ai_generate_commit_message(
        prompt, model, temperature, max_tokens, show_spinner, max_retries, test_mode
    )


def get_encoding(model: str):
    """Forward to gac.ai.get_encoding - import at runtime to avoid circular imports."""
    from gac.ai import get_encoding as ai_get_encoding

    return ai_get_encoding(model)


def is_ollama_available() -> bool:
    """Forward to gac.ai.is_ollama_available - import at runtime to avoid circular imports."""
    from gac.ai import is_ollama_available as ai_is_ollama_available

    return ai_is_ollama_available()


def is_ollama_model_available(model_name: str) -> bool:
    """Forward to gac.ai.is_ollama_model_available - import at runtime to avoid circular imports."""
    from gac.ai import is_ollama_model_available as ai_is_ollama_model_available

    return ai_is_ollama_model_available(model_name)


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
    Backwards compatibility wrapper for generate_commit_message.

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
