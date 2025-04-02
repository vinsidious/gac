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


class FormattingError(GACError):
    """Error related to code formatting."""

    exit_code = 5


class AIAuthenticationError(AIError):
    """Error related to AI authentication failures."""

    pass


class AIConnectionError(AIError):
    """Error related to AI connection failures."""

    pass


class AIRateLimitError(AIError):
    """Error related to AI rate limit exceeded."""

    pass


class AITimeoutError(AIError):
    """Error related to AI API timeouts."""

    pass


class AIModelError(AIError):
    """Error related to unsupported or invalid AI models."""

    pass


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
        AIError: "Please check your API key, model name, and internet connection.",
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


def safely_execute(
    operation: Callable[..., T],
    error_message: str,
    error_type: Type[GACError] = GACError,
    default_value: Optional[T] = None,
    quiet: bool = False,
    exit_on_error: bool = False,
) -> Optional[T]:
    """
    Execute a function with standardized error handling.

    Args:
        operation: The function to execute
        error_message: The error message to use if an exception occurs
        error_type: The specific error type to raise
        default_value: The value to return if an exception occurs
        quiet: If True, suppress non-error output
        exit_on_error: If True, exit the program on error

    Returns:
        The return value of the operation, or default_value if an exception occurs
    """
    try:
        return operation()
    except Exception as e:
        # Create a specific error with our message and the original error
        specific_error = error_type(f"{error_message}: {e}")
        # Handle the error using our standardized handler
        handle_error(specific_error, quiet=quiet, exit_program=exit_on_error)
        return default_value
