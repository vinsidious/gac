"""Configuration settings for gac.

This module handles all configuration-related functionality for the gac tool,
including loading environment variables, validating settings, and providing
default values.
"""

import logging
import os
from typing import Any, Dict, Optional

from .constants import (
    API_KEY_ENV_VARS,
    DEFAULT_CONFIG,
    ENV_VARS,
    PROVIDER_MODELS,
)

logger = logging.getLogger(__name__)

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

    Raises:
        ConfigError: If there's an issue with the configuration values
    """
    config = DEFAULT_CONFIG.copy()

    # Handle model selection with precedence
    if os.environ.get(ENV_VARS["model"]):
        model = os.environ[ENV_VARS["model"]]
        # Ensure model has provider prefix
        if ":" not in model:
            logger.warning(
                f"{ENV_VARS['model']} '{model}' does not include provider prefix, assuming 'anthropic:'"
            )
            model = f"anthropic:{model}"
        config["model"] = model
        logger.debug(f"Using model from {ENV_VARS['model']}: {model}")

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

    if os.environ.get(ENV_VARS["max_input_tokens"]):
        try:
            config["max_input_tokens"] = int(os.environ[ENV_VARS["max_input_tokens"]])
        except ValueError:
            logger.warning(f"Invalid {ENV_VARS['max_input_tokens']} value, using default")

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
        bool: True if configuration is valid, False otherwise
    """
    # Check for required API keys
    provider = config.get("provider", "anthropic")
    if provider not in API_KEY_ENV_VARS:
        raise ConfigError(f"Invalid provider: '{provider}'. Supported providers: {', '.join(API_KEY_ENV_VARS.keys())}")
    
    api_key_env = API_KEY_ENV_VARS[provider]
    if not os.environ.get(api_key_env):
        raise ConfigError(f"API key not set: {api_key_env}")

    # Check model format
    model = config.get("model")
    if not model:
        raise ConfigError("Model configuration is required")
    
    if ":" not in model:
        raise ConfigError(f"Invalid model format: '{model}'. Model string must be in format 'provider:model_name'")
    
    # Check token limits
    if config["max_output_tokens"] <= 0:
        raise ConfigError(f"max_output_tokens must be a positive integer (got {config['max_output_tokens']})")
    
    if config["max_input_tokens"] <= 0:
        raise ConfigError(f"max_input_tokens must be a positive integer (got {config['max_input_tokens']})")
    
    if config["max_input_tokens"] > 8192:
        logger.warning("max_input_tokens is set very high (>8192). This might cause issues with some models")
    
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
