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
    import ollama
except ImportError:
    ollama = None

# Re-export from ai.py
from gac.ai import count_tokens, extract_provider_and_model
from gac.ai import generate_commit_message as _generate_commit_message
from gac.ai import get_encoding, is_ollama_available, is_ollama_model_available
from gac.errors import AIAuthenticationError as APIAuthenticationError
from gac.errors import AIConnectionError as APIConnectionError
from gac.errors import AIError
from gac.errors import AIModelError as APIUnsupportedModelError
from gac.errors import AIRateLimitError as APIRateLimitError
from gac.errors import AITimeoutError as APITimeoutError

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 256

# Re-export with legacy names
extract_model_name = extract_provider_and_model

# For backwards compatibility
ai = None  # This is needed for the test patches to work


def chat(
    messages: List[Dict[str, str]],
    model: str = "anthropic:claude-3",
    system: Optional[str] = None,
    temperature: float = 0.7,
    test_mode: bool = False,
    save_conversation_path: Optional[str] = None,
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
        prompt=prompt, model=model, temperature=temperature, test_mode=test_mode
    )

    # Save conversation if path is provided
    if save_conversation_path:
        conversation_data = {"messages": messages, "response": response}
        with open(save_conversation_path, "w") as f:
            json.dump(conversation_data, f, indent=2)

    return response
