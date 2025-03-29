"""Configuration settings for gac."""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Default provider models - used when GAC_PROVIDER is set without GAC_MODEL_NAME
PROVIDER_MODELS = {
    "anthropic": "claude-3-5-haiku-latest",
    "openai": "gpt-4o-mini",
    "groq": "llama3-70b-8192",
    "mistral": "mistral-large-latest",
    "aws": "meta.llama3-1-70b-instruct-v1:0",
    "azure": "gpt-4o-mini",
    "google": "gemini-2.0-flash",
}

# Default settings
DEFAULT_CONFIG = {
    "model": "anthropic:claude-3-5-haiku-latest",  # Default model with provider prefix
    "use_formatting": True,  # Format Python files with black and isort
    "max_output_tokens": 512,  # Maximum tokens in model output
}


def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or use defaults.

    The function checks for:
    - GAC_MODEL: Fully qualified model ID (provider:model)
    - GAC_USE_FORMATTING: Whether to format Python files
    - GAC_MAX_TOKENS: Maximum output tokens

    Returns:
        Dict: The configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Handle model selection with precedence:
    # 1. GAC_MODEL (full provider:model)
    if os.environ.get("GAC_MODEL"):
        model = os.environ.get("GAC_MODEL")
        # Ensure model has provider prefix
        if ":" not in model:
            logger.warning(
                f"GAC_MODEL '{model}' does not include provider prefix, assuming 'anthropic:'"
            )
            model = f"anthropic:{model}"
        config["model"] = model
        logger.debug(f"Using model from GAC_MODEL: {model}")

    # Handle formatting preference
    if os.environ.get("GAC_USE_FORMATTING") is not None:
        use_formatting = os.environ.get("GAC_USE_FORMATTING").lower() == "true"
        config["use_formatting"] = use_formatting
        logger.debug(f"Code formatting {'enabled' if use_formatting else 'disabled'}")

    # Handle token limit
    if os.environ.get("GAC_MAX_TOKENS"):
        try:
            # Remove any comments and whitespace
            max_tokens_value = os.environ.get("GAC_MAX_TOKENS").split("#", 1)[0].strip()
            max_tokens = int(max_tokens_value)
            if max_tokens < 1:
                raise ValueError("GAC_MAX_TOKENS must be a positive integer")
            config["max_output_tokens"] = max_tokens
            logger.debug(f"Using max tokens: {max_tokens}")
        except ValueError as e:
            logger.warning(
                f"Invalid GAC_MAX_TOKENS value: {max_tokens_value}. "
                f"Using default: {config['max_output_tokens']}. Error: {str(e)}"
            )

    return config


def validate_config() -> bool:
    """Validate current configuration."""
    config = get_config()

    # Check for required API keys
    provider = config.get("provider", "anthropic")
    api_key_env = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
    }

    if provider in api_key_env:
        if not os.environ.get(api_key_env[provider]):
            print(f"Warning: {api_key_env[provider]} is not set")
            return False

    # Check model format
    model = config.get("model")
    if model and ":" not in model:
        print(f"Warning: Model '{model}' should be in format 'provider:model_name'")
        return False

    return True
