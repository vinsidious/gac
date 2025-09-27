"""AI provider integration for gac.

This module provides core functionality for AI provider interaction.
It consolidates all AI-related functionality including token counting and commit message generation.
"""

import logging

from gac.constants import EnvDefaults
from gac.errors import AIError
from gac.providers.anthropic import generate as anthropic_generate
from gac.providers.cerebras import generate as cerebras_generate
from gac.providers.groq import generate as groq_generate
from gac.providers.ollama import generate as ollama_generate
from gac.providers.openai import generate as openai_generate
from gac.providers.openrouter import generate as openrouter_generate

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
    try:
        _, _ = model.split(":", 1)
    except ValueError as err:
        raise AIError.model_error(
            f"Invalid model format: {model}. Please use the format 'provider:model_name'."
        ) from err

    # Parse the model string to extract provider and model name
    try:
        provider, model_name = model.split(":", 1)
    except ValueError as err:
        raise AIError.model_error(
            f"Invalid model format: {model}. Please use the format 'provider:model_name'."
        ) from err

    # Route to the appropriate provider function
    if provider == "openai":
        return openai_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "anthropic":
        return anthropic_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "groq":
        return groq_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "cerebras":
        return cerebras_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "ollama":
        return ollama_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    elif provider == "openrouter":
        return openrouter_generate(model_name, prompt, temperature, max_tokens, max_retries, quiet)
    else:
        raise AIError.model_error(f"Unsupported provider: {provider}")
