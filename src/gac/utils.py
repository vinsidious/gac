"""Utility functions for gac."""

import logging
import os
import subprocess
import sys
import threading
import time
from enum import Enum
from typing import List, Optional, Union

import click
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from gac.errors import GACError


def setup_logging(
    log_level: Union[int, str] = logging.WARNING, quiet: bool = False, force: bool = False
) -> None:
    """Configure logging for the application.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR)
        quiet: If True, only show error messages
        force: If True, use force=True when setting up basicConfig
    """
    # Convert string log level to int if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.WARNING)

    # Check for environment variable override
    log_level_env = os.environ.get("GAC_LOG_LEVEL")
    if log_level_env:
        log_level_env = log_level_env.upper()
        if log_level_env == "DEBUG":
            log_level = logging.DEBUG
        elif log_level_env == "INFO":
            log_level = logging.INFO
        elif log_level_env == "WARNING":
            log_level = logging.WARNING
        elif log_level_env == "ERROR":
            log_level = logging.ERROR

    # Use quiet mode if specified (only show errors)
    if quiet:
        log_level = logging.ERROR

    # Configure logging format based on level
    kwargs = {"force": force} if force else {}

    if log_level == logging.DEBUG:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            **kwargs,
        )
    else:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s", **kwargs)

    # Suppress excessive logs from libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Define a rich theme for colorful output
theme = Theme(
    {
        "success": "green bold",
        "info": "blue",
        "warning": "yellow",
        "error": "red bold",
        "header": "magenta",
    }
)

# Create a console for rich output
console = Console(theme=theme)

# Set up logger
logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7

# Bright versions
BRIGHT_BLACK = 8
BRIGHT_RED = 9
BRIGHT_GREEN = 10
BRIGHT_YELLOW = 11
BRIGHT_BLUE = 12
BRIGHT_MAGENTA = 13
BRIGHT_CYAN = 14
BRIGHT_WHITE = 15


class Color(Enum):
    """Color codes for terminal output."""

    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    BRIGHT_BLACK = 8
    BRIGHT_RED = 9
    BRIGHT_GREEN = 10
    BRIGHT_YELLOW = 11
    BRIGHT_BLUE = 12
    BRIGHT_MAGENTA = 13
    BRIGHT_CYAN = 14
    BRIGHT_WHITE = 15


def colorize(text: str, fg_color: Color = None, bg_color: Color = None, bold: bool = False) -> str:
    """
    Apply colors to text for terminal output.

    Args:
        text: The text to colorize
        fg_color: Foreground color from the Color enum
        bg_color: Background color from the Color enum
        bold: Whether to make the text bold

    Returns:
        The colorized text string
    """
    # Don't colorize if no colors are specified
    if fg_color is None and bg_color is None and not bold:
        return text

    # Use click's style function for coloring
    return click.style(
        text,
        fg=fg_color.name.lower() if fg_color else None,
        bg=bg_color.name.lower() if bg_color else None,
        bold=bold,
    )


def print_info(message: str) -> None:
    """Print an informational message with color."""
    console.print(message, style="info")


def print_success(message: str) -> None:
    """Print a success message with color."""
    console.print(message, style="success")


def print_warning(message: str) -> None:
    """Print a warning message with color."""
    console.print(message, style="warning")


def print_error(message: str) -> None:
    """Print an error message with color."""
    console.print(message, style="error")


def print_header(message: str) -> None:
    """
    Print a header message with color.

    Args:
        message: The message to print
    """
    console.print(Panel(message, style="header"))


def format_bordered_text(text: str, header: Optional[str] = None, add_border: bool = True) -> str:
    """
    Format text with a simple border using '===' style.

    Args:
        text: The text to format
        header: Optional header
        add_border: Whether to add header and border lines (default: True)

    Returns:
        Formatted text with or without border
    """
    # Split text into lines
    lines = text.split("\n")

    result = []

    # Add header if provided and border is enabled
    if header and add_border:
        # Calculate the length of the header, capped at 80 characters
        header_length = min(len(header), 80)

        # Add the header
        result.append(header)

        # Add the "=" underline
        result.append("=" * header_length)

    # Add content
    for line in lines:
        result.append(line)

    return "\n".join(result)


class Spinner:
    """A simple spinner to indicate progress."""

    def __init__(self, message: str = "Processing"):
        """
        Initialize the spinner.

        Args:
            message: The message to display with the spinner
        """
        self.message = message
        self.spinning = False
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_thread = None
        self.current_char_index = 0
        self.stop_event = threading.Event()
        self.message_lock = threading.Lock()  # Add lock for thread-safe message updates

    def _spin(self):
        """Spin the spinner in a separate thread."""
        last_message_length = 0

        while not self.stop_event.is_set():
            char = self.spinner_chars[self.current_char_index]

            # Get current message (thread-safe)
            with self.message_lock:
                current_message = self.message

            # Clear the previous line completely
            sys.stdout.write("\r" + " " * (last_message_length + 10))

            # Write new message
            display_text = f"\r{char} {current_message}..."
            sys.stdout.write(display_text)
            sys.stdout.flush()

            # Store length for next iteration
            last_message_length = len(display_text)

            self.current_char_index = (self.current_char_index + 1) % len(self.spinner_chars)
            time.sleep(0.1)

        # Clear the line when done
        sys.stdout.write("\r" + " " * (last_message_length + 10) + "\r")
        sys.stdout.flush()

    def update_message(self, new_message: str):
        """
        Update the spinner's message while it's running.

        Args:
            new_message: The new message to display
        """
        with self.message_lock:
            self.message = new_message

    def start(self):
        """Start the spinner."""
        if not self.spinning:
            self.spinning = True
            self.stop_event.clear()
            self.spinner_thread = threading.Thread(target=self._spin)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()

    def stop(self):
        """Stop the spinner."""
        if self.spinning:
            self.stop_event.set()
            if self.spinner_thread:
                self.spinner_thread.join()
            self.spinning = False

    def __enter__(self):
        """Start the spinner when used as a context manager."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the spinner when exiting the context manager."""
        self.stop()


def _simulate_git_command(command: List[str]) -> str:
    """
    Simulate git command execution for test mode.

    Args:
        command: Git command to simulate

    Returns:
        Simulated command output
    """
    logger.debug(f"TEST MODE: Simulating git command: {' '.join(command)}")

    # Simulate common git commands to avoid affecting the real repository
    if not command or command[0] != "git":
        return f"Simulated command: {' '.join(command)}"

    if command[1:2] == ["status"]:
        return "M src/gac/utils.py\nM tests/test_core.py\nM ROADMAP.md"
    elif command[1:2] == ["add"]:
        return f"Simulated adding files: {' '.join(command[2:])}"
    elif command[1:2] == ["commit"]:
        if "--allow-empty" in command:
            return "Simulated empty commit"
        return "Simulated commit"
    elif command[1:2] == ["push"]:
        return "Simulated push"
    elif command[1:2] == ["diff"]:
        return "Simulated diff content"
    elif command[:3] == ["git", "rev-parse", "--show-toplevel"]:
        return os.getcwd()  # Simulate project root
    else:
        # Generic simulation for other git commands
        return f"Simulated git command: {' '.join(command[1:])}"


def run_subprocess(
    command: List[str], silent: bool = False, timeout: int = 60, test_mode: bool = None
) -> str:
    """
    Run a subprocess command safely and return the output.

    Args:
        command: List of command and arguments
        silent: If True, suppress debug logging
        timeout: Timeout in seconds
        test_mode: Override for test mode detection

    Returns:
        The command output as a string
    """
    # If GAC_TEST_MODE environment variable is set, use test mode
    # Can be overridden by explicit test_mode parameter
    if test_mode is None:
        test_mode = os.environ.get("GAC_TEST_MODE") == "1"

    if test_mode:
        # Mock responses for git commands in test mode
        return _simulate_git_command(command)

    if not silent:
        logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # We'll handle errors manually
            timeout=timeout,
        )

        if result.returncode != 0:
            # Add stderr to the exception to help diagnose the issue
            error = subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )

            # Log the error for debugging
            if not silent:
                logger.debug(f"Command stderr: {result.stderr}")

            raise error

        return result.stdout
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        raise GACError(f"Command timed out: {' '.join(command)}") from e
    except Exception as e:
        if not silent:
            logger.debug(f"Command error: {e}")
        raise
