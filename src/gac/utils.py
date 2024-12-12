"""Utility functions for AI agents."""

import json
import time
from typing import Dict, List, Optional, Union

import aisuite as ai
import anthropic

MAX_OUTPUT_TOKENS = 8192


def chat(
    messages: List[Dict[str, str]],
    model: str = "anthropic:claude-3-5-haiku-latest",
    temperature: float = 1.0,
    save_conversation_path: Optional[str] = None,
    test_mode: bool = False,
    *args,
    **kwargs,
) -> str:
    """Chat with the AI model."""
    if test_mode:
        return "test_response"

    try:
        start_time = time.time()

        # Handle Anthropic models directly
        if model and model.startswith("anthropic:"):
            model_name = model.replace("anthropic:", "")
            client = anthropic.Anthropic()
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                role = "assistant" if msg["role"] == "assistant" else "user"
                anthropic_messages.append({"role": role, "content": msg["content"]})

            response = client.messages.create(
                model=model_name,
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=MAX_OUTPUT_TOKENS,
            )
            reply = response.content[0].text
        else:
            # Use aisuite for other models
            client = ai.Client()
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                *args,
                **kwargs,
            )
            reply = response.choices[0].message.content.strip()

        if save_conversation_path:
            with open(save_conversation_path, "w") as f:
                json.dump(
                    {
                        "messages": messages,
                        "response": reply,
                        "model": model,
                        "temperature": temperature,
                        "time": time.time() - start_time,
                    },
                    f,
                    indent=2,
                )

        return reply
    except Exception as e:
        print(f"Error in chat: {e}")
        raise


def count_tokens(
    messages: Union[str, List[Dict[str, str]]],
    model: str,
    test_mode: bool = False,
) -> int:
    """Count tokens using Anthropic's API."""
    if ":" not in model:
        raise ValueError(f"Invalid model: {model}")
    provider, model_name = model.split(":")
    if not provider or not model_name:
        raise ValueError(f"Invalid model: {model}")

    if test_mode:
        return 10

    if provider == "anthropic":
        if isinstance(messages, str):
            system_message = "You are a helpful assistant."
            messages = [{"role": "user", "content": messages}]
        elif messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]
        else:
            system_message = "You are a helpful assistant."

        token_client = anthropic.Anthropic()
        response = token_client.beta.messages.count_tokens(
            betas=["token-counting-2024-11-01"],
            model=model_name,
            system=system_message,
            messages=messages,
        )
        return response.input_tokens
    else:
        raise ValueError(f"Cannot count tokens for model: {model}")
