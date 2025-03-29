"""Constants for gac configuration and settings."""

from typing import Any, Dict

# Default provider models - used when GAC_PROVIDER is set without GAC_MODEL_NAME
PROVIDER_MODELS: Dict[str, str] = {
    "anthropic": "claude-3-5-haiku-latest",
    "openai": "gpt-4o-mini",
    "groq": "llama3-70b-8192",
    "mistral": "mistral-large-latest",
    "aws": "meta.llama3-1-70b-instruct-v1:0",
    "azure": "gpt-4o-mini",
    "google": "gemini-2.0-flash",
}

# Default settings
DEFAULT_CONFIG: Dict[str, Any] = {
    "model": "anthropic:claude-3-5-haiku-latest",  # Default model with provider prefix
    "use_formatting": True,  # Format Python files with black and isort
    "max_output_tokens": 512,  # Maximum tokens in model output
    "max_input_tokens": 1000,  # Maximum tokens in input prompt
}

# Environment variable names
ENV_VARS: Dict[str, str] = {
    "model": "GAC_MODEL",
    "provider": "GAC_PROVIDER",
    "model_name": "GAC_MODEL_NAME",
    "use_formatting": "GAC_USE_FORMATTING",
    "max_output_tokens": "GAC_MAX_OUTPUT_TOKENS",
    "max_input_tokens": "GAC_MAX_INPUT_TOKENS",
}

# API key environment variables by provider
API_KEY_ENV_VARS: Dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}
