"""Utility functions for gac."""

import logging
import subprocess
import sys
import threading
import time
from enum import Enum
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

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
    """
    Print an informational message with color.

    Args:
        message: The message to print
    """
    console.print(f"ℹ️ {message}", style="info")


def print_success(message: str) -> None:
    """
    Print a success message with color.

    Args:
        message: The message to print
    """
    console.print(f"✅ {message}", style="success")


def print_warning(message: str) -> None:
    """
    Print a warning message with color.

    Args:
        message: The message to print
    """
    console.print(f"⚠️ {message}", style="warning")


def print_error(message: str) -> None:
    """
    Print an error message with color.

    Args:
        message: The message to print
    """
    console.print(f"❌ {message}", style="error")


def print_header(message: str) -> None:
    """
    Print a header message with color.

    Args:
        message: The message to print
    """
    console.print(Panel(message, style="header"))


def format_bordered_text(text: str, header: Optional[str] = None) -> str:
    """
    Format text with a simple border using '===' style.

    Args:
        text: The text to format
        header: Optional header

    Returns:
        Formatted text with border
    """
    # Split text into lines
    lines = text.split("\n")

    result = []

    # Add header if provided
    if header:
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


def run_subprocess(
    command: List[str], timeout: int = 60, silent: bool = False, test_mode: bool = False
) -> str:
    """
    Run a subprocess command and return its output.

    Args:
        command: Command to run as a list of strings
        timeout: Timeout in seconds
        silent: Whether to suppress error output
        test_mode: If True, prevents execution of git commands and returns simulated response

    Returns:
        Output from the command

    Raises:
        subprocess.CalledProcessError: If the command fails
    """
    import os

    # Check if we're in test mode (either explicit parameter or environment variable)
    # The _TESTING_PRESERVE_MOCK env var is set when tests need to use their own mocks
    is_test = test_mode or (
        os.environ.get("GAC_TEST_MODE") == "1" and os.environ.get("_TESTING_PRESERVE_MOCK") != "1"
    )

    # If we're in test mode and this is a git command, return simulated response
    if is_test and command and command[0] == "git":
        logger.debug(f"TEST MODE: Simulating git command: {' '.join(command)}")

        # Simulate common git commands to avoid affecting the real repository
        if command[1:2] == ["status"]:
            return "M src/gac/utils.py\nM tests/test_core.py\nM ROADMAP.md"
        elif command[1:2] == ["add"]:
            return f"Simulated adding files: {' '.join(command[2:])}"
        elif command[1:2] == ["commit"]:
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

    # Special case for git diff --quiet --cached --exit-code
    if command == ["git", "diff", "--quiet", "--cached", "--exit-code"]:
        # This command is expected to fail if there are changes
        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True,
            )
            # If it succeeds, there are no changes
            return ""
        except subprocess.CalledProcessError:
            # If it fails, there are changes
            return "Changes detected"

    logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )

        # Manually check for errors
        if result.returncode != 0:
            if not silent:
                logger.error(f"Error executing '{' '.join(command)}': {result.stderr}")
            raise subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )

        output = result.stdout

        if result.stderr and not silent:
            logger.debug(f"Command stderr: {result.stderr}")

        return output.strip()

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds: {' '.join(command)}"
        logger.error(error_msg)
        raise subprocess.TimeoutExpired(command, timeout, output=error_msg)
