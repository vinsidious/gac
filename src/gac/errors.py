"""Error handling module for GAC."""

import logging
import sys
from typing import Callable, Optional, Type, TypeVar

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()
T = TypeVar("T")


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
    """Error related to AI provider or models."""

    exit_code = 4

    def __init__(self, message: str, error_type: str = "unknown", exit_code: Optional[int] = None):
        """Initialize an AIError with a specific error type.

        Args:
            message: The error message
            error_type: The type of AI error (from AI_ERROR_CODES keys)
            exit_code: Optional exit code to override the default
        """
        super().__init__(message, exit_code)
        self.error_type = error_type
        self.error_code = AI_ERROR_CODES.get(error_type, AI_ERROR_CODES["unknown"])

    @classmethod
    def authentication_error(cls, message: str) -> "AIError":
        """Create an authentication error."""
        return cls(message, error_type="authentication")

    @classmethod
    def connection_error(cls, message: str) -> "AIError":
        """Create a connection error."""
        return cls(message, error_type="connection")

    @classmethod
    def rate_limit_error(cls, message: str) -> "AIError":
        """Create a rate limit error."""
        return cls(message, error_type="rate_limit")

    @classmethod
    def timeout_error(cls, message: str) -> "AIError":
        """Create a timeout error."""
        return cls(message, error_type="timeout")

    @classmethod
    def model_error(cls, message: str) -> "AIError":
        """Create a model error."""
        return cls(message, error_type="model")


class FormattingError(GACError):
    """Error related to code formatting."""

    exit_code = 5


# Simplified error hierarchy - we use a single AIError class with error codes
# instead of multiple subclasses for better maintainability

# Error codes for AI errors
AI_ERROR_CODES = {
    "authentication": 401,  # Authentication failures
    "connection": 503,  # Connection issues
    "rate_limit": 429,  # Rate limits
    "timeout": 408,  # Timeouts
    "model": 400,  # Model-related errors
    "unknown": 500,  # Unknown errors
}


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

    # More specific remediation for AI errors based on error type
    if isinstance(error, AIError):
        if hasattr(error, "error_type"):
            if error.error_type == "authentication":
                return f"{base_message}\n\nPlease check your API key and ensure it is valid."
            elif error.error_type == "connection":
                return f"{base_message}\n\nPlease check your internet connection and try again."
            elif error.error_type == "rate_limit":
                return f"{base_message}\n\nYou've hit the rate limit for this AI provider. Please wait and try again later."
            elif error.error_type == "timeout":
                return f"{base_message}\n\nThe request timed out. Please try again or use a different model."
            elif error.error_type == "model":
                return f"{base_message}\n\nPlease check that the specified model exists and is available to you."
        return f"{base_message}\n\nPlease check your API key, model name, and internet connection."

    # Mapping of error types to remediation steps
    remediation_steps = {
        ConfigError: "Please check your configuration settings.",
        GitError: "Please ensure Git is installed and you're in a valid Git repository.",
        FormattingError: "Please check that required formatters are installed.",
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


def with_error_handling(
    error_type: Type[GACError], error_message: str, quiet: bool = False, exit_on_error: bool = True
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    A decorator that wraps a function with standardized error handling.

    Args:
        error_type: The specific error type to raise if an exception occurs
        error_message: The error message to use
        quiet: If True, suppress non-error output
        exit_on_error: If True, exit the program on error

    Returns:
        A decorator function that handles errors for the wrapped function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create a specific error with our message and the original error
                specific_error = error_type(f"{error_message}: {e}")
                # Handle the error using our standardized handler
                handle_error(specific_error, quiet=quiet, exit_program=exit_on_error)
                return None

        return wrapper

    return decorator
