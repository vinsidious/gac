"""
Compatibility module for AI utilities.

This module is maintained for backward compatibility with tests.
New code should use the ai.py module directly.
"""

import json
import logging
from typing import Dict, List, Optional

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

# Re-export from ai.py - these imports are needed for test patching
from gac.ai import count_tokens  # noqa
from gac.ai import generate_commit_message as _generate_commit_message
from gac.ai import get_encoding, is_ollama_available, is_ollama_model_available  # noqa
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

    # Call the new function
    response = _generate_commit_message(
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
