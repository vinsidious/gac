"""Configuration settings for gac.

This module handles all configuration-related functionality for the gac tool,
including loading environment variables, validating settings, and providing
default values.
"""

import logging
import os
from typing import Any, Dict, Optional

import questionary

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
    "ollama": "llama3.2",
}

# Default settings
DEFAULT_CONFIG = {
    "model": "anthropic:claude-3-5-haiku-latest",  # Default model with provider prefix
    "use_formatting": True,  # Whether to format code
    "max_output_tokens": 512,  # Maximum tokens in model output
    "warning_limit_input_tokens": 16000,  # Maximum tokens in input prompt
}

# Environment variable names
ENV_VARS = {
    "model": "GAC_MODEL",
    "provider": "GAC_PROVIDER",
    "model_name": "GAC_MODEL_NAME",
    "use_formatting": "GAC_USE_FORMATTING",
    "max_output_tokens": "GAC_MAX_OUTPUT_TOKENS",
    "warning_limit_input_tokens": "GAC_WARNING_LIMIT_INPUT_TOKENS",
}

# API key environment variables by provider
API_KEY_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "aws": "AWS_ACCESS_KEY_ID",  # AWS requires multiple credentials
    "azure": "AZURE_OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "ollama": None,  # Ollama doesn't require an API key for local models
}


class ConfigError(Exception):
    """Raised when there's an error with the configuration."""

    pass


def get_config() -> Dict[str, Any]:
    """Load configuration from environment variables or use defaults.

    The function checks for several environment variables and applies them
    to the configuration in the following order of precedence:
    1. GAC_MODEL (full provider:model)
    2. GAC_PROVIDER and GAC_MODEL_NAME (separate provider and model name)
    3. Default values from DEFAULT_CONFIG

    Returns:
        Dict[str, Any]: The configuration dictionary with all settings
    """
    config = DEFAULT_CONFIG.copy()

    # Debug logging of environment variables
    logger.debug("Loading configuration...")

    # Extract provider from current model setting
    current_model = config.get("model", "")
    if ":" in current_model:
        provider = current_model.split(":")[0]
        api_key_env = API_KEY_ENV_VARS.get(provider)
        if api_key_env:
            api_key = os.environ.get(api_key_env)
            if api_key:
                masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
                logger.debug(f"Found API key for {provider}: {masked_key}")
                # Store the API key in the config
                config["api_key"] = api_key
            else:
                logger.debug(f"No API key found for {provider} in {api_key_env}")

    # Handle model selection with precedence
    if os.environ.get(ENV_VARS["model"]):
        model = os.environ[ENV_VARS["model"]]
        # Ensure model has provider prefix
        if ":" not in model:
            logger.warning(
                f"{ENV_VARS['model']} '{model}' does not include provider prefix, "
                f"assuming 'anthropic:'"
            )
            model = f"anthropic:{model}"
        config["model"] = model
        logger.debug(f"Using model from {ENV_VARS['model']}: {model}")

        # Update API key based on the new model
        if ":" in model:
            provider = model.split(":")[0]
            api_key_env = API_KEY_ENV_VARS.get(provider)
            if api_key_env:
                api_key = os.environ.get(api_key_env)
                if api_key:
                    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
                    logger.debug(f"Found API key for {provider}: {masked_key}")
                    # Store the API key in the config
                    config["api_key"] = api_key
                else:
                    logger.debug(f"No API key found for {provider} in {api_key_env}")

    # Handle formatting preference
    if os.environ.get(ENV_VARS["use_formatting"]) is not None:
        use_formatting = os.environ[ENV_VARS["use_formatting"]].lower() == "true"
        config["use_formatting"] = use_formatting
        logger.debug(f"Code formatting {'enabled' if use_formatting else 'disabled'}")

    # Handle token limits
    if os.environ.get(ENV_VARS["max_output_tokens"]):
        try:
            config["max_output_tokens"] = int(os.environ[ENV_VARS["max_output_tokens"]])
        except ValueError:
            logger.warning(f"Invalid {ENV_VARS['max_output_tokens']} value, using default")

    if os.environ.get(ENV_VARS["warning_limit_input_tokens"]):
        try:
            config["warning_limit_input_tokens"] = int(
                os.environ[ENV_VARS["warning_limit_input_tokens"]]
            )
        except ValueError:
            logger.warning(f"Invalid {ENV_VARS['warning_limit_input_tokens']} value, using default")

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate the current configuration.

    Checks for:
    - Required API keys based on provider
    - Valid model format
    - Token limit ranges

    Args:
        config (Dict[str, Any]): The configuration dictionary to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ConfigError: If the configuration is invalid
    """
    # Extract provider from model
    model = config.get("model", "")
    if not model:
        raise ConfigError("Model configuration is required")

    if ":" not in model:
        raise ConfigError(
            f"Invalid model format: '{model}'. Model must be in format 'provider:model_name'"
        )

    provider = model.split(":")[0]

    # Check for required API keys
    if provider not in API_KEY_ENV_VARS:
        raise ConfigError(
            f"Invalid provider: '{provider}'. Supported: {', '.join(API_KEY_ENV_VARS.keys())}"
        )

    # Skip API key check for Ollama since it doesn't require one
    if provider != "ollama":
        api_key_env = API_KEY_ENV_VARS[provider]
        if not os.environ.get(api_key_env):
            raise ConfigError(f"API key not set: {api_key_env}")

    # Check token limits
    if config["max_output_tokens"] <= 0:
        raise ConfigError(f"max_output_tokens must be positive (got {config['max_output_tokens']})")

    if config["warning_limit_input_tokens"] <= 0:
        raise ConfigError(
            f"warning_limit_input_tokens must be positive "
            f"(got {config['warning_limit_input_tokens']})"
        )

    if config["warning_limit_input_tokens"] > 32000:
        logger.warning(
            "warning_limit_input_tokens is very high (>32000). "
            "This might cause issues with some models"
        )

    # Check formatting option
    use_formatting = config.get("use_formatting")
    if use_formatting not in [True, False]:
        raise ConfigError(f"use_formatting must be a boolean value (got {use_formatting})")

    return True


def get_provider_from_model(model: str) -> str:
    """Extract the provider name from a model string.

    Args:
        model (str): The model string in format 'provider:model_name'

    Returns:
        str: The provider name

    Raises:
        ValueError: If the model string is not in the correct format
    """
    if ":" not in model:
        raise ValueError("Model string must be in format 'provider:model_name'")
    return model.split(":")[0]


def run_config_wizard() -> Optional[Dict[str, Any]]:
    """Interactive configuration wizard for GAC.

    Guides the user through setting up their preferred AI provider and model.

    Returns:
        Optional[Dict[str, Any]]: Configured settings or None if wizard is cancelled
    """
    # Supported providers for this wizard
    supported_providers = ["anthropic", "openai", "groq", "mistral"]

    # Welcome message
    print("\n🚀 Git Auto Commit (GAC) Configuration Wizard")
    print("-------------------------------------------")

    # Provider selection
    provider = questionary.select(
        "Select your preferred AI provider:", choices=supported_providers
    ).ask()

    if not provider:
        print("Configuration wizard cancelled.")
        return None

    # Model selection based on provider
    models = {
        "anthropic": [
            "claude-3-5-haiku-latest",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ],
        "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        "groq": ["llama3-70b-8192", "mixtral-8x7b-32768"],
        "mistral": ["mistral-large-latest", "mistral-medium-latest"],
    }

    model_name = questionary.select(f"Select a {provider} model:", choices=models[provider]).ask()

    if not model_name:
        print("Configuration wizard cancelled.")
        return None

    # Formatting preference
    use_formatting = questionary.confirm(
        "Would you like to automatically format Python files?", default=True
    ).ask()

    # Construct full model configuration
    full_model = f"{provider}:{model_name}"

    # Confirm configuration
    print("\n📋 Configuration Summary:")
    print(f"Provider: {provider}")
    print(f"Model: {model_name}")
    print(f"Auto-formatting: {'Enabled' if use_formatting else 'Disabled'}")

    confirm = questionary.confirm("Do you want to save these settings?", default=True).ask()

    if not confirm:
        print("Configuration wizard cancelled.")
        return None

    # Create configuration dictionary
    config = {
        "model": full_model,
        "use_formatting": use_formatting,
        "max_output_tokens": DEFAULT_CONFIG["max_output_tokens"],
        "warning_limit_input_tokens": DEFAULT_CONFIG["warning_limit_input_tokens"],
    }

    try:
        validate_config(config)
        print("\n✅ Configuration validated successfully!")
        return config
    except ConfigError as e:
        print(f"❌ Configuration validation failed: {e}")
        return None
