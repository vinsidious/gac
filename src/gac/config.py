"""Configuration settings for gac."""

import logging
import os
from typing import Any, Dict

# Set up logging
logger = logging.getLogger(__name__)

# Default provider models - used when GAC_PROVIDER is set without GAC_MODEL_NAME
PROVIDER_MODELS = {
    "anthropic": "claude-3-5-sonnet-20240620",  # Anthropic Claude
    "openai": "gpt-4o",  # OpenAI GPT-4o
    "groq": "llama3-70b-8192",  # Groq Llama 3
    "mistral": "mistral-large-latest",  # Mistral
    "aws": "meta.llama3-1-70b-instruct-v1:0",  # AWS Bedrock Llama 3
    "azure": "gpt-4",  # Azure OpenAI
    "google": "gemini-1.5-pro-001",  # Google Gemini
}

# Default settings
DEFAULT_CONFIG = {
    "model": "anthropic:claude-3-5-sonnet-20240620",  # Default model with provider prefix
    "use_formatting": True,  # Format Python files with black and isort
    "max_output_tokens": 8192,  # Maximum tokens in model output
}


def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or use defaults.

    The function checks for:
    - GAC_MODEL: Fully qualified model ID (provider:model)
    - GAC_PROVIDER: Provider name (used with default or custom model name)
    - GAC_MODEL_NAME: Specific model name for the chosen provider
    - GAC_USE_FORMATTING: Whether to format Python files
    - GAC_MAX_TOKENS: Maximum output tokens

    Returns:
        Dict: The configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Handle model selection with precedence:
    # 1. GAC_MODEL (full provider:model)
    # 2. GAC_PROVIDER + GAC_MODEL_NAME
    # 3. GAC_PROVIDER + default model for provider
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
    elif os.environ.get("GAC_PROVIDER"):
        provider = os.environ.get("GAC_PROVIDER")

        # Get model name (either custom or default for the provider)
        model_name = os.environ.get("GAC_MODEL_NAME")
        if not model_name:
            if provider in PROVIDER_MODELS:
                model_name = PROVIDER_MODELS[provider]
                logger.debug(f"Using default model for {provider}: {model_name}")
            else:
                logger.warning(
                    f"Unknown provider '{provider}'. Using default model from PROVIDER_MODELS."
                )
                provider = "anthropic"
                model_name = PROVIDER_MODELS[provider]

        config["model"] = f"{provider}:{model_name}"
        logger.debug(f"Using model: {config['model']}")

    # Handle formatting preference
    if os.environ.get("GAC_USE_FORMATTING") is not None:
        use_formatting = os.environ.get("GAC_USE_FORMATTING").lower() == "true"
        config["use_formatting"] = use_formatting
        logger.debug(f"Code formatting {'enabled' if use_formatting else 'disabled'}")

    # Handle token limit
    if os.environ.get("GAC_MAX_TOKENS"):
        try:
            max_tokens = int(os.environ.get("GAC_MAX_TOKENS"))
            config["max_output_tokens"] = max_tokens
            logger.debug(f"Using max tokens: {max_tokens}")
        except ValueError:
            logger.warning(
                f"Invalid GAC_MAX_TOKENS value: {os.environ.get('GAC_MAX_TOKENS')}. "
                f"Using default: {config['max_output_tokens']}"
            )

    return config
