"""Configuration settings for gac."""

import os
from typing import Dict

# Default settings
DEFAULT_CONFIG = {
    "model": "anthropic:claude-3-5-haiku-latest",
    "use_formatting": True,
    "max_output_tokens": 8192,
}


def get_config() -> Dict:
    """Load configuration from environment variables or use defaults."""
    config = DEFAULT_CONFIG.copy()

    # Override with environment variables
    if os.environ.get("GAC_MODEL"):
        model = os.environ.get("GAC_MODEL")
        # Ensure model has provider prefix
        if ":" not in model:
            model = f"anthropic:{model}"
        config["model"] = model

    if os.environ.get("GAC_USE_FORMATTING") is not None:
        config["use_formatting"] = os.environ.get("GAC_USE_FORMATTING").lower() == "true"

    if os.environ.get("GAC_MAX_TOKENS"):
        try:
            config["max_output_tokens"] = int(os.environ.get("GAC_MAX_TOKENS"))
        except ValueError:
            pass

    return config
