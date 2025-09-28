"""AI provider integration for gac.

This module provides core functionality for AI provider interaction.
It consolidates all AI-related functionality including token counting and commit message generation.
"""

import logging

from gac.ai_utils import generate_with_retries
from gac.constants import EnvDefaults
from gac.errors import AIError
from gac.providers import (
    call_anthropic_api,
    call_cerebras_api,
    call_groq_api,
    call_ollama_api,
    call_openai_api,
    call_openrouter_api,
)

logger = logging.getLogger(__name__)


def generate_commit_message(
    model: str,
    prompt: str | tuple[str, str],
    temperature: float = EnvDefaults.TEMPERATURE,
    max_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS,
    max_retries: int = EnvDefaults.MAX_RETRIES,
    quiet: bool = False,
) -> str:
    """Generate a commit message using direct API calls to AI providers.

    Args:
        model: The model to use in provider:model_name format (e.g., 'anthropic:claude-3-5-haiku-latest')
        prompt: Either a string prompt (for backward compatibility) or tuple of (system_prompt, user_prompt)
        temperature: Controls randomness (0.0-1.0), lower values are more deterministic
        max_tokens: Maximum tokens in the response
        max_retries: Number of retry attempts if generation fails
        quiet: If True, suppress progress indicators

    Returns:
        A formatted commit message string

    Raises:
        AIError: If generation fails after max_retries attempts

    Example:
        >>> model = "anthropic:claude-3-5-haiku-latest"
        >>> system_prompt, user_prompt = build_prompt("On branch main", "diff --git a/README.md b/README.md")
        >>> generate_commit_message(model, (system_prompt, user_prompt))
        'docs: Update README with installation instructions'
    """
    # Handle both old (string) and new (tuple) prompt formats
    if isinstance(prompt, tuple):
        system_prompt, user_prompt = prompt
    else:
        # Backward compatibility: treat string as user prompt with no system prompt
        system_prompt = ""
        user_prompt = prompt

    # Provider functions mapping
    provider_funcs = {
        "anthropic": call_anthropic_api,
        "openai": call_openai_api,
        "groq": call_groq_api,
        "cerebras": call_cerebras_api,
        "ollama": call_ollama_api,
        "openrouter": call_openrouter_api,
    }

    # Generate the commit message using centralized retry logic
    try:
        return generate_with_retries(
            provider_funcs=provider_funcs,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            quiet=quiet,
        )
    except AIError:
        # Re-raise AIError exceptions as-is to preserve error classification
        raise
    except Exception as e:
        logger.error(f"Failed to generate commit message: {e}")
        raise AIError.model_error(f"Failed to generate commit message: {e}") from e
