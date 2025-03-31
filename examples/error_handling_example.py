#!/usr/bin/env python3
"""
Example demonstrating how to use the standardized error handling in GAC.

This file provides practical examples of using the various error types and
handling functions defined in the errors module.
"""

import logging
import os
import subprocess
from typing import Any, Dict

# Import GAC error utilities
from gac.errors import (
    AIAuthenticationError,
    AIConnectionError,
    AIRateLimitError,
    ConfigError,
    GACError,
    GitError,
    convert_exception,
    format_error_for_user,
    handle_error,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_config(config: Dict[str, Any]) -> None:
    """
    Demonstrates how to use ConfigError for configuration validation.

    Args:
        config: Configuration dictionary to verify

    Raises:
        ConfigError: If configuration is invalid
    """
    # Check for required configuration items
    if not config.get("model"):
        raise ConfigError("Model not specified in configuration")

    # Check for API keys based on provider
    provider = config.get("provider", "").lower()
    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        raise ConfigError("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
    elif provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise ConfigError(
            "Anthropic API key not found. Set the ANTHROPIC_API_KEY environment variable."
        )


def check_git_repository() -> None:
    """
    Demonstrates how to use GitError for Git operations.

    Raises:
        GitError: If not in a valid Git repository
    """
    try:
        # Run git status to check if we're in a git repository
        subprocess.run(
            ["git", "status"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        # Convert the generic subprocess error to a GitError
        git_error = convert_exception(
            e,
            GitError,
            "Not in a valid Git repository. Please run this command in a Git repository.",
        )
        raise git_error


def simulate_api_call(status_code: int) -> None:
    """
    Demonstrates how to handle different API error cases.

    Args:
        status_code: HTTP status code to simulate

    Raises:
        Various AIProviderError subclasses based on the status code
    """
    if status_code == 401:
        raise AIAuthenticationError("Authentication failed: Invalid API key")
    elif status_code == 429:
        raise AIRateLimitError("Rate limit exceeded: Too many requests")
    elif status_code in (500, 502, 503, 504):
        raise AIConnectionError(f"Service unavailable: Error {status_code}")


def main() -> None:
    """Main function demonstrating error handling patterns."""

    # Example 1: Configuration validation with try/except
    try:
        # Simulate an empty configuration
        empty_config = {}
        verify_config(empty_config)
    except Exception as e:
        # Use handle_error for standardized error handling
        print("Example 1: Configuration validation")
        formatted_message = format_error_for_user(e)
        print(formatted_message)
        print("-" * 80)
        # Note: We're not calling handle_error() here because it would exit the program

    # Example 2: Git repository check with error conversion
    try:
        # Only runs if we're not in a git repository
        if not os.path.exists(".git"):
            check_git_repository()
    except Exception as e:
        print("Example 2: Git repository check")
        formatted_message = format_error_for_user(e)
        print(formatted_message)
        print("-" * 80)

    # Example 3: API error handling
    for status_code in [401, 429, 503]:
        try:
            print(f"Example 3: API call with status {status_code}")
            simulate_api_call(status_code)
        except Exception as e:
            formatted_message = format_error_for_user(e)
            print(formatted_message)
            print("-" * 80)

    # Example 4: Generic error conversion
    try:
        # Simulate a division by zero error
        _ = 1 / 0  # Using _ to indicate we're not using the result
    except Exception as e:
        # Convert the generic exception to a GAC-specific error
        gac_error = convert_exception(e, GACError, f"Calculation error: {e}")
        print("Example 4: Generic error conversion")
        formatted_message = format_error_for_user(gac_error)
        print(formatted_message)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # In a real command, we would use this pattern to handle any uncaught errors
        handle_error(e)
