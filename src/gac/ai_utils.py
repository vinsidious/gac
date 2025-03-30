"""Utility functions for AI agents."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import aisuite as ai
import tiktoken

# Set up logging
logger = logging.getLogger(__name__)

# Default maximum output tokens
MAX_OUTPUT_TOKENS = 8192
# Default encoding to use as fallback
DEFAULT_ENCODING = "cl100k_base"


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


def chat(
    messages: List[Dict[str, str]],
    model: str = "anthropic:claude-3-5-sonnet-20240620",
    temperature: float = 1.0,
    save_conversation_path: Optional[str] = None,
    test_mode: bool = False,
    system: Optional[str] = None,
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
        **kwargs: Additional keyword arguments to pass to the AI provider.

    Returns:
        The model's response as a string.

    Raises:
        Exception: Any error that occurs during the API call.
    """
    if test_mode:
        return "test_response"

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

        # Initialize the aisuite client
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
        end_time = time.time()
        logger.debug(f"Received response in {end_time - start_time:.2f} seconds")

        # Save conversation history if requested
        if save_conversation_path:
            save_data = {
                "messages": messages,
                "response": reply,
                "model": model,
                "temperature": temperature,
                "time": end_time - start_time,
            }
            try:
                with open(save_conversation_path, "w") as f:
                    json.dump(save_data, f, indent=2)
                logger.debug(f"Saved conversation to {save_conversation_path}")
            except Exception as e:
                logger.warning(f"Failed to save conversation: {e}")

        return reply
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise
