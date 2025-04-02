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
    """Configure logging for the application."""
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.WARNING)

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

    if quiet:
        log_level = logging.ERROR

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

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


theme = Theme(
    {
        "success": "green bold",
        "info": "blue",
        "warning": "yellow",
        "error": "red bold",
        "header": "magenta",
    }
)

console = Console(theme=theme)
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
    """Apply colors to text for terminal output."""
    if fg_color is None and bg_color is None and not bold:
        return text

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
    """Print a header message with color."""
    console.print(Panel(message, style="header"))


def format_bordered_text(text: str, header: Optional[str] = None, add_border: bool = True) -> str:
    """Format text with a simple border using '===' style."""
    lines = text.split("\n")
    result = []

    if header and add_border:
        header_length = min(len(header), 80)
        result.append(header)
        result.append("=" * header_length)

    for line in lines:
        result.append(line)

    return "\n".join(result)


class Spinner:
    """A simple spinner to indicate progress."""

    def __init__(self, message: str = "Processing"):
        """Initialize the spinner."""
        self.message = message
        self.spinning = False
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_thread = None
        self.current_char_index = 0
        self.stop_event = threading.Event()
        self.message_lock = threading.Lock()

    def _spin(self):
        """Spin the spinner in a separate thread."""
        last_message_length = 0

        while not self.stop_event.is_set():
            char = self.spinner_chars[self.current_char_index]

            with self.message_lock:
                current_message = self.message

            sys.stdout.write("\r" + " " * (last_message_length + 10))

            display_text = f"\r{char} {current_message}..."
            sys.stdout.write(display_text)
            sys.stdout.flush()

            last_message_length = len(display_text)

            self.current_char_index = (self.current_char_index + 1) % len(self.spinner_chars)
            time.sleep(0.1)

        sys.stdout.write("\r" + " " * (last_message_length + 10) + "\r")
        sys.stdout.flush()

    def update_message(self, new_message: str):
        """Update the spinner's message while it's running."""
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


def _simulate_git_command(command: List[str]) -> str:
    """Simulate git command execution for test mode."""
    logger.debug(f"TEST MODE: Simulating git command: {' '.join(command)}")

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
        return os.getcwd()
    else:
        return f"Simulated git command: {' '.join(command[1:])}"


def run_subprocess(
    command: List[str],
    silent: bool = False,
    timeout: int = 60,
    test_mode: bool = None,
    check: bool = True,
    strip_output: bool = True,
    raise_on_error: bool = True,
) -> str:
    """Run a subprocess command safely and return the output.

    Args:
        command: List of command arguments
        silent: If True, suppress debug logging
        timeout: Command timeout in seconds
        test_mode: If True, simulate command execution (for testing)
        check: Whether to check return code (for compatibility)
        strip_output: Whether to strip whitespace from output
        raise_on_error: Whether to raise an exception on error

    Returns:
        Command output as string

    Raises:
        GACError: If the command times out
        subprocess.CalledProcessError: If the command fails and raise_on_error is True
    """
    if test_mode is None:
        test_mode = os.environ.get("GAC_TEST_MODE") == "1"

    if test_mode:
        return _simulate_git_command(command)

    if not silent:
        logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )

        if result.returncode != 0 and (check or raise_on_error):
            if not silent:
                logger.debug(f"Command stderr: {result.stderr}")

            error = subprocess.CalledProcessError(
                result.returncode, command, result.stdout, result.stderr
            )
            raise error

        output = result.stdout
        if strip_output:
            output = output.strip()

        return output
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        raise GACError(f"Command timed out: {' '.join(command)}") from e
    except subprocess.CalledProcessError as e:
        if not silent:
            logger.error(f"Command failed: {e.stderr.strip() if hasattr(e, 'stderr') else str(e)}")
        if raise_on_error:
            raise
        return ""
    except Exception as e:
        if not silent:
            logger.debug(f"Command error: {e}")
        if raise_on_error:
            raise
        return ""
