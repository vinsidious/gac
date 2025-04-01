"""
Error handling module for GAC.

This module provides standardized error types and handling functions for consistent
error management across the application.
"""

import logging
import sys
from typing import Optional, Type

from rich.console import Console

# Set up logger
logger = logging.getLogger(__name__)

# Set up console for rich output
console = Console()


class GACError(Exception):
    """Base exception class for all GAC errors."""

    exit_code = 1  # Default exit code

    def __init__(self, message: str, exit_code: Optional[int] = None):
        """
        Initialize a new GACError.

        Args:
            message: The error message
            exit_code: Optional exit code to use when exiting the program
        """
        super().__init__(message)
        self.message = message
        if exit_code is not None:
            self.exit_code = exit_code


class ConfigError(GACError):
    """Error related to configuration issues."""

    exit_code = 2


class GitError(GACError):
    """Error related to Git operations."""

    exit_code = 3


class AIError(GACError):
    """Base class for AI-related errors."""

    exit_code = 4


class AIProviderError(AIError):
    """Base class for AI provider related errors."""

    exit_code = 4


class AIConnectionError(AIProviderError):
    """Error connecting to the AI provider."""

    exit_code = 5


class AIAuthenticationError(AIProviderError):
    """Authentication error with the AI provider."""

    exit_code = 6


class AIRateLimitError(AIProviderError):
    """Rate limit exceeded for the AI provider."""

    exit_code = 7


class AITimeoutError(AIProviderError):
    """Timeout when calling the AI provider."""

    exit_code = 8


class AIModelError(AIProviderError):
    """Error related to AI model specification."""

    exit_code = 9


class FormattingError(GACError):
    """Error related to code formatting."""

    exit_code = 10


class CacheError(GACError):
    """Error related to caching."""

    exit_code = 11


def handle_error(error: Exception, quiet: bool = False, exit_program: bool = True) -> None:
    """
    Handle an exception in a standardized way.

    Args:
        error: The exception to handle
        quiet: If True, suppress non-error output
        exit_program: If True, exit the program with the appropriate exit code
    """
    # Determine the error type
    if isinstance(error, GACError):
        exit_code = error.exit_code
        message = str(error)
    else:
        exit_code = 1
        message = f"Unexpected error: {str(error)}"

    # Log the error
    logger.error(message)

    # Print the error unless quiet mode is enabled
    if not quiet:
        console.print(f"❌ {message}", style="bold red")

    # Exit if requested
    if exit_program:
        sys.exit(exit_code)


def format_error_for_user(error: Exception) -> str:
    """
    Format an error message for display to the user.

    Args:
        error: The exception to format

    Returns:
        A user-friendly error message with remediation steps if applicable
    """
    base_message = str(error)

    # Mapping of error types to remediation steps
    remediation_steps = {
        AIConnectionError: "Please check your internet connection and try again.",
        AIAuthenticationError: "Please check your API key and ensure it's properly set.",
        AIRateLimitError: "Please wait a few minutes and try again.",
        AITimeoutError: "The AI service took too long to respond. Please try again later.",
        AIModelError: "Please check the model name or use a different model.",
        ConfigError: "Please check your configuration settings.",
        GitError: "Please ensure Git is installed and you're in a valid Git repository.",
        FormattingError: "Please check that required formatters are installed.",
        CacheError: "Try clearing the cache with --clear-cache and try again.",
    }

    # Generic remediation for unexpected errors
    if not any(isinstance(error, t) for t in remediation_steps.keys()):
        return f"{base_message}\n\nIf this issue persists, please report it as a bug."

    # Get remediation steps for the specific error type
    for error_class, steps in remediation_steps.items():
        if isinstance(error, error_class):
            return f"{base_message}\n\n{steps}"

    # Fallback (though we should never reach this)
    return base_message


def convert_exception(
    error: Exception, target_error_class: Type[GACError], message: Optional[str] = None
) -> GACError:
    """
    Convert a generic exception to a GAC-specific error type.

    Args:
        error: The original exception
        target_error_class: The GAC error class to convert to
        message: Optional custom message (uses str(error) if not provided)

    Returns:
        A new exception of the target_error_class
    """
    error_msg = message if message is not None else str(error)
    return target_error_class(error_msg)
